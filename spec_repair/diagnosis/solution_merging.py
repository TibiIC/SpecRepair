"""
Merging repaired specifications back into a single solution.

This is the one implementation of the merge procedure. It previously existed in
three near-identical copies - `scripts/merge_two_specs.py`,
`scripts/merge_all_specs.py` and `RepairBro.merge_two_solutions` - which had
quietly drifted apart: the two-spec versions asserted that the original
specification implies each repair, while the all-specs version had that check
commented out, so the same inputs could pass one path and fail another.

The binary case is just the n-ary case with two elements, so only
`merge_solutions` exists; `merge_two_solutions` is a thin alias kept for
readability at call sites that genuinely have exactly two.
"""
import logging
from typing import List, Optional, Sequence

from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.diagnosis.trivial_solution import get_all_trivial_solutions_guarantee_only
from spec_repair.interfaces.ioracle import IOracle
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.ltl_types import GR1FormulaType

log = logging.getLogger(__name__)


class UnrealisableInputError(ValueError):
    """Raised when a specification handed to the merge is not realisable."""


class NotAWeakeningError(ValueError):
    """Raised in strict mode when a spec is not implied by the original spec."""


def check_weakens_original(
        spec: ISpecification,
        og_spec: ISpecification,
        label: str = "specification",
        strict: bool = False,
) -> bool:
    """
    Check that `spec` really is a weakening of `og_spec` - i.e. the original
    implies it, on both assumptions and guarantees. Repairs are produced by
    weakening, so this should hold for anything coming out of the repair search.

    Returns True when it holds. When it does not, raises NotAWeakeningError if
    `strict`, otherwise logs a warning and returns False.

    Non-fatal by default deliberately: the three original implementations
    disagreed about whether this is an invariant (the two-spec paths asserted
    it, the all-specs path had it commented out), so failing hard by default
    would reject inputs that the directory-merging path has always accepted.
    Callers that treat it as a true invariant should pass strict=True.
    """
    failed = [
        formula_type.name
        for formula_type in (GR1FormulaType.ASM, GR1FormulaType.GAR)
        if not og_spec.implies(spec, formula_type)
    ]
    if not failed:
        return True
    message = (f"{label} is not implied by the original specification "
               f"({', '.join(failed)}), so it is not a weakening of it")
    if strict:
        raise NotAWeakeningError(message)
    log.warning(message)
    return False


def merge_solutions(
        specs: Sequence[ISpecification],
        og_spec: Optional[ISpecification] = None,
        oracle: Optional[IOracle] = None,
        strict: bool = False,
) -> List[ISpecification]:
    """
    Merge two or more repaired specifications into as few solutions as possible.

    Every input must be realisable. The specs are merged pairwise, left to
    right. If the result is realisable it is returned on its own; if it is not,
    the guarantee-only trivial solutions of the merge are returned instead,
    which is how an over-constrained merge gets broken back down into realisable
    pieces.

    :param specs: at least two specifications to merge.
    :param og_spec: optional original specification. When given, each input is
        checked to be a weakening of it - see `check_weakens_original`.
    :param oracle: realisability oracle; defaults to SpectraGR1Oracle.
    :param strict: make the weakening check fatal instead of a warning.
    :raises ValueError: if fewer than two specs are given.
    :raises UnrealisableInputError: if any input spec is unrealisable.
    """
    if len(specs) < 2:
        raise ValueError(f"Need at least 2 specifications to merge, got {len(specs)}.")
    oracle = oracle if oracle is not None else SpectraGR1Oracle()

    for i, spec in enumerate(specs):
        if not oracle.is_realisable(spec):
            raise UnrealisableInputError(f"Specification at index {i} is not realisable.")
        if og_spec is not None:
            check_weakens_original(spec, og_spec, label=f"Specification at index {i}", strict=strict)

    merged_spec = specs[0]
    for spec in specs[1:]:
        merged_spec = merged_spec.merge(spec)

    if oracle.is_realisable(merged_spec):
        return [merged_spec]

    # The merge conjoins guarantees, so it can easily over-constrain the system.
    # Fall back to the trivial guarantee-only solutions of the merged spec.
    new_merged_specs = get_all_trivial_solutions_guarantee_only(merged_spec)
    for new_merged_spec in new_merged_specs:
        if not oracle.is_realisable(new_merged_spec):
            log.warning("Merged solution is unrealisable:\n%s", new_merged_spec)
    return new_merged_specs


def merge_two_solutions(
        spec1: ISpecification,
        spec2: ISpecification,
        og_spec: Optional[ISpecification] = None,
        oracle: Optional[IOracle] = None,
        strict: bool = False,
) -> List[ISpecification]:
    """Readability alias for `merge_solutions([spec1, spec2], ...)`."""
    return merge_solutions([spec1, spec2], og_spec=og_spec, oracle=oracle, strict=strict)
