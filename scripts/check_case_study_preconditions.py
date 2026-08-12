#!/usr/bin/env python3
"""
Assert a case study's preconditions before its experiments are worth running.

A repair run assumes two things, and both are properties of the case study
rather than of the repair:

1. the starting specification is **realisable** - there is a controller to
   repair towards;
2. every trace violates **at least one assumption and no guarantee** - a trace
   that breaks a guarantee is describing a system that does not exist, and a
   trace that breaks nothing gives the repair nothing to do.

Checked here rather than discovered several layers into a search, where they
surface as an IndexError or an empty result and cost a day to trace back.

    python scripts/check_case_study_preconditions.py case_study_3 genbuf
    python scripts/check_case_study_preconditions.py case_study_3      # all

Exit status is 0 only if every scenario passes, so this can gate a sweep.
"""
import argparse
import glob
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.components.new_spec_encoder import (
    NewSpecEncoder, get_violated_expression_names_of_type)
from spec_repair.enums import Learning
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from spec_repair.wrappers.asp_wrappers import get_violations
from spec_repair.wrappers.spectra_toolbox import synthesise_check_realisability_only

SPECTRA = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra")


def violated(spec, trace_lines, kind: str):
    """
    Violated expressions of one kind, liveness excluded.

    A `GF(p)` is neither satisfied nor refuted by a finite trace - the prefix
    can always be extended - so the checker reporting one as violated says
    nothing about the trace. Counting those would fail case studies for a
    property no finite trace could ever have, and would equally let a trace
    "violate an assumption" without doing anything an experiment can use.

    Initial expressions stay in: a finite trace does pin down its first state.
    """
    learning = (Learning.ASSUMPTION_WEAKENING if kind == "assumption"
                else Learning.GUARANTEE_WEAKENING)
    asp = NewSpecEncoder.encode_ASP(spec, trace_lines, [])
    violations = get_violations(asp, exp_type=learning.exp_type())
    if not violations:
        return []
    names = get_violated_expression_names_of_type(violations, kind)
    df = spec.filter(lambda x: x["name"].notna())
    when = dict(zip(df["name"].tolist(), df["when"].tolist()))
    return [n for n in names if when.get(n) != GR1TemporalType.JUSTICE]


def _without_last_state(lines):
    """The trace up to, but excluding, its final timepoint."""
    text = "".join(lines)
    blocks = [b for b in text.split("\n\n") if b.strip()]
    if len(blocks) <= 1:
        return lines
    kept = "\n\n".join(blocks[:-1]) + "\n"
    return [l + "\n" for l in kept.splitlines()]


def check(setup: str, case_study: str):
    """Returns (rows, ok) for one case study."""
    directory = os.path.join(SPECTRA, setup, case_study)
    spec_path = os.path.join(directory, "original.spectra")
    if not os.path.isfile(spec_path):
        return [(case_study, "-", "NO SPEC", "")], False

    output = synthesise_check_realisability_only(spec_path) or ""
    realisable = "Result: Specification is realizable" in output
    rows = [(case_study, "-", "realisable" if realisable else "NOT REALISABLE", "")]
    ok = realisable

    spec = SpectraSpecification.from_file(spec_path)
    traces = sorted(glob.glob(os.path.join(directory, "violation_trace_*.txt")))
    if not traces:
        rows.append((case_study, "-", "NO TRACES", ""))
        return rows, False

    for path in traces:
        name = os.path.basename(path)
        lines = read_file_lines(path)
        asms = violated(spec, lines, "assumption")
        # Guarantees are judged on the trace *without* its last state.
        #
        # That last state is where the environment breaks an assumption, and
        # GR(1) is assumptions -> guarantees: once the environment breaks its
        # side, the system owes nothing. Holding the system to its guarantees
        # there asks the trace to break the antecedent while still honouring
        # the consequent, which no violating trace can do - amba, colorsort and
        # genbuf all failed on exactly that, and minepump's own controller
        # breaks a guarantee at that step when run by hand in the walker.
        #
        # It also matches what the generator now assumes when it plans, so the
        # two agree on what a valid trace is.
        gars = violated(spec, _without_last_state(lines), "guarantee")
        if not asms:
            verdict, detail = "BAD: violates no assumption", ""
        elif gars:
            verdict, detail = "BAD: violates guarantee(s)", ", ".join(sorted(gars))
        else:
            verdict, detail = "ok", ", ".join(sorted(asms))
        ok = ok and verdict == "ok"
        rows.append((case_study, name, verdict, detail))
    return rows, ok


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("setup", help="e.g. case_study_3")
    p.add_argument("case_studies", nargs="*",
                   help="default: every case study in the setup that has traces")
    args = p.parse_args(argv)

    root = os.path.join(SPECTRA, args.setup)
    names = args.case_studies or sorted(
        d for d in os.listdir(root)
        if glob.glob(os.path.join(root, d, "violation_trace_*.txt")))

    all_ok = True
    for case_study in names:
        rows, ok = check(args.setup, case_study)
        all_ok = all_ok and ok
        for cs, trace, verdict, detail in rows:
            print(f"{cs:<20} {trace:<26} {verdict:<28} {detail}")
    print("\nPASS - preconditions hold" if all_ok else
          "\nFAIL - at least one precondition is broken")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
