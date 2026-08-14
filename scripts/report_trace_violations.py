#!/usr/bin/env python3
"""
What each case_study_3 trace actually violates, as a markdown table.

The traces.json manifest records what a trace *aimed* at and what the generator
believed it broke. This asks the repair machinery instead - the same
`get_spec_violations` call the learner makes - so the table says what the search
will actually see, and reports guarantee violations as well as assumption ones.

Regenerate it whenever the traces change:

    python scripts/report_trace_violations.py --setup case_study_3
    python scripts/report_trace_violations.py --setup case_study_3 --case-study genbuf
    python scripts/report_trace_violations.py --setup case_study_3 \
        -o docs/results/case-study-3-trace-violations.md

Needs clingo and the JVM, so it belongs on a Linux box for the large case
studies.
"""
import argparse
import datetime
import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.components.new_spec_encoder import get_violated_expression_names_of_type
from spec_repair.enums import Learning
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines

TRACE_RE = re.compile(r"violation_trace_(\d+)\.txt$")


def violations_for(spec, trace_lines):
    """The assumption and guarantee names this trace violates, as the learner sees them."""
    violations = OptimisingSpecLearner().get_spec_violations(
        spec, trace_lines, [], Learning.ASSUMPTION_WEAKENING)
    assumptions = sorted(get_violated_expression_names_of_type(violations, "assumption"))
    guarantees = sorted(get_violated_expression_names_of_type(violations, "guarantee"))
    return assumptions, guarantees


def rows_for_setup(setup, only_case_study=None):
    root = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra", setup)
    rows = []
    for case_study in sorted(os.listdir(root)):
        if only_case_study and case_study != only_case_study:
            continue
        case_dir = os.path.join(root, case_study)
        spec_path = os.path.join(case_dir, "original.spectra")
        if not os.path.isdir(case_dir) or not os.path.isfile(spec_path):
            continue
        traces = sorted(glob.glob(os.path.join(case_dir, "violation_trace_*.txt")),
                        key=lambda p: int(TRACE_RE.search(p).group(1)))
        if not traces:
            continue
        spec = SpectraSpecification.from_file(spec_path)
        for path in traces:
            trace_id = int(TRACE_RE.search(path).group(1))
            asms, gars = violations_for(spec, read_file_lines(path))
            rows.append({"case_study": case_study, "trace": trace_id,
                         "assumptions": asms, "guarantees": gars})
            print(f"  {case_study} trace {trace_id}: "
                  f"{len(asms)} assumption(s), {len(gars)} guarantee(s)",
                  file=sys.stderr, flush=True)
    return rows


def to_markdown(rows, setup):
    today = datetime.date.today().isoformat()
    out = [
        f"# What each {setup} trace violates",
        "",
        f"Generated {today} by `scripts/report_trace_violations.py`. Regenerate it "
        "whenever the traces change - it is derived, not written by hand.",
        "",
        "Taken from the repair machinery's own `get_spec_violations`, not from the "
        "`traces.json` manifest, so it reports what the search actually sees. A "
        "trace is built to break at least one assumption at its last step; "
        "guarantee violations are listed where they occur, since the system is "
        "released from its guarantees once the environment breaks its side.",
        "",
        "| case study | trace | assumptions violated | guarantees violated |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        asms = ", ".join(f"`{a}`" for a in row["assumptions"]) or "-"
        gars = ", ".join(f"`{g}`" for g in row["guarantees"]) or "-"
        out.append(f"| {row['case_study']} | {row['trace']} | {asms} | {gars} |")

    singles = sum(1 for r in rows if len(r["assumptions"]) == 1)
    with_gars = sum(1 for r in rows if r["guarantees"])
    out += [
        "",
        f"{len(rows)} trace(s). **{singles}** violate exactly one assumption, which "
        "are the ones that isolate a single weakening; the rest break several at "
        f"once and so cover fewer distinct cases than their count suggests. "
        f"**{with_gars}** violate a guarantee as well.",
    ]
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--setup", default="case_study_3")
    parser.add_argument("--case-study", default=None)
    parser.add_argument("-o", "--output", default=None,
                        help="write the table here as well as to stdout")
    args = parser.parse_args()

    print(f"Computing violations for {args.setup}...", file=sys.stderr, flush=True)
    rows = rows_for_setup(args.setup, args.case_study)
    if not rows:
        print("No traces found.", file=sys.stderr)
        return 1

    table = to_markdown(rows, args.setup)
    print(table)
    if args.output:
        path = args.output if os.path.isabs(args.output) else os.path.join(REPO_ROOT, args.output)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as handle:
            handle.write(table)
        print(f"written to {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
