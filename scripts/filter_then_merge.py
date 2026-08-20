#!/usr/bin/env python3
"""
Filter first, merge second - the methodology, in the order it was specified.

    1. semantically unique   drop any specification that another in the pool is
                             semantically equivalent to
    2. strongest guarantees  of those, keep the ones no other specification's
                             guarantees are strictly stronger than (incomparable
                             ones all survive)

Stage 1 comes first and there is no input cap. The order is not interchangeable:
equivalent specifications imply each other in both directions, so neither is
"strictly stronger" and stage 2 keeps them both. Stage 2 therefore cannot remove
a single duplicate, and running it first would pay a full O(n^2) of guarantee
implications while leaving stage 1 exactly as much work as before. Measured, the
filters bear that out - stage 1 removes 50-65% of a pool, stage 2 removed
nothing at all on every 21-specification run.
    3. merge                 only that pool is merged

`scripts/run_experiment_pipeline.py` has had this backwards since it was written
on 2026-07-27: it merges the whole pool and then filters the *merged* output.
That inflates the merge from a handful of specifications to the entire result
set - 24,619 for traffic_single trace 1 - and conjoins fifteen variants of the
same assumption, five of them carrying `PREV`, whose rewrite expands a
563-character formula into 177,492 characters of nested `X`.

Reports the count at each stage, because that is the number the methodology is
described by.

    python scripts/filter_then_merge.py <run_dir> [--out <dir>] [--workers N]
"""
import argparse
import glob
from concurrent.futures import ThreadPoolExecutor
import itertools
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.exceptions import EquivalenceUndecided
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file


UNDECIDED = []


def _equivalent_or_undecided(spec, other):
    """
    Whether `spec` is equivalent to `other`, counting the checks that time out.

    An undecided check is reported as *not* equivalent, which keeps both
    specifications. That is the conservative direction for a filter - it can
    only leave the pool larger than the exact answer would, never smaller, so no
    repair is ever discarded on the strength of a question that was not
    answered. It does mean the unique count is an upper bound whenever anything
    lands in `UNDECIDED`, and the run says so at the end rather than reporting a
    number that looks exact.
    """
    try:
        return spec.equivalent_to(other)
    except EquivalenceUndecided as e:
        UNDECIDED.append(str(e))
        return False


def _equivalent_to_any(spec, kept, workers):
    """
    True if `spec` is equivalent to anything in `kept`.

    Every check is an `ltlfilt`/`ltl2tgba` subprocess that this thread only
    waits on, so threads - not processes - are the right pool: the GIL is
    released for the whole call and nothing has to be pickled. Submitted in
    order and consumed in order, cancelling the rest at the first hit, so the
    common case (an early duplicate) still costs about what the serial loop
    cost, while a genuinely new specification gets its whole scan in parallel.
    """
    if not kept:
        return False
    if workers <= 1:
        return any(_equivalent_or_undecided(spec, other) for other in kept)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_equivalent_or_undecided, spec, other)
                   for other in kept]
        try:
            for f in futures:
                if f.result():
                    return True
        finally:
            for f in futures:
                f.cancel()
    return False


def semantically_unique(specs, workers=1):
    """
    One representative per equivalence class, keeping first-seen order.

    Two tiers, both exact - this never merges specifications that differ:

    1. identical serialisations collapse with no Spot call at all. A BFS search
       reaches the same specification by many paths, and those cost nothing to
       recognise.
    2. what survives is compared semantically against the representatives kept
       so far, `workers` checks at a time.

    There is deliberately no bucketing by automaton size or any other cheap
    "semantic fingerprint". Spot's minimisation is heuristic, not canonical, so
    two equivalent specifications can minimise to different-sized automata;
    bucketing on that would put them in different buckets, keep both, and
    silently report more unique specifications than there are. An
    over-reported uniqueness count is exactly the kind of wrong number that
    reads as a result.
    """
    by_text = {}
    for spec in specs:
        by_text.setdefault(spec.to_str(), spec)
    candidates = list(by_text.values())
    if len(candidates) < len(specs):
        print(f"stage 1a identical serialisations     {len(specs)} -> {len(candidates)}",
              flush=True)

    kept = []
    for spec in candidates:
        if not _equivalent_to_any(spec, kept, workers):
            kept.append(spec)
    return kept


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


