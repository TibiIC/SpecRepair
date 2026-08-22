"""
Merging by enumerating maximal realisable subsets, rather than by greedy pairing.

**The problem with the greedy merge.** `merge_solutions` conjoins the pool left
to right and, when the conjunction comes out unrealisable, splits the set in
half and recurses. What it returns is therefore *one* partition of the input,
chosen by the order the specs arrived in, and it never revisits a pair that
landed either side of a split. Which merges it finds is luck.

Measured consequence, on `minepump_trace1_fastlas_2026-08-13`: the run's 26,877
specifications contain `G(methane -> (next(!pump) | next(methane)))` fifteen
times and the untouched `G(highwater -> next(pump))` 2,127 times, but never both
in the same specification. Every one of the fifteen is therefore strictly
dominated on guarantees, `strongest_gar` deletes all fifteen before the merge
runs, and the merge cannot conjoin what it never receives. Case study 1's
minepump kept that formula by a single specification which happened to pair it
with the untouched guarantee, and that one specification is why its merge
reached guarantees as strong as the original's.

**Why enumeration can promise what pairing cannot.** Realisability is antitone
under conjunction: adding a guarantee can only take realisability away, never
give it back. So the realisable subsets of a pool of guarantees are closed
downwards, and the strongest conjunctions anyone could form are exactly the
maximal elements of that family - the maximal realisable subsets. Enumerate
those and "no stronger realisable merge exists" holds by construction, whatever
order the pool arrived in.

That is the same monotone structure MARCO already exploits to enumerate cores,
so this reuses `AllUnrealisableCores`, which computes the maximal subsets on its
way to the cores.

**Granularity.** The pool is the distinct *formulas*, not the specifications
carrying them. Specification-level merging would work too - conjunction absorbs
a weakened variant that arrives alongside a stronger one, since
`G_weak & G_strong == G_strong` - but pooling formulas keeps the element set
small (roughly a thousand for minepump, against 26,877 specs) and stops a
formula's fate depending on its company.

**Assumptions are never enumerated over.** Realisability is antitone in the
guarantees but *monotone* in the assumptions - a stronger assumption asks the
system to handle fewer environments, so it can only help - and a predicate that
moves both ways at once is not the monotone one MARCO needs. The assumption side
is therefore fixed before the enumeration starts, by one of two policies:

``conjoin`` (the default)
    One pool. The assumptions are every distinct assumption formula in the
    input, conjoined, which is what `SpectraSpecification.merge` has always done
    and keeps these results comparable with the existing pipeline's. Each input
    assumption is a weakening of the original's, so the conjunction still is;
    but conjoining moves *back towards* the original, and far enough back it can
    put the violating trace outside the specification again. That is the failure
    `warn_if_merge_undid_the_weakening` exists to report, and it is unchanged
    here.

``group``
    Merge only specifications that already agree on their assumptions, leaving
    each assumption set exactly as some repair produced it. Nothing can undo a
    weakening, at the cost of merging much less - on minepump trace 0, whose
    repairs vary only in `assumption1_1`, this yields 17 groups of one and
    merges nothing at all.

Which is right depends on what the assumption side is claiming, so the caller
chooses; the guarantee-side guarantee is the same either way.

Every returned specification is realisable, and is still a weakening of the
original: each pooled formula is implied by the original's corresponding
formula, and a conjunction of consequences of `G_orig` is a consequence of
`G_orig`, so the property survives conjunction without needing a check.
"""
from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from spec_repair.diagnosis.all_unrealisable_cores import AllUnrealisableCores
from spec_repair.ltl_types import GR1FormulaType

log = logging.getLogger(__name__)

# Given a candidate specification, is it realisable?
SpecOracle = Callable[[object], bool]


@dataclass
class MergeGroup:
    """
    One assumption set, and the distinct guarantees pooled across it.

    `formulas` is keyed by an opaque `f0`, `f1`, ... rather than by the formula
    itself. The enumerator round-trips its element names through clingo, whose
    model parser reads `sel(<name>)` with a regex that stops at the first
    bracket, so a name containing `(` comes back truncated. Identity for pooling
    is tracked separately in `_identities`.
    """
    assumptions_key: str
    template: object                      # a spec holding only the assumptions
    formulas: Dict[str, pd.Series] = field(default_factory=dict)
    source_count: int = 0
    _identities: Dict[str, str] = field(default_factory=dict, repr=False)

    def __len__(self) -> int:
        return len(self.formulas)

    def add(self, row: pd.Series) -> None:
        identity = _formula_identity(row)
        if identity in self._identities:
            return
        key = f"f{len(self.formulas)}"
        self._identities[identity] = key
        self.formulas[key] = row


def _formula_identity(row: pd.Series) -> str:
    """Identity of a formula for pooling: what it says, not what it is called."""
    return f"{row['type']}\x1f{row['when']}\x1f{row['formula']}"


def _assumptions_key(spec) -> str:
    """Identity of an assumption set, order-insensitive."""
    rows = spec._formulas_df
    asm = rows[rows["type"] == GR1FormulaType.ASM]
    return "\n".join(sorted(f"{r['when']}|{r['formula']}" for _, r in asm.iterrows()))


