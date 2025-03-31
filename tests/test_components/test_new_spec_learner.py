import os
from unittest import TestCase

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.new_spec_learner import NewSpecLearner
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines


class TestNewSpecLearner(TestCase):
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

    def test_learn_spec_asm_1(self):
        spec_learner = NewSpecLearner(NoFilterHeuristicManager())

        spec: SpectraSpecification = SpectraSpecification.from_file(
            '../input-files/case-studies/spectra/minepump/strong.spectra')
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")

        expected_spec: list[str] = SpectraSpecification.from_file(
            './test_files/minepump_aw_methane.spectra')

        new_specs: list[ISpecification]
        new_specs = spec_learner.learn_new(spec, (trace, [], Learning.ASSUMPTION_WEAKENING))

        print(expected_spec)
        print(new_specs)
        self.assertEqual(expected_spec, new_specs[0])
