import os
from typing import Dict
from unittest import TestCase

from scripts.bfs_repair_orchestrator import BFSRepairOrchestrator, SpecLogger
from spec_repair.components.arca_learner import ARCALearner
from spec_repair.components.interfaces.ilearner import ILearner
from spec_repair.components.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.components.new_spec_oracle import NewSpecOracle
from spec_repair.components.learning_type_spec_mitigator import LearningTypeSpecMitigator
from spec_repair.components.spectra_discriminator import SpectraDiscriminator
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.choose_first_heuristic_manager import ChooseFirstHeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.helpers.spectra_boolean_specification import SpectraBooleanSpecification
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines, write_to_file
from spec_repair.util.mittigation_strategies import move_one_to_guarantee_weakening, complete_counter_traces, \
    move_all_to_guarantee_weakening
from spec_repair.util.spec_util import synthesise_controller


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

    def test_bfs_repair_spec_arbiter(self):
        case_study_name = 'arbiter'
        case_study_path = '../input-files/case-studies/spectra/arbiter'
        out_test_dir_name = "./test_files/out/new_arbiter_test_bfs"
        new_spec_strings = self.run_bfs_repair(
            case_study_name,
            case_study_path,
            out_test_dir_name,
            is_debug=True
        )

    def test_bfs_repair_spec_traffic_single(self):
        case_study_name = 'traffic_single'
        case_study_path = '../input-files/case-studies/spectra/traffic-single'
        out_test_dir_name = "./test_files/out/traffic_single_2025_08_08"
        new_spec_strings = self.run_bfs_repair(
            case_study_name,
            case_study_path,
            out_test_dir_name,
            is_debug=True
        )

    def test_bfs_repair_spec_traffic_updated(self):
        case_study_name = 'traffic_updated'
        case_study_path = '../input-files/case-studies/spectra/traffic-updated'
        out_test_dir_name = "./test_files/out/new_traffic_updated_test_bfs"
        new_spec_strings = self.run_bfs_repair(
            case_study_name,
            case_study_path,
            out_test_dir_name
        )

    def test_bfs_repair_spec_lift(self):
        case_study_name = 'lift'
        case_study_path = '../input-files/case-studies/spectra/lift'
        out_test_dir_name = "./test_files/out/lift_all_bfs"
        new_spec_strings = self.run_bfs_repair(case_study_name, case_study_path, out_test_dir_name)

        expected_specs_files: list[str] = os.listdir('./test_files/lift_weakenings')
        expected_spec_strings: list[SpectraBooleanSpecification] = [
            SpectraBooleanSpecification.from_file(f"./test_files/lift_weakenings/{spec_file}")
            for spec_file in expected_specs_files
        ]

        for new_spec_str in new_spec_strings:
            print(new_spec_str)
        self.assertEqual(len(expected_spec_strings), len(new_spec_strings))
        for i, expected_spec in enumerate(expected_spec_strings):
            print(i)
            self.assertIn(expected_spec.to_str(), new_spec_strings)

    def test_single_repair_spec_minepump(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/minepump_enum'
        out_test_dir_name = "./test_files/out/minepump_enum_single"
        new_spec_strings = self.run_single_repair(case_study_name, case_study_path, out_test_dir_name)
        print(new_spec_strings)

    def test_bfs_repair_spec_minepump(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/minepump'
        out_test_dir_name = "./test_files/out/minepump_arca_bfs"
        new_spec_strings = self.run_bfs_repair(case_study_name, case_study_path, out_test_dir_name)

        expected_specs_files: list[str] = os.listdir('./test_files/minepump_weakenings')
        expected_spec_strings: list[SpectraBooleanSpecification] = [
            SpectraBooleanSpecification.from_file(f"./test_files/minepump_weakenings/{spec_file}")
            for spec_file in expected_specs_files
        ]

        self.assertEqual(len(expected_spec_strings), len(new_spec_strings))
        for i, expected_spec in enumerate(expected_spec_strings):
            print(i)
            self.assertIn(expected_spec.to_str(), new_spec_strings)

    def run_bfs_repair(self, case_study_name, case_study_path, out_test_dir_name, is_debug=False):
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        log_file = f"{out_test_dir_name}/log.txt"
        if not os.path.exists(out_test_dir_name):
            os.mkdir(out_test_dir_name)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraBooleanSpecification = SpectraBooleanSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        learners: Dict[str, ILearner] = {
            "assumption_weakening": OptimisingSpecLearner(
                heuristic_manager=NoFilterHeuristicManager()
            ),
            "guarantee_weakening": OptimisingSpecLearner(
                heuristic_manager=NoFilterHeuristicManager()
            )
        }
        if is_debug:
            recorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        else:
            recorder = UniqueSpecRecorder()
        repairer: BFSRepairOrchestrator = BFSRepairOrchestrator(
            learners,
            NewSpecOracle(),
            SpectraDiscriminator(),
            LearningTypeSpecMitigator({
                Learning.ASSUMPTION_WEAKENING: move_one_to_guarantee_weakening,
                Learning.GUARANTEE_WEAKENING: complete_counter_traces
            }),
            NoFilterHeuristicManager(),
            recorder,
            SpecLogger(filename=log_file)
        )
        # Getting all possible repairs
        repairer.repair_bfs(spec, (trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0))
        new_spec_strings: list[str] = [spec.to_str() for spec in recorder.get_all_values()]
        for i, new_spec in enumerate(new_spec_strings):
            write_to_file(f"{out_test_dir_name}/{case_study_name}_fix_{i}.spectra", new_spec)
        return new_spec_strings

    def run_single_repair(self, case_study_name, case_study_path, out_test_dir_name, is_debug=False):
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        log_file = f"{out_test_dir_name}/log.txt"
        if not os.path.exists(out_test_dir_name):
            os.mkdir(out_test_dir_name)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        learners: Dict[str, ILearner] = {
            "assumption_weakening": ARCALearner(
                heuristic_manager=ChooseFirstHeuristicManager()
            ),
            "guarantee_weakening": OptimisingSpecLearner(
                heuristic_manager=ChooseFirstHeuristicManager()
            )
        }
        if is_debug:
            recorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        else:
            recorder = UniqueSpecRecorder()
        repairer: BFSRepairOrchestrator = BFSRepairOrchestrator(
            learners,
            NewSpecOracle(),
            SpectraDiscriminator(),
            LearningTypeSpecMitigator({
                Learning.ASSUMPTION_WEAKENING: move_one_to_guarantee_weakening,
                Learning.GUARANTEE_WEAKENING: complete_counter_traces
            }),
            ChooseFirstHeuristicManager(),
            recorder,
            SpecLogger(filename=log_file)
        )
        # Getting all possible repairs
        repairer.repair_bfs(spec, (trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0))
        new_spec_strings: list[str] = [spec.to_str() for spec in recorder.get_all_values()]
        for i, new_spec in enumerate(new_spec_strings):
            write_to_file(f"{out_test_dir_name}/{case_study_name}_fix_{i}.spectra", new_spec)
        assert len(new_spec_strings) == 1, "Expected exactly one new specification after single repair."
        synthesise_controller(
            f"{os.getcwd()}/{out_test_dir_name}/{case_study_name}_fix_0.spectra",
            f"{os.getcwd()}/{out_test_dir_name}/{case_study_name}_controller",
        )
        return new_spec_strings
