"""
Steps 2-6 of the experiment methodology, for one pulled experiment date.

Step 1 (pulling the run from the remote) is scripts/pull_experiment_from_ssh.sh.
This script picks up from the local copy and, for each case study in that date's
folder, produces:

    tests/test_files/out_ssh/<date>/<case_study>_<date>/
        final_specs/                  <- pulled from the remote (input)
        merged_specs/                 <- step 2: merge of all final_specs
        max_merged_specs/             <- step 3: maximal by guarantee (GAR)
        unique_max_merged_specs/      <- step 4: semantically unique
        implication_graph.png         <- step 6: colour-coded graph

Step 5 (trivial solutions) is local and independent of the remote; generate it
with tests/test_diagnosis/test_trivial_solution.py, which writes to
tests/test_files/out/trivial_solutions/<date>/all/<case_study>/. This script
picks those up for the graph if they exist.

Step 3 filters on guarantees only (GAR). All merged specifications share the
same assumptions - merging conjoins them and every input came from the same
original - so filtering on assumptions as well cannot remove anything, and
comparing them costs a spot equivalence check per pair.

Usage:
    python scripts/run_experiment_pipeline.py 2026-07-27
    python scripts/run_experiment_pipeline.py 2026-07-27 --case-study pcar
    python scripts/run_experiment_pipeline.py 2026-07-27 --skip-graph
"""
import argparse
import os
import re
import subprocess
import sys
from typing import List, Optional, Tuple

