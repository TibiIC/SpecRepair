"""
The repair's preconditions on its case study, asserted before the search starts.

A repair run assumes a realisable input specification and a trace that violates
at least one non-initial assumption. Both are properties of the case study, and
8 of the 70 shipped ones broke them - which surfaced as an IndexError or a
TypeError several layers down rather than as "this input is malformed".
"""
import os
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
        humanoid_updated's trace violates nothing. Previously this sent an
        already-realisable spec into guarantee weakening, where the unrealisable
        core is empty, the learning task is UNSAT, and the branch died without
        reaching a leaf.
        """
        d = f'{CASE_STUDIES}/case_study_1/humanoid_updated'
        with self.assertRaises(InvalidCaseStudyException) as ctx:
            _run(f'{d}/strong.spectra', f'{d}/violation_trace.txt')
        self.assertIn("no assumption at all", str(ctx.exception))

    def test_a_trace_violating_only_an_initial_assumption_is_rejected(self):
        """
        gyro's trace 0 violates only `initially_not_ready`. Weakening an initial
        assumption pulls system variables into it, which Spectra's CLI forbids.
        """
        d = f'{CASE_STUDIES}/case_study_2/gyro'
        with self.assertRaises(InvalidCaseStudyException) as ctx:
            _run(f'{d}/original.spectra', f'{d}/violation_trace_0.txt')
        self.assertIn("initial assumption", str(ctx.exception))

    def test_a_valid_case_study_is_not_rejected(self):
        """elevator violates a non-initial assumption from a realisable spec."""
        d = f'{CASE_STUDIES}/case_study_2/elevator'
        _run(f'{d}/original.spectra', f'{d}/violation_trace_0.txt')


if __name__ == "__main__":
    unittest.main()
