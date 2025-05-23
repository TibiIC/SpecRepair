import os
from unittest import TestCase

from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.spectra_specification import SpectraSpecification


class TestASP(TestCase):
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

    def test_asp(self):
        spec = SpectraSpecification.from_file("./debug_logs/problem_spec.spectra")
        spec.to_asp(for_clingo=True, hm=NoFilterHeuristicManager())