def pool_all(specs: Sequence) -> List[MergeGroup]:
    """
    One group: every distinct assumption conjoined, every distinct guarantee.

    The `conjoin` policy. Assumption variants sharing a name are renamed
    `assumption1_1_0`, `assumption1_1_1`, ... the same way guarantee variants
    are, so the result is a specification Spectra will accept.
    """
    rows: Dict[str, pd.Series] = {}
    group: Optional[MergeGroup] = None
    for spec in specs:
        frame = spec._formulas_df
        for _, row in frame[frame["type"] == GR1FormulaType.ASM].iterrows():
            rows.setdefault(_formula_identity(row), row)
    if not specs:
        return []
    template = specs[0].extract_sub_specification(
        lambda df: df["type"] == GR1FormulaType.ASM)
    assumptions = _disambiguate_names(
        pd.DataFrame(list(rows.values())).reset_index(drop=True))
    template = deepcopy(template)
    template._formulas_df = assumptions.reset_index(drop=True)
    group = MergeGroup(assumptions_key="<conjoined>", template=template)
    for spec in specs:
        group.source_count += 1
        frame = spec._formulas_df
        for _, row in frame[frame["type"] == GR1FormulaType.GAR].iterrows():
            group.add(row)
    return [group]


def group_by_assumptions(specs: Sequence) -> List[MergeGroup]:
    """
    Pool the distinct guarantees of `specs`, one group per assumption set.

    The `group` policy. Groups come back largest first, since that is the order
    worth spending the oracle budget in.
    """
    groups: Dict[str, MergeGroup] = {}
    for spec in specs:
        key = _assumptions_key(spec)
        group = groups.get(key)
        if group is None:
            template = spec.extract_sub_specification(
                lambda df: df["type"] == GR1FormulaType.ASM)
            group = groups[key] = MergeGroup(assumptions_key=key, template=template)
        group.source_count += 1
        rows = spec._formulas_df
        for _, row in rows[rows["type"] == GR1FormulaType.GAR].iterrows():
            group.add(row)
    return sorted(groups.values(), key=lambda g: (-len(g), g.assumptions_key))


def _in_pool_order(keys) -> List[str]:
    """`f0, f1, ... f10` rather than the lexicographic `f0, f1, f10, f2`."""
    return sorted(keys, key=lambda k: int(k[1:]))


def _build(group: MergeGroup, keys: Sequence[str]):
    """A specification: the group's assumptions plus the named guarantees."""
    spec = deepcopy(group.template)
    rows = [group.formulas[k] for k in keys]
    if rows:
        chosen = pd.DataFrame(rows).reset_index(drop=True)
        chosen = _disambiguate_names(chosen)
        spec._formulas_df = pd.concat(
            [spec._formulas_df, chosen], ignore_index=True)
    spec._formulas_df = spec._formulas_df.reset_index(drop=True)
    return spec


def _disambiguate_names(rows: pd.DataFrame) -> pd.DataFrame:
    """
    Several variants of one original formula can share a name; Spectra cannot.

    Variants of `guarantee1_1` become `guarantee1_1_0`, `guarantee1_1_1`, ...
    and a name used once keeps it unchanged - the convention
    `SpectraSpecification.merge` already produces.
    """
    rows = rows.copy()
    counts = rows["name"].value_counts()
    seen: Dict[str, int] = {}
    names = []
    for name in rows["name"]:
        if counts[name] == 1:
            names.append(name)
            continue
        index = seen.get(name, 0)
        seen[name] = index + 1
        names.append(f"{name}_{index}")
    rows["name"] = names
    return rows


def _default_oracle() -> SpecOracle:
    from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
    return SpectraGR1Oracle().is_realisable


def maximal_merges(
        specs: Sequence,
        oracle: Optional[SpecOracle] = None,
        progress_every: float = 60.0,
        assumptions: str = "conjoin",
) -> List:
    """
    Every maximal realisable conjunction of the guarantees in `specs`.

    No returned specification can be strengthened by adding any other guarantee
    from the pool without losing realisability, and no ordering of the input
    changes the result. Two of them may still be incomparable in strength - that
    is a real property of the pool, not an artefact, and is the honest answer to
    "how many repairs are there".

    :param specs: the pool. Grouped by assumption set; each group merged apart.
    :param oracle: given a candidate specification, is it realisable? Defaults
        to Spectra.
    :param progress_every: seconds between progress lines; 0 silences them.
    :param assumptions: `"conjoin"` to merge every assumption into one pool, as
        the existing merge does, or `"group"` to merge only specifications that
        already agree on their assumptions. See the module docstring.
    """
    if assumptions not in ("conjoin", "group"):
        raise ValueError(f"assumptions must be 'conjoin' or 'group', got {assumptions!r}")
    if not specs:
        return []
    oracle = oracle or _default_oracle()
    results = []
    groups = (pool_all(specs) if assumptions == "conjoin"
              else group_by_assumptions(specs))
    log.info("merging %d spec(s) in %d assumption group(s) [%s]",
             len(specs), len(groups), assumptions)
    for number, group in enumerate(groups, start=1):
        log.info("group %d/%d: %d distinct guarantee(s) from %d spec(s)",
                 number, len(groups), len(group), group.source_count)
        results.extend(_merge_group(group, oracle, progress_every))
    return results


def _merge_group(group: MergeGroup, oracle: SpecOracle,
                 progress_every: float) -> List:
    keys = _in_pool_order(group.formulas)
    if not keys:
        return [deepcopy(group.template)]

    # The whole pool at once is one oracle call, and when it succeeds it is the
    # unique maximum - there is nothing left to enumerate. Worth trying first:
    # it is the common case on the small case studies, and the expensive path
    # below only exists for pools where it fails.
    everything = _build(group, keys)
    if oracle(everything):
        log.info("  the whole pool is realisable together - one maximal merge")
        return [everything]

    def subset_oracle(selected) -> bool:
        return oracle(_build(group, _in_pool_order(selected)))

    finder = AllUnrealisableCores(keys, subset_oracle)
    enumeration = finder.enumerate_all(progress_every=progress_every)
    log.info("  %s", enumeration.stats)
    return [_build(group, _in_pool_order(subset))
            for subset in enumeration.maximal_realisable_subsets]
