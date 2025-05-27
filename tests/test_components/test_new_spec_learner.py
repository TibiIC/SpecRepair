import os
from typing import Any, Tuple
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

        expected_specs: list[ISpecification] = []
        expected_specs.append(SpectraSpecification.from_file('./test_files/minepump_aw_methane.spectra'))
        expected_specs.append(SpectraSpecification.from_file('./test_files/minepump_aw_highwater.spectra'))
        expected_specs.append(SpectraSpecification.from_file('./test_files/minepump_aw_pump.spectra'))
        expected_specs.append(SpectraSpecification.from_file('./test_files/minepump_aw_ev.spectra'))

        new_tasks: list[Tuple[ISpecification, Any]]
        new_tasks = spec_learner.learn_new(spec, (trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0))
        new_specs_str: list[str] = [new_spec.to_str() for new_spec, new_data in new_tasks]

        for new_spec_str in new_specs_str:
            print(new_spec_str)
        for i, expected_spec in enumerate(expected_specs):
            print(i)
            self.assertIn(expected_spec.to_str(), new_specs_str)
