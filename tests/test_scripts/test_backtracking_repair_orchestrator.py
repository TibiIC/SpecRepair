import os
import unittest
from unittest import TestCase

from scripts.backtracking_repair_orchestrator import BacktrackingRepairOrchestrator
from spec_repair.builders.spec_recorder import SpecRecorder
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.util.file_util import read_file_lines, write_to_file
from spec_repair.util.spec_util import format_spec
from spec_repair.wrappers.spec import Spec


class TestBacktrackingRepairOrchestrator(TestCase):

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
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(SpecLearner(), SpecOracle())

        # Getting all possible repairs
        new_specs_recorder: SpecRecorder = repairer.repair_spec_bfs(spec, trace)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        out_test_dir_name = "./test_files/out/lift_test_bfs"
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/lift_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: SpecRecorder = SpecRecorder()
        for spec_file in os.listdir('./test_files/lift_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/lift_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_arbiter(self):
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Arbiter/Arbiter_FINAL_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/arbiter_strong_auto_violation.txt")
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(SpecLearner(), SpecOracle())

        # Getting all possible repairs
        new_specs_recorder: SpecRecorder = repairer.repair_spec_bfs(spec, trace)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        out_test_dir_name = "./test_files/out/arbiter_test_bfs"
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/arbiter_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: SpecRecorder = SpecRecorder()
        for spec_file in os.listdir('./test_files/arbiter_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/arbiter_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_traffic_updated(self):
        spec: list[str] = format_spec(read_file_lines(
            './test_files/traffic/traffic_updated_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/traffic/traffic_updated_auto_violation.txt")
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(SpecLearner(), SpecOracle())

        # Getting all possible repairs
        new_specs_recorder: SpecRecorder = repairer.repair_spec_bfs(spec, trace)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        out_test_dir_name = "./test_files/out/traffic_test_bfs"
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: SpecRecorder = SpecRecorder()
        for spec_file in os.listdir('./test_files/traffic_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/traffic_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    # @unittest.skip("Probably takes way too long to finalise")
    def test_bfs_repair_spec_minepump(self):
        spec: list[str] = format_spec(read_file_lines(
            './test_files/minepump_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(SpecLearner(), SpecOracle())

        # Getting all possible repairs
        new_specs_recorder: SpecRecorder = repairer.repair_spec_bfs(spec, trace)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        out_test_dir_name = "./test_files/out/minepump_test_bfs"
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/minepump_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: SpecRecorder = SpecRecorder()
        for spec_file in os.listdir('./test_files/minepump_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/minepump_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)
