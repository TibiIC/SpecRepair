"""
Generate execution traces that deliberately violate a specification's assumptions.

This supports the trace-violation experimental setup: instead of artificially
strengthening a known-good specification and repairing back down, we take the
original specification as-is and look for short environment behaviours it does
not admit. Repair then has to weaken the real specification to accommodate a
real trace, with no synthetic strengthening step in between.

Approach: SYNTECH's Rich Controller Walker (the Eclipse plugin that lets a user
step a controller and deliberately pick environment-violating moves) is not
available here - none of the Spectra jars in ~/Tools ship any walker classes, as
they only contain the CLI and games/controller sources. So the trace is found
with ASP instead, reusing the same encoding the repair pipeline already uses:

  * `spec.to_asp(for_clingo=True)` turns every formula into rules deriving
    `violation_holds(E, T, S)`,
  * `files/background_knowledge.txt` supplies the GR(1) semantics,
  * a choice rule *guesses* the trace rather than reading it from a file,
  * constraints force exactly the chosen assumptions to be violated and
    everything else - the other assumptions and all guarantees - to hold.

Traces are finite prefixes, so they end in the same `weak_timepoint` the rest of
the codebase uses: a slot where every atom both holds and does not hold, letting
formulas about the future be satisfied vacuously instead of making every short
prefix unsatisfiable.
"""
import itertools
import random
import re
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

from spec_repair.components.spec_generator import SpecGenerator
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.asp_trace_util import create_atom_signature_asp, run_clingo_raw
from spec_repair.util.file_util import generate_temp_filename, write_to_file

DEFAULT_TRACE_NAME = "trace_name_0"
WEAK_TIMEPOINT = "weak_t"

_ATOM_LINE = re.compile(r"\b((?:not_)?holds_at\([^)]*\))")
_TIMEPOINT_OF = re.compile(r"(?:not_)?holds_at\([^,]+,([^,]+),")


def _is_weak(fact: str) -> bool:
    match = _TIMEPOINT_OF.search(fact)
    return match is not None and not match.group(1).strip().isdigit()


class GeneratedTrace(NamedTuple):
    """A generated trace plus which assumptions it was built to violate."""
    lines: List[str]
    violated_assumptions: List[str]
    n_timepoints: int


def get_formula_names(spec: SpectraSpecification, formula_type: Optional[GR1FormulaType] = None) -> List[str]:
    df = spec._formulas_df
    if formula_type is not None:
        df = df[df["type"] == formula_type]
    return [str(name) for name in df["name"]]


def _trace_skeleton_asp(trace_name: str, n_timepoints: int) -> str:
    """
    The trace/timepoint/next/weak_timepoint facts for a prefix of the given
    length, matching what asp_trace_util.trace_single_to_asp_form emits for a
    real trace so a generated trace and a read one are encoded identically.
    """
    lines = [f"trace({trace_name}).", ""]
    lines += [f"timepoint({t},{trace_name})." for t in range(n_timepoints)]
    lines.append(f"weak_timepoint({WEAK_TIMEPOINT},{trace_name}).")
    lines += [f"next({t + 1},{t},{trace_name})." for t in range(n_timepoints - 1)]
    lines.append(f"next({WEAK_TIMEPOINT},{n_timepoints - 1},{trace_name}).")
    lines.append(f"next({WEAK_TIMEPOINT},{WEAK_TIMEPOINT},{trace_name}).")
    return "\n".join(lines) + "\n\n"


def _guess_and_constrain_asp(to_violate: Sequence[str]) -> str:
    """
    Guess the trace, then pin down exactly which expressions may fail.

    Every atom is independently true or false at every real timepoint. The two
    integrity constraints are the whole point of the generator: the chosen
    assumptions *must* be violated somewhere, and nothing else may be violated
    anywhere - so the environment misbehaves in exactly the intended way while
    the system, and every other assumption, still behaves.
    """
    to_violate_facts = "\n".join(f"to_violate({name})." for name in to_violate)
    return f"""
%---*** Trace generation ***---

{to_violate_facts}

% Guess: each atom either holds or does not, at each real timepoint.
1 {{ holds_at(A,T,S) ; not_holds_at(A,T,S) }} 1 :-
    atom(A),
    trace(S),
    timepoint(T,S),
    not weak_timepoint(T,S).

violated_exp(E,S):-
    violation_holds(E,T,S),
    trace(S),
    timepoint(T,S).

% Nothing outside the chosen set may be violated.
:- violation_holds(E,T,S), not to_violate(E).

% Every chosen assumption must actually be violated.
:- to_violate(E), trace(S), not violated_exp(E,S).

#show holds_at/3.
#show not_holds_at/3.
"""


