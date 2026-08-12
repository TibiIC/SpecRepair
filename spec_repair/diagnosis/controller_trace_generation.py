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
import hashlib
import os
import random
import re
import shutil
import tempfile
import time
from itertools import product
from typing import Dict, List, Optional, Sequence, Set, Tuple

import jpype

from spec_repair.components.new_spec_encoder import (
    NewSpecEncoder, get_violated_expression_names_of_type)
from spec_repair.components.spec_generator import SpecGenerator
from spec_repair.config import PROJECT_PATH
from spec_repair.diagnosis.violation_trace_generation import (
    _parse_models, _trace_skeleton_asp)
from spec_repair.enums import Learning
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.patterns import PRS_REG
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


_PROGRESS_START: Optional[float] = None


def _progress(message: str) -> None:
    """
    A line per step, so a long run is legible while it happens.

    Generation logged only when a whole trace finished, which for amba meant
    nothing at all between "amba:" and a result an hour later - leaving CPU
    percentage and log mtime as the only evidence it was alive. Steps are where
    the time goes, so steps are what this prints.

    Silenced with SPEC_REPAIR_TRACE_GEN_QUIET=1; the tests set it, since a line
    per step across every case study buries the assertion that failed.
    """
    if os.environ.get("SPEC_REPAIR_TRACE_GEN_QUIET"):
        return
    global _PROGRESS_START
    if _PROGRESS_START is None:
        _PROGRESS_START = time.time()
    elapsed = int(time.time() - _PROGRESS_START)
    print(f"    [{elapsed // 60:3d}m{elapsed % 60:02d}s] {message}", flush=True)


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



def _asp_name(name: str) -> str:
    """
    A variable or expression as the ASP encoding spells it.

    Two name spaces are in play and they differ in exactly one character. The
    specification file - and the controller built from it - keeps the author's
    casing: `InputMoveMode_fwd`, `Obstacle_clear`. The ASP encoding lowercases
    the first letter, because a capitalised token is a *variable* to clingo,
    not a constant. Every other case study is lowercase throughout, so the two
    spaces coincide and nothing shows; humanoid is the one that is not, and it
    cost three separate misdiagnoses today - a dump tool that grounded to an
    error, an `is_guarantee` fact wrongly suspected, and finally this: plan
    extraction filtering the solver's atoms against the controller's spelling
    and discarding every one of them, so a SATISFIABLE query looked like "no
    violating input reachable".

    Translate at the boundary, in both directions, rather than lowercasing at
    a fourth call site.
    """
    return name[:1].lower() + name[1:] if name else name


def _controller_names(env_domains: Dict[str, List[str]]) -> Dict[str, str]:
    """ASP spelling -> the controller's spelling, for handing inputs back."""
    return {_asp_name(name): name for name in env_domains}


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


def _next_input_constraint_asp(targets: Set[str],
                               guarantees: Sequence[str] = (),
                               last_real: int = 0) -> str:
    """
    What the next step has to achieve: break exactly the targets, or nothing.

    The compliant prefix and the violating step are the same question asked with
    a different constraint, which is why both go through the solver rather than
    only the interesting one.
    """
    if not targets:
        return "\n:- violation_holds(E,T,S).\n"
    facts = "\n".join(f"to_violate({name})." for name in sorted(targets))
    gar_facts = "\n".join(f"is_guarantee({name})." for name in sorted(guarantees))
    return f"""
{facts}

{gar_facts}

violated_exp(E,S) :- violation_holds(E,T,S), trace(S), timepoint(T,S).

% The system's moves in a plan are guesses - the controller has not made them
% yet - so they have to be guesses the controller could actually make. A
% synthesised controller satisfies its guarantees by construction, so a plan
% that relies on one breaking is a plan against a system that does not exist.
% Without this the solver was free to invent a cooperative system, propose the
% input that suited it, and be contradicted the moment the real controller
% answered - which is why deepening the horizon alone changed nothing.
:- violation_holds(E,T,S), is_guarantee(E), T < {last_real}.

% The target must break. Nothing says it has to break *alone*: requiring that
% made the target unreachable wherever assumptions overlap - a step that breaks
% a mutual-exclusion assumption may be the only way to reach the state where
% the intended one can break at all. The trace records everything it violated,
% so a repair still knows what it is being asked for.
:- to_violate(E), trace(S), not violated_exp(E,S).
"""


