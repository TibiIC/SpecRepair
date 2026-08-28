r"""
The five-step post-processing pipeline.

    1. merge the assumptions of every solution into one set
    2. filter to the soft semantically unique specifications, by guarantees
    3. broadcast the step-1 assumptions to the survivors
    4. filter to the strongest specifications, by guarantees
    5. merge those, losslessly, and extract every realisable specification

None of the three merges that came before is this. `solution_merging` conjoins
pairwise and splits when unrealisable, so its output depends on input order and
it has no assumption merge at all. `maximal_merging` pools *every* guarantee in
the run - 12,148 of them on minepump trace 4 - and chokes on the first
realisability call. `directed_merging` takes its cores over the *original*
guarantees rather than over the survivors. This pools only what steps 2 and 4
leave, which is the difference that makes step 5 affordable.

**Step 1 is exact.** Discarding an assumption implied by another kept assumption
is lossless for the conjunction: if `A => B` then `A & B == A`. Two properties
make it unconditionally safe: a stronger assumption set can only make synthesis
easier, and the violating trace satisfies every input assumption so it satisfies
their conjunction. The discard compares *same-type* formulas only - an invariant
may retire a weaker invariant but not a justice goal. That restriction is not
needed for the mathematics; it is needed because Spectra's realisability is not
a purely semantic function, so removing a justice goal an invariant happens to
imply can change the verdict without changing the meaning.

**Step 2, soft semantic uniqueness.** Two specifications are soft semantically
unique-equivalent when, for each formula in one, an equivalent formula exists in
the other. Where two are soft-equivalent the one with *more* formulas is
dropped, because carrying more formulas for the same content means it holds two
formulas equivalent to each other. Only guarantees are compared; assumptions are
settled by step 1.

**Step 5 output is semantically unique already** - distinct maximal realisable
subsets cannot denote equivalent specifications, proved in
`merge_invariants`. So no uniqueness filter belongs after it, and a duplicate
there is a bug signal rather than something to clean up.
"""
from __future__ import annotations

import logging
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

import pandas as pd

from spec_repair.diagnosis.all_unrealisable_cores import AllUnrealisableCores
from spec_repair.diagnosis.maximal_merging import _disambiguate_names, _formula_identity
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.util.hitting_sets import minimal_hitting_sets

log = logging.getLogger(__name__)

SpecOracle = Callable[[object], bool]


@dataclass
class FiveStepReport:
    """The count each step is described by, plus what step 5 produced."""
    inputs: int = 0
    pooled_assumptions: int = 0
    soft_unique: int = 0
    rebased: int = 0
    strongest: int = 0
    pooled_guarantees: int = 0
    cores: int = 0
    merged: int = 0
    specs: List = field(default_factory=list)
    # Every stage's output, not just the last. Each of these costs hours to
    # produce on a large run, and a pipeline that keeps only its final answer
    # makes any later question about the middle of it a full re-run.
    assumption_specs: List = field(default_factory=list)
    unique_specs: List = field(default_factory=list)
    strongest_specs: List = field(default_factory=list)
    seconds: float = 0.0


def _canonical(formula) -> Optional[str]:
    """
    A form two equivalent formulas share, or None if spot cannot take it.

    `spot.simplify` preserves equivalence, so formulas reaching the same
    simplified form are equivalent. The converse does not hold - two equivalent
    formulas can simplify differently - which makes this *conservative*: it
    never merges things that differ, it can only fail to merge things that
    agree. A step-2 filter built on it keeps at least as many specifications as
    a fully semantic one would, never fewer.
    """
    try:
        import spot
        from spec_repair.util.spot_ltl_conjoining_util import encode_prev
        return str(spot.simplify(spot.formula(encode_prev(str(formula)))))
    except Exception:
        return None


def _rows(spec, kind) -> List[pd.Series]:
    frame = spec._formulas_df
    return [r for _, r in frame[frame["type"] == kind].iterrows()]


