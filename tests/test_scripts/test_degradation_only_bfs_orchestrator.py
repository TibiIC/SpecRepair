import os
from datetime import datetime
from typing import Dict

from scripts.bfs_repair_orchestrator import BFSRepairOrchestrator, SpecLogger
from spec_repair.components.interfaces.ilearner import ILearner
from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.components.oracles.new_spec_oracle import NewSpecOracle
from spec_repair.components.mitigators.learning_type_spec_mitigator import LearningTypeSpecMitigator
from spec_repair.components.discriminators.spectra_discriminator import SpectraDiscriminator
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file
from spec_repair.util.mittigation_strategies import complete_counter_traces
from tests.base_test_case import BaseTestCase


class TestBFSRepairOrchestrator(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_str = datetime.now().strftime("%Y-%m-%d")

    def test_bfs_repair_spec_weird_uc(self):
        case_study_name = 'weird_uc'
        case_study_path = '../input-files/case-studies/spectra/weird_uc'
        new_spec_strings = self.run_bfs_degradation(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def run_bfs_degradation(self, case_study_name, case_study_path, out_test_dir_name=None, is_debug=False):
        if not out_test_dir_name:
            out_test_dir_name = f"./test_files/out/degradation/{case_study_name}_{self.date_str}"
        log_file = f"{out_test_dir_name}/log.txt"
        if not os.path.exists(out_test_dir_name):
            os.mkdir(out_test_dir_name)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        learners: Dict[str, ILearner] = {
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
                Learning.GUARANTEE_WEAKENING: complete_counter_traces
            }),
            NoFilterHeuristicManager(),
            recorder,
            SpecLogger(filename=log_file)
        )
        # Getting all possible repairs
        repairer.repair_bfs(spec, ("", [], Learning.GUARANTEE_WEAKENING, [], 0, 0))
        new_spec_strings: list[str] = [spec.to_str() for spec in recorder.get_all_values()]
        for i, new_spec in enumerate(new_spec_strings):
            write_to_file(f"{out_test_dir_name}/{case_study_name}_fix_{i}.spectra", new_spec)
        return new_spec_strings