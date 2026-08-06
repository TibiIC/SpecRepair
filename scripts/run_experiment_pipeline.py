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
        implication_graph_asm.png     <- step 6: assumptions only
        implication_graph_gar.png     <- step 6: guarantees only
        implication_graph_gr1.png     <- step 6: whole spec (asm -> gar)

Step 5 (trivial solutions) is local and independent of the remote; generate it
with tests/test_diagnosis/test_trivial_solution.py, which writes to
tests/test_files/out/trivial_solutions/<date>/all/<case_study>/. This script
picks those up for the graph if they exist.

Step 3 filters on guarantees only (GAR). All merged specifications share the
same assumptions - merging conjoins them and every input came from the same
original - so filtering on assumptions as well cannot remove anything, and
comparing them costs a spot equivalence check per pair.

All three graphs are drawn every time, because no single comparison tells the
whole story - see GRAPH_TYPES below for why the gr1 one in particular is easy to
misread.

Both experimental setups run through this same pipeline; `--setup` selects which
case-study folder the reference specifications on the graph come from. Steps 2-4
are identical either way - only what step 6 draws alongside the results differs.

Usage:
    python scripts/run_experiment_pipeline.py 2026-07-27
    python scripts/run_experiment_pipeline.py 2026-07-27 --case-study pcar
    python scripts/run_experiment_pipeline.py 2026-07-27 --graph-type gar
    python scripts/run_experiment_pipeline.py 2026-07-27 --skip-graph

    # the trace-violation case studies, whose runs are named
    # <case_study>_trace<ID>_<date> and reference original.spectra
    python scripts/run_experiment_pipeline.py 2026-07-30 --setup case_study_2
