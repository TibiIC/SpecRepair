#!/usr/bin/env python3
"""
Regenerate the ASP and ILASP encodings of `simple_implication.spectra`.

The point of this folder is to have the smallest possible formula - a single
`G(a->b)` guarantee - passed through the *existing* GR(1) translation, so that
the encoding of an implication under the current semantics is visible in one
screen. Extending the semantics to `until` means changing how a formula becomes
`holds_at`/`violation_holds` rules; re-running this script and diffing the two
outputs shows exactly what a change did.

Nothing here is hand-written: both files come out of `NewSpecEncoder`, the same
encoder the repair loop uses.

    conda activate arm_env
    python files/until_semantics/generate.py

Writes, beside this script:
    simple_implication.asp   the clingo program (semantics + formula + trace)
    simple_implication.las   the ILASP learning task for weakening g1
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.enums import Learning
from spec_repair.wrappers.asp_wrappers import get_violations
from spec_repair.util.file_util import read_file_lines

SPEC = os.path.join(HERE, "simple_implication.spectra")
TRACE = os.path.join(HERE, "violation_trace.txt")
# G(a->b) is a guarantee here, so the repair direction is guarantee weakening.
LEARNING = Learning.GUARANTEE_WEAKENING


def main() -> int:
    spec = SpectraSpecification.from_file(SPEC)
    trace = read_file_lines(TRACE)

    # 1. ASP: the clingo program. Semantics rules + the formula + the trace.
    asp = NewSpecEncoder.encode_ASP(spec, trace, [])
    with open(os.path.join(HERE, "simple_implication.asp"), "w") as f:
        f.write(asp)

    # 2. Ask clingo which expressions the trace violates. This is the step that
    #    proves the encoding works: an empty list means the trace does not
    #    violate g1 under the current semantics, and the .las below would be
    #    vacuous.
    violations = get_violations(asp, exp_type=LEARNING.exp_type())
    print("violations found:", violations or "NONE - check the trace")

    # 3. ILASP: the learning task that would weaken the violated guarantee.
    encoder = NewSpecEncoder(NoFilterHeuristicManager())
    las = encoder.encode_ILASP(spec, trace, [], violations, LEARNING)
    with open(os.path.join(HERE, "simple_implication.las"), "w") as f:
        f.write(las)

    print("wrote simple_implication.asp and simple_implication.las")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