def _undecided_note() -> str:
    """A suffix naming how many equivalence checks were never decided."""
    if not UNDECIDED:
        return ""
    return (f"   [upper bound: {len(UNDECIDED)} equivalence check(s) hit "
            f"SPEC_REPAIR_EQUIV_TIMEOUT and were counted as not equivalent]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None, help="where to write the merged result")
    ap.add_argument("--workers", type=int, default=8,
                    help="concurrent ltlfilt/ltl2tgba subprocesses (default 8)")
    ap.add_argument("--unique-only", action="store_true",
                    help="stop after the equivalence filter, applied to the raw "
                         "pool, and write the representatives to unique_specs/. "
                         "This is the count the paper reports as 'unique', which "
                         "is not the same number the full pipeline reaches: there "
                         "the guarantee filter has already removed dominated "
                         "specifications, so classes that were entirely dominated "
                         "never reach the equivalence check at all.")
    ap.add_argument("--strongest-first", action="store_true",
                    help="run the guarantee filter before the equivalence filter. "
                         "Same final set, far cheaper on a large pool")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.run_dir, "final_specs", "*.spectra")))
    print(f"stage 0  final specs on disk          {len(files)}", flush=True)
    if not files:
        return 1

    specs = [SpectraSpecification.from_file(f) for f in files]
    by_text = {}
    for spec in specs:
        by_text.setdefault(spec.to_str(), spec)
    if len(by_text) < len(specs):
        print(f"stage 0a identical serialisations     {len(specs)} -> {len(by_text)}",
              flush=True)
        specs = list(by_text.values())

    if args.unique_only:
        unique = semantically_unique(specs, workers=args.workers)
        print(f"stage 1  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)
        # A name of its own: `unique_specs/` is what run_experiment_pipeline
        # writes for its own stage 2, and these two are not the same set.
        out = args.out or os.path.join(args.run_dir, "unique_from_final_specs")
        os.makedirs(out, exist_ok=True)
        for i, spec in enumerate(unique):
            write_to_file(os.path.join(out, f"spec_{i}.spectra"), spec.to_str())
        print(f"         written to {out}", flush=True)
        return 0

    if args.strongest_first:
        # Same final set, reached more cheaply. Dropping a dominated
        # specification needs GAR-only implications and stops at the first
        # dominator; proving two specifications equivalent needs the whole
        # specification and cannot stop early. On a pool where most entries are
        # dominated it is much cheaper to throw them out before paying for any
        # equivalence check. The composition is unchanged either way: equivalent
        # specifications imply each other in both directions, so the guarantee
        # filter never separates an equivalence class - it keeps all of a class
        # or, if something dominates it, none of it.
        strongest = strongest_guarantees(specs, workers=args.workers)
        print(f"stage 1  strongest guarantees         {len(strongest)}", flush=True)
        unique = semantically_unique(strongest, workers=args.workers)
        print(f"stage 2  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)
        strongest = unique
    else:
        unique = semantically_unique(specs, workers=args.workers)
        print(f"stage 1  semantically unique          {len(unique)}"
              f"{_undecided_note()}", flush=True)

        strongest = strongest_guarantees(unique, workers=args.workers)
        print(f"stage 2  strongest guarantees         {len(strongest)}", flush=True)

    from spec_repair.diagnosis.solution_merging import merge_solutions
    merged = (list(strongest) if len(strongest) < 2
              else merge_solutions(strongest, verify_inputs=False))
    print(f"stage 3  merged                       {len(merged)}", flush=True)

    out = args.out or os.path.join(args.run_dir, "filtered_merged_specs")
    os.makedirs(out, exist_ok=True)
    for i, spec in enumerate(merged):
        write_to_file(os.path.join(out, f"spec_{i}.spectra"), spec.to_str())
    print(f"         written to {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
