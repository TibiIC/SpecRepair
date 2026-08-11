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
import re
import shutil
import tempfile
from itertools import product
from typing import Dict, List, Optional, Set, Tuple

import jpype

from spec_repair.components.new_spec_encoder import (
    NewSpecEncoder, get_violated_expression_names_of_type)
from spec_repair.components.spec_generator import SpecGenerator
from spec_repair.diagnosis.violation_trace_generation import (
    _parse_models, _trace_skeleton_asp)
from spec_repair.enums import Learning
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.asp_trace_util import create_atom_signature_asp, run_clingo_raw
from spec_repair.util.file_util import generate_temp_filename, write_to_file
from spec_repair.wrappers.asp_wrappers import get_violations
from spec_repair.wrappers.spectra_toolbox import synthesise_controller

# How many random environment inputs to try per step before giving up on finding
# an assumption-respecting one. The input space is exponential in the number of
# environment variables, so it is sampled rather than enumerated once it is
# large - exhaustive search is only worth it while it is cheap.
MAX_CANDIDATES_PER_STEP = 64
EXHAUSTIVE_LIMIT = 64

# How many environment inputs to ask the solver for per step. Each is a
# hypothesis about what the system will do next, so more than one is worth
# having: when the controller's actual response contradicts the first, the
# second is tried without solving again. Small, because they are alternatives
# for one step, not a search.
ASP_MODELS_PER_STEP = 8

# How far ahead the solver may plan to reach a state where the target can break.
# Two is enough for lift's `G(b1 & f1 -> next(!b1))`; the rest is headroom for
# assumptions whose antecedent takes longer to set up. Deeper costs more per
# solve and is only paid when shallower horizons come back UNSATISFIABLE.
MAX_PLAN_HORIZON = 6

# The guess rule, lifted verbatim from the case_study_2 generator so a trace
# built here and a trace built there mean the same thing. `_pinned_prefix_asp`
# then fixes everything already observed, leaving only the new timepoint free.
GUESS_ASP = """
%---*** Environment step construction ***---

1 { holds_at(A,T,S) ; not_holds_at(A,T,S) } 1 :-
    atom(A),
    trace(S),
    timepoint(T,S),
    not weak_timepoint(T,S).

#show holds_at/3.
#show not_holds_at/3.
"""

_HOLDS_RE = re.compile(r"^(not_)?holds_at\(([^,]+),([^,]+),")


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


def _violatable_by_a_finite_prefix(spec: SpectraSpecification) -> set:
    """
    The assumptions a finite trace could actually break: the invariants.

    A JUSTICE assumption is liveness - `GF(p)` says p holds infinitely often,
    and no finite prefix can refute that, since the prefix can always be
    extended. Offering one as a target is not merely fruitless but expensive:
    every attempt runs its full step budget, with an ASP call per step, before
    giving up. Measured on gyro, whose `ready_infinitely_often` made a run with
    --attempts 14 slower than the entire rest of the suite.

    This is the same reason arbiter has no trace at all, and the same reason
    `not_police_often`, `no_emergency_often` and minepump_liveness's
    `assumption4_1` never appear as violated.
    """
    return set(spec.filter(
        lambda x: x['when'] == GR1TemporalType.INVARIANT)["name"])


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



def _pinned_prefix_asp(states: List[Dict[str, str]], variables: List[str],
                       trace_name: str) -> str:
    """
    The trace so far, as facts, so the solver reasons about what happened.

    Pinning a fact beside the guess rule prunes it rather than clashing with
    it: the choice is `1 { holds_at ; not_holds_at } 1`, so asserting one leaves
    the other unsatisfiable, and the prefix stops being a degree of freedom.
    """
    lines = []
    for t, state in enumerate(states):
        for var in variables:
            prefix = "" if str(state.get(var, "false")).lower() == "true" else "not_"
            lines.append(f"{prefix}holds_at({var},{t},{trace_name}).")
    return "\n".join(lines) + ("\n" if lines else "")


