"""
Spectra's output has to survive the process that produced it.

Spectra runs inside this process's JVM, so a native crash during synthesis
takes the repair run with it. The output used to be captured into an in-memory
ByteArrayOutputStream read back only after the call returned, so a run that died
mid-verification left an ordinary progress line as its last word and no cause -
five FastLAS runs on 2026-08-08 ended exactly that way. The capture is now a
file, flushed per line.
"""
import os
import tempfile
import unittest
from unittest import mock

from spec_repair.wrappers.spectra_toolbox import (spectra_call_log_path,
                                                  synthesise_check_realisability_only)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MINEPUMP = os.path.join(PROJECT_ROOT, "input-files", "case-studies", "spectra",
                        "case_study_3", "minepump", "original.spectra")
ENV = "SPEC_REPAIR_SPECTRA_CALL_LOG_DIR"


class TestSpectraCallLogPath(unittest.TestCase):
    def test_uses_the_configured_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "jvm")
            with mock.patch.dict(os.environ, {ENV: target}):
                path = spectra_call_log_path()
            self.assertEqual(target, os.path.dirname(path))
            self.assertTrue(os.path.isdir(target),
                            "the directory must be created, not merely named - the sweep "
                            "points this at a logdir subdirectory that does not exist yet")

    def test_names_the_file_per_process(self):
        """Concurrent runs share a filesystem; they must not share a file."""
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {ENV: tmp}):
                self.assertIn(str(os.getpid()), os.path.basename(spectra_call_log_path()))

    def test_falls_back_to_the_temp_directory(self):
        """An unsupervised run must not fail for want of a log directory."""
        for value in ({}, {ENV: "   "}):
            with self.subTest(env=value):
                with mock.patch.dict(os.environ, value, clear=(value == {})):
                    self.assertEqual(tempfile.gettempdir(),
                                     os.path.dirname(spectra_call_log_path()))


class TestSpectraOutputSurvivesTheCall(unittest.TestCase):
    def test_output_is_on_disk_as_well_as_returned(self):
        """
        The returned string is what callers parse; the file is what is left
        behind when the process does not live to return one.
        """
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {ENV: tmp}):
                returned = synthesise_check_realisability_only(MINEPUMP)
                on_disk = open(spectra_call_log_path(), encoding="utf-8").read()

        self.assertIn("Result: Specification is", returned,
                      "the realisability verdict is what every caller reads")
        self.assertEqual(returned, on_disk)


if __name__ == "__main__":
    unittest.main()
