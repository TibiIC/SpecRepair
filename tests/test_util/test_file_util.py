import os
import tempfile
from unittest import TestCase

from spec_repair.util.file_util import is_file_extension, read_file_lines, write_trace


class TestFileUtil(TestCase):
    def test_degrade_spec_step(self):
        self.assertTrue(is_file_extension(".csv"))
        self.assertTrue(is_file_extension(".txt"))
        self.assertFalse(is_file_extension("data.csv"))
        self.assertFalse(is_file_extension("file_without_extension"))
        self.assertTrue(is_file_extension(".answer_set"))


class TestWriteTrace(TestCase):
    """
    write_trace appends each trace under the next trace_name_<n>.

    Replaces the deleted test_debug/test_asp.py::test_hongbo, which drove this
    indirectly through generate_trace_asp against fixed debug artefacts and had
    been on the skip-list for failing on an empty trace.txt. The numbering rule
    was what it actually exercised, so it is asserted here directly - against a
    temporary file, so a run cannot mutate a checked-in fixture the way that
    test did.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.trace_file = os.path.join(self.tmp, "trace.txt")

    def names_written(self):
        return ''.join(read_file_lines(self.trace_file))

    def test_a_missing_file_starts_at_zero(self):
        write_trace({0: ["highwater"]}, self.trace_file)
        self.assertIn("trace_name_0", self.names_written())

    def test_an_existing_empty_file_also_starts_at_zero(self):
        """
        Regression: an existing but empty file took the success branch, where
        max() over no trace names raised ValueError. Both "no file" and "file
        with no traces" mean nothing has been written yet.
        """
        open(self.trace_file, "w").close()
        write_trace({0: ["highwater"]}, self.trace_file)
        self.assertIn("trace_name_0", self.names_written())

    def test_writing_again_uses_the_next_number(self):
        write_trace({0: ["highwater"]}, self.trace_file)
        write_trace({0: ["methane"]}, self.trace_file)
        written = self.names_written()
        self.assertIn("trace_name_0", written)
        self.assertIn("trace_name_1", written)