def _asp_next_inputs(spec, states, variables, env_names, targets, trace_name,
                     n_models: int = ASP_MODELS_PER_STEP,
                     horizon: int = 1) -> List[List[Dict[str, str]]]:
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
    # Safety guarantees only. A `GF(p)` guarantee is liveness, and a finite
    # prefix neither satisfies nor refutes it - but the encoding reports it as
    # violated whenever p has not happened yet, which for a real prefix is most
    # of the time. Constraining those made the *pinned history* unsatisfiable,
    # so every plan was UNSAT however deep it went, for amba's seven justice
    # guarantees in particular. Symmetric with only ever targeting invariant
    # assumptions, and for the same reason.
    guarantee_names = sorted(spec.filter(
        lambda x: (x["type"] == GR1FormulaType.GAR)
        & (x["when"] == GR1TemporalType.INVARIANT))["name"])
    program = (SpecGenerator.background_knowledge
               + spec.to_asp(for_clingo=True)
               + create_atom_signature_asp(spec.get_atoms())
               + _trace_skeleton_asp(trace_name, n_timepoints)
               + GUESS_ASP
               + _pinned_prefix_asp(states, variables, trace_name)
               + _next_input_constraint_asp(targets, guarantee_names,
                                            last_real=n_timepoints - 1))

    path = generate_temp_filename(".lp")
    write_to_file(path, program)
    try:
        output = run_clingo_raw(path, n_models=n_models)
    finally:
        if os.path.exists(path):
            os.remove(path)

    # An UNSAT program is the thing worth looking at, and it is the one thing
    # that was never kept: the temp file is deleted, so every diagnosis so far
    # has been done on a *reconstruction* with a synthetic prefix, which
    # misleads in both directions - a fabricated history that violates the
    # guarantees, or no history at all. Set SPEC_REPAIR_DUMP_UNSAT to a
    # directory to keep the real one.
    dump_dir = os.environ.get("SPEC_REPAIR_DUMP_UNSAT", "").strip()
    if dump_dir and "UNSATISFIABLE" in output:
        os.makedirs(dump_dir, exist_ok=True)
        label = "-".join(sorted(targets)) if targets else "compliant"
        name = f"unsat_t{len(states)}_h{horizon}_{label}.lp"[:120]
        with open(os.path.join(dump_dir, name), "w") as f:
            f.write(f"% UNSAT: {len(states)} pinned state(s), horizon {horizon}, "
                    f"target(s) {sorted(targets) or '(none)'}\n"
                    f"% the prefix below is real controller output, not a stand-in\n\n")
            f.write(program)

    # Every new timepoint, in order - the plan, not just its first move. The
    # early steps respect the assumptions and exist to set up the antecedent;
    # the last one breaks it. Executing the first and re-planning threw those
    # away and then went looking for them again, which is what turned a
    # three-step plan into a twenty-step wander.
    first = len(states)
    plans = []
    for model in _parse_models(output):
        steps = {}
        for fact in model:
            m = _HOLDS_RE.match(fact)
            if not m:
                continue
            negated, var, timepoint = m.group(1), m.group(2), int(m.group(3))
            if timepoint < first or var not in env_names:
                continue
            steps.setdefault(timepoint, {})[var] = "false" if negated else "true"
        plan = [steps[t] for t in sorted(steps)
                if len(steps[t]) == len(env_names)]
        if plan and plan not in plans:
            plans.append(plan)
    return plans


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
                     rng, trace_name) -> List[List[Dict[str, str]]]:
    """
    Plans: each a list of environment moves, the last of which breaks a target.

    A plan is asked for once and returned whole. Its early moves respect the
    assumptions and exist to reach the state where the target becomes
    breakable - they are not separate "violate nothing" steps to be gone
    looking for afterwards.
    """
    # The solver speaks the encoding's names; the controller speaks the
    # specification's. Ask in one, translate the answer back to the other.
    controller_name = _controller_names(env_domains)
    env_names = sorted(controller_name)

    # The trace ends in a weak timepoint where everything holds vacuously, so a
    # violation involving `next` has to land before the end: horizon k buys k-1
    # usable steps, and horizon 1 buys none. That is why a `next`-based
    # assumption is always UNSAT at 1, and why the search starts at 2. A GR(1)
    # invariant needs three steps at worst, so six is generous headroom.
    if not targets:
        horizons = (2,)
    else:
        horizons = range(2, MAX_PLAN_HORIZON + 1)

    for horizon in horizons:
        plans = _asp_next_inputs(spec, states, variables, env_names,
                                 targets, trace_name, horizon=horizon)
        if plans:
            plans = [[{controller_name[k]: v for k, v in stepd.items()}
                      for stepd in plan] for plan in plans]
            if targets:
                _progress(f"PLAN   t={len(states)} horizon={horizon} -> "
                          f"{len(plans)} plan(s), {len(plans[0])} step(s)")
            # Every plan clingo returned breaks the target, so choosing between
            # them at random is choosing between correct answers - and it is
            # what makes five traces of one case study five *different* traces
            # rather than five copies. Seeded, so a trace is still reproducible.
            rng.shuffle(plans)
            return plans
    if targets:
        _progress(f"PLAN   t={len(states)} UNSAT to horizon {MAX_PLAN_HORIZON} "
                  f"for {sorted(targets)}")
    return []


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
    names = sorted(_violatable_by_a_finite_prefix(spec) & set(
        spec.filter(lambda x: x["type"] == GR1FormulaType.ASM)["name"]))
    return [n for n in names if n not in _response_shaped(spec_path)]


