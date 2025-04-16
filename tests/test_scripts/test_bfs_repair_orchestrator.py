import os
from typing import Dict
from unittest import TestCase

import dill

from scripts.bfs_repair_orchestrator import BFSRepairOrchestrator
from spec_repair.components.interfaces.ilearner import ILearner
from spec_repair.components.new_spec_learner import NewSpecLearner
from spec_repair.components.new_spec_oracle import NewSpecOracle
from spec_repair.components.spec_mittigator import SpecMittigator
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.components.spectra_discriminator import SpectraDiscriminator
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.logger import RepairLogger
from spec_repair.helpers.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines, write_to_file


class TestBFSRepairOrchestrator(TestCase):
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

    def test_bfs_repair_spec_lift(self):
        out_test_dir_name = "./test_files/out/new_lift_test_bfs"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        # spec: SpectraSpecification = SpectraSpecification.from_file('../input-files/case-studies/spectra/lift/strong.spectra')
        with open('spec_lift_strong.dill', 'rb') as f:
            spec: SpectraSpecification = dill.load(f)
        trace: list[str] = read_file_lines("../input-files/case-studies/spectra/lift/violation_trace.txt")
        learners: Dict[str, ILearner] = {
            "assumption_weakening": NewSpecLearner(NoFilterHeuristicManager()),
            "guarantee_weakening": NewSpecLearner(NoFilterHeuristicManager())
        }
        recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        repairer: BFSRepairOrchestrator = BFSRepairOrchestrator(
            learners,
            NewSpecOracle(),
            SpectraDiscriminator(),
            SpecMittigator(),
            NoFilterHeuristicManager(),
            recorder
        )

        # Getting all possible repairs
        repairer.repair_bfs(spec, (trace, [], Learning.ASSUMPTION_WEAKENING))
        new_specs: list[str] = recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/lift_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        expected_specs_files: list[str] = os.listdir('./test_files/lift_weakenings')
        expected_specs_files.sort()  # To mimic the actual order of weakening from the algorithm
        expected_specs_files.reverse()  # To mimic the actual order of weakening from the algorithm
        for spec_file in expected_specs_files:
            print(spec_file)
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/lift_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(len(expected_specs), len(new_specs))
        self.assertEqual(expected_specs, new_specs)