"""
import argparse
import logging
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
SPECTRA_CASE_STUDIES = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra")

# The two experimental setups differ in what step 6 draws alongside the merged
# results - which is the only place the pipeline needs to know them apart:
#
#   case_study_1    - repairs weaken a manufactured `strong.spectra` back down,
#                     so both it and the `ideal.spectra` it was strengthened
#                     from are meaningful reference points on the graph.
#   case_study_2    - there is no manufactured spec and no known-good answer;
#                     the one reference point is `original.spectra`, the thing
#                     that was repaired.
#
# Everything before step 6 - merging, maximal, unique - is identical, so it is a
# flag rather than a second script.
SETUPS = {
    "case_study_1": {
        "dir": os.path.join(SPECTRA_CASE_STUDIES, "case_study_1"),
        "reference_specs": ("strong.spectra", "ideal.spectra"),
        "og_spec": "strong.spectra",
    },
    "case_study_2": {
        "dir": os.path.join(SPECTRA_CASE_STUDIES, "case_study_2"),
        "reference_specs": ("original.spectra",),
        "og_spec": "original.spectra",
    },
}

FINAL_SPECS = "final_specs"
MERGED = "merged_specs"
MAX_MERGED = "max_merged_specs"
UNIQUE_MAX_MERGED = "unique_max_merged_specs"


def graph_name(graph_type: str) -> str:
    return f"implication_graph_{graph_type}.png"


# All three comparisons are drawn by default, because no single one tells the
# whole story and reading the wrong one is actively misleading:
#
#   asm  - assumptions only
#   gar  - guarantees only
#   gr1  - the whole specification, formatted as (assumptions) -> (guarantees)
#
# The gr1 view is the one to be careful with: strengthening the assumptions
# makes that implication *weaker*, so when a run weakens assumptions and leaves
# guarantees untouched, gr1 orders the specifications purely by the assumption
# side and in the opposite direction to intuition. Compare asm and gar
# side-by-side to see what actually changed.
GRAPH_TYPES = ("asm", "gar", "gr1")


def case_study_name_from_run_dir(run_dir_name: str, date: str) -> str:
    """`pcar_updated_2026-07-27` -> `pcar_updated`."""
    return re.sub(rf"_{re.escape(date)}$", "", run_dir_name)


# A run directory is named `<case_study>[_trace<ID>][_<learner>]_<date>`. Both
# optional parts identify the *run*, not the case study, so both have to come
# off before looking up the case study's own files. Order matters: the learner
# suffix is appended last, so it is stripped first.
#
# Only non-default learners appear - an ILASP run keeps the unsuffixed name that
# every pulled directory so far was written with.
LEARNER_SUFFIX_RE = re.compile(r"_(fastlas)$")
TRACE_SUFFIX_RE = re.compile(r"_trace(\d+)$")


def case_study_dir_name(run_name: str) -> str:
    """
    `minepump_trace3_fastlas` -> `minepump`; anything without those suffixes is
    returned unchanged.
    """
    return TRACE_SUFFIX_RE.sub("", LEARNER_SUFFIX_RE.sub("", run_name))


def find_run_dirs(date: str, only: Optional[str] = None,
                  runs_root: Optional[str] = None) -> List[str]:
    """
    The `<name>_<date>` run directories to process.

    `runs_root` overrides the default `out_ssh/<date>/`, for runs that were
    produced locally rather than pulled - those land in
    `tests/test_files/out/case_study_1/` and `.../case_study_2/`, with no date
    subdirectory, since the tests write them directly.
    """
    date_root = runs_root or os.path.join(OUT_SSH_ROOT, date)
    if not os.path.isdir(date_root):
        raise FileNotFoundError(
            f"No experiment run directory at {date_root}. Run "
            f"./scripts/pull_experiment_from_ssh.sh {date} first, "
            f"or pass --runs-root for locally produced runs.")
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

    print(f"  step 2: merging {len(files_with_specs)} final specs...", flush=True)
    # verify_inputs=False: these came out of the BFS repair search, which only
    # records a spec once its oracle has accepted it, so they are realisable by
    # construction. Re-checking costs one Spectra synthesis call each - about
    # 11 minutes for a run like elevator_updated's 966 specs - to re-establish
    # something already known. The post-merge realisability check still runs.
    # An unrealisable merge is split in half and each half merged separately,
    # rather than torn down with Spectra's exhaustive unrealisable-core search,
    # so a large run no longer has to be refused up front to avoid hanging.
    merged = merge_solutions([s for _, s in files_with_specs], og_spec=og_spec,
                             verify_inputs=False)
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


def step_6_graph(run_dir: str, case_study: str, date: str, graph_types: Tuple[str, ...],
                 setup: dict, legend: str = "compact") -> None:
    groups: List[Tuple[str, str]] = []
    case_study_dir = os.path.join(setup["dir"], case_study_dir_name(case_study))
    references = [(os.path.splitext(spec)[0], os.path.join(case_study_dir, spec))
                  for spec in setup["reference_specs"]]
    for label, path in (references
                        + [("trivial", os.path.join(TRIVIAL_ROOT, date, "all",
                                                    case_study_dir_name(case_study))),
                           ("unique_max_merged", os.path.join(run_dir, UNIQUE_MAX_MERGED))]):
        if os.path.exists(path):
            groups.append((label, path))
        else:
            print(f"  step 6: no {label} at {path} - omitted from graph")

    if not groups:
        print("  step 6: nothing to draw")
        return

    group_args = []
    for label, path in groups:
        group_args += ["--group", f"{label}={path}"]

    for graph_type in graph_types:
        output = os.path.join(run_dir, graph_name(graph_type))
        cmd = [sys.executable, os.path.join(REPO_ROOT, "scripts", "visualise_resulting_specs.py"),
               "-o", output, "-t", graph_type, "--legend", legend] + group_args
        subprocess.run(cmd, check=True, cwd=REPO_ROOT)
    print(f"  step 6: drew {len(graph_types)} graph(s): "
          f"{', '.join(graph_name(t) for t in graph_types)}")


def main(argv=None) -> int:
    # INFO so the library's progress messages during long merges are visible;
    # without them a large run looks indistinguishable from a hang.
    logging.basicConfig(level=logging.INFO, format="  %(message)s")
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("date", help="experiment date, YYYY-MM-DD, as pulled into out_ssh/")
    parser.add_argument("--case-study", default=None,
                        help="only process this case study (default: all in that date)")
    parser.add_argument("--setup", choices=sorted(SETUPS), default="case_study_1",
                        help="which experimental setup the pulled runs came from. Selects the "
                             "case-study folder and the reference specifications drawn on the "
                             "graph: strong+ideal for case_study_1, original for case_study_2 "
                             "(default: case_study_1)")
    parser.add_argument("--og-spec-from-case-study", action="store_true",
                        help="pass the case study's reference specification (strong.spectra, or "
                             "original.spectra under --setup case_study_2) to the merge as the "
                             "original spec")
    parser.add_argument("--graph-type", nargs="+", default=list(GRAPH_TYPES),
                        choices=list(GRAPH_TYPES), metavar="TYPE",
                        help="which implication graphs to draw (default: all three - asm, gar, gr1)")
    parser.add_argument("--legend", choices=("compact", "full", "none"), default="compact",
                        help="legend style on the graphs (default: compact - small, bottom-right)")
    parser.add_argument("--runs-root", default=None,
                        help="directory holding the <name>_<date> run directories, instead of "
                             "out_ssh/<date>/. Use for locally produced runs, which land in "
                             "tests/test_files/out/case_study_1 or .../case_study_2")
    parser.add_argument("--skip-graph", action="store_true", help="skip step 6")
    args = parser.parse_args(argv)
    setup = SETUPS[args.setup]

    run_dirs = find_run_dirs(args.date, args.case_study, args.runs_root)
    print(f"Found {len(run_dirs)} case-study run(s) for {args.date}\n")

    failures = []
    for run_dir in run_dirs:
        case_study = case_study_name_from_run_dir(os.path.basename(run_dir), args.date)
        print(f"{case_study}:")
        try:
            og_spec = None
            if args.og_spec_from_case_study:
                og_path = os.path.join(setup["dir"], case_study_dir_name(case_study),
                                       setup["og_spec"])
                og_spec = SpectraSpecification.from_file(og_path) if os.path.exists(og_path) else None

            if step_2_merge(run_dir, og_spec) == 0:
                continue
            step_3_maximal(run_dir)
            step_4_unique(run_dir)
            if not args.skip_graph:
                step_6_graph(run_dir, case_study, args.date, tuple(args.graph_type),
                             setup, legend=args.legend)
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
