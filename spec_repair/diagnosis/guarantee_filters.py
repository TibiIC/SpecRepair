"""
Filters over a pool of repaired specifications, by their guarantees.

Lifted out of `scripts/filter_then_merge.py` so the five-step pipeline can use
the same implementation rather than a second, slower one. The first version in
`five_step` compared all n^2 pairs and stalled on minepump trace 1, whose step-4
input is 12,881 specifications - 166 million implication checks.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from spec_repair.ltl_types import GR1FormulaType

log = logging.getLogger(__name__)


def strongest_guarantees(specs, workers=1):
    """
    The maximal specifications under "strictly stronger guarantees".

    `a` is strictly stronger than `b` when a's guarantees imply b's and b's do
    not imply a's. That relation is a strict partial order - transitive, because
    implication is, and asymmetric by construction - so the maximal set can be
    built incrementally instead of by comparing all n^2 pairs:

        for each specification, compare it against the maxima found so far;
        if one of them is strictly stronger, discard it and stop;
        otherwise drop any maxima it is strictly stronger than, and keep it.

    That costs O(n * |maxima|), not O(n^2), and |maxima| shrinks whenever a
    dominating specification turns up. On a pool where most specifications are
    dominated - a BFS repair search producing thousands of progressively weaker
    variants - this is the cheap filter, and it is cheap in the right currency:
    every check is a GAR-only implication, on the guarantees alone, rather than
    a whole-specification equivalence.

    Guarantee-incomparable specifications all survive. They are different
    answers, not worse ones.
    """
    def strictly_stronger(a, b):
        return (a.implies(b, GR1FormulaType.GAR)
                and not b.implies(a, GR1FormulaType.GAR))

    maxima = []
    for n, spec in enumerate(specs, 1):
        dominated = False
        if workers <= 1 or len(maxima) < 4:
            for m in maxima:
                if strictly_stronger(m, spec):
                    dominated = True
                    break
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(strictly_stronger, m, spec) for m in maxima]
                try:
                    for f in futures:
                        if f.result():
                            dominated = True
                            break
                finally:
                    for f in futures:
                        f.cancel()
        if dominated:
            continue
        maxima = [m for m in maxima if not strictly_stronger(spec, m)]
        maxima.append(spec)
        if n % 250 == 0:
            print(f"         ...{n}/{len(specs)} scanned, {len(maxima)} maxima",
                  flush=True)
    return maxima
