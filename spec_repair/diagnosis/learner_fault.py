r"""
A learned solution that still violates its own trace is a **defect**, not a
branch outcome.

The learning task asks for a hypothesis under which the violation trace is
entailed - `#pos({entailed(trace_name_1)},{},{...})`. A solution to that task
therefore *cannot* leave the trace violating an assumption. If one does, the
chain from task to specification is broken somewhere: the mode declarations, the
bias, the ASP encoding of the formula, the parsing of the returned rules, or the
application of the adaptations. Every one of those is a correctness bug that
silently weakens the wrong thing and produces results that look genuine.

This is what happened on minepump_liveness trace 1 and it went unnoticed through
a full sweep: three of seventeen `final_specs` failed the trace they were
repaired for, and the merge downstream inherited the failure. Nothing in the run
said so. `disjunction_index` was being applied to a disjunct list that the
previous adaptation had already rewritten - see
`GR1Formula._integrate_antecedent_exceptions`.

So the check is an assertion about the learning pipeline, and when it fires the
run writes a complete bundle - the task the solver was given, its raw output,
the adaptations parsed from it, the specification before and after, and the
violations that remain - so the fault can be reproduced offline without
re-running the search. It is logged at ERROR, counted, and surfaced in the run's
final summary.

The search continues rather than aborting: a sweep of fifty runs should not lose
forty-nine results to one bad branch, and the bundle is what makes the fault
actionable either way. `SPEC_REPAIR_STRICT_LEARNER=1` turns it into an immediate
`LearnerContractViolation` for anyone who would rather stop at the first one.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

_logger = logging.getLogger(__name__)


class LearnerContractViolation(Exception):
    """A learned solution does not satisfy the example its task demanded."""


@dataclass
class LearningArtifact:
    """One invocation of a solver: what it was asked, and what it answered."""
    solver: str
    task: str
    raw_outputs: List[str] = field(default_factory=list)
    learning_type: str = ""
    config: str = ""


def strict_mode() -> bool:
    return os.environ.get("SPEC_REPAIR_STRICT_LEARNER", "") == "1"


def _bundle_root(debug_folder: Optional[str]) -> str:
    # Beside the run's other output when there is one, so a fault travels with
    # the results it corrupted rather than landing in whatever the cwd was.
    base = os.path.dirname(debug_folder.rstrip("/")) if debug_folder else "."
    return os.path.join(base, "learner_faults")


def report_learner_fault(
        *,
        spec_before,
        spec_after,
        adaptations,
        violated_assumptions: List[str],
        artifacts: List[LearningArtifact],
        trace: List[str],
        debug_folder: Optional[str] = None,
        note: str = "",
) -> str:
    """
    Write a reproduction bundle for one trace-violating solution and log it.

    Returns the directory written. Raises `LearnerContractViolation` first when
    `SPEC_REPAIR_STRICT_LEARNER=1`.
    """
    root = _bundle_root(debug_folder)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    out = os.path.join(root, stamp)

    summary = {
        "when": stamp,
        "note": note,
        "violated_assumptions": violated_assumptions,
        "n_adaptations": len(adaptations),
        "adaptations": [str(a) for a in adaptations],
        "solvers": [a.solver for a in artifacts],
        "n_learning_tasks": len(artifacts),
    }

    try:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "summary.json"), "w") as fh:
            json.dump(summary, fh, indent=2)
        with open(os.path.join(out, "spec_before.spectra"), "w") as fh:
            fh.write(spec_before.to_str())
        with open(os.path.join(out, "spec_after.spectra"), "w") as fh:
            fh.write(spec_after.to_str())
        with open(os.path.join(out, "violation_trace.txt"), "w") as fh:
            fh.writelines(trace)
        with open(os.path.join(out, "adaptations.txt"), "w") as fh:
            fh.write("\n".join(str(a) for a in adaptations) + "\n")
        for i, art in enumerate(artifacts):
            with open(os.path.join(out, f"task_{i}.{art.solver}.las"), "w") as fh:
                fh.write(art.task)
            for j, raw in enumerate(art.raw_outputs):
                with open(os.path.join(out, f"task_{i}_output_{j}.txt"), "w") as fh:
                    fh.write(raw)
    except OSError as e:
        # Never let the diagnostic be the thing that kills the run.
        _logger.error("could not write learner-fault bundle to %s: %s", out, e)
        out = ""

    _logger.error(
        "LEARNER CONTRACT VIOLATED: the learned specification still violates "
        "%s on the trace it was repaired for. The task required "
        "entailed(<trace>), so no solution to it can leave the trace violating. "
        "%d adaptation(s) from %d learning task(s). Bundle: %s. %s",
        ", ".join(violated_assumptions) or "an assumption",
        len(adaptations), len(artifacts), out or "<unwritable>", note)

    if strict_mode():
        raise LearnerContractViolation(
            f"learned specification still violates {violated_assumptions}; "
            f"bundle at {out}")
    return out
