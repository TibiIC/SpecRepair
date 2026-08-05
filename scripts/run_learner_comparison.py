"""
Run the BFS repair case studies under a chosen learner, and record what happened.

Drives exactly the same unittest methods the tmux runners drive, with
`SPEC_REPAIR_LEARNER` set, one subprocess per case study so a run that does not
terminate can be killed without taking the sweep with it. That matters here:
some (learner, case study) pairs do not finish in any reasonable time, and the
useful result is *which* ones, measured, rather than a hung terminal.

    # FastLAS over the trace-violation case studies, 15 minutes each
    python scripts/run_learner_comparison.py --learner fastlas \\
        --setup trace_violation --timeout 900

    # both learners over both setups, writing a JSON summary
    python scripts/run_learner_comparison.py --learner fastlas ilasp \\
        --setup strengthened trace_violation -o results.json

Results are appended to the JSON file as each run finishes, so a sweep that is
interrupted still leaves everything completed up to that point.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_OUT = os.path.join(REPO_ROOT, "tests", "test_files", "out")

ORCHESTRATOR_TEST = ("tests.test_main.test_bfs_repair_orchestrator"
                     ".TestBFSRepairOrchestrator.test_bfs_repair_spec_{case_study}_syn")
TRACE_TEST = ("tests.test_main.test_bfs_repair_trace_violation"
              ".TestBFSRepairTraceViolation"
              ".test_bfs_repair_trace_violation_{case_study}_{trace}_syn")

# arbiter appears under strengthened only: in the trace-violation setup its sole
# assumption is GF(a), which a finite prefix always satisfies, so it has no
# violating trace and no run to make.
STRENGTHENED_CASE_STUDIES = [
    "arbiter", "colorsort", "elevator", "gyro", "humanoid",
    "lift", "minepump", "pcar", "traffic_single", "traffic_updated",
]
TRACE_CASE_STUDIES = [
    "colorsort", "elevator", "gyro", "humanoid", "lift",
    "minepump", "minepump_liveness", "pcar", "traffic_single", "traffic_updated",
]

SETUPS = {
    "strengthened": (STRENGTHENED_CASE_STUDIES, "repair_syn"),
    "trace_violation": (TRACE_CASE_STUDIES, "repair_trace_syn"),
}


def out_dir_for(setup: str, case_study: str, learner: str, trace: int, date: str) -> str:
    """Mirror of the naming the test helpers use, for reading results back."""
    _, subdir = SETUPS[setup]
    suffix = "" if learner == "ilasp" else f"_{learner}"
    name = case_study if setup == "strengthened" else f"{case_study}_trace{trace}"
    return os.path.join(TESTS_OUT, subdir, f"{name}{suffix}_{date}")


def count_specs(run_dir: str) -> Dict[str, int]:
    counts = {}
    for kind in ("final_specs", "intermediate_specs"):
        path = os.path.join(run_dir, kind)
        counts[kind] = (len([f for f in os.listdir(path) if f.endswith(".spectra")])
                        if os.path.isdir(path) else 0)
    return counts


def run_one(setup: str, case_study: str, learner: str, trace: int,
            timeout: int, date: str, fastlas_runs: int = 1) -> dict:
    test = (ORCHESTRATOR_TEST if setup == "strengthened" else TRACE_TEST).format(
        case_study=case_study, trace=trace)
    env = dict(os.environ, SPEC_REPAIR_LEARNER=learner,
               SPEC_REPAIR_FASTLAS_RUNS=str(fastlas_runs))
    label = f"{setup}/{case_study}" + ("" if setup == "strengthened" else f" trace{trace}")
    print(f"  {label} [{learner}] ...", end="", flush=True)

    start = time.time()
    status = "ok"
    try:
        proc = subprocess.run([sys.executable, "-m", "unittest", test],
                              cwd=REPO_ROOT, env=env, timeout=timeout,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            status = "failed"
    except subprocess.TimeoutExpired:
        status = "timeout"
        proc = None
    elapsed = time.time() - start

    run_dir = out_dir_for(setup, case_study, learner, trace, date)
    result = {
        "setup": setup, "case_study": case_study, "learner": learner,
        "trace": trace if setup == "trace_violation" else None,
        "status": status, "seconds": round(elapsed, 1),
        "run_dir": os.path.relpath(run_dir, REPO_ROOT),
        **count_specs(run_dir),
    }
    if status == "failed" and proc is not None:
        # The last stderr line is usually the assertion or exception; the whole
        # thing is far too long to keep in a summary table.
        tail = [ln for ln in proc.stderr.strip().splitlines() if ln.strip()]
        result["error"] = tail[-1] if tail else "(no stderr)"
    print(f" {status} in {elapsed:.0f}s ({result['final_specs']} final specs)")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--learner", nargs="+", default=["fastlas"],
                        choices=["ilasp", "fastlas"])
    parser.add_argument("--setup", nargs="+", default=list(SETUPS), choices=list(SETUPS))
    parser.add_argument("--case-study", nargs="+", default=None,
                        help="restrict to these case studies")
    parser.add_argument("--trace", type=int, default=0,
                        help="which violating trace to use for trace_violation (default: 0)")
    parser.add_argument("--fastlas-runs", type=int, default=1,
                        help="FastLAS invocations per learning step. FastLAS returns one "
                             "solution per run and picks non-deterministically among "
                             "equally-optimal candidates, so this is how many of ILASP's "
                             "alternatives a run samples. Ignored for --learner ilasp.")
    parser.add_argument("--timeout", type=int, default=900,
                        help="per-run wall-clock limit in seconds (default: 900)")
    parser.add_argument("--date", default=None,
                        help="date stamp the runs write under (default: today, as the tests use)")
    parser.add_argument("-o", "--output", default=None, help="write a JSON summary here")
    args = parser.parse_args(argv)

    from datetime import datetime
    date = args.date or datetime.now().strftime("%Y-%m-%d")

    results: List[dict] = []
    for learner in args.learner:
        for setup in args.setup:
            case_studies, _ = SETUPS[setup]
            if args.case_study:
                case_studies = [c for c in case_studies if c in args.case_study]
            print(f"\n=== {learner} / {setup} ({len(case_studies)} case studies) ===")
            for case_study in case_studies:
                results.append(run_one(setup, case_study, learner, args.trace,
                                       args.timeout, date,
                                       fastlas_runs=args.fastlas_runs))
                if args.output:
                    with open(args.output, "w") as f:
                        json.dump(results, f, indent=2)

    print(f"\n{'setup':16s} {'case study':20s} {'learner':9s} {'status':9s} "
          f"{'seconds':>8s} {'final':>6s}")
    for r in results:
        print(f"{r['setup']:16s} {r['case_study']:20s} {r['learner']:9s} "
              f"{r['status']:9s} {r['seconds']:8.0f} {r['final_specs']:6d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
