import os
from typing import Optional
from unittest import TestCase

from py_ltl.formula import AtomicProposition

from spec_repair.helpers.trace import Trace
from spec_repair.util.file_util import read_file_lines
from tests.base_test_case import BaseTestCase


class TestTrace(BaseTestCase):
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

    def test_to_asp_str(self):
        trace = Trace(
            values=[
                (
                    AtomicProposition("highwater", False),
                    AtomicProposition("methane", False),
                    AtomicProposition("pump", False)
                ),
                (
                    AtomicProposition("highwater", True),
                    AtomicProposition("methane", True),
                    AtomicProposition("pump", False)
                )
            ],
            name="trace_name_0",
            loop_index=None
        )
        expected_output = """\
%---*** Violation Trace ***---

trace(trace_name_0).

timepoint(0,trace_name_0).
timepoint(1,trace_name_0).
next(1,0,trace_name_0).

not_holds_at(highwater,0,trace_name_0).
not_holds_at(methane,0,trace_name_0).
not_holds_at(pump,0,trace_name_0).
holds_at(highwater,1,trace_name_0).
holds_at(methane,1,trace_name_0).
not_holds_at(pump,1,trace_name_0).\
"""
        asp_str = trace.to_asp_str()
        asp_str = "%---*** Violation Trace ***---\n\n" + asp_str
        self.assertEqual(asp_str.strip(), expected_output.strip())