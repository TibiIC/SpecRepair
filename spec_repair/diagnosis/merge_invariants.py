r"""
What a correct merge output must satisfy, checked rather than assumed.

The merge returns the maximal realisable subsets of the pooled guarantees - the
complements of the minimal hitting sets of the unrealisable cores. Two
properties follow from that construction, and both are cheap enough to verify:

**Every output is realisable.** By construction, so a failure means the cores
were wrong or the hitting sets were computed over the wrong set.

**No two outputs are semantically equivalent.** This one is worth the proof,
because it is not obvious and because the failures it catches are silent.

    Fix the merged assumptions A*. For S a subset of the pooled guarantees E,
    write <S> for (A*, /\S) and R(S) for "<S> is realisable". Assume R is
    semantic - it depends only on the meaning of /\S - and monotone.

    Theorem. If S1 != S2 are both maximal realisable, then /\S1 !== /\S2.

    Proof. Suppose /\S1 == /\S2. Both are maximal by inclusion, so neither is a
    proper subset of the other, and there is some x in S2 \\ S1. From x in S2,
    /\S2 => x, so /\S1 => x, so /\(S1 + {x}) == /\S1. S1 is realisable, hence so
    is S1 + {x}, which strictly contains S1 - contradicting its maximality.

So a duplicate is never a cosmetic problem to be filtered away afterwards. It
means one of three things went wrong:

* the subsets were not maximal - typically an incomplete core enumeration, since
  the hitting-set argument needs *every* core and each one minimal;
* the merge returned something that is not a maximal realisable subset at all;
* realisability is not behaving semantically.

The third is not hypothetical here. Spectra calls
`G(h->Xp) & G(m->X!p)` unrealisable and
`G(h->Xp) & G(m->(X!p|Xm)) & G(m->(X!p|Xh)) & G(m->F X!p)` realisable, under
identical assumptions, though spot and a hand proof agree the two are
equivalent. The difference is a response-shaped `G(a -> F b)`, which sits
outside the GR(1) justice fragment. When a duplicate turns up, look for one of
those before suspecting the hitting sets.
"""
from __future__ import annotations

import logging
from typing import Callable, List, Optional, Sequence, Tuple

from spec_repair.ltl_types import GR1FormulaType

log = logging.getLogger(__name__)


class MergeInvariantViolated(Exception):
    """A merge output failed a property its construction guarantees."""


def find_equivalent_pairs(specs: Sequence,
                          formula_type: Optional[GR1FormulaType] = None
                          ) -> List[Tuple[int, int]]:
    """
    Indices of every pair of `specs` that are semantically equivalent.

    Quadratic in the number of specifications and each comparison is two
    implication checks, so this is for merge *outputs* - a handful - not for a
    pool. `formula_type` restricts the comparison; the default compares whole
    specifications, which is what the theorem is about.
    """
    pairs = []
    for i in range(len(specs)):
        for j in range(i + 1, len(specs)):
            a, b = specs[i], specs[j]
            if a.implies(b, formula_type) and b.implies(a, formula_type):
                pairs.append((i, j))
    return pairs


def check_merge_output(specs: Sequence,
                       oracle: Optional[Callable[[object], bool]] = None,
                       strict: bool = False) -> List[str]:
    """
    Verify what the merge's construction promises, and report what it finds.

    :param specs: the merge output.
    :param oracle: realisability check; when given, every output is tested.
        Skipped when None, since the caller has usually just paid for it.
    :param strict: raise `MergeInvariantViolated` instead of returning problems.
    :returns: a list of human-readable problems, empty when the output is sound.
    """
    problems: List[str] = []

    if oracle is not None:
        for index, spec in enumerate(specs):
            if not oracle(spec):
                problems.append(
                    f"specification {index} is not realisable; every merge "
                    f"output is realisable by construction, so the cores or the "
                    f"hitting sets are wrong")

    for i, j in find_equivalent_pairs(specs):
        problems.append(
            f"specifications {i} and {j} are semantically equivalent; distinct "
            f"maximal realisable subsets cannot be, so either they are not "
            f"maximal (an incomplete core enumeration), or realisability is not "
            f"behaving semantically - look for a response-shaped G(a -> F b) "
            f"among their guarantees before suspecting the hitting sets")

    for problem in problems:
        log.warning("merge invariant: %s", problem)
    if problems and strict:
        raise MergeInvariantViolated("; ".join(problems))
    return problems


def response_shaped_guarantees(spec) -> List[str]:
    """
    Guarantees of the form `G(... -> F ...)`, named.

    These are the ones Spectra reads more weakly than LTL does, so they are the
    first thing to look at when the semantic-uniqueness check fails.
    """
    rows = spec._formulas_df
    out = []
    for _, row in rows[rows["type"] == GR1FormulaType.GAR].iterrows():
        text = str(row["formula"])
        if "F(" in text:
            out.append(str(row["name"]))
    return out