def _response_shaped(spec_path: str) -> Set[str]:
    """
    Assumptions of the form `G(a -> F(b))`, which no finite trace can break.

    They are classified as invariants because the outer operator is `G`, so
    they arrive as targets - but the consequent is `F`, and an eventually is
    never refuted by a prefix: the obligation can always be discharged one step
    later. Aiming at one costs a full horizon search per attempt and can only
    ever come back UNSAT. amba spends three of its five seeds this way, on
    `a10_0`, `a10_1` and `a10_2`.

    Detected with the same pattern the pRespondsToS rewrite uses, so the two
    agree on what a response formula is.
    """
    shaped, current = set(), None
    for line in open(spec_path):
        stripped = line.strip()
        if stripped.startswith("assumption"):
            current = stripped.split("--")[-1].strip() if "--" in stripped else None
        elif current and PRS_REG.search(line.strip("\t\n;")):
            shaped.add(current)
            current = None
        elif stripped and not stripped.startswith("assumption"):
            current = current if not stripped.endswith(";") else None
    return shaped


def _controller_cache_dir(spec_path: str) -> str:
    """
    Where a synthesised controller is kept between runs.

    Keyed by the specification's contents, not its path: an edited spec must not
    be answered with the controller of the old one, and two paths holding the
    same spec may share.
    """
    digest = hashlib.sha256(open(spec_path, "rb").read()).hexdigest()[:16]
    name = os.path.basename(os.path.dirname(spec_path))
    root = os.environ.get("SPEC_REPAIR_CONTROLLER_CACHE") or os.path.join(
        PROJECT_PATH, "tests", "test_files", "out", "controller_cache")
    return os.path.join(root, f"{name}_{digest}")


def _cached_controller(spec_path: str) -> str:
    """
    Synthesise the controller, or reuse the one already on disk.

    Synthesis depends only on the specification and is deterministic, but it is
    not cheap: amba takes about eight minutes, and it was being paid again on
    every invocation because each run built into a fresh temporary directory
    that was deleted on the way out. Across a session of repeated attempts that
    is most of the runtime, spent recomputing an identical answer.

    Written to a temporary directory and renamed into place, so a run that dies
    mid-synthesis cannot leave a half-written controller for the next one to
    load.
    """
    cache_dir = _controller_cache_dir(spec_path)
    if os.path.isdir(cache_dir) and os.listdir(cache_dir):
        return cache_dir

    os.makedirs(os.path.dirname(cache_dir), exist_ok=True)
    staging = f"{cache_dir}.building.{os.getpid()}"
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    if not synthesise_controller(spec_path, staging, suppress=True):
        shutil.rmtree(staging, ignore_errors=True)
        raise ControllerTraceError(
            f"Spectra would not synthesise a controller for {spec_path}. The "
            f"specification must be realisable, and in a form the CLI accepts.")
    try:
        os.rename(staging, cache_dir)
    except OSError:
        # Another process got there first; its copy is as good as this one.
        shutil.rmtree(staging, ignore_errors=True)
    return cache_dir


