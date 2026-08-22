"""
Which runs actually weakened a guarantee?

The merge-first pipeline only changes the answer for a run whose guarantees were
degraded: where a merge already reaches the original's guarantees it has hit the
ceiling, since every repair weakens, so no stronger realisable merge can exist
and no filter before it can have cost anything.

Both sides are parsed and re-serialised before comparing. The merged files are
written by the model and `original.spectra` is hand-written source, so comparing
them as text reports every formatting difference as a change - on the first run
of this that flagged 40 of 47 runs, including ones whose guarantees are provably
equivalent to the original's.

A guarantee the merge dropped altogether is reported as `<name>(DROPPED)`;
iterating over what the merge kept cannot see those, and they are the worst
degradation there is.

    python scripts/report_guarantee_degradation.py
"""
import glob, os, re, sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.ltl_types import GR1FormulaType

ROOT = "tests/test_files/out/case_study_3"
SPECS = "input-files/case-studies/spectra/case_study_3"
DATE = "2026-08-13"


def guarantees(path):
    spec = SpectraSpecification.from_file(path)
    rows = spec._formulas_df
    out = {}
    for _, r in rows[rows["type"] == GR1FormulaType.GAR].iterrows():
        name = re.sub(r'_\d+$', '', str(r["name"]))
        out.setdefault(name, set()).add(" ".join(str(r["formula"]).split()))
    return out


rows = []
for d in sorted(glob.glob(f"{ROOT}/*_{DATE}")):
    base = os.path.basename(d).replace(f"_fastlas_{DATE}", "")
    case = re.sub(r"_trace\d+$", "", base)
    orig_path = f"{SPECS}/{case}/original.spectra"
    if not os.path.exists(orig_path):
        continue
    og = guarantees(orig_path)
    merged = sorted(glob.glob(f"{d}/filtered_merged_specs/*.spectra"))
    if not merged:
        rows.append((base, 0, None))
        continue
    degraded = set()
    for f in merged:
        got = guarantees(f)
        for name, forms in got.items():
            if name not in og or (forms - og[name]):
                degraded.add(name)
        # A guarantee the merge dropped altogether is the worst degradation
        # there is, and iterating over what the merge kept cannot see it.
        for name in og:
            if name not in got:
                degraded.add(f"{name}(DROPPED)")
    rows.append((base, len(merged), sorted(degraded)))

print(f"{'run':30} {'merged':>6}  guarantees weakened")
for base, n, degraded in rows:
    if degraded is None:
        print(f"{base:30} {n:>6}  -- no merge")
    else:
        print(f"{base:30} {n:>6}  {', '.join(degraded) if degraded else '(none)'}")
hits = [b for b, n, d in rows if d]
print()
print("RUNS WITH GUARANTEE DEGRADATION:", len(hits))
print(" ".join(hits))
