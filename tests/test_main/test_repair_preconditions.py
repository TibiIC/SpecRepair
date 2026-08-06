"""
The repair's preconditions on its case study, asserted before the search starts.

A repair run assumes a realisable input specification and a trace that violates
at least one non-initial assumption. Both are properties of the case study, and
8 of the 70 shipped ones broke them - which surfaced as an IndexError or a
TypeError several layers down rather than as "this input is malformed".
"""
import os
import tempfile
import unittest

from main.bfs_repair_orchestrator_builder import BFSRepairOrchestratorBuilder
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.exceptions import InvalidCaseStudyException
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from tests.base_test_case import BaseTestCase

CASE_STUDIES = '../input-files/case-studies/spectra'


def _repairer():
    return (BFSRepairOrchestratorBuilder.syntactic()
            .enabling("INCLUDE_NEXT", "INCLUDE_PREV")
            .with_log_file(os.devnull).build())


def _run(spec_path, trace_path):
    spec = SpectraSpecification.from_file(spec_path)
    trace = read_file_lines(trace_path)
    _repairer().repair_bfs(
        spec, RepairData(trace, counter_traces=[],
                         learning_type=Learning.ASSUMPTION_WEAKENING))


class TestRepairPreconditions(BaseTestCase):
    def test_a_trace_violating_no_assumption_is_rejected(self):
        """
        A trace that violates nothing must be refused up front. Previously it
        sent an already-realisable spec into guarantee weakening, where the
        unrealisable core is empty, the learning task is UNSAT, and the branch
        died without reaching a leaf.

        The offending input is *derived* rather than named. This used to point
        at humanoid_updated, whose shipped trace violated nothing - and then the
        2026-08-06 audit regenerated exactly those traces, so the fixture became
        valid and the test asserted a rejection that correctly no longer
        happened. A test of the preconditions must not depend on a case study
        staying broken when the whole point is to fix them.

        A repaired specification is the construction that cannot rot: a solution
        is by definition one whose assumptions the trace no longer violates, so
        feeding one back with the trace that produced it must trip precondition
        2 for as long as the definition holds.
        """
        d = f'{CASE_STUDIES}/case_study_2/minepump'
        spec = SpectraSpecification.from_file(f'{d}/original.spectra')
        trace = read_file_lines(f'{d}/violation_trace_0.txt')
        repairer = _repairer()
        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[],
                                             learning_type=Learning.ASSUMPTION_WEAKENING))
        repaired = repairer.recorder.get_specs()
        self.assertTrue(repaired, "minepump produced no repair to build the fixture from")

        already_repaired = SpectraSpecification.from_str(repaired[0])
        with self.assertRaises(InvalidCaseStudyException) as ctx:
            _repairer().repair_bfs(
                already_repaired,
                RepairData(trace, counter_traces=[],
                           learning_type=Learning.ASSUMPTION_WEAKENING))
        self.assertIn("no assumption at all", str(ctx.exception))

    def test_a_trace_violating_only_an_initial_assumption_is_rejected(self):
        """
        Weakening an initial assumption pulls system variables into it, which
        Spectra's CLI forbids - so a trace whose only violation is initial does
        not describe a repairable problem.

        The trace is built here rather than taken from a case study, for the
        reason given above: this pointed at gyro's trace 0, which the audit then
        regenerated, leaving the test to run a full repair and assert a rejection
        that no longer happened.

        Against minepump, `highwater` at time 0 violates
        `initial_assumption` (!highwater & !methane) and nothing else:
        `assumption1_1` needs `pump` in two consecutive states and `assumption2_1`
        needs `highwater` and `methane` together, so holding both `pump` and
        `methane` false throughout leaves the initial one the only violation.
        """
        spec_path = f'{CASE_STUDIES}/case_study_2/minepump/original.spectra'
        timepoints = [
            "holds_at(highwater,{t},trace_name_0).",
            "not_holds_at(methane,{t},trace_name_0).",
            "not_holds_at(pump,{t},trace_name_0).",
        ]
        trace = "\n\n".join(
            "\n".join(line.format(t=t) for line in timepoints) for t in range(3)) + "\n"

        with tempfile.TemporaryDirectory() as tmp:
            trace_path = os.path.join(tmp, "initial_only_violation.txt")
            with open(trace_path, "w") as f:
                f.write(trace)
            with self.assertRaises(InvalidCaseStudyException) as ctx:
                _run(spec_path, trace_path)
        self.assertIn("initial assumption", str(ctx.exception))

    def test_a_valid_case_study_is_not_rejected(self):
        """
        minepump violates a non-initial assumption from a realisable spec, so
        the preconditions must let it through.

        Named deliberately, unlike the two rejection cases above: that a shipped
        case study still satisfies the preconditions is a claim worth making
        about the shipped case studies, and one that should fail loudly if a
        regenerated trace ever stops satisfying them.
        """
        d = f'{CASE_STUDIES}/case_study_2/minepump'
        _run(f'{d}/original.spectra', f'{d}/violation_trace_0.txt')


if __name__ == "__main__":
    unittest.main()