from spec_repair.diagnosis.solution_merging import merge_solutions
from spec_repair.diagnosis.spec_filtering import (
    filter_semantically_unique_specifications,
    find_maximal_specifications_from_folder,
    get_files_with_specs_from_directory,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_SSH_ROOT = os.path.join(REPO_ROOT, "tests", "test_files", "out_ssh")
TRIVIAL_ROOT = os.path.join(REPO_ROOT, "tests", "test_files", "out", "trivial_solutions")
CASE_STUDIES_DIR = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra")

FINAL_SPECS = "final_specs"
MERGED = "merged_specs"
MAX_MERGED = "max_merged_specs"
UNIQUE_MAX_MERGED = "unique_max_merged_specs"
GRAPH_NAME = "implication_graph.png"


def case_study_name_from_run_dir(run_dir_name: str, date: str) -> str:
    """`pcar_updated_2026-07-27` -> `pcar_updated`."""
    return re.sub(rf"_{re.escape(date)}$", "", run_dir_name)


def find_run_dirs(date: str, only: Optional[str] = None) -> List[str]:
    date_root = os.path.join(OUT_SSH_ROOT, date)
    if not os.path.isdir(date_root):
        raise FileNotFoundError(
            f"No pulled experiment at {date_root}. Run "
            f"./scripts/pull_experiment_from_ssh.sh {date} first.")
    run_dirs = sorted(
        os.path.join(date_root, name)
        for name in os.listdir(date_root)
        if os.path.isdir(os.path.join(date_root, name)) and name.endswith(date)
    )
    if only:
        run_dirs = [d for d in run_dirs
                    if case_study_name_from_run_dir(os.path.basename(d), date) == only]
        if not run_dirs:
            raise FileNotFoundError(f"No run directory for case study '{only}' at {date_root}")
    return run_dirs


def save_specs(specs, out_dir: str, prefix: str = "spec") -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    # Clear stale files, otherwise a rerun that produces fewer specs leaves
    # last run's higher-numbered ones behind and the next stage reads both.
    for stale in os.listdir(out_dir):
        if stale.endswith(".spectra"):
            os.remove(os.path.join(out_dir, stale))
    paths = []
    for i, spec in enumerate(specs):
        path = os.path.join(out_dir, f"{prefix}_{i}.spectra")
        write_to_file(path, spec.to_str())
        paths.append(path)
    return paths


def step_2_merge(run_dir: str, og_spec: Optional[SpectraSpecification]) -> int:
    final_specs_dir = os.path.join(run_dir, FINAL_SPECS)
    if not os.path.isdir(final_specs_dir):
        print(f"  SKIP: no {FINAL_SPECS}/ in {run_dir}")
        return 0
    files_with_specs = get_files_with_specs_from_directory(final_specs_dir)
    if len(files_with_specs) < 2:
        print(f"  step 2: only {len(files_with_specs)} final spec(s); "
              f"nothing to merge, copying through")
        save_specs([s for _, s in files_with_specs], os.path.join(run_dir, MERGED))
        return len(files_with_specs)

    merged = merge_solutions([s for _, s in files_with_specs], og_spec=og_spec)
    save_specs(merged, os.path.join(run_dir, MERGED))
    print(f"  step 2: merged {len(files_with_specs)} final specs -> {len(merged)} merged spec(s)")
    return len(merged)


def step_3_maximal(run_dir: str) -> int:
    merged_dir = os.path.join(run_dir, MERGED)
    maximal = find_maximal_specifications_from_folder(merged_dir, GR1FormulaType.GAR)
    save_specs([s for _, s in maximal], os.path.join(run_dir, MAX_MERGED))
    print(f"  step 3: {len(maximal)} maximal (GAR) merged spec(s)")
    return len(maximal)


def step_4_unique(run_dir: str) -> int:
    max_dir = os.path.join(run_dir, MAX_MERGED)
    files_with_specs = get_files_with_specs_from_directory(max_dir)
    unique = filter_semantically_unique_specifications(files_with_specs)
    save_specs([s for _, s in unique], os.path.join(run_dir, UNIQUE_MAX_MERGED))
    print(f"  step 4: {len(unique)} semantically unique maximal merged spec(s)")
    return len(unique)


def step_6_graph(run_dir: str, case_study: str, date: str, graph_type: str) -> None:
    groups: List[Tuple[str, str]] = []
    case_study_dir = os.path.join(CASE_STUDIES_DIR, case_study)
    for label, path in (("strong", os.path.join(case_study_dir, "strong.spectra")),
                        ("ideal", os.path.join(case_study_dir, "ideal.spectra")),
                        ("trivial", os.path.join(TRIVIAL_ROOT, date, "all", case_study)),
                        ("unique_max_merged", os.path.join(run_dir, UNIQUE_MAX_MERGED))):
        if os.path.exists(path):
            groups.append((label, path))
        else:
            print(f"  step 6: no {label} at {path} - omitted from graph")

    if not groups:
        print("  step 6: nothing to draw")
        return

    output = os.path.join(run_dir, GRAPH_NAME)
    cmd = [sys.executable, os.path.join(REPO_ROOT, "scripts", "visualise_resulting_specs.py"),
           "-o", output, "-t", graph_type]
    for label, path in groups:
        cmd += ["--group", f"{label}={path}"]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("date", help="experiment date, YYYY-MM-DD, as pulled into out_ssh/")
    parser.add_argument("--case-study", default=None,
                        help="only process this case study (default: all in that date)")
    parser.add_argument("--og-spec-from-case-study", action="store_true",
                        help="pass the case study's strong.spectra to the merge as the original spec")
    parser.add_argument("--graph-type", default="gr1", choices=["asm", "gar", "gr1"],
                        help="implication relation used for the graph (default: gr1)")
    parser.add_argument("--skip-graph", action="store_true", help="skip step 6")
    args = parser.parse_args(argv)

    run_dirs = find_run_dirs(args.date, args.case_study)
    print(f"Found {len(run_dirs)} case-study run(s) for {args.date}\n")

    failures = []
    for run_dir in run_dirs:
        case_study = case_study_name_from_run_dir(os.path.basename(run_dir), args.date)
        print(f"{case_study}:")
        try:
            og_spec = None
            if args.og_spec_from_case_study:
                strong_path = os.path.join(CASE_STUDIES_DIR, case_study, "strong.spectra")
                og_spec = SpectraSpecification.from_file(strong_path) if os.path.exists(strong_path) else None

            if step_2_merge(run_dir, og_spec) == 0:
                continue
            step_3_maximal(run_dir)
            step_4_unique(run_dir)
            if not args.skip_graph:
                step_6_graph(run_dir, case_study, args.date, args.graph_type)
        except Exception as e:  # keep going: one bad case study should not sink the batch
            print(f"  ERROR: {type(e).__name__}: {e}")
            failures.append(case_study)
        print()

    if failures:
        print(f"Completed with failures in: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("Pipeline complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
