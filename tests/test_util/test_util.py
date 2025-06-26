from unittest import TestCase

from spec_repair.config import PROJECT_PATH
from spec_repair.util.file_util import is_file_format
from spec_repair.util.spec_util import synthesise_controller


class TestUtil(TestCase):
    def test_is_file_format(self):
        real_file_path: str = f"{PROJECT_PATH}/minempump_fixed.spectra"
        self.assertTrue(
            is_file_format(real_file_path, ".spectra")
        )

        self.assertFalse(
            is_file_format(f"complete_jibberish^etc.txt", ".txt")
        )

        self.assertFalse(
            is_file_format(real_file_path, ".txt")
        )

    def test_synthesise_controller_minepump(self):
        spec_path = f'{PROJECT_PATH}/input-files/case-studies/spectra/minepump/ideal.spectra'
        path_to_controller = f'{PROJECT_PATH}/tests/test_files/out/controllers/minepump_test'
        result = synthesise_controller(spec_path, path_to_controller)
        self.assertTrue(result)

    def test_synthesise_controller_arbiter(self):
        spec_path = f'{PROJECT_PATH}/input-files/case-studies/spectra/arbiter/ideal.spectra'
        path_to_controller = f'{PROJECT_PATH}/tests/test_files/out/controllers/arbiter_test'
        result = synthesise_controller(spec_path, path_to_controller)
        self.assertTrue(result)

    def test_synthesise_controller_invalid_minepump(self):
        spec_path = f'{PROJECT_PATH}/input-files/case-studies/spectra/minepump/unrealisable.spectra'
        path_to_controller = f'{PROJECT_PATH}/tests/test_files/out/controllers/minepump_test'
        result = synthesise_controller(spec_path, path_to_controller)
        self.assertFalse(result)
