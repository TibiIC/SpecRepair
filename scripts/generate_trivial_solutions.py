#!/usr/bin/env python3
"""
Step 5 of the experiment pipeline: the trivial solutions for a setup and date.

A trivial solution is the degenerate repair - the specification weakened just
enough to permit the violating trace, with nothing else asked of it. It is the
baseline the graph draws every real repair against, so a graph without it is
missing its floor.

Why this exists beside tests/test_diagnosis/test_trivial_solution.py: that
module is hardcoded to case_study_1's layout, reading `strong.spectra` and a
single `violation_trace.txt` per case study. case_study_3 has neither. It
repairs `original.spectra`, and it has one violating trace *per run*
(`violation_trace_<N>.txt`), because each trace comes from a different
controller run. A trivial solution therefore exists per (case study, trace),
not per case study, and writing them to the per-case-study path would mean
five different traces overwriting each other.

Output, one directory per run, so the graph for `<case study>_trace<N>` can be
handed exactly the trivial solutions for the trace it repaired:

    tests/test_files/out/trivial_solutions/<date>/all/<case_study>_trace<N>/spec_<i>.spectra

The date is the *experiment's* date, not today's: the graph looks the trivial
solutions up beside the run it is drawing. A trivial solution depends only on
the specification and the trace, so re-stamping the same solutions under
several dates is expected rather than duplicated work.

Usage:
    python scripts/generate_trivial_solutions.py 2026-08-08 --setup case_study_3
    python scripts/generate_trivial_solutions.py 2026-08-08 --setup case_study_3 \
        --case-study minepump
"""
import argparse
import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.diagnosis.trivial_solution import (
    get_all_trivial_solution, get_all_trivial_solutions_marco)
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines, write_to_file

SPECTRA_CASE_STUDIES = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra")
TRIVIAL_ROOT = os.path.join(REPO_ROOT, "tests", "test_files", "out", "trivial_solutions")

# Which specification is weakened, and where the violating traces are found.
# case_study_1 keeps its single-trace layout; the two trace-violation setups
# have one numbered trace per run.
SETUPS = {
    "case_study_1": {"spec": "strong.spectra", "traces": "violation_trace.txt"},
    "case_study_2": {"spec": "original.spectra", "traces": "violation_trace_*.txt"},
    "case_study_3": {"spec": "original.spectra", "traces": "violation_trace_*.txt"},
}

TRACE_ID_RE = re.compile(r"violation_trace_(\d+)\.txt$")


def run_name(case_study: str, trace_path: str) -> str:
    """`minepump` + `violation_trace_3.txt` -> `minepump_trace3`."""
    m = TRACE_ID_RE.search(os.path.basename(trace_path))
    return f"{case_study}_trace{m.group(1)}" if m else case_study


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("date", help="experiment date to stamp the output with, YYYY-MM-DD")
    parser.add_argument("--setup", choices=sorted(SETUPS), default="case_study_3")
    parser.add_argument("--case-study", default=None,
                        help="only this case study (default: every one with traces)")
    parser.add_argument("--trace", type=int, default=None,
                        help="only this trace number (default: every trace). One "
                             "run per box is how the expensive case studies are "
                             "parallelised.")
    parser.add_argument("--marco", action="store_true",
                        help="take the cores from our MARCO enumeration instead of "
                             "Syntech's exploreAllCores. Needed for genbuf, where "
                             "exploreAllCores does not finish.")
    args = parser.parse_args(argv)

    setup = SETUPS[args.setup]
    root = os.path.join(SPECTRA_CASE_STUDIES, args.setup)
    case_studies = ([args.case_study] if args.case_study
                    else sorted(d for d in os.listdir(root)
                                if os.path.isdir(os.path.join(root, d))))

    written = skipped = failed = 0
    for case_study in case_studies:
        spec_path = os.path.join(root, case_study, setup["spec"])
        traces = sorted(glob.glob(os.path.join(root, case_study, setup["traces"])))
        if not os.path.exists(spec_path) or not traces:
            # A case study with no traces is not an error: case_study_3 covers
            # only the ones its controller reached a violation for.
            skipped += 1
            continue
        if args.trace is not None:
            traces = [t for t in traces
                      if TRACE_ID_RE.search(os.path.basename(t))
                      and int(TRACE_ID_RE.search(os.path.basename(t)).group(1)) == args.trace]
        for trace_path in traces:
            name = run_name(case_study, trace_path)
            out_dir = os.path.join(TRIVIAL_ROOT, args.date, "all", name)
            try:
                spec = SpectraSpecification.from_file(spec_path)
                trace = read_file_lines(trace_path)
                specs = (get_all_trivial_solutions_marco(spec, trace) if args.marco
                         else get_all_trivial_solution(spec, trace))
            except Exception as e:  # noqa: BLE001 - one bad case study must not stop the rest
                print(f"  {name}: FAILED ({type(e).__name__}: {e})")
                failed += 1
                continue
            if not specs:
                print(f"  {name}: no trivial solution")
                failed += 1
                continue
            os.makedirs(out_dir, exist_ok=True)
            for i, s in enumerate(specs):
                write_to_file(os.path.join(out_dir, f"spec_{i}.spectra"), s.to_str())
            print(f"  {name}: {len(specs)} trivial solution(s) -> {out_dir}")
            written += 1

    print(f"\n{written} run(s) written, {failed} failed, "
          f"{skipped} case study(ies) without a spec or traces.")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
