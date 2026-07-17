"""
Generate mutated, semantically stronger specifications and matching
violating traces from an ideal (realizable) specification.

Modernized port of the assumption-strengthening/violation-generation
pipeline in spec_repair/legacy/old_experiments.py (drop_random,
drop_and_evaluate) to operate on SpectraSpecification/GR1Formula objects
instead of raw regex-edited .spectra text.

Methodology (see old_experiments.py's module docstring-equivalent
research description): starting from an ideal specification, randomly
apply an assumption-strengthening pattern to obtain a mutated
specification with strictly narrower (stronger) assumptions/guarantees.
Each realizable mutation is paired with an execution trace, found via
clingo (util.asp_trace_util.generate_trace_asp, unchanged), that
satisfies the ideal specification's semantics while violating the
mutated specification's.

Three strengthening patterns are applied, chosen to match patterns
observed in this repo's own case-study fixtures
(input-files/case-studies/spectra/*/ideal.spectra vs strong.spectra):
- drop one disjunct from a formula's consequent (or the eventually-wrapped
  consequent of a response pattern) - narrows what satisfies the formula
- drop one conjunct from a formula's antecedent - broadens when the
  formula's consequent is required, narrowing the formula overall
- narrow a justice formula GF(f) to an invariant G(f) - drops the
  "eventually" allowance entirely
"""
import random
from copy import deepcopy
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from py_ltl.formula import Eventually, LTLFormula

from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.model.gr1_formula import GR1Formula
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.asp_trace_util import generate_trace_asp, get_individual_traces
from spec_repair.util.file_util import generate_temp_filename, read_file_lines, write_to_file
from spec_repair.util.ltl_formula_util import conjoin, disjoin_all, get_conjuncts_from_conjunction, \
    get_disjuncts_from_disjunction

DEFAULT_FORMULA_TYPES: Tuple[GR1FormulaType, ...] = (GR1FormulaType.ASM,)


def _try_strengthen(formula: GR1Formula, rng: random.Random) -> Optional[GR1Formula]:
    """
    Randomly pick one strengthening pattern applicable to `formula` and
    apply it, returning a new, strictly stronger GR1Formula. Returns None
    if no pattern applies (e.g. every consequent/antecedent is already a
    single literal, and the formula is already an invariant).
    """
    is_response = isinstance(formula.consequent, Eventually)
    consequent_target: LTLFormula = formula.consequent.formula if is_response else formula.consequent
    consequent_disjuncts = get_disjuncts_from_disjunction(consequent_target)
    antecedent_conjuncts = get_conjuncts_from_conjunction(formula.antecedent)

    moves: List[Callable[[], GR1Formula]] = []

    if len(consequent_disjuncts) > 1:
        def drop_consequent_disjunct() -> GR1Formula:
            remaining = list(consequent_disjuncts)
            remaining.pop(rng.randrange(len(remaining)))
            new_consequent = disjoin_all(remaining)
            if is_response:
                new_consequent = Eventually(new_consequent)
            return GR1Formula(formula.temp_type, deepcopy(formula.antecedent), new_consequent)

        moves.append(drop_consequent_disjunct)

    if len(antecedent_conjuncts) > 1:
        def drop_antecedent_conjunct() -> GR1Formula:
            remaining = list(antecedent_conjuncts)
            remaining.pop(rng.randrange(len(remaining)))
            new_antecedent = conjoin(remaining)
            return GR1Formula(formula.temp_type, new_antecedent, deepcopy(formula.consequent))

        moves.append(drop_antecedent_conjunct)

    if formula.temp_type == GR1TemporalType.JUSTICE:
        def justice_to_invariant() -> GR1Formula:
            return GR1Formula(GR1TemporalType.INVARIANT, deepcopy(formula.antecedent), deepcopy(formula.consequent))

        moves.append(justice_to_invariant)

    if not moves:
        return None
    return rng.choice(moves)()


def strengthen_random_formula(
        spec: SpectraSpecification,
        formula_types: Iterable[GR1FormulaType] = DEFAULT_FORMULA_TYPES,
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


def generate_realizable_mutations(
        ideal_spec: SpectraSpecification,
        n: int,
        formula_types: Iterable[GR1FormulaType] = DEFAULT_FORMULA_TYPES,
        max_attempts_per_mutation: int = 50,
        rng: Optional[random.Random] = None,
) -> List[SpectraSpecification]:
    """
    Generate up to `n` distinct, realizable, semantically-stronger
    mutations of `ideal_spec`. Each mutation is a single strengthening
    step away from `ideal_spec` (matching the granularity observed in
    this repo's own ideal.spectra/strong.spectra case-study fixtures).
    Stops early (with fewer than `n` results) if no formula can be
    strengthened further, or if realizable mutations can't be found
    within the attempt budget.
    """
    rng = rng or random
    mutations: List[SpectraSpecification] = []
    attempts = 0
    while len(mutations) < n and attempts < n * max_attempts_per_mutation:
        attempts += 1
        mutated = strengthen_random_formula(ideal_spec, formula_types, rng)
        if mutated is None:
            break
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