def build_violation_asp(
        spec: SpectraSpecification,
        to_violate: Sequence[str],
        n_timepoints: int,
        trace_name: str = DEFAULT_TRACE_NAME,
) -> str:
    """The full ASP program whose answer sets are the traces we want."""
    return (SpecGenerator.background_knowledge
            + spec.to_asp(for_clingo=True)
            + create_atom_signature_asp(spec.get_atoms())
            + _trace_skeleton_asp(trace_name, n_timepoints)
            + _guess_and_constrain_asp(to_violate))


def _parse_models(clingo_output: str) -> List[List[str]]:
    """
    Split clingo output into one list of atom facts per answer set.

    Parsed with a regex over the whole block rather than line by line: clingo
    prints an answer set as one long space-separated line, and the repo's
    run_clingo helper re-wraps long lines, so neither line structure is
    dependable.
    """
    if "UNSATISFIABLE" in clingo_output:
        return []
    models = []
    for block in re.split(r"Answer:\s*\d+\s*\n", clingo_output)[1:]:
        block = block.split("SATISFIABLE")[0]
        # Drop the weak timepoint. Background knowledge derives both
        # holds_at and not_holds_at there for every atom, by design - it is the
        # open end of a finite prefix, not an observed state - so those facts
        # are not part of the trace and never appear in a trace file.
        atoms = [f"{m}." for m in _ATOM_LINE.findall(block) if not _is_weak(m)]
        if atoms:
            models.append(atoms)
    return models


def _sort_trace(lines: Sequence[str]) -> List[str]:
    """Order by timepoint then atom name, so a trace file reads chronologically."""
    def key(line: str):
        match = re.match(r"(not_)?holds_at\(([^,]+),([^,]+),", line)
        if not match:
            return (0, "", "")
        negated, atom, timepoint = match.groups()
        return (int(timepoint) if timepoint.isdigit() else 0, atom, negated or "")
    return sorted(lines, key=key)


def _format_trace(lines: Sequence[str], n_timepoints: int) -> List[str]:
    """Blank-line-separate timepoints, matching the committed trace fixtures."""
    out: List[str] = []
    current = None
    for line in _sort_trace(lines):
        match = re.match(r"(?:not_)?holds_at\([^,]+,([^,]+),", line)
        timepoint = match.group(1) if match else None
        if current is not None and timepoint != current:
            out.append("")
        current = timepoint
        out.append(line)
    return out


def find_violable_assumptions(
        spec: SpectraSpecification,
        min_timepoints: int = 1,
        max_timepoints: int = 3,
        trace_name: str = DEFAULT_TRACE_NAME,
) -> Dict[str, List[int]]:
    """
    For each assumption, the trace lengths at which it can be violated on its own
    while every other formula still holds. An assumption mapping to `[]` cannot
    be violated at any length in the range.

    Worth checking before generating, because "unviolable" has two very
    different causes and both are invisible from a failed draw:

    * The assumption is a **tautology** and can never be violated at any length.
      Real example: minepump's `assumption2_1` is
      `G(!highwater -> (!highwater | !methane))`, which spot confirms is
      equivalent to `true`.
    * Violating it needs **more timepoints than allowed**. A trace is a finite
      prefix ending in the weak timepoint, where every atom both holds and does
      not, so any `next` evaluated at the last real timepoint is satisfied
      vacuously. A violation involving `next` therefore has to occur at least
      one timepoint before the end. minepump's
      `G((PREV(pump) & pump) -> next(!highwater))` needs 4: `!pump` at t0 forced
      by `initial_guarantee`, then pump at t1 and t2, then highwater at t3.
    """
    violable: Dict[str, List[int]] = {}
    for name in get_formula_names(spec, GR1FormulaType.ASM):
        lengths = []
        for n in range(min_timepoints, max_timepoints + 1):
            asp_file = generate_temp_filename(ext=".lp")
            write_to_file(asp_file, build_violation_asp(spec, [name], n, trace_name))
            if _parse_models(run_clingo_raw(asp_file, n_models=1)):
                lengths.append(n)
        violable[name] = lengths
    return violable


def candidate_violation_groups(
        assumption_names: Sequence[str],
        max_violated: int,
        rng: Optional[random.Random] = None,
) -> List[Tuple[str, ...]]:
    """
    The groups of assumptions to try violating, smallest first and shuffled
    within each size.

    Smallest first because a trace violating a single assumption is the clearest
    evidence of what went wrong; larger groups are only worth reaching for once
    the singletons are used up. Shuffled within a size so repeated runs with
    different seeds explore different assumptions rather than always the first
    few in file order.
    """
    rng = rng or random
    groups: List[Tuple[str, ...]] = []
    for size in range(1, max(1, min(max_violated, len(assumption_names))) + 1):
        same_size = [tuple(sorted(c)) for c in itertools.combinations(assumption_names, size)]
        rng.shuffle(same_size)
        groups.extend(same_size)
    return groups


