"""
Scratch files must not accumulate.

They went loose into /tmp and were deleted by nobody. On 2026-08-08 that filled
a 32G tmpfs on every GPU box - 1.2M `.lp`, 121k `.las` and 133k `.spectra` on
gpu11 alone - and every case_study_2 ILASP run and every case_study_3 FastLAS
run failed with `OSError: [Errno 28] No space left on device`. It looked like a
code regression and was a full disk.
"""
import os
import unittest

from spec_repair.util import file_util
from spec_repair.util.file_util import (discard_temp_file,
                                        generate_temp_filename)


class TestTempFileLocation(unittest.TestCase):
    def test_temp_files_live_in_a_per_process_directory(self):
        """
        Grouping by pid means a killed run leaves one identifiable directory
        rather than files indistinguishable from anyone else's.
        """
        path = generate_temp_filename(".lp")
        self.assertIn(f"spec_repair_{os.getpid()}", path)
        discard_temp_file(path)

    def test_the_directory_exists_so_writing_does_not_fail(self):
        path = generate_temp_filename(".lp")
        with open(path, "w") as f:
            f.write("a.\n")
        self.assertTrue(os.path.isfile(path))
        discard_temp_file(path)

    def test_discarding_a_missing_file_is_not_an_error(self):
        """Losing a scratch file is never worth failing a repair over."""
        discard_temp_file(os.path.join(file_util._TEMP_DIR, "never_existed.lp"))

    def test_names_do_not_collide(self):
        names = {generate_temp_filename(".lp") for _ in range(200)}
        self.assertEqual(200, len(names))
        for n in names:
            discard_temp_file(n)


class TestSolverPathsCleanUp(unittest.TestCase):
    """
    The hot paths delete as they go. Waiting for process exit is not enough: a
    single search makes thousands, and that is what filled the disk.
    """

    def _temp_files(self):
        if not os.path.isdir(file_util._TEMP_DIR):
            return []
        return os.listdir(file_util._TEMP_DIR)

    def test_running_clingo_leaves_nothing_behind(self):
        from spec_repair.wrappers.asp_wrappers import run_clingo
        before = len(self._temp_files())
        for _ in range(5):
            run_clingo("a. b :- a.\n")
        self.assertEqual(before, len(self._temp_files()),
                         "clingo left scratch files behind")


if __name__ == "__main__":
    unittest.main()