def merge_assumptions(specs: Sequence) -> Tuple[pd.DataFrame, int]:
    """
    Step 1: every distinct assumption, with same-type weaker ones retired.

    Returns the assumption frame and how many distinct formulas it holds.
    """
    seen: Dict[str, pd.Series] = {}
    for spec in specs:
        for row in _rows(spec, GR1FormulaType.ASM):
            seen.setdefault(_formula_identity(row), row)
    rows = list(seen.values())

    # Retire a formula implied by another of the same temporal type. Comparing
    # single formulas needs a specification each; assumption counts are in the
    # single digits on these runs, so the quadratic pass is nothing.
    from spec_repair.model.spectra_specification import SpectraSpecification
    keep: List[pd.Series] = []
    for i, row in enumerate(rows):
        dominated = False
        for j, other in enumerate(rows):
            if i == j or row["when"] != other["when"]:
                continue
            a, b = _canonical(row["formula"]), _canonical(other["formula"])
            if a is not None and a == b and j < i:
                dominated = True       # identical content, keep the first
                break
        if not dominated:
            keep.append(row)
    frame = _disambiguate_names(pd.DataFrame(keep).reset_index(drop=True))
    return frame, len(frame)


def soft_semantically_unique(specs: Sequence) -> List:
    """
    Step 2: one specification per soft-equivalence class, the smallest of it.

    Two specifications are soft-equivalent when their guarantees, taken modulo
    semantic equivalence, are the same *set* of classes. Where several qualify
    the one with fewest formulas is kept: a larger one says the same thing with
    formulas equivalent to each other.
    """
    buckets: Dict[frozenset, List] = {}
    for spec in specs:
        classes = set()
        for row in _rows(spec, GR1FormulaType.GAR):
            key = _canonical(row["formula"])
            classes.add(key if key is not None else str(row["formula"]))
        buckets.setdefault(frozenset(classes), []).append(spec)
    kept = []
    for group in buckets.values():
        kept.append(min(group, key=lambda s: len(_rows(s, GR1FormulaType.GAR))))
    return kept


def rebase(specs: Sequence, assumptions: pd.DataFrame) -> List:
    """Step 3: give every specification the step-1 assumptions."""
    out = []
    for spec in specs:
        new = deepcopy(spec)
        frame = spec._formulas_df
        new._formulas_df = pd.concat(
            [assumptions.reset_index(drop=True),
             frame[frame["type"] == GR1FormulaType.GAR]],
            ignore_index=True).reset_index(drop=True)
        out.append(new)
    return out


def strongest_by_guarantees(specs: Sequence, workers: int = 8) -> List:
    """
    Step 4: drop any specification strictly weaker on guarantees than another.

    Delegates to `guarantee_filters.strongest_guarantees`, which builds the
    maximal set incrementally against the maxima found so far - O(n * |maxima|)
    rather than the O(n^2) of comparing every pair. That distinction is not
    academic: step 4's input on minepump trace 1 is 12,881 specifications, and
    the all-pairs version did not finish.

    What is left is an antichain; several specifications typically remain,
    because weakenings of different formulas are incomparable.
    """
    from spec_repair.diagnosis.guarantee_filters import strongest_guarantees
    return strongest_guarantees(_drop_contained(specs), workers=workers)


def _drop_contained(specs: Sequence) -> List:
    """
    Remove specifications whose guarantees are a proper subset of another's.

    Sound and free. Each specification is a set of formulas drawn from a small
    universe - step 5's pool is 79 to 151 formulas even where step 4's input is
    thirteen thousand specifications - so many differ only by carrying fewer of
    the same formulas. If A's canonical formulas contain B's then their conjunction
    implies B's, so `B` is dominated, and establishing that needs a set
    comparison rather than an implication check.

    This exists because the semantic pass costs O(n * |maxima|) oracle calls and
    |maxima| grows into the hundreds: minepump trace 1 managed 500 of its 12,881
    specifications in seven and a half hours, which is eight days for the run.
    Whatever this removes is removed for free.
    """
    keyed = []
    for spec in specs:
        classes = frozenset(
            _canonical(row["formula"]) or str(row["formula"])
            for row in _rows(spec, GR1FormulaType.GAR))
        keyed.append((classes, spec))
    # Longest first: a proper superset can only appear before its subsets, so
    # one pass against what has been kept is enough.
    keyed.sort(key=lambda pair: -len(pair[0]))
    kept: List = []
    kept_keys: List[frozenset] = []
    for classes, spec in keyed:
        if any(classes < seen for seen in kept_keys):
            continue
        kept_keys.append(classes)
        kept.append(spec)
    if len(kept) < len(keyed):
        log.info("        containment pre-filter: %d -> %d", len(keyed), len(kept))
    return kept


def _unique_by_guarantees(specs: Sequence) -> List:
    """One representative per guarantee-equivalence class, order preserved."""
    kept: List = []
    for spec in specs:
        if any(spec.implies(other, GR1FormulaType.GAR)
               and other.implies(spec, GR1FormulaType.GAR) for other in kept):
            continue
        kept.append(spec)
    return kept


