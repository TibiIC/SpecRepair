"""
Violation traces produced by running a real controller, not by ASP.

The third experimental setup. The first two manufacture their traces
symbolically: ASP is asked for a trace violating some assumption, and it obliges
- but it constrains the system's moves only by the specification, so the trace
can contain system behaviour no synthesised controller would ever produce. A
repair learned against such a trace is a repair against a fiction.

Here the system half of every trace is genuine controller output:

1. Synthesise a controller from the specification.
2. Run it for N steps against an environment that **respects the assumptions**,
   so the prefix is behaviour the controller was designed for.
3. From step N+1 the environment stops respecting them and acts at random, until
   it violates an assumption.
4. The run so far is the violation trace.

**The environment side is ours.** Syntech ships controller execution
(`ControllerExecutor` in spectra-executor, used here) but nothing that drives an
environment: `getAllLegalSystemOutputs` has no counterpart for inputs, and
spectra-sim's examples each hand-roll their own environment rather than sharing
one. So "does this input respect the assumptions" is answered with this
project's own ASP violation check - the same one the repair, the preconditions
and the oracle all use, which keeps one definition of "violates an assumption"
across the whole pipeline rather than inventing a second.
"""
import os
import random
import shutil
import tempfile
from itertools import product
from typing import Dict, List, Optional, Tuple

import jpype

from spec_repair.components.new_spec_encoder import (
    NewSpecEncoder, get_violated_expression_names_of_type)
from spec_repair.enums import Learning
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.wrappers.asp_wrappers import get_violations
from spec_repair.wrappers.spectra_toolbox import synthesise_controller

# How many random environment inputs to try per step before giving up on finding
# an assumption-respecting one. The input space is exponential in the number of
# environment variables, so it is sampled rather than enumerated once it is
# large - exhaustive search is only worth it while it is cheap.
MAX_CANDIDATES_PER_STEP = 64
EXHAUSTIVE_LIMIT = 64


class ControllerTraceError(RuntimeError):
    """The controller could not be built or run for this specification."""


def _spec_variable_names(spec: SpectraSpecification) -> List[str]:
    """
    The specification's own variables.

    A synthesised controller carries auxiliary state of its own - `Zn`, and a
    `PREV_aux_<n>` per PREV subformula - which is an artefact of synthesis and
    means nothing to the specification. Emitting it into a trace would produce
    `holds_at` atoms for variables the repair has never heard of.
    """
    return sorted(atom.name for atom in spec.get_atoms())


def _trace_lines(states: List[Dict[str, str]], variables: List[str],
                 trace_name: str) -> List[str]:
    """Render states as the `holds_at`/`not_holds_at` form the repair reads."""
    out: List[str] = []
    for t, state in enumerate(states):
        for var in variables:
            value = state.get(var, "false")
            prefix = "" if str(value).lower() == "true" else "not_"
            out.append(f"{prefix}holds_at({var},{t},{trace_name}).\n")
        out.append("\n")
    return out


def _violated_assumptions(spec: SpectraSpecification, trace: List[str]) -> List[str]:
    """Which assumptions this trace violates, by the project's own definition."""
    asp = NewSpecEncoder.encode_ASP(spec, trace, [])
    violations = get_violations(asp, exp_type=Learning.ASSUMPTION_WEAKENING.exp_type())
    if not violations:
        return []
    return get_violated_expression_names_of_type(violations, "assumption")


def _non_initial_assumption_names(spec: SpectraSpecification) -> set:
    return set(spec.filter(
        lambda x: x['when'] != GR1TemporalType.INITIAL)["name"])


def _candidate_inputs(env_domains: Dict[str, List[str]],
                      rng: random.Random) -> List[Dict[str, str]]:
    """
    Environment inputs to consider this step, most-promising order irrelevant.

    Enumerated exhaustively (shuffled) while the space is small, sampled once it
    is not - amba has enough environment variables that 2^n is not worth
    building.
    """
    names = sorted(env_domains)
    sizes = [len(env_domains[n]) for n in names]
    total = 1
    for s in sizes:
        total *= s
        if total > EXHAUSTIVE_LIMIT:
            break
    if total <= EXHAUSTIVE_LIMIT:
        combos = [dict(zip(names, values))
                  for values in product(*(env_domains[n] for n in names))]
        rng.shuffle(combos)
        return combos
    return [{n: rng.choice(env_domains[n]) for n in names}
            for _ in range(MAX_CANDIDATES_PER_STEP)]



def _hypothetical_violations(spec, states, candidate, variables, repairable,
                             trace_name) -> set:
    """
    Which repairable assumptions this environment input would break, if taken.

    Evaluated on a hypothetical next state: the candidate's environment values
    over the system's current output, since the system has not moved yet. Exact
    for the assumption shapes that matter here, and where it is not, the real
    check after the step still decides - nothing is accepted on the strength of
    this prediction alone.

    Returns the *set*, not a yes/no. Which assumptions break is the whole
    question: a trace that breaks all of them at once describes no deployment
    anyone would recognise, and gives the repair nothing to discriminate on.
    """
    hypothetical = list(states)
    previous = dict(states[-1]) if states else {}
    previous.update({k: v for k, v in candidate.items() if k in variables})
    hypothetical.append(previous)
    violated = set(_violated_assumptions(
        spec, _trace_lines(hypothetical, variables, trace_name)))
    return violated & repairable


