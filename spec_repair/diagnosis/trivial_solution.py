from copy import deepcopy
from typing import Any, Optional

from spec_repair.components.new_spec_encoder import get_violated_expression_names_of_type
from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.enums import Learning
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.util.set_util import first_minimal_hitting_set, all_minimal_hitting_sets
from spec_repair.wrappers.spectra_toolbox import run_all_unrealisable_cores


def get_trivial_solution(spec: SpectraSpecification, violation_trace: list[str]) -> SpectraSpecification:
    """
    Generate a trivial solution for a given specification and violation trace.

    The function works by:
    1. Removing violated assumptions from the specification
    2. Finding unrealizable cores in the remaining specification
    3. Removing minimal set of guarantees to make spec realizable

    :param spec: The original specification to be modified
    :param violation_trace: Execution trace that violates the specification
    :return: Modified specification with removed assumptions and guarantees
    :raises ValueError: If spec or violation_trace is None
    """
    # Input validation
    if spec is None or violation_trace is None:
        raise ValueError("Specification and violation trace must not be None")

    # Step 1: Remove violated assumptions
    learner = OptimisingSpecLearner()
    violated_assumptions = get_violated_expression_names_of_type(
        learner.get_spec_violations(spec, violation_trace, [], Learning.ASSUMPTION_WEAKENING),
        'assumption'
    )
    print("Violated assumptions:", violated_assumptions)
    new_spec = spec.extract_sub_specification(
        lambda x: (x['type'] == GR1FormulaType.GAR) | (~x['name'].isin(violated_assumptions))
    )

    # Step 2: Find unrealizable cores
    unrealisable_cores = run_all_unrealisable_cores(new_spec.to_str(is_to_compile=True))
    if not (unrealisable_cores):
        print("No unrealizable cores found, new spec actually realizable.")
        return new_spec

    # Step 3: Remove minimal set of guarantees
    guarantees_to_remove = first_minimal_hitting_set(unrealisable_cores)
    print("Guarantees to remove:", guarantees_to_remove)
    trivial_spec = new_spec.extract_sub_specification(
        lambda x: (x['type'] == GR1FormulaType.ASM) | (~x['name'].isin(guarantees_to_remove))
    )

    return trivial_spec

def get_all_trivial_solution(spec: SpectraSpecification, violation_trace: list[str]) -> list[SpectraSpecification]:
    """
    Generate a trivial solution for a given specification and violation trace.

    The function works by:
    1. Removing violated assumptions from the specification
    2. Finding unrealizable cores in the remaining specification
    3. Removing minimal set of guarantees to make spec realizable

    :param spec: The original specification to be modified
    :param violation_trace: Execution trace that violates the specification
    :return: Modified specification with removed assumptions and guarantees
    :raises ValueError: If spec or violation_trace is None
    """
    # Input validation
    if spec is None or violation_trace is None:
        raise ValueError("Specification and violation trace must not be None")

    # Step 1: Remove violated assumptions
    learner = OptimisingSpecLearner()
    violated_assumptions = get_violated_expression_names_of_type(
        learner.get_spec_violations(spec, violation_trace, [], Learning.ASSUMPTION_WEAKENING),
        'assumption'
    )
    print("Violated assumptions:", violated_assumptions)
    new_spec = spec.extract_sub_specification(
        lambda x: (x['type'] == GR1FormulaType.GAR) | (~x['name'].isin(violated_assumptions))
    )

    return get_all_trivial_solutions_guarantee_only(new_spec)


def get_all_trivial_solutions_guarantee_only(
        new_spec: SpectraSpecification,
        cores: Optional[list[set]] = None,
        _seen: Optional[dict] = None,
) -> list[Any]:
    """
    Every trivialisation of `new_spec` that removes only guarantees.

    Syntech's `exploreAllCores` does not return every unrealisable core, and the
    ones it returns are not necessarily minimal, so removing a hitting set of
    them does not reliably yield a realisable specification. Hence the recheck:
    each candidate is verified, and any still-unrealisable one is trivialised
    again. That is inherent to the incomplete core enumeration, not something
    this function can assume away.

    What it *can* avoid is doing the same expensive work twice:

    * **The cores are passed into the recursion.** The recheck computed a
      candidate's cores and then called back in, which recomputed exactly those
      cores as its first act. Every unrealisable intermediate therefore cost two
      full core searches instead of one.
    * **No `list.remove` on specifications.** `SpectraSpecification.__eq__` is
      *semantic* equivalence via spot, so removing one candidate from the list
      ran an LTL equivalence check against each of the others. The list is now
      built by appending what survives.
    * **Results are memoised by specification text** across the recursion, since
      sibling branches routinely reach the same trivialisation by removing the
      same guarantees in a different order.

    Only the number of searches changes, not which solutions come back. It
    matters on the specifications where a single core search is measured in
    minutes rather than milliseconds - colorsort being the one that made this
    visible, at >150s where every other case study finishes under a second.
    """
    _seen = {} if _seen is None else _seen
    key = new_spec.to_str(is_to_compile=True)
    if key in _seen:
        return _seen[key]

    if cores is None:
        cores = run_all_unrealisable_cores(key)
    if not cores:
        _seen[key] = [new_spec]
        return [new_spec]

    trivial_specs: list[Any] = []
    for guarantees_to_remove in all_minimal_hitting_sets(cores):
        candidate = deepcopy(new_spec)
        for guarantee_to_remove in guarantees_to_remove:
            candidate.remove_formula(guarantee_to_remove)

        remaining = run_all_unrealisable_cores(candidate.to_str(is_to_compile=True))
        if remaining:
            trivial_specs.extend(
                get_all_trivial_solutions_guarantee_only(candidate, remaining, _seen))
        else:
            trivial_specs.append(candidate)

    _seen[key] = trivial_specs
    return trivial_specs
