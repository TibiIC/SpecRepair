#!/usr/bin/env python3
"""
What each repair actually changed, per run, as a markdown table.

Reads `final_specs/` and compares every repaired specification against the
original by formula *name*: which assumptions and guarantees were weakened,
which were dropped entirely, and how many distinct expressions the run touched
across all its solutions.

Needs no merging and no realisability check, so it runs on completed results
immediately, on any machine.

    python scripts/report_repair_modifications.py 2026-08-13 --setup case_study_3
    python scripts/report_repair_modifications.py 2026-08-13 -o docs/results/x.md
"""
import argparse
import datetime
import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

RUN_RE = re.compile(r"^(?P<case>[a-z_]+?)_trace(?P<trace>\d+)(?:_(?P<learner>fastlas|ilasp))?_(?P<date>\d{4}-\d{2}-\d{2})$")
BLOCK_RE = re.compile(r"^\s*(assumption|guarantee|asm|gar)\s*--\s*(\S+)\s*$")


def parse_formulas(path):
    """
    {name: (kind, formula_text)} for one .spectra file, **re-serialised first**.

    Both sides go through SpectraSpecification before being compared. Comparing
    the files as written flags every formula as changed whenever the repaired
    specification was serialised with different whitespace or parenthesisation
    than the original - which is what made lift report 18 of 18 formulas
    modified and minepump 6 of 6 on 2026-08-15.
    """
    from spec_repair.model.spectra_specification import SpectraSpecification
    text = SpectraSpecification.from_file(path).to_str(is_to_compile=True)
    out = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = BLOCK_RE.match(lines[i])
        if m:
            body, j = [], i + 1
            while j < len(lines):
                body.append(lines[j].strip())
                if ";" in lines[j]:
                    break
                j += 1
            kind = "asm" if m.group(1) in ("assumption", "asm") else "gar"
            out[m.group(2)] = (kind, re.sub(r"\s+", " ", " ".join(body)).strip())
            i = j + 1
        else:
            i += 1
    return out


def compare(original, repaired):
    """(weakened_asm, weakened_gar, dropped_asm, dropped_gar) as name sets."""
    w_asm, w_gar, d_asm, d_gar = set(), set(), set(), set()
    for name, (kind, text) in original.items():
        if name not in repaired:
            (d_asm if kind == "asm" else d_gar).add(name)
        elif repaired[name][1] != text:
            (w_asm if kind == "asm" else w_gar).add(name)
    return w_asm, w_gar, d_asm, d_gar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--setup", default="case_study_3")
    ap.add_argument("--runs-root", default=None)
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    runs_root = args.runs_root or os.path.join(
        REPO_ROOT, "tests", "test_files", "out", args.setup)
    specs_root = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra", args.setup)

    rows = []
    for d in sorted(os.listdir(runs_root)):
        m = RUN_RE.match(d)
        if not m or m.group("date") != args.date:
            continue
        case, trace = m.group("case"), int(m.group("trace"))
        learner = m.group("learner") or "ilasp"
        # The merged result is the unit worth reporting - one specification per
        # run - and comparing 91k final_specs through the model is neither
        # affordable nor more informative. Falls back to final_specs only when a
        # run has not been merged yet, sampling the first few.
        merged = sorted(glob.glob(os.path.join(
            runs_root, d, "unique_max_merged_specs", "*.spectra")))
        finals = merged or sorted(glob.glob(os.path.join(
            runs_root, d, "final_specs", "*.spectra")))[:5]
        if not finals:
            continue
        source = "merged" if merged else "final (sample)"
        orig_path = os.path.join(specs_root, case, "original.spectra")
        if not os.path.isfile(orig_path):
            continue
        original = parse_formulas(orig_path)

        all_w_asm, all_w_gar, all_d_asm, all_d_gar = set(), set(), set(), set()
        per_spec = []
        for f in finals:
            w_asm, w_gar, d_asm, d_gar = compare(original, parse_formulas(f))
            per_spec.append(len(w_asm) + len(w_gar) + len(d_asm) + len(d_gar))
            all_w_asm |= w_asm; all_w_gar |= w_gar
            all_d_asm |= d_asm; all_d_gar |= d_gar
        rows.append({
            "case": case, "trace": trace, "learner": learner, "specs": len(finals),
            "source": source,
            "w_asm": sorted(all_w_asm), "w_gar": sorted(all_w_gar),
            "d_asm": sorted(all_d_asm), "d_gar": sorted(all_d_gar),
            "min_changes": min(per_spec), "max_changes": max(per_spec),
        })

    today = datetime.date.today().isoformat()
    out = [
        f"# What the repairs changed - {args.setup}, run {args.date}",
        "",
        f"Generated {today} by `scripts/report_repair_modifications.py`, from "
        "`final_specs/` compared against `original.spectra` by formula name. "
        "Weakened means the formula text changed; dropped means it is absent "
        "from the repaired specification.",
        "",
        "`changes/spec` is the range across that run's solutions - the smallest "
        "and largest number of expressions any single repaired specification "
        "touched.",
        "",
        "| case study | trace | learner | from | specs | asm weakened | gar weakened | dropped | changes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in sorted(rows, key=lambda r: (r["case"], r["trace"], r["learner"])):
        w_a = ", ".join(f"`{x}`" for x in r["w_asm"]) or "-"
        w_g = ", ".join(f"`{x}`" for x in r["w_gar"]) or "-"
        dropped = ", ".join(f"`{x}`" for x in r["d_asm"] + r["d_gar"]) or "-"
        rng = (f"{r['min_changes']}" if r["min_changes"] == r["max_changes"]
               else f"{r['min_changes']}-{r['max_changes']}")
        out.append(f"| {r['case']} | {r['trace']} | {r['learner']} | {r['source']} "
                   f"| {r['specs']} | {w_a} | {w_g} | {dropped} | {rng} |")

    total_specs = sum(r["specs"] for r in rows)
    asm_only = sum(1 for r in rows if r["w_asm"] and not r["w_gar"])
    both = sum(1 for r in rows if r["w_asm"] and r["w_gar"])
    out += [
        "",
        f"{len(rows)} run(s), {total_specs} repaired specification(s). "
        f"**{asm_only}** weakened assumptions only; **{both}** touched guarantees too.",
    ]
    table = "\n".join(out) + "\n"
    print(table)
    if args.output:
        p = args.output if os.path.isabs(args.output) else os.path.join(REPO_ROOT, args.output)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(table)
        print(f"written to {p}", file=sys.stderr)


if __name__ == "__main__":
    main()
