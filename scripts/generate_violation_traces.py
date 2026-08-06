"""
Generate assumption-violating traces for trace-violation case studies.

Given an `original.spectra`, writes one or more `violation_trace_<ID>.txt` files
beside it, each a short execution the specification's assumptions do not admit -
while every other assumption and every guarantee still holds.

    # one case study
    python scripts/generate_violation_traces.py \
        input-files/case-studies/spectra/case_study_2/minepump

    # every case study in the new-approach folder
    python scripts/generate_violation_traces.py \
        input-files/case-studies/spectra/case_study_2 --all

    # report which assumptions are violable, without writing anything
    python scripts/generate_violation_traces.py <dir> --report-only

Trace length defaults to 1-3 timepoints. Raise `--max-timepoints` when an
assumption is reported as not violable: a trace is a finite prefix ending in a
weak timepoint where everything holds vacuously, so a violation involving `next`
must occur at least one timepoint before the end.
"""
import argparse
import os
import random
import sys
from typing import List

from spec_repair.diagnosis.violation_trace_generation import (
    INVARIANT_WHEN,
    find_violable_assumptions,
    generate_assumption_violating_traces,
    get_formula_names,
)
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file

ORIGINAL_SPEC = "original.spectra"
TRACE_PREFIX = "violation_trace_"


def case_study_dirs(root: str, process_all: bool) -> List[str]:
    if not process_all:
        return [root]
    return sorted(
        os.path.join(root, name) for name in os.listdir(root)
        if os.path.isfile(os.path.join(root, name, ORIGINAL_SPEC))
    )


def process(case_study_dir: str, args, rng: random.Random) -> int:
    name = os.path.basename(os.path.normpath(case_study_dir))
    spec_path = os.path.join(case_study_dir, ORIGINAL_SPEC)
    if not os.path.isfile(spec_path):
        print(f"{name}: no {ORIGINAL_SPEC}, skipped")
        return 0
    spec = SpectraSpecification.from_file(spec_path)

    # Resolved per case study, since --invariant-only names different assumptions
    # in each one and --only-assumptions is only meaningful for a single spec.
    only_assumptions = args.only_assumptions
    if args.invariant_only:
        only_assumptions = get_formula_names(spec, GR1FormulaType.ASM, when=INVARIANT_WHEN)
        if not only_assumptions:
            print(f"{name}: no invariant (G) assumptions, skipped")
            return 0

    if args.report_only:
        violable = find_violable_assumptions(spec, args.min_timepoints, args.max_timepoints,
                                             only_assumptions=only_assumptions)
        print(f"{name}:")
        for assumption, lengths in violable.items():
            print(f"  {assumption:40s} {lengths or 'not violable in range'}")
        return 0

    if args.clean:
        for stale in sorted(os.listdir(case_study_dir)):
            if stale.startswith(TRACE_PREFIX) and stale.endswith(".txt"):
                os.remove(os.path.join(case_study_dir, stale))

    try:
        traces = generate_assumption_violating_traces(
            spec,
            n_traces=args.n_traces,
            min_timepoints=args.min_timepoints,
            max_timepoints=args.max_timepoints,
            max_violated_assumptions=args.max_violated_assumptions,
            rng=rng,
            only_assumptions=only_assumptions,
        )
    except ValueError as e:
        print(f"{name}: ERROR {e}")
        return 0

    for i, trace in enumerate(traces):
        path = os.path.join(case_study_dir, f"{TRACE_PREFIX}{i}.txt")
        write_to_file(path, "\n".join(trace.lines) + "\n")
        print(f"{name}: {os.path.basename(path)} violates "
              f"{', '.join(trace.violated_assumptions)} over {trace.n_timepoints} timepoint(s)")
    if not traces:
        print(f"{name}: no traces found")
    return len(traces)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help=f"a case-study directory containing {ORIGINAL_SPEC}, "
                                     f"or their parent with --all")
    parser.add_argument("--all", action="store_true", dest="process_all",
                        help="treat PATH as a parent directory and process every case study in it")
    parser.add_argument("-n", "--n-traces", type=int, default=1,
                        help="traces to generate per case study (default: 1)")
    parser.add_argument("--min-timepoints", type=int, default=1)
    parser.add_argument("--max-timepoints", type=int, default=3)
    parser.add_argument("--max-violated-assumptions", type=int, default=1,
                        help="a trace may violate up to this many assumptions at once (default: 1)")
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument("--invariant-only", action="store_true",
                         help="only target invariant (G) assumptions, skipping initial (ini) and "
                              "liveness (GF) ones. An `ini` violation only says the run started in "
                              "an excluded state, and `GF` cannot be violated on a finite prefix")
    targets.add_argument("--only-assumptions", nargs="+", metavar="NAME", default=None,
                         help="only target these assumptions by name (single case study only). "
                              "Every other formula must still hold")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed for reproducible generation")
    parser.add_argument("--report-only", action="store_true",
                        help="report which assumptions are violable, write nothing")
    parser.add_argument("--clean", action="store_true",
                        help=f"delete existing {TRACE_PREFIX}*.txt before generating")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.path):
        print(f"ERROR: not a directory: {args.path}", file=sys.stderr)
        return 2

    rng = random.Random(args.seed)
    total = 0
    for case_study_dir in case_study_dirs(args.path, args.process_all):
        total += process(case_study_dir, args, rng)
    if not args.report_only:
        print(f"\nGenerated {total} trace(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