def generate_assumption_violating_traces(
        spec: SpectraSpecification,
        n_traces: int = 1,
        min_timepoints: int = 1,
        max_timepoints: int = 3,
        max_violated_assumptions: int = 1,
        rng: Optional[random.Random] = None,
        trace_name: str = DEFAULT_TRACE_NAME,
        models_per_attempt: int = 20,
        max_attempts_per_trace: int = 25,
) -> List[GeneratedTrace]:
    """
    Find up to `n_traces` distinct traces, each violating a randomly chosen,
    non-empty set of `spec`'s assumptions and nothing else.

    Each attempt draws a fresh set of assumptions to violate and a fresh trace
    length in [min_timepoints, max_timepoints], because which combinations are
    satisfiable is not knowable up front: some assumptions cannot be violated
    within one timepoint (anything under `next`), and some pairs cannot be
    violated together while every guarantee still holds. Unsatisfiable draws are
    simply retried rather than reported as failures.

    :returns: the traces found; fewer than `n_traces` if the attempt budget runs
        out, which for a small specification usually means few distinct traces
        exist rather than that something went wrong.
    """
    rng = rng or random
    all_assumptions = get_formula_names(spec, GR1FormulaType.ASM)
    if not all_assumptions:
        raise ValueError("Specification has no assumptions to violate.")
    if min_timepoints < 1 or max_timepoints < min_timepoints:
        raise ValueError(f"Invalid timepoint range: [{min_timepoints}, {max_timepoints}]")

    # Draw only from assumptions that can actually be violated in this range,
    # otherwise most attempts are spent on draws that are unsatisfiable for
    # reasons no amount of retrying will change - see find_violable_assumptions.
    violable = find_violable_assumptions(spec, min_timepoints, max_timepoints, trace_name)
    assumption_names = [name for name, lengths in violable.items() if lengths]
    if not assumption_names:
        raise ValueError(
            f"None of {spec._module_name}'s {len(all_assumptions)} assumption(s) can be violated "
            f"within {min_timepoints}-{max_timepoints} timepoints. Either they are tautologies, "
            f"or violating them needs a longer trace - try raising max_timepoints.")
    skipped = [name for name, lengths in violable.items() if not lengths]
    if skipped:
        print(f"Note: {len(skipped)} assumption(s) not violable within "
              f"{min_timepoints}-{max_timepoints} timepoints, skipped: {', '.join(skipped)}")

    # Work through distinct groups of assumptions rather than drawing at random,
    # so a set of traces covers different violations instead of witnessing the
    # same one several ways. Groups are only revisited once every one of them
    # has been tried, and then only to top up the requested count.
    groups = candidate_violation_groups(assumption_names, max_violated_assumptions, rng)
    results: List[GeneratedTrace] = []
    seen: Set[str] = set()
    used_groups: Set[Tuple[str, ...]] = set()
    attempts = 0
    budget = n_traces * max_attempts_per_trace

    while len(results) < n_traces and attempts < budget:
        pending = [g for g in groups if g not in used_groups] or groups
        made_progress = False
        for group in pending:
            if len(results) >= n_traces or attempts >= budget:
                break
            attempts += 1
            # Only lengths at which every assumption in the group is individually
            # violable can possibly work; anything else is a guaranteed UNSAT.
            feasible = sorted(set.intersection(*(set(violable[name]) for name in group)))
            if not feasible:
                used_groups.add(group)
                continue
            n_timepoints = rng.choice(feasible)

            asp = build_violation_asp(spec, list(group), n_timepoints, trace_name)
            asp_file = generate_temp_filename(ext=".lp")
            write_to_file(asp_file, asp)
            models = _parse_models(run_clingo_raw(asp_file, n_models=models_per_attempt))
            if not models:
                # A group can be unsatisfiable as a whole even when each of its
                # assumptions is violable alone - violating both at once may be
                # impossible while every guarantee still holds.
                used_groups.add(group)
                continue

            rng.shuffle(models)
            for model in models:
                fingerprint = "\n".join(_sort_trace(model))
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                used_groups.add(group)
                results.append(GeneratedTrace(_format_trace(model, n_timepoints),
                                              sorted(group), n_timepoints))
                made_progress = True
                break
        if not made_progress:
            break
    return results
