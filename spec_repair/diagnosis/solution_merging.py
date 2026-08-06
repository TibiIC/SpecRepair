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


class MergeTooLargeError(ValueError):
    """
    Deprecated, and no longer raised by anything here.

    It used to guard the unrealisable-merge teardown with a formula-count cap,
    which refused to produce an answer at all above the limit. Divide and
    conquer removed the need for it - see `merge_solutions`. Kept only so an
    `except MergeTooLargeError` in older code still imports.
    """


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


def warn_if_merge_undid_the_weakening(
        merged: ISpecification,
        og_spec: ISpecification,
        label: str = "Merged specification",
) -> bool:
    """
    Check the merge is still a *strict* weakening of the original on assumptions.

    Returns True when it is. Otherwise logs a warning and returns False.

    Why this needs checking at all: merging conjoins, and the repair search
    routinely produces several weakenings of the same formula by adding
    alternative disjuncts. When two of those disjuncts cannot both hold -
    complementary literals like `X(p)` and `X(!p)`, or two members of a mutually
    exclusive family like `X(floor_middle)` and `X(floor_lower)` - conjoining
    them cancels the added disjunct and restores exactly the formula that was
    weakened. Measured on 2026-07-31: elevator, humanoid, lift and pcar all merge
    to assumptions semantically equivalent to the unrepaired original.

    Nothing else catches it. The merged spec is still realisable, and the ASP
    violation check still reports the trace as admitted, because on a finite
    prefix the disjuncts are individually satisfiable even though their
    conjunction is not. So it passes every other test while being, semantically,
    the specification the repair started from.

    A warning rather than an exception, matching `check_weakens_original`: the
    merge is not *wrong*, it is just not a repair, and callers studying the
    solution space may still want the result. See
    docs/session-notes/2026-07-31-merge-collapse-investigation.md.
    """
    if not og_spec.implies(merged, GR1FormulaType.ASM):
        # Not weaker at all - a different failure, already covered by
        # check_weakens_original on the inputs.
        return True
    if merged.implies(og_spec, GR1FormulaType.ASM):
        log.warning(
            "%s has assumptions semantically EQUIVALENT to the original, so the merge "
            "has undone the weakening it was built from. This usually means two repairs "
            "weakened the same formula with disjuncts that cannot both hold, and "
            "conjoining them restored the original.", label)
        return False
    return True


def _conjoin(specs: Sequence[ISpecification], progress_every: int = 0) -> ISpecification:
    """Merge a sequence of specifications pairwise, left to right."""
    merged = specs[0]
    for i, spec in enumerate(specs[1:], start=1):
        if progress_every and i % progress_every == 0:
            log.info("merging: %d/%d", i, len(specs))
        merged = merged.merge(spec)
    return merged


def _merge_realisable_pieces(
        specs: Sequence[ISpecification],
        oracle: IOracle,
        stats: dict,
        progress_every: int = 0,
) -> List[ISpecification]:
    """
    Merge `specs` into as few realisable specifications as possible, by divide
    and conquer.

    Merge the lot; if the result is realisable, that is the answer. If it is
    not, the set over-constrains the system, so split it in half and merge each
    half independently - a specification that cannot be merged with everything
    may still merge with most things.

    This replaces the previous "merge everything, then break the wreckage back
    down with the unrealisable-core search" approach, and the formula-count cap
    that had to guard it. The teardown was the problem: it starts from Spectra's
    exhaustive all-unrealisable-cores search, the same cost centre that makes
    ColorSort intractable, which on a 134-formula merge does not return at all -
    and being a blocking JVM call, cannot be interrupted from Python. Capping the
    formula count only converted a hang into a refusal; neither produces a
    result.

    Splitting instead means the expensive search is never reached on a large
    input. The cost is realisability checks, and it is proportional to how
    fragmented the answer actually is rather than to how many inputs there are:
    the recursion visits one node per check and bottoms out at k leaves, so k
    pieces cost 2k-1 checks. One check when everything merges, which is the
    common case - every small case study returns a single merged spec without
    ever splitting. Measured: lift 21 inputs -> 1 piece, 1 check; elevator_updated
    966 inputs -> 373 pieces, 745 checks, 173s, where the old teardown never
    returned.

    Termination is structural - each recursion halves the set, and a single
    specification cannot be split further.
    """
    merged = _conjoin(specs, progress_every=progress_every)
    stats["checks"] += 1
    if oracle.is_realisable(merged):
        return [merged]

    if len(specs) == 1:
        # A single specification that is unrealisable on its own - so an input
        # was unrealisable, not the merge. Break it down with the trivial
        # solutions, which is safe here in a way it is not on a large merge:
        # this is one repair-sized spec, the size the core search handles in
        # well under a second.
        log.warning("a single input specification is unrealisable on its own; "
                    "recovering realisable pieces from it via trivial solutions")
        stats["teardowns"] += 1
        return get_all_trivial_solutions_guarantee_only(merged)

    mid = len(specs) // 2
    stats["splits"] += 1
    log.info("merge of %d specs is unrealisable; splitting into %d + %d",
             len(specs), mid, len(specs) - mid)
    return (_merge_realisable_pieces(specs[:mid], oracle, stats)
            + _merge_realisable_pieces(specs[mid:], oracle, stats))


