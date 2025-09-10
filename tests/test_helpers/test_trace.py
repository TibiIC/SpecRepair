import os
from typing import Optional
from unittest import TestCase

from py_ltl.formula import AtomicProposition

from spec_repair.helpers.trace import Trace
from spec_repair.util.file_util import read_file_lines


class TestTrace(TestCase):
    @classmethod
    def setUpClass(cls):
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        test_components_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(test_components_dir)
        os.chdir(tests_dir)

    @classmethod
    def tearDownClass(cls):
        # Restore the original working directory
        os.chdir(cls.original_working_directory)

    def test_from_str(self):
        case_study_path = '../input-files/case-studies/spectra/minepump'
        expected_sets = [(
            AtomicProposition("highwater", False),
            AtomicProposition("methane", False),
            AtomicProposition("pump", False)
        ), (
            AtomicProposition("highwater", True),
            AtomicProposition("methane", True),
            AtomicProposition("pump", False)
        )]
        self.run_compare_case_study(
            case_study_path,
            expected_sets,
            loops_at_index=None
        )

    def run_compare_case_study(self, case_study_path, expected_sets, loops_at_index: Optional[int] = None):
        trace_str: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        trace = Trace.from_str("\n".join(trace_str))
        if loops_at_index is not None:
            self.assertEqual(len(trace), -1)
        else:
            self.assertEqual(len(trace), len(expected_sets))
        for i, expected in enumerate(expected_sets):
            self.assertEqual(trace[i], expected)
        if loops_at_index is not None:
            self.assertEqual(trace[loops_at_index], trace[len(expected_sets)])
