import os
from unittest import TestCase

from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.spectra_boolean_specification import SpectraBooleanSpecification
from spec_repair.util.spec_util import generate_trace_asp


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
        spec = SpectraBooleanSpecification.from_file("./debug_logs/specification.spectra")
        spec.to_asp(for_clingo=True, hm=NoFilterHeuristicManager())

    def test_hongbo(self):
        ideal_spec_file = "./test_debug/hongbo_helper_files/ideal_spec.spectra"
        strong_spec_file = "./test_debug/hongbo_helper_files/strong_spec.spectra"
        trace_file = "./test_debug/hongbo_helper_files/trace.txt"
        generate_trace_asp(strong_spec_file, ideal_spec_file, trace_file)