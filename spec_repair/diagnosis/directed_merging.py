"""
Merging directed by the original specification's unrealisable cores.

**The shape of the problem.** A repaired pool holds thousands of alternative
weakenings of a handful of named formulas: minepump trace 4's 27,589
specifications carry 12,148 distinct guarantees between them, but the original
specification has *three*. `maximal_merging` searches the 12,148 directly, and
its first act - conjoining all of them for one realisability check - crashed the
JVM after seven hours on trace 4 and had not returned after two days on traces 1
to 3.

**The shape of the answer.** Start from the original guarantees, not from the
pool, and descend only as far as the cores force:

    base = pooled assumptions + the ORIGINAL guarantees
    if realisable(base):            base is the unique maximum, and we are done
    cores = minimal unrealisable cores of base    (MARCO, over ~3-5 elements)
    for each minimal hitting set H of those cores:
        every name in H must give way; weaken it from the pool
    the results are maximal because nothing was weakened that was not forced

Measured on minepump trace 4: the base check takes **1.2 seconds** and the core
enumeration **0.3 seconds**, returning one core, `{guarantee1_1, guarantee2_1}`.
Seven seconds against seven hours.

**This is the trivial-solution methodology, generalised.**
`trivial_solution.get_all_trivial_solutions_marco` already does cores, then
minimal hitting sets, then realisable-by-construction. It *deletes* each
implicated guarantee. This weakens it instead, deleting only when nothing in the
pool works - so deletion is the special case where the replacement is `true`.
Same skeleton, same completeness argument; one gives the floor, the other the
ceiling.

**Losslessness** rests on the same requirement as that path: every core, each
one minimal. A truncated enumeration silently breaks the hitting-set argument,
which is why nothing here is bounded.

By the MUS/MCS duality (Liffiton & Sakallah, JAR 40(1), 2008) the maximal
realisable subsets are the complements of the minimal hitting sets of the cores,
so they are read off combinatorially rather than reached by growing a seed one
oracle call at a time - which is what made the flat enumeration hopeless at this
size.

* Liffiton, Previti, Malik, Marques-Silva, *Fast, flexible MUS enumeration*,
  Constraints 21(2), 2016. https://doi.org/10.1007/s10601-015-9183-0
* Liffiton, Sakallah, *Algorithms for computing minimal unsatisfiable subsets of
  constraints*, JAR 40(1), 2008. https://doi.org/10.1007/s10817-007-9084-z
"""
from __future__ import annotations

import logging
import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Set

import pandas as pd