def _pinned_response_asp(states: List[Dict[str, str]], sys_names: List[str],
                         trace_name: str) -> str:
    """
    Pin the system's values at the new timepoint to what it is doing *now*.

    The controller has not moved yet, so the system half of the new state is
    unknown to both the solver and the checker. They must assume the same thing
    about it or they are answering different questions: left free, the solver
    picks whichever system response makes the constraint easiest, proposes an
    input that depends on it, and `_hypothetical_violations` - which holds the
    system at its current output - then rejects the model. Every model gets
    rejected that way, and the walk never lands a violation. It cost minepump
    every violation it used to find, which is what the end-to-end tests caught.

    So this mirrors `_hypothetical_violations` exactly: the previous state's
    system values, or false at the start where there is no previous state.
    """
    t = len(states)
    previous = states[-1] if states else {}
    lines = []
    for var in sys_names:
        value = str(previous.get(var, "false")).lower()
        prefix = "" if value == "true" else "not_"
        lines.append(f"{prefix}holds_at({var},{t},{trace_name}).")
    return "\n".join(lines) + ("\n" if lines else "")


def _next_input_constraint_asp(targets: Set[str]) -> str:
    """
    What the next step has to achieve: break exactly the targets, or nothing.

    The compliant prefix and the violating step are the same question asked with
    a different constraint, which is why both go through the solver rather than
    only the interesting one.
    """
    if not targets:
        return "\n:- violation_holds(E,T,S).\n"
    facts = "\n".join(f"to_violate({name})." for name in sorted(targets))
    return f"""
{facts}

violated_exp(E,S) :- violation_holds(E,T,S), trace(S), timepoint(T,S).

% The target must break. Nothing says it has to break *alone*: requiring that
% made the target unreachable wherever assumptions overlap - a step that breaks
% a mutual-exclusion assumption may be the only way to reach the state where
% the intended one can break at all. The trace records everything it violated,
% so a repair still knows what it is being asked for.
:- to_violate(E), trace(S), not violated_exp(E,S).
"""


def _asp_next_inputs(spec, states, variables, env_names, targets, trace_name,
                     n_models: int = ASP_MODELS_PER_STEP,
                     horizon: int = 1) -> List[Dict[str, str]]:
    """
    Environment inputs for the next step, *constructed* rather than sampled.

    This replaces enumerate-and-test. The old approach drew up to 64 candidate
    assignments and ran the violation check on each, which is exhaustive only
    while the environment has at most six or so boolean variables: amba and
    genbuf have nine (512 assignments), colorsort sixteen (65,536), and there
    the sampler simply missed. It is also why "no trace" was indistinguishable
    from "not looked hard enough" - genbuf ran ~72,000 solver calls and reported
    nothing, which is not the same as impossible.

    Here the solver is asked for assignments that meet the constraint, so
    UNSATISFIABLE is a real answer, and the cost stops depending on how many
    environment variables there are.

    The system's values at the new timepoint are guessed by the solver, because
    the controller has not moved yet - so a returned input is a *hypothesis*,
    exactly as before, and the real check after the controller responds still
    decides. Several models are returned so a hypothesis the controller
    contradicts can be followed by another without re-solving.
    """
    # `horizon` timepoints beyond the trace so far. Only the first is executed;
    # the rest are the plan that justifies it. An invariant like
    # `G(b1 & f1 -> next(!b1))` cannot be broken from wherever the walk happens
    # to be - the antecedent has to be reached first, and reaching it may take
    # several moves whose own effect is nothing at all. Asking one step at a
    # time can only ever find violations that are one step away, which is why
    # the case studies needing two or more produced nothing however long they
    # ran.
    n_timepoints = len(states) + horizon
    sys_names = [v for v in variables if v not in set(env_names)]
    program = (SpecGenerator.background_knowledge
               + spec.to_asp(for_clingo=True)
               + create_atom_signature_asp(spec.get_atoms())
               + _trace_skeleton_asp(trace_name, n_timepoints)
               + GUESS_ASP
               + _pinned_prefix_asp(states, variables, trace_name)
               + _pinned_response_asp(states, sys_names, trace_name)
               + _next_input_constraint_asp(targets))

    path = generate_temp_filename(".lp")
    write_to_file(path, program)
    try:
        output = run_clingo_raw(path, n_models=n_models)
    finally:
        if os.path.exists(path):
            os.remove(path)

    t = len(states)
    inputs = []
    for model in _parse_models(output):
        assignment = {}
        for fact in model:
            m = _HOLDS_RE.match(fact)
            if not m:
                continue
            negated, var, timepoint = m.group(1), m.group(2), int(m.group(3))
            if timepoint != t or var not in env_names:
                continue
            assignment[var] = "false" if negated else "true"
        if len(assignment) == len(env_names) and assignment not in inputs:
            inputs.append(assignment)
    return inputs


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
    ranked = _targeted_inputs(spec, states, env_domains, variables, repairable,
                              targets, rng, trace_name)
    return ranked[0] if ranked else None


