#!/usr/bin/env python3
"""
Write the ASP program that chooses one environment step, for inspection.

The step generator builds this program, hands it to clingo and reads the
environment values out of the answer sets. Nothing else decides the environment's
behaviour, so this file is the whole of it - runnable on its own:

    python scripts/dump_env_step_asp.py amba --target a30 --horizon 2 -o /tmp/amba.lp
    clingo /tmp/amba.lp 5

Without `--target` the program asks for a step that violates nothing, which is
what the compliant prefix uses. With one, it asks for a step - or a plan of
`--horizon` steps - after which that assumption is violated.

The answer sets contain `holds_at/3` and `not_holds_at/3` for every atom at every
timepoint. The generator reads only the environment variables at the first new
timepoint; the rest is the plan that justifies it. The system's values are chosen
by the solver subject to the guarantees, never pinned - the controller's next
move is the one that maintains those guarantees, so fixing it in advance and
then demanding them is contradictory, and made every program unsatisfiable.
"""
import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from spec_repair.components.spec_generator import SpecGenerator
from spec_repair.diagnosis import controller_trace_generation as ctg
from spec_repair.diagnosis.violation_trace_generation import _trace_skeleton_asp
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.asp_trace_util import create_atom_signature_asp

SPECTRA = os.path.join(REPO_ROOT, "input-files", "case-studies", "spectra")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("case_study")
    p.add_argument("--setup", default="case_study_2",
                   help="which folder the specification comes from (default: case_study_2)")
    p.add_argument("--target", default=None,
                   help="assumption to violate; omit for a step that violates nothing")
    p.add_argument("--horizon", type=int, default=1,
                   help="timepoints to plan over, of which only the first is executed")
    p.add_argument("--prefix-steps", type=int, default=0,
                   help="how many all-false states to pin as the trace so far")
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--list-targets", action="store_true",
                   help="print the violatable assumptions and exit")
    args = p.parse_args(argv)

    spec_path = os.path.join(SPECTRA, args.setup, args.case_study, "original.spectra")
    if not os.path.isfile(spec_path):
        print(f"No specification at {spec_path}", file=sys.stderr)
        return 2

    if args.list_targets:
        for name in ctg.violatable_assumptions(spec_path):
            print(name)
        return 0

    spec = SpectraSpecification.from_file(spec_path)
    variables = ctg._spec_variable_names(spec)
    env_names = sorted(l.split()[-1].rstrip(";")
                       for l in open(spec_path) if l.strip().startswith("env "))
    sys_names = [v for v in variables if v not in set(env_names)]
    # Safety guarantees only - see _asp_next_inputs: liveness cannot be held
    # against a finite prefix, and constraining it makes every program UNSAT.
    guarantees = sorted(spec.filter(
        lambda x: (x["type"] == GR1FormulaType.GAR)
        & (x["when"] == GR1TemporalType.INVARIANT))["name"])
    targets = {args.target} if args.target else set()
    trace_name = "trace_name_0"

    # A stand-in for the trace so far. The real generator pins the states the
    # controller actually produced; all-false is enough to see the shape.
    states = [{v: "false" for v in variables} for _ in range(args.prefix_steps)]

    program = (SpecGenerator.background_knowledge
               + spec.to_asp(for_clingo=True)
               + create_atom_signature_asp(spec.get_atoms())
               + _trace_skeleton_asp(trace_name, len(states) + args.horizon)
               + ctg.GUESS_ASP
               + ctg._pinned_prefix_asp(states, variables, trace_name)
               + ctg._next_input_constraint_asp(targets, guarantees))

    header = (f"% {args.case_study} ({args.setup})\n"
              f"% environment variables : {', '.join(env_names)}\n"
              f"% system variables      : {', '.join(sys_names)}\n"
              f"% target                : {args.target or '(violate nothing)'}\n"
              f"% timepoints            : {len(states)}..{len(states) + args.horizon - 1}"
              f" (first new one is {len(states)})\n"
              f"% read the environment values at timepoint {len(states)}\n\n")

    out = header + program
    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"Wrote {args.output} ({len(out.splitlines())} lines). Run: clingo {args.output} 5")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