from spec_repair.diagnosis.all_unrealisable_cores import AllUnrealisableCores
from spec_repair.diagnosis.maximal_merging import (
    _disambiguate_names,
    _formula_identity,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.util.set_util import all_minimal_hitting_sets

log = logging.getLogger(__name__)

SpecOracle = Callable[[object], bool]


def _root_name(name: str, originals: Optional[Set[str]] = None) -> str:
    """
    Which original formula a name is a variant of.

    Regex alone cannot do this: the originals are themselves called
    `guarantee1_1`, so stripping a trailing `_<n>` turns an original name into
    `guarantee1`, which is nothing. The merge appends suffixes to make variants
    unique (`guarantee1_1_0`, `guarantee1_1_1`), so the rule is to strip
    suffixes only while the result is not already an original name, and to stop
    as soon as it is.
    """
    name = str(name)
    if originals is None or name in originals:
        return name
    candidate = name
    while True:
        stripped = re.sub(r"_\d+$", "", candidate)
        if stripped == candidate:
            return name          # nothing matched; keep it as its own root
        if stripped in originals:
            return stripped
        candidate = stripped


@dataclass
class Pool:
    """What the run produced, indexed by the original formula each entry weakens."""
    assumptions: pd.DataFrame
    variants: Dict[str, List[pd.Series]] = field(default_factory=dict)
    spec_count: int = 0

    def variant_count(self) -> int:
        return sum(len(v) for v in self.variants.values())


def build_pool(specs: Sequence, sample: Optional[int] = None,
               original_names: Optional[Set[str]] = None) -> Pool:
    """
    Distinct assumptions and distinct guarantee variants, grouped by root name.

    `sample` limits how many specifications are read when collecting
    *assumptions* only - these runs carry four or five distinct assumption sets
    across tens of thousands of files, so reading all of them buys nothing.
    Guarantee variants are always taken from every specification given.
    """
    seen_asm: Dict[str, pd.Series] = {}
    seen_gar: Dict[str, Set[str]] = {}
    variants: Dict[str, List[pd.Series]] = {}
    for index, spec in enumerate(specs):
        frame = spec._formulas_df
        if sample is None or index < sample:
            for _, row in frame[frame["type"] == GR1FormulaType.ASM].iterrows():
                seen_asm.setdefault(_formula_identity(row), row)
        for _, row in frame[frame["type"] == GR1FormulaType.GAR].iterrows():
            root = _root_name(row["name"], original_names)
            identity = _formula_identity(row)
            bucket = seen_gar.setdefault(root, set())
            if identity in bucket:
                continue
            bucket.add(identity)
            variants.setdefault(root, []).append(row)
    assumptions = _disambiguate_names(
        pd.DataFrame(list(seen_asm.values())).reset_index(drop=True))
    return Pool(assumptions=assumptions, variants=variants, spec_count=len(specs))


def _assemble(template, assumptions: pd.DataFrame, rows: Sequence[pd.Series]):
    """A specification from an assumption frame and a list of guarantee rows."""
    spec = deepcopy(template)
    frames = [assumptions.reset_index(drop=True)]
    if rows:
        frames.append(_disambiguate_names(
            pd.DataFrame(list(rows)).reset_index(drop=True)))
    spec._formulas_df = pd.concat(frames, ignore_index=True).reset_index(drop=True)
    return spec


def _default_oracle() -> SpecOracle:
    from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
    return SpectraGR1Oracle().is_realisable


def directed_merges(
        specs: Sequence,
        original,
        oracle: Optional[SpecOracle] = None,
        progress_every: float = 60.0,
        assumption_sample: Optional[int] = 300,
) -> List:
    """
    The strongest realisable weakenings of `original` reachable from `specs`.

    :param specs: the repaired pool.
    :param original: the specification the repairs weaken; its guarantees are
        the ceiling the search starts from.
    :param oracle: realisability of a candidate. Defaults to Spectra.
    :param progress_every: seconds between progress lines; 0 silences them.
    :param assumption_sample: how many specifications to read assumptions from;
        None reads all of them.
    """
    if not specs:
        return []
    oracle = oracle or _default_oracle()
    started = time.time()

    frame = original._formulas_df
    original_names = {str(r["name"]) for _, r in
                      frame[frame["type"] == GR1FormulaType.GAR].iterrows()}
    pool = build_pool(specs, sample=assumption_sample,
                      original_names=original_names)
    log.info("pool: %d spec(s), %d distinct assumption(s), %d guarantee variant(s) "
             "across %d name(s)", pool.spec_count, len(pool.assumptions),
             pool.variant_count(), len(pool.variants))

    originals = [row for _, row in frame[frame["type"] == GR1FormulaType.GAR].iterrows()]

    base = _assemble(original, pool.assumptions, originals)
    log.info("base: %d assumption(s) + %d ORIGINAL guarantee(s) - one check",
             len(pool.assumptions), len(originals))
    if oracle(base):
        log.info("base is realisable: the unique maximum, in one call (%.1fs)",
                 time.time() - started)
        return [base]

    names = [str(r["name"]) for r in originals]
    finder = AllUnrealisableCores(
        names,
        lambda keep: oracle(_assemble(
            original, pool.assumptions,
            [r for r in originals if str(r["name"]) in keep])))
    cores = finder.enumerate_all(progress_every=progress_every).cores
    log.info("cores over the original guarantees: %d (%.1fs)",
             len(cores), time.time() - started)
    for core in cores:
        log.info("   core: %s", sorted(core))
    if not cores:
        raise RuntimeError(
            "base was unrealisable but has no unrealisable core; the oracle "
            "is not monotone, or the base failed for a reason other than "
            "unrealisability.")

    results = []
    hitting_sets = list(all_minimal_hitting_sets(cores))
    log.info("minimal hitting sets: %d - one branch each", len(hitting_sets))
    for number, hs in enumerate(hitting_sets, start=1):
        implicated = {_root_name(n, original_names) for n in hs}
        kept = [r for r in originals
                if _root_name(r["name"], original_names) not in implicated]
        candidates = [v for name in sorted(implicated)
                      for v in pool.variants.get(name, [])]
        log.info("branch %d/%d: weakening %s - %d variant(s) available, "
                 "%d original guarantee(s) held fixed",
                 number, len(hitting_sets), sorted(implicated),
                 len(candidates), len(kept))
        results.extend(
            _weakest_forced(original, pool, kept, candidates, oracle, progress_every))

    log.info("directed merge produced %d specification(s) in %.1fs",
             len(results), time.time() - started)
    return results


def _weakest_forced(original, pool: Pool, kept, candidates, oracle,
                    progress_every: float) -> List:
    """
    Maximal realisable conjunctions of `candidates`, with `kept` always present.

    The guarantees held fixed are the ones no core implicated, so they are never
    in question; only the variants of the implicated names are enumerated over.
    A branch whose candidates are all unusable degenerates to `kept` alone, which
    is the trivial solution for that hitting set - deletion as the limiting case
    of weakening.
    """
    if not candidates:
        return [_assemble(original, pool.assumptions, kept)]
    keys = [f"v{i}" for i in range(len(candidates))]
    lookup = dict(zip(keys, candidates))

    def check(selected) -> bool:
        rows = kept + [lookup[k] for k in sorted(selected, key=lambda k: int(k[1:]))]
        return oracle(_assemble(original, pool.assumptions, rows))

    enumeration = AllUnrealisableCores(keys, check).enumerate_all(
        progress_every=progress_every)
    log.info("   %s", enumeration.stats)
    out = []
    for subset in enumeration.maximal_realisable_subsets:
        rows = kept + [lookup[k] for k in sorted(subset, key=lambda k: int(k[1:]))]
        out.append(_assemble(original, pool.assumptions, rows))
    return out or [_assemble(original, pool.assumptions, kept)]