def _targeted_input(spec, states, env_domains, variables, repairable, targets,
                    rng, trace_name):
    """
    An environment input that breaks the target assumptions and nothing else.

    Three preferences, in order:

    1. an input whose violations are exactly the targets - the trace we want;
    2. an input that breaks a non-empty subset of the targets - still on
       target, and the remainder may follow;
    3. an input that breaks nothing at all - keep the run going and try again
       from the next state.

    An input that would break something *outside* the targets is never chosen.
    A real environment fails in one way at a time; one that violates every
    assumption simultaneously is not a deployment scenario, and the repair
    cannot tell which weakening the trace is actually asking for.
    """
    on_target = []
    partial = []
    harmless = []
    for candidate in _candidate_inputs(env_domains, rng):
        violated = _hypothetical_violations(
            spec, states, candidate, variables, repairable, trace_name)
        if violated - targets:
            continue                      # breaks something we are not aiming at
        if violated == targets:
            on_target.append(candidate)
        elif violated:
            partial.append(candidate)
        else:
            harmless.append(candidate)
    for bucket in (on_target, partial, harmless):
        if bucket:
            return bucket[0]
    return None


def violatable_assumptions(spec_path: str) -> List[str]:
    """
    The non-initial assumptions a trace could be made to violate.

    Public so the case-study generator can hand a different one to each trace.
    Left to itself, every trace picks its own target and the easy assumption
    wins repeatedly - gyro produced `ready_stays_ready` five times over. Five
    traces breaking five different assumptions exercise five weakenings; five
    breaking the same one exercise a single weakening five times.
    """
    spec = SpectraSpecification.from_file(spec_path)
    repairable = _non_initial_assumption_names(spec)
    return sorted(repairable & set(
        spec.filter(lambda x: x["type"] == GR1FormulaType.ASM)["name"]))


def _executor_for(spec_path: str, work_dir: str):
    """Synthesise a controller for this specification and open it for stepping."""
    controller_dir = os.path.join(work_dir, "controller")
    os.makedirs(controller_dir, exist_ok=True)
    if not synthesise_controller(spec_path, controller_dir, suppress=True):
        raise ControllerTraceError(
            f"Spectra would not synthesise a controller for {spec_path}. The "
            f"specification must be realisable, and in a form the CLI accepts.")
    StaticController = jpype.JClass("tau.smlab.syntech.controller.StaticController")
    ControllerExecutor = jpype.JClass(
        "tau.smlab.syntech.controller.executor.ControllerExecutor")
    return ControllerExecutor(StaticController(), controller_dir)


def _state_from(executor, variables: List[str]) -> Dict[str, str]:
    """The current step as a plain dict, spec variables only."""
    state = {}
    for source in (executor.getCurrInputs(), executor.getCurrOutputs()):
        for k, v in source.items():
            name = str(k)
            if name in variables:
                state[name] = str(v)
    return state


