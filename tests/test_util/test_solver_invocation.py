"""
A solver that cannot run must not look like a solver that found nothing.

`get_violations` returned an empty list for both, so clingo failing to start
read as "this trace violates no assumption" - a claim about the specification,
made because a shared library was missing. Found on the Slurm compute nodes,
where clingo could not load `liblua5.1.so.0`: a trace that passes the check
locally was reported as violating nothing at all.
"""
import os
import stat
import tempfile
import unittest

from spec_repair.exceptions import SolverInvocationError
from spec_repair.util.asp_trace_util import CLINGO_VERDICT_CODES, run_clingo_raw
from spec_repair.util.subprocess_util import run_subprocess


def _fake_binary(directory: str, name: str, body: str) -> str:
    path = os.path.join(directory, name)
    with open(path, "w") as f:
        f.write(body)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    return path


class TestClingoVerdicts(unittest.TestCase):
    """Clingo reports through its exit code; 10/20/30 are verdicts, else failure."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _program(self, text: str) -> str:
        path = os.path.join(self.tmp, "p.lp")
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_a_satisfiable_program_still_works(self):
        self.assertIn("SATISFIABLE", run_clingo_raw(self._program("a. b :- a.\n")))

    def test_unsatisfiable_is_a_verdict_not_a_failure(self):
        """
        The distinction that makes exit codes the right test. UNSAT is an
        answer - the repair relies on it - and exits 20.
        """
        self.assertIn("UNSATISFIABLE", run_clingo_raw(self._program("a.\n:- a.\n")))

    def test_a_malformed_program_raises_instead_of_returning_nothing(self):
        """
        Exit 65, and clingo still prints "UNKNOWN" - so reading the output
        alone cannot tell an error from an answer. Only the code can.
        """
        with self.assertRaises(SolverInvocationError):
            run_clingo_raw(self._program("this is not asp {{{\n"))

    def test_the_verdict_codes_are_the_ones_clingo_uses(self):
        self.assertEqual((10, 20, 30), CLINGO_VERDICT_CODES)


class TestReturnCodeChecking(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_a_binary_that_cannot_start_raises_with_its_stderr(self):
        """
        The Slurm failure exactly: the binary exists, exits non-zero before
        doing anything, and says why on stderr - which was being discarded.
        """
        binary = _fake_binary(self.tmp, "broken", (
            '#!/bin/bash\n'
            'echo "error while loading shared libraries: liblua5.1.so.0" >&2\n'
            'exit 127\n'))
        with self.assertRaises(SolverInvocationError) as ctx:
            run_subprocess([binary], ok_returncodes=(0,))
        self.assertIn("127", str(ctx.exception))
        self.assertIn("liblua5.1", str(ctx.exception),
                      "the reason was on stderr and should be reported")

    def test_checking_is_off_unless_asked_for(self):
        """
        The other callers read failure out of the output in their own way, so
        adding a check must not change what they see.
        """
        binary = _fake_binary(self.tmp, "quiet", '#!/bin/bash\necho out\nexit 3\n')
        self.assertEqual("out\n", run_subprocess([binary]))


if __name__ == "__main__":
    unittest.main()