def _targeted_inputs(spec, states, env_domains, variables, repairable, targets,
                     rng, trace_name) -> List[Dict[str, str]]:
    """
    The same, ranked, so a caller can try the next one when the controller
    refuses the first. A refusal does not advance the executor, so trying
    another is free - and it is what decides whether the violating state ends
    up with a real controller response or a carried-over one.
    """
    # Constructed first. Only if the solver is unavailable - not if it says
    # UNSATISFIABLE, which is an answer - does this fall back to sampling.
    env_names = sorted(env_domains)
    # Deepen until the target becomes reachable. Horizon 1 answers "can it break
    # now"; deeper horizons answer "is there a way to get somewhere it can".
    constructed, solver_spoke = [], False
    horizons = (1,) if not targets else range(1, MAX_PLAN_HORIZON + 1)
    for horizon in horizons:
        try:
            constructed = _asp_next_inputs(spec, states, variables, env_names,
                                           targets, trace_name, horizon=horizon)
            solver_spoke = True
        except Exception:  # noqa: BLE001 - a solver failure must not lose the episode
            constructed, solver_spoke = [], False
            break
        if constructed:
            break

    if solver_spoke:
        matching = []
        for candidate in constructed:
            violated = _hypothetical_violations(
                spec, states, candidate, variables, repairable, trace_name)
            if targets and (violated & targets):
                matching.append(candidate)      # on target - extra breakage is allowed
            elif not violated:
                matching.append(candidate)      # a step toward it, breaking nothing
        if matching:
            # Clingo generates the candidates; the choice among them is the only
            # thing left to chance, and it is seeded. Randomness picks between
            # equally valid answers - it is not used to find them.
            rng.shuffle(matching)
            return matching
        # UNSATISFIABLE here means the targets cannot be broken *from this
        # state*, which is not the same as not at all - an assumption over
        # `next` needs the right predecessor, and the walk has to be allowed to
        # reach one. So ask for a step that breaks nothing and keep going,
        # which is what the sampler's third bucket did by accident and this
        # does on purpose. Returning nothing instead ended the episode, and cost
        # minepump every violation it used to find.
        if not constructed and targets:
            keep_walking = _asp_next_inputs(spec, states, variables, env_names,
                                            set(), trace_name)
            harmless = [c for c in keep_walking
                        if not _hypothetical_violations(spec, states, c, variables,
                                                        repairable, trace_name)]
            if harmless:
                return harmless
        if not constructed and not targets:
            return []

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
    # Ranked, not just the best one: the caller retries down the list when the
    # controller refuses, and on-target inputs are the ones most likely to be
    # refused - refusal *is* the violation, from the controller's side.
    return on_target + partial + harmless


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
    return sorted(_violatable_by_a_finite_prefix(spec) & set(
        spec.filter(lambda x: x["type"] == GR1FormulaType.ASM)["name"]))


def _executor_for(spec_path: str, work_dir: str):
    """Synthesise a controller for this specification and open it for stepping."""
    controller_dir = os.path.join(work_dir, "controller")
    os.makedirs(controller_dir, exist_ok=True)
    # Synthesised once per call, not once per episode. The controller depends
    # only on the specification, and every attempt was rebuilding it: measured
    # on amba, 15 syntheses in two hours at ~8 minutes each, which is the whole
    # runtime - the episode never got as far as walking. The executor still has
    # to be fresh each time, since it carries the run's state, but it can be
    # opened on a controller that is already on disk.
    if not os.listdir(controller_dir):
        if not synthesise_controller(spec_path, controller_dir, suppress=True):
            raise ControllerTraceError(
                f"Spectra would not synthesise a controller for {spec_path}. The "
                f"specification must be realisable, and in a form the CLI accepts.")
    StaticController = jpype.JClass("tau.smlab.syntech.controller.StaticController")
    # FlexibleControllerExecutor rather than ControllerExecutor, for
    # reproducibility. A controller usually has several legal responses to an
    # input; the plain executor picks one itself and does not pick the same one
    # every time, so identical seeds produced different traces - across separate
    # processes, and differing in length, not just in values. The flexible one
    # stops after each step with `waitingForChoice` set, hands back the
    # successor states via getChoices(), and takes the decision from us.
    FlexibleControllerExecutor = jpype.JClass(
        "tau.smlab.syntech.controller.executor.FlexibleControllerExecutor")
    return FlexibleControllerExecutor(StaticController(), controller_dir)