def _run_episode(spec, spec_path, work_dir, variables, repairable, targets,
                 compliant_steps, max_random_steps, rng, trace_name):
    """
    One attempt: a compliant prefix, then a rogue environment.

    Returns (lines, violated) on success, or None if the attempt is unusable -
    the environment tripped an assumption during the compliant phase, or the
    controller refused a move there. A controller step cannot be undone: the
    executor has advanced and there is no rewind, so a spoiled prefix means
    abandoning the episode rather than backtracking within it.
    """
    executor = _executor_for(spec_path, work_dir)
    env_domains = {str(k): [str(x) for x in v]
                   for k, v in executor.getEnvVars().items()}
    states: List[Dict[str, str]] = []
    started = False

    def step(inputs: Dict[str, str]) -> bool:
        nonlocal started
        java_inputs = jpype.JClass("java.util.HashMap")()
        for k, v in inputs.items():
            java_inputs.put(k, v)
        try:
            if not started:
                executor.initState(java_inputs)
                started = True
            else:
                executor.updateState(java_inputs)
        except jpype.JException:
            # The controller has no legal response. In GR(1) that means the
            # environment has broken its side of the contract - the event being
            # hunted - but the step did not happen, so there is no state for it.
            return False
        states.append(_state_from(executor, variables))
        return True

    # Phase 1: an environment that respects the assumptions.
    #
    # A refused step is free to retry: the controller rejected the move, so the
    # executor never advanced and the next candidate starts from the same state.
    # That is the common case here - Spectra's controller simply will not accept
    # an input its assumptions forbid, which does most of the filtering for us.
    #
    # A step that succeeds and *then* turns out to violate is the unrecoverable
    # one: the executor has advanced and there is no rewind, so the episode is
    # abandoned and retried from a fresh controller.
    for _ in range(compliant_steps):
        for candidate in _candidate_inputs(env_domains, rng):
            if step(candidate):
                break
        else:
            return None
        if _violated_assumptions(spec, _trace_lines(states, variables, trace_name)):
            return None

    # Phase 2: an environment that no longer cares, and aims.
    for _ in range(max_random_steps):
        inputs = _targeted_input(spec, states, env_domains, variables,
                                 repairable, targets, rng, trace_name)
        if inputs is None:
            # Every candidate would break something outside the targets. Better
            # to abandon the episode than to record a trace that violates more
            # than it was asked to.
            return None
        if not step(inputs):
            # The controller refused the move. That is not a dead end - it is
            # the event being hunted: in GR(1) the controller is only obliged to
            # respond while the environment keeps its assumptions, so a refusal
            # means the environment has just broken one. The step is recorded
            # with the system holding its previous output, since the system does
            # not move: it has nothing legal to move to.
            #
            # Missing this cost most of the case studies. minepump's controller
            # happens to accept the violating input and carry on, so it produced
            # traces while every other case study produced none - the difference
            # was whether the controller tolerated the violation, not whether one
            # occurred.
            last_outputs = {k: v for k, v in (states[-1] if states else {}).items()
                            if k not in inputs}
            states.append({**last_outputs, **{k: v for k, v in inputs.items()
                                              if k in variables}})
            violated = set(_violated_assumptions(
                spec, _trace_lines(states, variables, trace_name))) & repairable
            if violated and not violated - targets:
                return (_trace_lines(states, variables, trace_name),
                        sorted(violated))
            return None
        violated = set(_violated_assumptions(
            spec, _trace_lines(states, variables, trace_name))) & repairable
        if violated - targets:
            # Overshot: the step broke something outside the targets after all,
            # and a step cannot be undone.
            return None
        if violated:
            return _trace_lines(states, variables, trace_name), sorted(violated)
    return None


def generate_controller_violation_trace(
        spec_path: str,
        compliant_steps: int = 5,
        max_random_steps: int = 40,
        seed: int = 0,
        attempts: int = 25,
        trace_name: str = "trace_name_0",
        target_assumptions: Optional[List[str]] = None,
        max_targets: int = 1,
) -> Tuple[List[str], List[str]]:
    """
    Run a controller until the environment breaks an assumption.

    :param compliant_steps: N - how long the environment behaves before going
        rogue. The prefix is the point of the whole exercise: real controller
        responses to legal environment behaviour.
    :param max_random_steps: give up after this many rogue steps. A violation is
        not guaranteed - a liveness assumption cannot be violated by any finite
        prefix - so the search must be bounded.
    :param attempts: how many episodes to try. An episode is abandoned when the
        compliant phase spoils itself, which is cheap and unremarkable; each
        retry draws different choices from the same seeded generator, so a whole
        call is still reproducible.
    :returns: (trace lines, names of the non-initial assumptions violated)
    :raises ControllerTraceError: no controller, or no violation within budget.
    """
    rng = random.Random(seed)
    spec = SpectraSpecification.from_file(spec_path)
    variables = _spec_variable_names(spec)
    repairable = _non_initial_assumption_names(spec)
    assumption_names = sorted(
        repairable & set(spec.filter(lambda x: x["type"] == GR1FormulaType.ASM)["name"]))
    if not assumption_names:
        raise ControllerTraceError(
            f"{spec_path} has no non-initial assumption to violate.")

    if target_assumptions:
        candidates = [[a] for a in target_assumptions if a in assumption_names]
        if not candidates:
            raise ControllerTraceError(
                f"None of {target_assumptions} is a non-initial assumption of "
                f"{spec_path}. It has: {assumption_names}")
    else:
        # Each attempt aims at a different assumption, in an order the seed
        # decides. Spreading the target across traces is the point: five traces
        # all breaking the same easy assumption exercise one weakening five
        # times, where five traces breaking five assumptions exercise five.
        shuffled = list(assumption_names)
        rng.shuffle(shuffled)
        candidates = [[a] for a in shuffled]
        if max_targets > 1:
            # Pairs only after every single target has been tried alone.
            candidates += [sorted(pair) for pair in
                           zip(shuffled, shuffled[1:] + shuffled[:1])]

    work_dir = tempfile.mkdtemp(prefix="controller_trace_")
    try:
        for attempt in range(attempts):
            targets = set(candidates[attempt % len(candidates)])
            result = _run_episode(spec, spec_path, work_dir, variables, repairable,
                                  targets, compliant_steps, max_random_steps, rng,
                                  trace_name)
            if result is not None:
                return result
        raise ControllerTraceError(
            f"No targeted assumption was violated for {spec_path} in {attempts} "
            f"episodes of {compliant_steps} compliant + {max_random_steps} "
            f"random steps, over targets {assumption_names}. They may be "
            f"liveness properties, which no finite prefix can violate.")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
