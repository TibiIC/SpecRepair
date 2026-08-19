#!/usr/bin/env python3
"""
Merge the assumptions of every specification a repair run found, into one.

Merging assumptions means conjoining them, and a conjunct that the accumulated
conjunction already implies contributes nothing:

    if  C |= A'   then   C & A' == C

so A' is dropped. Only a formula that *changes the semantics* of the merged
assumption is kept. The result is a minimal set of assumption formulas whose
conjunction is equivalent to the conjunction of every assumption in the pool.

Two properties make this the right operation on a pool of repairs:

* it stays a repair. Each specification's assumptions admit the violating trace
  - that is what made it a repair - and a trace satisfying every A_i satisfies
  their conjunction, so the merged assumption admits it too.
* it stays a weakening. Each A_i is weaker than the original's assumptions, so
  the conjunction is weaker than or equal to them as well; it cannot collapse
  back to the original.

Runs over `final_specs/` - every repair the search found - deliberately, and not
over the filtered pool. The strongest-guarantees filter drops a repair whenever
another has strictly stronger guarantees, which on these case studies removes
every guarantee-weakening repair as soon as one assumption-only repair exists.
Those repairs still learned something about the environment, and this step is
where their assumptions get counted.

    python scripts/merge_assumptions.py <run_dir> [--out <dir>] [--workers N]
"""
import argparse
import glob
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file


def assumption_rows(spec):
    """(name, GR1Formula) for each assumption, in file order."""
    df = spec._formulas_df
    return [(r["name"], r["formula"])
            for _, r in df[df["type"] == GR1FormulaType.ASM].iterrows()]


def without_assumptions(spec):
    bare = deepcopy(spec)
    for name, _ in assumption_rows(bare):
        bare.remove_formula(name)
    return bare


def with_only(template, formulas):
    """A specification carrying `formulas` as its assumptions and nothing else."""
    out = deepcopy(template)
    for i, formula in enumerate(formulas):
        out.add_formula(deepcopy(formula), f"merged_asm_{i}", GR1FormulaType.ASM)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=8,
                    help="concurrent implication checks when screening candidates")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.run_dir, "final_specs", "*.spectra")))
    print(f"stage 0  final specs on disk          {len(files)}", flush=True)
    if not files:
        return 1

    specs = [SpectraSpecification.from_file(f) for f in files]

    # Syntactically distinct conjuncts first. A BFS search repeats the same
    # assumption across thousands of specifications, and recognising that costs
    # no Spot call at all - without it the implication checks below are run once
    # per occurrence rather than once per distinct formula.
    seen, candidates = set(), []
    total = 0
    for spec in specs:
        for _, formula in assumption_rows(spec):
            total += 1
            key = str(formula)
            if key not in seen:
                seen.add(key)
                candidates.append(formula)
    print(f"stage 1  assumption formulas          {total} -> {len(candidates)} distinct",
          flush=True)

    template = without_assumptions(specs[0])

    kept = []
    for n, candidate in enumerate(candidates, 1):
        if kept:
            acc = with_only(template, kept)
            cand = with_only(template, [candidate])
            # Already implied: conjoining it would not change the semantics.
            if acc.implies(cand, GR1FormulaType.ASM):
                continue
            # It says something new. Anything already kept that *it* implies is
            # now redundant in turn, so drop those rather than carrying them.
            keep_after = []
            for existing in kept:
                one = with_only(template, [existing])
                if not cand.implies(one, GR1FormulaType.ASM):
                    keep_after.append(existing)
            kept = keep_after
        kept.append(candidate)
        if n % 25 == 0:
            print(f"         ...{n}/{len(candidates)} screened, {len(kept)} kept",
                  flush=True)
    print(f"stage 2  semantically distinct        {len(kept)}", flush=True)

    merged = with_only(template, kept)
    out = args.out or os.path.join(args.run_dir, "merged_assumptions")
    os.makedirs(out, exist_ok=True)
    write_to_file(os.path.join(out, "merged_assumptions.spectra"), merged.to_str())
    print(f"         written to {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