def _settle(executor, rng) -> None:
    """
    Resolve the controller's outstanding choice, reproducibly.

    After `updateState` the executor is waiting: `getChoices()` lists the
    successor states and nothing advances until `chooseNextState` picks one.
    The choices are sorted into a canonical order first - they arrive from a BDD
    traversal, whose order is not something to depend on - and then drawn with
    the run's seeded generator. Seeded rather than always-first so different
    seeds still explore different controller behaviour, which is the point of
    generating five traces.
    """
    choices = executor.getChoices()
    if choices is None or len(choices) == 0:
        return
    canonical = sorted(
        ({str(k): str(v) for k, v in choice.items()} for choice in choices),
        key=lambda state: tuple(sorted(state.items())))
    picked = canonical[rng.randrange(len(canonical))]
    java_state = jpype.JClass("java.util.HashMap")()
    for k, v in picked.items():
        java_state.put(k, v)
    executor.chooseNextState(java_state)


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
    refusal = ""            # why the controller last refused a step, if it did

    def step(inputs: Dict[str, str]) -> bool:
        nonlocal started, refusal
        refusal = ""
        java_inputs = jpype.JClass("java.util.HashMap")()
        for k, v in inputs.items():
            java_inputs.put(k, v)
        try:
            if not started:
                executor.initState(java_inputs)
                started = True
            else:
                executor.updateState(java_inputs)
            # updateState leaves the executor waiting on a choice; nothing
            # advances and getCurrOutputs is not meaningful until it is made.
            _settle(executor, rng)
        except jpype.JException as e:
            # The controller has no legal response - but *why* decides whether
            # this is the event being hunted or a dead end, and Syntech says
            # which through the exception type:
            #
            #   IllegalArgumentException - this input violates a safety
            #       assumption. That is the event: the environment has broken
            #       its side of the contract.
            #   IllegalStateException - the environment is in a deadlock, with
            #       no safe input available from this state at all. Nothing was
            #       violated by choosing this input; there was nothing to
            #       choose. Recording it as a violation would attribute to the
            #       environment's behaviour something that is a property of the
            #       state it was already in.
            #
            # Both were caught as one, so a deadlock was written down as a
            # violation of whichever assumption the checker then reported.
            refusal = str(e.getClass().getSimpleName())
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

        # One input, taken as ranked. Retrying until the controller accepts a
        # violating input would be backwards: a controller is obliged to
        # respond only while the environment keeps its assumptions, so refusal
        # is the expected answer to a violating input, and searching for an
        # accepted one selects for the weakest violations available.
        accepted = step(inputs)
        if not accepted and refusal == "IllegalStateException":
            # An environment deadlock, not a violation. No input was available
            # from this state at all, so nothing the environment did here broke
            # anything; the episode has run into a corner and is abandoned.
            return None
        if not accepted:
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
            if violated & targets:
                return (_trace_lines(states, variables, trace_name),
                        sorted(violated))
            return None
        violated = set(_violated_assumptions(
            spec, _trace_lines(states, variables, trace_name))) & repairable
        if violated & targets:
            # On target. Anything else it broke on the way is recorded rather
            # than disqualifying: insisting the target break alone made it
            # unreachable wherever assumptions overlap, and the manifest names
            # everything violated, so nothing is hidden by allowing it.
            return _trace_lines(states, variables, trace_name), sorted(violated)
        if violated:
            # Broke something, but not what was aimed at. The step cannot be
            # undone, so this episode no longer serves its target.
            return None
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
    assumption_names = violatable_assumptions(spec_path)
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
