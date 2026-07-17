from typing import Iterable, List, Optional, Tuple
import random

from spec_repair.diagnosis.spec_mutation import DEFAULT_FORMULA_TYPES, generate_realizable_mutations, \
    generate_violating_traces
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification


def generate_stronger_specs_with_violations(
        ideal_spec: SpectraSpecification,
        n_mutations: int,
        n_traces_per_mutation: int = 1,
        formula_types: Iterable[GR1FormulaType] = DEFAULT_FORMULA_TYPES,
        rng: Optional[random.Random] = None,
) -> List[Tuple[SpectraSpecification, List[List[str]]]]:
    """
    Starting from an ideal (realizable) specification, generate up to
    `n_mutations` mutated specifications with semantically stronger
    assumptions (and/or guarantees, if `formula_types` includes GAR),
    each paired with up to `n_traces_per_mutation` execution traces that
    satisfy the ideal specification while violating the mutated one.

    Mutations for which no violating trace could be found are dropped -
    every (spec, traces) pair returned has at least one trace.
    """
    mutated_specs = generate_realizable_mutations(
        ideal_spec, n_mutations, formula_types=formula_types, rng=rng
    )
    results: List[Tuple[SpectraSpecification, List[List[str]]]] = []
    for mutated_spec in mutated_specs:
        traces = generate_violating_traces(ideal_spec, mutated_spec, n_traces=n_traces_per_mutation)
        if traces:
            results.append((mutated_spec, traces))
    return results
