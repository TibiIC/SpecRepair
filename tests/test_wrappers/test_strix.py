"""
Test suite for the Strix Python wrapper.

Tests are split into two groups:
- StrixMockedTests: use unittest.mock to patch subprocess.Popen, so they
  run without a Strix binary installed. These cover all wrapper logic.
- StrixIntegrationTests: actually invoke the binary and are skipped
  automatically when it is not found on PATH or at STRIX_BINARY.

Set the environment variable STRIX_BINARY to point at your binary if it
is not on PATH, e.g.:
    STRIX_BINARY=/path/to/strix python -m pytest test_strix.py
"""

import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from spec_repair.wrappers.strix import Strix, StrixResult, OutputFormat, LabelEncoding

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ARBITER_FORMULA = (
    "G (req0 -> F grant0) & G (req1 -> F grant1) & G (!(grant0 & grant1))"
)
ARBITER_INS = ["req0", "req1"]
ARBITER_OUTS = ["grant0", "grant1"]

UNREALIZABLE_FORMULA = "G (r -> grant) & G (!grant)"
UNREALIZABLE_INS = ["r"]
UNREALIZABLE_OUTS = ["grant"]


def _make_proc(stdout: str, stderr: str = "", returncode: int = 0) -> MagicMock:
    """Return a mock Popen process whose communicate() returns (stdout, stderr)."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc


# ---------------------------------------------------------------------------
# Mocked tests  (no binary required)
# ---------------------------------------------------------------------------

class StrixMockedTests(unittest.TestCase):
    """Unit tests that mock subprocess.Popen to test wrapper logic in isolation."""

    def setUp(self):
        self.strix = Strix(binary="strix")

    # --- StrixResult parsing ---

    def test_realizable_flag_set_true_on_realizable_output(self):
        proc = _make_proc("REALIZABLE\nHOA: v1\n...")
        with patch("subprocess.Popen", return_value=proc):
            result = self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        self.assertTrue(result.realizable)

    def test_realizable_flag_set_false_on_unrealizable_output(self):
        proc = _make_proc("UNREALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc):
            result = self.strix.check_realizability(
                UNREALIZABLE_FORMULA, UNREALIZABLE_INS, UNREALIZABLE_OUTS
            )
        self.assertFalse(result.realizable)

    def test_realizable_flag_none_on_empty_output(self):
        proc = _make_proc("")
        with patch("subprocess.Popen", return_value=proc):
            result = self.strix._run(["-f", "G p", "--ins=", "--outs=p"])
        self.assertIsNone(result.realizable)

    def test_output_preserved_verbatim(self):
        raw = "REALIZABLE\nHOA: v1\nStates: 1\n"
        proc = _make_proc(raw)
        with patch("subprocess.Popen", return_value=proc):
            result = self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        self.assertEqual(result.output, raw)

    def test_stderr_preserved(self):
        proc = _make_proc("REALIZABLE\n", stderr="some warning")
        with patch("subprocess.Popen", return_value=proc):
            result = self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        self.assertEqual(result.stderr, "some warning")

    def test_returncode_preserved(self):
        proc = _make_proc("REALIZABLE\n", returncode=0)
        with patch("subprocess.Popen", return_value=proc):
            result = self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        self.assertEqual(result.returncode, 0)

    def test_result_is_strix_result_dataclass(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc):
            result = self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        self.assertIsInstance(result, StrixResult)

    # --- check_realizability command construction ---

    def test_realizability_passes_realizability_flag(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.check_realizability(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertIn("--realizability", cmd)

    def test_realizability_passes_formula(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.check_realizability(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertIn(ARBITER_FORMULA, cmd)

    def test_realizability_passes_ins(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.check_realizability(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertTrue(any("req0,req1" in arg for arg in cmd))

    def test_realizability_passes_outs(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.check_realizability(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertTrue(any("grant0,grant1" in arg for arg in cmd))

    # --- synthesize command construction ---

    def test_synthesize_default_format_is_hoa(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertIn("hoa", cmd)
        self.assertNotIn("--aiger", cmd)

    def test_synthesize_aag_format(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(
                ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS,
                output_format=OutputFormat.AAG,
            )
        cmd = mock_popen.call_args[0][0]
        self.assertIn("aag", cmd)

    def test_synthesize_aiger_format_uses_flag(self):
        """OutputFormat.AIGER should produce --aiger instead of -o aiger."""
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(
                ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS,
                output_format=OutputFormat.AIGER,
            )
        cmd = mock_popen.call_args[0][0]
        self.assertIn("--aiger", cmd)

    def test_synthesize_label_encoding_included(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(
                ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS,
                label_encoding=LabelEncoding.STRUCTURED,
            )
        cmd = mock_popen.call_args[0][0]
        self.assertIn("-l", cmd)
        self.assertIn("structured", cmd)

    def test_synthesize_no_label_encoding_by_default(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertNotIn("-l", cmd)

    def test_synthesize_does_not_pass_realizability_flag(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertNotIn("--realizability", cmd)

    # --- binary path ---

    def test_custom_binary_path_used(self):
        strix = Strix(binary="/Users/tg4018/Tools/bin/strix")
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        cmd = mock_popen.call_args[0][0]
        self.assertEqual(cmd[0], "/Users/tg4018/Tools/bin/strix")

    # --- Popen configuration ---

    def test_popen_uses_pipes(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        kwargs = mock_popen.call_args[1]
        self.assertEqual(kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(kwargs["stderr"], subprocess.PIPE)

    def test_popen_uses_text_mode(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc) as mock_popen:
            self.strix.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)
        kwargs = mock_popen.call_args[1]
        self.assertTrue(kwargs.get("text"))

    # --- Timeout handling ---

    def test_timeout_passed_to_communicate(self):
        proc = _make_proc("REALIZABLE\n")
        with patch("subprocess.Popen", return_value=proc):
            self.strix.synthesize(
                ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS, timeout=30.0
            )
        proc.communicate.assert_called_once_with(timeout=30.0)

    def test_timeout_raises_timeout_error(self):
        proc = MagicMock()
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="strix", timeout=1),
            ("", ""),  # cleanup call after proc.kill()
        ]
        proc.returncode = -1
        with patch("subprocess.Popen", return_value=proc):
            with self.assertRaises(TimeoutError):
                self.strix.synthesize(
                    ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS, timeout=1.0
                )

    def test_timeout_kills_process_on_expiry(self):
        proc = MagicMock()
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="strix", timeout=1),
            ("", ""),  # cleanup call after proc.kill()
        ]
        proc.returncode = -1
        with patch("subprocess.Popen", return_value=proc):
            with self.assertRaises(TimeoutError):
                self.strix.synthesize(
                    ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS, timeout=1.0
                )
        proc.kill.assert_called_once()


# ---------------------------------------------------------------------------
# Integration tests  (require actual binary)
# ---------------------------------------------------------------------------

def _strix_binary() -> str:
    return os.environ.get("STRIX_BINARY", "strix")


def _binary_available() -> bool:
    try:
        subprocess.run(
            [_strix_binary(), "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@unittest.skipUnless(_binary_available(), "Strix binary not found; skipping integration tests")
class StrixIntegrationTests(unittest.TestCase):
    """End-to-end tests that run the real Strix binary."""

    def setUp(self):
        self.strix = Strix(binary=_strix_binary())

    def test_arbiter_is_realizable(self):
        result = self.strix.check_realizability(
            ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS
        )
        self.assertTrue(result.realizable)
        self.assertEqual(result.returncode, 0)

    def test_unrealizable_formula(self):
        result = self.strix.check_realizability(
            UNREALIZABLE_FORMULA, UNREALIZABLE_INS, UNREALIZABLE_OUTS
        )
        self.assertFalse(result.realizable)

    def test_synthesize_hoa_contains_hoa_header(self):
        result = self.strix.synthesize(
            ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS,
            output_format=OutputFormat.HOA,
        )
        self.assertTrue(result.realizable)
        self.assertIn("HOA:", result.output)

    def test_synthesize_aag_contains_aag_header(self):
        result = self.strix.synthesize(
            ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS,
            output_format=OutputFormat.AAG,
        )
        self.assertTrue(result.realizable)
        self.assertIn("aag", result.output)

    def test_synthesize_structured_label_encoding(self):
        result = self.strix.synthesize(
            ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS,
            output_format=OutputFormat.HOA,
            label_encoding=LabelEncoding.STRUCTURED,
        )
        self.assertTrue(result.realizable)
        self.assertIn("HOA:", result.output)

    def test_returncode_zero_on_success(self):
        result = self.strix.synthesize(
            ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS
        )
        self.assertEqual(result.returncode, 0)

    def test_invalid_binary_raises_file_not_found(self):
        bad = Strix(binary="/nonexistent/strix")
        with self.assertRaises(FileNotFoundError):
            bad.synthesize(ARBITER_FORMULA, ARBITER_INS, ARBITER_OUTS)


if __name__ == "__main__":
    unittest.main()