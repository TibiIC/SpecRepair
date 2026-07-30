"""
Generate mutated, semantically stronger specifications and matching
violating traces from an ideal (realizable) specification.

Modernized port of the assumption-strengthening/violation-generation
pipeline in spec_repair/legacy/old_experiments.py (drop_random,
drop_and_evaluate) to operate on SpectraSpecification/GR1Formula objects
instead of raw regex-edited .spectra text.

Methodology (see old_experiments.py's module docstring-equivalent
research description): starting from an ideal specification, apply a
handful of strengthening steps to obtain a mutated specification with
strictly narrower (stronger) assumptions and/or guarantees. Assumptions are
strengthened first, then guarantees: narrowing what the environment may do
tends to leave a system just as easy (or easier) to satisfy, so
realizability usually survives; only once that slack exists is it spent on
strengthening what the system promises, which is far likelier to break
realizability outright. This mirrors old_experiments.py's drop_random,
which forces its first random drop to be an assumption specifically before
allowing further drops (of either kind) - see strengthen_spec's docstring
for the precise difference from that legacy behaviour. Each realizable
mutation is paired with an execution trace, found via clingo
(util.asp_trace_util.generate_trace_asp), that satisfies the ideal
specification's semantics while violating the mutated specification's
(assumptions, guarantees, or both).

Three strengthening patterns are applied, chosen to match patterns
observed in this repo's own case-study fixtures
(input-files/case-studies/spectra/strengthened/*/ideal.spectra vs strong.spectra):
- drop one disjunct from a formula's consequent (or the eventually-wrapped
  consequent of a response pattern) - narrows what satisfies the formula
- drop one conjunct from a formula's antecedent - broadens when the
  formula's consequent is required, narrowing the formula overall
- narrow a justice formula GF(f) to an invariant G(f) - drops the
  "eventually" allowance entirely
"""
import random
from copy import deepcopy
from typing import Iterable, List, Optional

from py_ltl.formula import Eventually, LTLFormula

from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.model.gr1_formula import GR1Formula
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.asp_trace_util import generate_trace_asp, get_individual_traces
from spec_repair.util.file_util import generate_temp_filename, read_file_lines, write_to_file
from spec_repair.util.ltl_formula_util import conjoin, disjoin_all, get_conjuncts_from_conjunction, \
    get_disjuncts_from_disjunction


def _try_strengthen(formula: GR1Formula, rng: random.Random) -> Optional[GR1Formula]:
    """
    Randomly pick one strengthening pattern applicable to `formula` and
    apply it, returning a new, strictly stronger GR1Formula. Returns None
    if no pattern applies (e.g. every consequent/antecedent is already a
    single literal, and the formula is already an invariant), or if every
    applicable pattern only produces results that are semantically
    equivalent to `formula` itself.

    That last case is real, not defensive: a formula can contain a
    redundant disjunct/conjunct - e.g. a tautological clause like
    `!highwater -> !highwater|!methane`, where dropping `!methane` leaves
    `!highwater -> !highwater`, syntactically different but logically
    identical to the original (still a tautology) - so not every
    syntactically-valid drop is an actual strengthening. GR1Formula's
    `__eq__` already does the semantic (spot-backed) equivalence check
    needed to catch this; candidates are generated exhaustively per move
    (rather than one random pick per move) specifically so the vacuous ones
    can be filtered out before choosing among what's left.
    """
    is_response = isinstance(formula.consequent, Eventually)
    consequent_target: LTLFormula = formula.consequent.formula if is_response else formula.consequent
    consequent_disjuncts = get_disjuncts_from_disjunction(consequent_target)
    antecedent_conjuncts = get_conjuncts_from_conjunction(formula.antecedent)

    candidates: List[GR1Formula] = []

    if len(consequent_disjuncts) > 1:
        for i in range(len(consequent_disjuncts)):
            remaining = list(consequent_disjuncts)
            remaining.pop(i)
            new_consequent = disjoin_all(remaining)
            if is_response:
                new_consequent = Eventually(new_consequent)
            candidates.append(GR1Formula(formula.temp_type, deepcopy(formula.antecedent), new_consequent))

    if len(antecedent_conjuncts) > 1:
        for i in range(len(antecedent_conjuncts)):
            remaining = list(antecedent_conjuncts)
            remaining.pop(i)
            new_antecedent = conjoin(remaining)
            candidates.append(GR1Formula(formula.temp_type, new_antecedent, deepcopy(formula.consequent)))

    if formula.temp_type == GR1TemporalType.JUSTICE:
        candidates.append(
            GR1Formula(GR1TemporalType.INVARIANT, deepcopy(formula.antecedent), deepcopy(formula.consequent))
        )

    candidates = [candidate for candidate in candidates if candidate != formula]
    if not candidates:
        return None
    return rng.choice(candidates)


def strengthen_random_formula(
        spec: SpectraSpecification,
        formula_types: Iterable[GR1FormulaType],
        rng: Optional[random.Random] = None,
) -> Optional[SpectraSpecification]:
    """
    Return a new specification, semantically stronger than `spec`, by
    applying one randomly-chosen strengthening pattern to one
    randomly-chosen candidate formula of the given types. `spec` itself
    is left unmodified. Returns None if no formula of the requested
    types has an applicable strengthening pattern.
    """
    rng = rng or random
    rows = [row for _, row in spec._formulas_df.iterrows() if row["type"] in formula_types]
    rng.shuffle(rows)
    for row in rows:
        new_formula = _try_strengthen(row["formula"], rng)
        if new_formula is not None:
            new_spec = deepcopy(spec)
            new_spec.replace_formula(row["name"], new_formula)
            return new_spec
    return None


