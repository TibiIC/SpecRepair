import os
from typing import List
from unittest import TestCase

from scripts.backtracking_repair_orchestrator import BacktrackingRepairOrchestrator
from spec_repair.helpers.heuristic_managers.no_eventually_hypothesis_heuristic_manager import \
    NoEventuallyHypothesisHeuristicManager
from spec_repair.helpers.recorders.non_unique_spec_recorder import NonUniqueSpecRecorder
from spec_repair.helpers.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.helpers.logger import RepairLogger
from spec_repair.util.file_util import read_file_lines, write_to_file
from spec_repair.util.spec_util import format_spec
from spec_repair.wrappers.spec import Spec


class TestBacktrackingRepairOrchestrator(TestCase):
    maxDiff = None

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

    # To run this on the command line, use the following command:
    # python -m unittest tests.test_scripts.test_backtracking_repair_orchestrator.TestBacktrackingRepairOrchestrator.test_bfs_repair_spec_lift
    def test_bfs_repair_spec_lift(self):
        out_test_dir_name = "./test_files/out/lift_test_bfs"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
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

    # @unittest.skip("Probably takes way too long to finalise")
    def test_bfs_repair_spec_arbiter(self):
        out_test_dir_name = "./test_files/out/arbiter_test_bfs"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Arbiter/Arbiter_FINAL_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/arbiter_strong_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/arbiter_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/arbiter_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/arbiter_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_traffic_updated(self):
        out_test_dir_name = "./test_files/out/traffic_test_bfs"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: list[str] = format_spec(read_file_lines(
            './test_files/traffic/traffic_updated_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/traffic/traffic_updated_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/traffic_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/traffic_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_minepump(self):
        out_test_dir_name = "./test_files/out/minepump_test_bfs"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: List[str] = format_spec(read_file_lines(
            './test_files/minepump_strong.spectra'))
        trace: List[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/minepump_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/minepump_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/minepump_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_minepump_no_eventually(self):
        out_test_dir_name = "./test_files/out/minepump_test_bfs_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: List[str] = format_spec(read_file_lines(
            './test_files/minepump_strong.spectra'))
        trace: List[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/minepump_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/minepump_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/minepump_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_traffic_updated_no_eventually(self):
        out_test_dir_name = "./test_files/out/traffic_test_bfs_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: list[str] = format_spec(read_file_lines(
            './test_files/traffic/traffic_updated_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/traffic/traffic_updated_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/traffic_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/traffic_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_arbiter_no_eventually(self):
        out_test_dir_name = "./test_files/out/arbiter_test_bfs_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Arbiter/Arbiter_FINAL_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/arbiter_strong_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/arbiter_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/arbiter_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/arbiter_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_minepump_non_unique_no_eventually(self):
        out_test_dir_name = "./test_files/out/minepump_test_bfs_non_unique_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: List[str] = format_spec(read_file_lines(
            './test_files/minepump_strong.spectra'))
        trace: List[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/minepump_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/minepump_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/minepump_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_minepump_non_unique(self):
        out_test_dir_name = "./test_files/out/minepump_test_bfs_non_unique"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: List[str] = format_spec(read_file_lines(
            './test_files/minepump_strong.spectra'))
        trace: List[str] = read_file_lines(
            "./test_files/minepump_strong_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/minepump_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/minepump_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/minepump_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_arbiter_non_unique(self):
        # Run this from the terminal using the following command
        # python -m unittest tests.test_scripts.test_backtracking_repair_orchestrator.TestBacktrackingRepairOrchestrator.test_bfs_repair_spec_arbiter_non_unique
        out_test_dir_name = "./test_files/out/arbiter_test_bfs_non_unique"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Arbiter/Arbiter_FINAL_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/arbiter_strong_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = NonUniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/arbiter_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/arbiter_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/arbiter_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_arbiter_non_unique_no_eventually(self):
        # Run this from the terminal using the following command
        # python -m unittest tests.test_scripts.test_backtracking_repair_orchestrator.TestBacktrackingRepairOrchestrator.test_bfs_repair_spec_arbiter_non_unique_no_eventually
        out_test_dir_name = "./test_files/out/arbiter_test_bfs_non_unique_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/Arbiter/Arbiter_FINAL_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/arbiter_strong_auto_violation.txt")
        new_specs_recorder: UniqueSpecRecorder = NonUniqueSpecRecorder(debug_folder=out_test_dir_name)
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/arbiter_test_fix_{i}.spectra", new_spec)

        # Getting expected repairs
        expected_specs_recorder: UniqueSpecRecorder = UniqueSpecRecorder()
        for spec_file in os.listdir('./test_files/arbiter_weakenings'):
            expected_specs_recorder.add(
                Spec(''.join(format_spec(read_file_lines(f'./test_files/arbiter_weakenings/{spec_file}')))))
        expected_specs: list = expected_specs_recorder.get_specs()
        expected_specs.sort()

        self.assertEqual(expected_specs, new_specs)

    def test_bfs_repair_spec_traffic_updated_non_unique_no_eventually(self):
        out_test_dir_name = "./test_files/out/traffic_non_unique_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            './test_files/traffic/traffic_updated_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/traffic/traffic_updated_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()


    def test_bfs_repair_spec_traffic_updated_non_unique_eventually(self):
        out_test_dir_name = "./test_files/out/traffic_non_unique_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            './test_files/traffic/traffic_updated_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/traffic/traffic_updated_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()

    def test_bfs_repair_spec_traffic_single_non_unique_no_eventually(self):
        out_test_dir_name = "./test_files/out/traffic_single_non_unique_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            './test_files/traffic/traffic_single_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/traffic/traffic_single_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()


    def test_bfs_repair_spec_traffic_single_non_unique_eventually(self):
        out_test_dir_name = "./test_files/out/traffic_single_non_unique_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            './test_files/traffic/traffic_single_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/traffic/traffic_single_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()

    def test_bfs_repair_spec_lift_non_unique_no_eventually(self):
        out_test_dir_name = "./test_files/out/lift_non_unique_no_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()


    def test_bfs_repair_spec_lift_non_unique_eventually(self):
        out_test_dir_name = "./test_files/out/lift_non_unique_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/lift_FINAL_NEW_strong.spectra'))
        trace: list[str] = read_file_lines(
            "./test_files/lift_strong_auto_violation.txt")
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()

    def test_bfs_repair_spec_genbuf_non_unique_no_eventually(self):
        out_test_dir_name = "./test_files/out/genbuf_non_unique_no_eventually_2"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/case-studies/spectra/genbuf/strong.spectra'))
        trace: list[str] = read_file_lines(
            './test_files/genbuf_auto_violation.txt')
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoEventuallyHypothesisHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()


    def test_bfs_repair_spec_genbuf_non_unique_eventually(self):
        out_test_dir_name = "./test_files/out/genbuf_non_unique_eventually"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        else:
            os.makedirs(out_test_dir_name)
        spec: list[str] = format_spec(read_file_lines(
            '../input-files/examples/genbuf_05_normalised_dropped.spectra'))
        trace: list[str] = read_file_lines(
            './test_files/genbuf_auto_violation.txt')
        new_specs_recorder: NonUniqueSpecRecorder = NonUniqueSpecRecorder()
        repairer: BacktrackingRepairOrchestrator = BacktrackingRepairOrchestrator(
            SpecLearner(),
            SpecOracle(),
            NoFilterHeuristicManager(),
            RepairLogger(transitions_file_path, debug=True)
        )

        # Getting all possible repairs
        repairer.repair_spec_bfs(spec, trace, new_specs_recorder)
        new_specs: list[str] = new_specs_recorder.get_specs()
        new_specs.sort()
        for i, new_spec in enumerate(new_specs):
            write_to_file(f"{out_test_dir_name}/traffic_test_fix_{i}.spectra", new_spec)

        self.fail()