def _executor_for(spec_path: str, work_dir: str):
    """Synthesise a controller for this specification and open it for stepping."""
    controller_dir = _cached_controller(spec_path)
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

    # Phase 1: a compliant prefix, one solved step at a time.
    for _ in range(compliant_steps):
        plans = _targeted_inputs(spec, states, env_domains, variables,
                                 repairable, set(), rng, trace_name)
        if not plans or not step(plans[0][0]):
            return None
        _progress(f"PREFIX t={len(states) - 1} accepted")

    # Phase 2: one plan, executed whole.
    #
    # The plan's early moves respect the assumptions and exist to reach the
    # state where the target becomes breakable; its last move breaks it.
    # Executing only the first and re-planning discarded exactly those moves
    # and then went looking for them again, which is what turned a three-step
    # plan into a twenty-step wander.
    plans = _targeted_inputs(spec, states, env_domains, variables,
                             repairable, targets, rng, trace_name)
    if not plans:
        return None

    for plan in plans:
        for position, inputs in enumerate(plan):
            accepted = step(inputs)
            if not accepted and refusal == "IllegalStateException":
                _progress("AIM    environment deadlock - no input available here")
                return None
            if not accepted:
                # The controller will not answer. Only defensible at the last
                # move, where the environment has just broken its side of the
                # contract; earlier it means the plan assumed a response the
                # controller would not give.
                if position != len(plan) - 1:
                    _progress(f"AIM    refused mid-plan at step {position} - "
                              f"the plan assumed a response the controller "
                              f"would not make")
                    return None
                last_outputs = {k: v for k, v in (states[-1] if states else {}).items()
                                if k not in inputs}
                states.append({**last_outputs, **{k: v for k, v in inputs.items()
                                                  if k in variables}})
            violated = set(_violated_assumptions(
                spec, _trace_lines(states, variables, trace_name))) & repairable
            _progress(f"AIM    t={len(states) - 1} "
                      + (f"violated {sorted(violated)}" if violated
                         else "no violation yet"))
            if violated & targets:
                return _trace_lines(states, variables, trace_name), sorted(violated)
            if not accepted:
                return None
        # Plan exhausted without the target breaking: the controller's actual
        # responses diverged from what the plan assumed.
        _progress("AIM    plan finished without breaking the target")
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
        # The precondition for this setup: a specification needs at least one
        # invariant assumption. Only invariants can be broken by a finite
        # prefix - a liveness assumption `GF(p)` is never refuted by one,
        # because the prefix can always be extended. arbiter, whose only
        # assumption is `GF(a)`, fails this and always will; that is a property
        # of the specification, not a shortcoming of the generator, and it is
        # reported as such rather than after exhausting a budget.
        raise ControllerTraceError(
            f"{spec_path} has no invariant assumption. Only invariants can be "
            f"violated by a finite trace, so this specification cannot yield "
            f"one at any length or budget.")

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
        # The prefix shortens as attempts go on. A controller step cannot be
        # undone, so if five compliant steps walk into a state the target
        # cannot be reached from, the only way back is a fresh episode with a
        # shorter run-up. lift is the case: unreachable after five steps,
        # solved immediately after one or two. Later attempts therefore try
        # progressively shorter prefixes rather than the same one again, and
        # only fall back to a single step once every length has been tried.
        for attempt in range(attempts):
            targets = set(candidates[attempt % len(candidates)])
            cycle = attempt // max(1, len(candidates))
            prefix = compliant_steps - cycle
            if prefix < 1:
                prefix = 1
            if prefix != compliant_steps:
                _progress(f"RETRY  attempt {attempt} with a {prefix}-step prefix")
            result = _run_episode(spec, spec_path, work_dir, variables, repairable,
                                  targets, prefix, max_random_steps, rng,
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