def strengthen_spec(
        spec: SpectraSpecification,
        n_assumption_steps: int,
        n_guarantee_steps: int,
        rng: random.Random,
) -> Optional[SpectraSpecification]:
    """
    Apply `n_assumption_steps` assumption-strengthening steps, then
    `n_guarantee_steps` guarantee-strengthening steps, each building on the
    previous step's result (so the same formula can be hit more than once,
    compounding - e.g. dropping 2 of 3 antecedent conjuncts across two
    steps - or different formulas can be hit each time; both are valid
    single mutations).

    Unlike old_experiments.py's drop_random (which draws its whole batch of
    n drops from one combined assumption+guarantee pool, only pinning the
    *first* drop to an assumption), this keeps the two phases fully
    separate: every assumption step completes before any guarantee step is
    attempted. That guarantees the assumption side is always strengthened
    at least once (n_assumption_steps >= 1 in normal use), and any
    guarantee strengthening only ever happens on top of that - never
    interleaved with it.

    Returns None if some step finds no formula of that type left to
    strengthen (e.g. every candidate is already down to single-literal
    antecedents/consequents and not a justice formula) - the caller should
    treat that as "this particular (n_assumption_steps, n_guarantee_steps)
    combination isn't achievable right now" and retry with a fresh draw,
    not as "no more mutations exist at all".
    """
    current = spec
    for _ in range(n_assumption_steps):
        current = strengthen_random_formula(current, (GR1FormulaType.ASM,), rng)
        if current is None:
            return None
    for _ in range(n_guarantee_steps):
        current = strengthen_random_formula(current, (GR1FormulaType.GAR,), rng)
        if current is None:
            return None
    return current


def generate_realizable_mutations(
        ideal_spec: SpectraSpecification,
        n: int,
        max_assumption_steps: int = 2,
        max_guarantee_steps: int = 2,
        max_attempts_per_mutation: int = 50,
        rng: Optional[random.Random] = None,
) -> List[SpectraSpecification]:
    """
    Generate up to `n` distinct, realizable, semantically-stronger
    mutations of `ideal_spec`. Each attempt strengthens 1..max_assumption_steps
    assumptions first, then 0..max_guarantee_steps guarantees on top (so a
    mutation may leave guarantees untouched entirely) - see strengthen_spec.
    Guarantee-only strengthening isn't attempted on its own: touching a
    system's promises without first narrowing what it can assume about the
    environment is close to guaranteed to make it unrealizable, which is
    exactly the naive behaviour this two-phase approach is designed to
    avoid.

    Realizability is checked once per attempt, against the fully-composed
    mutation - matching old_experiments.py's drop_and_evaluate, which also
    only checks realizability after applying its whole batch of random
    drops, not per-drop.

    Stops early (with fewer than `n` results) if the attempt budget runs
    out before finding `n` distinct realizable mutations - e.g. because the
    formula pool is small enough to exhaust (arbiter's single assumption
    has exactly one possible mutation), or because most draws turn out
    unrealizable or duplicate an already-found mutation.
    """
    rng = rng or random
    mutations: List[SpectraSpecification] = []
    attempts = 0
    while len(mutations) < n and attempts < n * max_attempts_per_mutation:
        attempts += 1
        n_assumption_steps = rng.randint(1, max_assumption_steps)
        n_guarantee_steps = rng.randint(0, max_guarantee_steps)
        mutated = strengthen_spec(ideal_spec, n_assumption_steps, n_guarantee_steps, rng)
        if mutated is None:
            continue
        if any(mutated == existing for existing in mutations):
            continue
        if not SpectraGR1Oracle.is_realisable(mutated):
            continue
        mutations.append(mutated)
    return mutations


def generate_violating_traces(
        ideal_spec: SpectraSpecification,
        mutated_spec: SpectraSpecification,
        n_traces: int = 1,
) -> List[List[str]]:
    """
    Find up to `n_traces` distinct execution traces that satisfy
    `ideal_spec` while violating `mutated_spec`'s (stronger)
    assumptions/guarantees, via clingo (asp_trace_util.generate_trace_asp).
    Returns each trace as a list of ASP `holds_at(...)` fact lines.
    Returns fewer than `n_traces` (possibly none) if clingo can't find
    that many distinct violating traces within 3 timepoints.
    """
    ideal_file = generate_temp_filename(".spectra")
    mutated_file = generate_temp_filename(".spectra")
    trace_file = generate_temp_filename(".txt")
    # Plain to_str(), not is_to_compile=True: generate_trace_asp's extraction
    # (extract_expressions_from_file) regex-matches response patterns as
    # literal G(ant->F(cons)) text. is_to_compile=True instead rewrites those
    # into the pRespondsToS(...) macro form meant for Spectra CLI synthesis
    # input - an undefined ASP atom to this encoding, making it unsatisfiable.
    write_to_file(ideal_file, ideal_spec.to_str())
    write_to_file(mutated_file, mutated_spec.to_str())

    found = 0
    for _ in range(n_traces):
        result_file, _violation = generate_trace_asp(mutated_file, ideal_file, trace_file)
        if result_file is None:
            break
        found += 1

    if found == 0:
        return []
    return get_individual_traces(read_file_lines(trace_file))