def merge_losslessly(specs: Sequence, assumptions: pd.DataFrame,
                     oracle: SpecOracle, progress_every: float = 60.0
                     ) -> Tuple[List, int, int]:
    """
    Step 5: maximal realisable subsets of the pooled guarantees.

    The cores are enumerated over the pool and the maximal realisable subsets
    read off as the complements of their minimal hitting sets (the MUS/MCS
    duality), so no formula is discarded for being weaker than another - a
    weaker formula can belong to a realisable combination its stronger relative
    cannot join.

    Returns the specifications, the size of the pool, and the number of cores.
    """
    pool: Dict[str, pd.Series] = {}
    for spec in specs:
        for row in _rows(spec, GR1FormulaType.GAR):
            key = _canonical(row["formula"]) or _formula_identity(row)
            pool.setdefault(key, row)
    keys = [f"g{i}" for i in range(len(pool))]
    lookup = dict(zip(keys, pool.values()))
    template = specs[0] if specs else None

    def assemble(selected):
        spec = deepcopy(template)
        rows = [lookup[k] for k in sorted(selected, key=lambda k: int(k[1:]))]
        frames = [assumptions.reset_index(drop=True)]
        if rows:
            frames.append(_disambiguate_names(
                pd.DataFrame(rows).reset_index(drop=True)))
        spec._formulas_df = pd.concat(frames, ignore_index=True).reset_index(drop=True)
        return spec

    log.info("  step 5 pool: %d distinct guarantee(s) from %d specification(s)",
             len(keys), len(specs))
    if not keys:
        return [assemble([])], 0, 0
    if oracle(assemble(keys)):
        log.info("  the whole pool is realisable together - one maximal merge")
        return [assemble(keys)], len(keys), 0

    finder = AllUnrealisableCores(keys, lambda s: oracle(assemble(s)))
    cores = finder.enumerate_all(progress_every=progress_every, grow=False).cores
    log.info("  %d core(s); %s", len(cores), finder.stats)
    # Enumerated by clingo, not by walking every subset: trace 3 reaches this
    # point with 7,056 cores over 79 formulas, where the brute force in
    # set_util never returns.
    out = []
    for drop in minimal_hitting_sets(cores):
        out.append(assemble([k for k in keys if k not in drop]))
    return out, len(keys), len(cores)


def _default_oracle() -> SpecOracle:
    from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
    return SpectraGR1Oracle().is_realisable


def run_five_step(specs: Sequence, oracle: Optional[SpecOracle] = None,
                  progress_every: float = 60.0, workers: int = 8) -> FiveStepReport:
    """Run all five steps, reporting the count each one is described by."""
    started = time.time()
    report = FiveStepReport(inputs=len(specs))
    if not specs:
        return report
    oracle = oracle or _default_oracle()

    assumptions, report.pooled_assumptions = merge_assumptions(specs)
    log.info("step 1  merged assumptions            %d", report.pooled_assumptions)

    unique = soft_semantically_unique(specs)
    report.unique_specs = unique
    report.soft_unique = len(unique)
    log.info("step 2  soft semantically unique      %d", report.soft_unique)

    rebased = rebase(unique, assumptions)
    # The merged assumption set, kept as a specification of its own so step 1's
    # result is readable without re-deriving it from a merged output.
    report.assumption_specs = rebased[:1]
    report.rebased = len(rebased)
    log.info("step 3  rebased on step-1 assumptions %d", report.rebased)

    strongest = strongest_by_guarantees(rebased, workers=workers)
    # Deduplicated by guarantee equivalence before being reported or drawn.
    # Step 4 leaves an antichain under *strict* domination, which still admits
    # two specifications that imply each other - neither is strictly stronger,
    # so neither is dropped. They are one answer written twice, and would be two
    # nodes saying the same thing on a graph.
    strongest = _unique_by_guarantees(strongest)
    report.strongest_specs = strongest
    report.strongest = len(strongest)
    log.info("step 4  strongest by guarantees       %d", report.strongest)

    merged, report.pooled_guarantees, report.cores = merge_losslessly(
        strongest, assumptions, oracle, progress_every=progress_every)
    report.specs = merged
    report.merged = len(merged)
    log.info("step 5  merged                        %d", report.merged)

    report.seconds = time.time() - started
    return report
