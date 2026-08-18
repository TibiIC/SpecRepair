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

    python scripts/filter_then_merge.py <run_dir> [--out <dir>]
"""
import argparse
import glob
import itertools
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file


def semantically_unique(specs):
    """One representative per equivalence class, keeping first-seen order."""
    kept = []
    for spec in specs:
        if not any(spec.equivalent_to(other) for other in kept):
            kept.append(spec)
    return kept


def strongest_guarantees(specs):
    """
    Those no other specification's guarantees are strictly stronger than.

    `a` is strictly stronger than `b` when a's guarantees imply b's and b's do
    not imply a's. Incomparable specifications all survive, which is the point -
    they are different answers, not worse ones.
    """
    kept = []
    for i, spec in enumerate(specs):
        dominated = False
        for j, other in enumerate(specs):
            if i == j:
                continue
            if (other.implies(spec, GR1FormulaType.GAR)
                    and not spec.implies(other, GR1FormulaType.GAR)):
                dominated = True
                break
        if not dominated:
            kept.append(spec)
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None, help="where to write the merged result")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.run_dir, "final_specs", "*.spectra")))
    print(f"stage 0  final specs on disk          {len(files)}", flush=True)
    if not files:
        return 1

    specs = [SpectraSpecification.from_file(f) for f in files]

    unique = semantically_unique(specs)
    print(f"stage 1  semantically unique          {len(unique)}", flush=True)

    strongest = strongest_guarantees(unique)
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
