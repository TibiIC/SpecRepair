"""
One sweep must stamp one date into its output directory names.

`datetime.now()` is evaluated when the *job* starts, not when the sweep does,
and a sweep releases its jobs through a concurrency semaphore over many hours.
The 2026-08-08 sweep launched at 20:11 and its later jobs therefore wrote
`gyro_trace2_fastlas_2026-08-09` beside `gyro_trace2_fastlas_2026-08-08`. That
is not cosmetic: `pull_experiment_from_ssh.sh` and every pipeline step after it
select a run by globbing `*_<date>`, so the jobs that crossed midnight were
silently left on the remote. A two-day sweep would scatter across three dates.

The runner now resolves the date once and exports `SPEC_REPAIR_RUN_DATE`.
"""
import os
import unittest
from datetime import datetime
from unittest import mock

from tests.test_main.test_case_study_1 import run_date_str


class TestRunDateStamp(unittest.TestCase):
    def test_unset_falls_back_to_today(self):
        """A developer running a single test still gets today's date."""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SPEC_REPAIR_RUN_DATE", None)
            self.assertEqual(run_date_str(), datetime.now().strftime("%Y-%m-%d"))

    def test_the_exported_date_wins_over_today(self):
        """
        The point of the variable: a job starting after midnight must still
        stamp the date its sweep was launched on, not its own.
        """
        with mock.patch.dict(os.environ, {"SPEC_REPAIR_RUN_DATE": "2026-08-08"}):
            self.assertEqual(run_date_str(), "2026-08-08")

    def test_blank_is_treated_as_unset(self):
        """`export SPEC_REPAIR_RUN_DATE=` must not name a directory ``."""
        with mock.patch.dict(os.environ, {"SPEC_REPAIR_RUN_DATE": "   "}):
            self.assertEqual(run_date_str(), datetime.now().strftime("%Y-%m-%d"))

    def test_a_malformed_date_is_refused(self):
        """
        The value becomes part of a directory name the pipeline globs on, so a
        typo must fail at launch rather than produce a directory no later step
        can find.
        """
        for bad in ("2026-8-8", "08-08-2026", "yesterday", "2026-08-08/../.."):
            with self.subTest(bad=bad):
                with mock.patch.dict(os.environ, {"SPEC_REPAIR_RUN_DATE": bad}):
                    with self.assertRaises(ValueError):
                        run_date_str()


if __name__ == "__main__":
    unittest.main()