def _deduplicate(specs: Sequence[ISpecification]) -> List[ISpecification]:
    """
    Drop syntactically identical results, keeping order.

    Two halves of a split can easily merge to the same thing. Syntactic only -
    semantic deduplication is a separate, far more expensive step the pipeline
    already runs later.
    """
    seen = set()
    unique = []
    for spec in specs:
        key = spec.to_str()
        if key not in seen:
            seen.add(key)
            unique.append(spec)
    return unique


def merge_solutions(
        specs: Sequence[ISpecification],
        og_spec: Optional[ISpecification] = None,
        oracle: Optional[IOracle] = None,
        strict: bool = False,
        verify_inputs: bool = True,
        progress_every: int = 100,
        max_formulas_for_trivial_fallback: Optional[int] = None,
) -> List[ISpecification]:
    """
    Merge two or more repaired specifications into as few solutions as possible.

    The specs are merged pairwise, left to right. If the result is realisable it
    is returned on its own. If it is not, the set over-constrains the system, so
    it is split in half and each half merged independently, recursively - see
    `_merge_realisable_pieces`. Every returned specification is realisable.

    :param specs: at least two specifications to merge.
    :param og_spec: optional original specification. When given, each input is
        checked to be a weakening of it - see `check_weakens_original`.
    :param oracle: realisability oracle; defaults to SpectraGR1Oracle.
    :param strict: make the weakening check fatal instead of a warning.
    :param verify_inputs: check every input is realisable before merging. Each
        check is a separate Spectra synthesis call - around 0.7s on a small spec
        - so this is linear in the number of inputs and dominates everything
        else on a large set: 966 inputs cost ~11 minutes before any merging
        starts. Pass False when the inputs are realisable by construction, e.g.
        specs recorded by the BFS repair search, which only records a spec once
        the oracle has accepted it. Turning it off degrades gracefully rather
        than silently: merging is monotone, so an unrealisable input makes the
        merge unrealisable, which the post-merge check below still catches.
    :param progress_every: log progress every N specs during the long loops, so
        a large merge is visibly working rather than apparently hung.
    :param max_formulas_for_trivial_fallback: **deprecated and ignored.** It
        capped the size of merge whose teardown would be attempted; divide and
        conquer never reaches that teardown on a large merge, so there is
        nothing left to cap. Accepted so existing callers keep working.
    :raises ValueError: if fewer than two specs are given.
    :raises UnrealisableInputError: if any input spec is unrealisable.
    """
    if len(specs) < 2:
        raise ValueError(f"Need at least 2 specifications to merge, got {len(specs)}.")
    oracle = oracle if oracle is not None else SpectraGR1Oracle()
    if max_formulas_for_trivial_fallback is not None:
        log.warning("max_formulas_for_trivial_fallback is deprecated and ignored; "
                    "the merge now splits instead of capping")

    if verify_inputs or og_spec is not None:
        for i, spec in enumerate(specs):
            if progress_every and i and i % progress_every == 0:
                log.info("checking input specifications: %d/%d", i, len(specs))
            if verify_inputs and not oracle.is_realisable(spec):
                raise UnrealisableInputError(f"Specification at index {i} is not realisable.")
            if og_spec is not None:
                check_weakens_original(spec, og_spec, label=f"Specification at index {i}", strict=strict)

    # The merge conjoins guarantees, so it can easily over-constrain the system.
    # Rather than merging everything and then trying to break the wreckage back
    # down, split whenever the merge comes out unrealisable.
    stats = {"checks": 0, "splits": 0, "teardowns": 0}
    merged_specs = _deduplicate(
        _merge_realisable_pieces(specs, oracle, stats, progress_every=progress_every))

    log.info("merged %d specs into %d realisable specification(s) "
             "using %d realisability check(s), %d split(s)",
             len(specs), len(merged_specs), stats["checks"], stats["splits"])

    if og_spec is not None:
        for i, merged in enumerate(merged_specs):
            warn_if_merge_undid_the_weakening(merged, og_spec, label=f"Merged specification {i}")
    return merged_specs


def merge_two_solutions(
        spec1: ISpecification,
        spec2: ISpecification,
        og_spec: Optional[ISpecification] = None,
        oracle: Optional[IOracle] = None,
        strict: bool = False,
) -> List[ISpecification]:
    """Readability alias for `merge_solutions([spec1, spec2], ...)`."""
    return merge_solutions([spec1, spec2], og_spec=og_spec, oracle=oracle, strict=strict)
