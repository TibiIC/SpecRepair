import os
import pickle
import unittest
from datetime import datetime
from typing import Dict

import networkx as nx
from pyvis.network import Network

from main.bfs_repair_orchestrator import BFSRepairOrchestrator, SpecLogger
from spec_repair.components.interfaces.ilearner import ILearner
from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.components.mitigators.learning_type_spec_mitigator import LearningTypeSpecMitigator
from spec_repair.components.discriminators.spectra_discriminator import SpectraDiscriminator
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.components.orchestration_managers.orchestration_manager_semantic_equivalence import \
    OrchestrationManagerSemanticEquivalence
from spec_repair.components.orchestration_managers.orchestration_manager_syntactic_equivalence import \
    OrchestrationManagerSyntacticEquivalence
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.choose_first_heuristic_manager import ChooseFirstHeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines, write_to_file
from spec_repair.util.mittigation_strategies import move_one_to_guarantee_weakening, complete_counter_traces
from spec_repair.util.spec_util import synthesise_controller
from tests.base_test_case import BaseTestCase


def save_layered_graph(G: nx.DiGraph, filepath: str):
    # Convert NetworkX graph to Graphviz Digraph
    A = nx.nx_agraph.to_agraph(G)
    A.node_attr.update(fontsize=24)

    # Find the node with '0' in its label
    target_node_name = None
    for node_name in G.nodes():
        if node_name == 0:
            target_node_name = node_name
        if '#' in str(node_name):
            leaf_node = A.get_node(node_name)
            leaf_node.attr['color'] = 'blue'
    target_node = A.get_node(target_node_name)
    target_node.attr['penwidth'] = '5'

    # Render the Graphviz AGraph to an image file using Graphviz
    A.draw(f"{filepath}/graph.png", format='png', prog='dot')

    with open(f"{filepath}/graph.pkl", "wb") as f:
        pickle.dump(G, f)

    # Create the interactive visualization
    net = Network(height="800px", width="100%")
    net.from_nx(G)
    # Write the HTML file
    net.write_html(f"{filepath}/graph.html")


class TestBFSRepairOrchestrator(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_str = datetime.now().strftime("%Y-%m-%d")

    def test_bfs_repair_spec_arbiter(self):
        case_study_name = 'arbiter'
        case_study_path = '../input-files/case-studies/spectra/arbiter'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_bfs_repair_spec_traffic_single(self):
        case_study_name = 'traffic_single'
        case_study_path = '../input-files/case-studies/spectra/traffic_single'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_bfs_repair_spec_traffic_single_syn(self):
        case_study_name = 'traffic_single'
        case_study_path = '../input-files/case-studies/spectra/traffic_single'
        new_spec_strings = self.run_bfs_repair_syn_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_bfs_repair_spec_traffic_updated(self):
        case_study_name = 'traffic_updated'
        case_study_path = '../input-files/case-studies/spectra/traffic_updated'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path
        )

    def test_bfs_repair_spec_submarine(self):
        case_study_name = 'submarine'
        case_study_path = '../input-files/case-studies/spectra/submarine'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_bfs_repair_spec_lift_syn(self):
        case_study_name = 'lift'
        case_study_path = '../input-files/case-studies/spectra/lift'
        new_spec_strings = self.run_bfs_repair_syn_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

    def test_bfs_repair_spec_lift(self):
        case_study_name = 'lift'
        case_study_path = '../input-files/case-studies/spectra/lift'
        new_spec_strings = self.run_bfs_repair_sem_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

        expected_specs_files: list[str] = os.listdir('./test_files/lift_weakenings/2026_06_03')
        expected_specs: list[SpectraSpecification] = [
            SpectraSpecification.from_file(f"./test_files/lift_weakenings/2026_06_03/{spec_file}")
            for spec_file in expected_specs_files
        ]

        actual_specs: list[SpectraSpecification] = [
            SpectraSpecification.from_str(new_spec_string)
            for new_spec_string in new_spec_strings
        ]

        self.assertEqual(len(expected_specs), len(new_spec_strings))

        for i, expected_specs in enumerate(expected_specs):
            print(i)
            self.assertIn(expected_specs.to_str(), new_spec_strings)


    # @unittest.skip("skip test")
    def test_single_repair_spec_minepump(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/minepump'
        out_test_dir_name = "./test_files/out/minepump_single"
        new_spec_strings = self.run_single_repair(case_study_name, case_study_path, out_test_dir_name)
        print(new_spec_strings)

    @unittest.skip("skip test")
    def test_single_repair_spec_minepump_liveness(self):
        case_study_name = 'minepump_liveness'
        case_study_path = '../input-files/case-studies/spectra/minepump_liveness'
        out_test_dir_name = "./test_files/out/minepump_liveness_single"
        new_spec_strings = self.run_single_repair(case_study_name, case_study_path, out_test_dir_name)
        print(new_spec_strings)

    def test_bfs_repair_spec_minepump_syn(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/minepump'
        new_spec_strings = self.run_bfs_repair_syn_unique(
            case_study_name,
            case_study_path,
            is_debug=True
        )

        expected_specs_files: list[str] = os.listdir('./test_files/minepump_weakenings')
        expected_spec_strings: list[SpectraSpecification] = [
            SpectraSpecification.from_file(f"./test_files/minepump_weakenings/{spec_file}")
            for spec_file in expected_specs_files
        ]

        self.assertEqual(len(expected_spec_strings), len(new_spec_strings))
        for i, expected_spec in enumerate(expected_spec_strings):
            print(i)
            self.assertIn(expected_spec.to_str(), new_spec_strings)

    def test_bfs_repair_spec_minepump(self):
        case_study_name = 'minepump'
        case_study_path = '../input-files/case-studies/spectra/minepump'
        new_spec_strings = self.run_bfs_repair_sem_unique(case_study_name, case_study_path, is_debug=True)

        expected_specs_files: list[str] = os.listdir('./test_files/minepump_weakenings')
        expected_spec_strings: list[SpectraSpecification] = [
            SpectraSpecification.from_file(f"./test_files/minepump_weakenings/{spec_file}")
            for spec_file in expected_specs_files
        ]

        self.assertEqual(len(expected_spec_strings), len(new_spec_strings))
        for i, expected_spec in enumerate(expected_spec_strings):
            print(i)
            self.assertIn(expected_spec.to_str(), new_spec_strings)

    def run_bfs_repair_sem_unique(self, case_study_name, case_study_path, out_test_dir_name=None, is_debug=False):
        if not out_test_dir_name:
            out_test_dir_name = f"./test_files/out/repair/{case_study_name}_{self.date_str}"
        log_file = f"{out_test_dir_name}/log.txt"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if not os.path.exists(out_test_dir_name):
            os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        hm = NoFilterHeuristicManager()
        hm.set_enabled("INCLUDE_NEXT")
        hm.set_enabled("INCLUDE_PREV")
        learners: Dict[str, ILearner] = {
            "assumption_weakening": OptimisingSpecLearner(heuristic_manager=hm),
            "guarantee_weakening": OptimisingSpecLearner(heuristic_manager=hm)
        }
        if is_debug:
            recorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        else:
            recorder = UniqueSpecRecorder()

        # will be set after repairer is constructed
        repairer_ref = []

        def on_new_spec_found(idx, spec, data):
            if repairer_ref:
                save_layered_graph(repairer_ref[0]._om._graph, out_test_dir_name)

        repairer: BFSRepairOrchestrator = BFSRepairOrchestrator(
            learners,
            SpectraGR1Oracle(),
            SpectraDiscriminator(),
            LearningTypeSpecMitigator({
                Learning.ASSUMPTION_WEAKENING: move_one_to_guarantee_weakening,
                Learning.GUARANTEE_WEAKENING: complete_counter_traces
            }),
            om=OrchestrationManagerSemanticEquivalence(),
            hm=hm,
            recorder=recorder,
            logger=SpecLogger(filename=log_file, on_record=on_new_spec_found)
        )
        repairer_ref.append(repairer)

        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[], learning_type=Learning.ASSUMPTION_WEAKENING))
        new_spec_strings: list[str] = recorder.get_specs()
        save_layered_graph(repairer._om._graph, out_test_dir_name)
        return new_spec_strings

    def run_single_repair(self, case_study_name, case_study_path, out_test_dir_name, is_debug=False):
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        log_file = f"{out_test_dir_name}/log.txt"
        if not os.path.exists(out_test_dir_name):
            os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        hm = ChooseFirstHeuristicManager()
        # hm.set_enabled("INCLUDE_NEXT")
        learners: Dict[str, ILearner] = {
            "assumption_weakening": OptimisingSpecLearner(
                heuristic_manager=hm
            ),
            "guarantee_weakening": OptimisingSpecLearner(
                heuristic_manager=hm
            )
        }
        if is_debug:
            recorder = UniqueSpecRecorder(debug_folder=out_test_dir_name)
        else:
            recorder = UniqueSpecRecorder()
        repairer: BFSRepairOrchestrator = BFSRepairOrchestrator(
            learners,
            SpectraGR1Oracle(),
            SpectraDiscriminator(),
            LearningTypeSpecMitigator({
                Learning.ASSUMPTION_WEAKENING: move_one_to_guarantee_weakening,
                Learning.GUARANTEE_WEAKENING: complete_counter_traces
            }),
            hm,
            recorder,
            SpecLogger(filename=log_file)
        )
        # Getting all possible repairs
        repairer.repair_bfs(spec, (trace, [], Learning.ASSUMPTION_WEAKENING, [], 0, 0))
        new_spec_strings: list[str] = recorder.get_specs()
        for i, new_spec in enumerate(new_spec_strings):
            write_to_file(f"{out_test_dir_name}/{case_study_name}_fix_{i}.spectra", new_spec)
        assert len(new_spec_strings) == 1, "Expected exactly one new specification after single repair."
        synthesise_controller(
            f"{os.getcwd()}/{out_test_dir_name}/{case_study_name}_fix_0.spectra",
            f"{os.getcwd()}/{out_test_dir_name}/{case_study_name}_controller",
        )
        return new_spec_strings

    def run_bfs_repair_syn_unique(self, case_study_name, case_study_path, out_test_dir_name=None, is_debug=False):
        if not out_test_dir_name:
            out_test_dir_name = f"./test_files/out/repair_syn/{case_study_name}_{self.date_str}"
        log_file = f"{out_test_dir_name}/log.txt"
        transitions_file_path = f"{out_test_dir_name}/transitions.csv"
        if not os.path.exists(out_test_dir_name):
            os.makedirs(out_test_dir_name, exist_ok=True)
        if os.path.exists(transitions_file_path):
            os.remove(transitions_file_path)
        spec: SpectraSpecification = SpectraSpecification.from_file(f"{case_study_path}/strong.spectra")
        trace: list[str] = read_file_lines(f"{case_study_path}/violation_trace.txt")
        hm = NoFilterHeuristicManager()
        hm.set_enabled("INCLUDE_NEXT")
        hm.set_enabled("INCLUDE_PREV")
        learners: Dict[str, ILearner] = {
            "assumption_weakening": OptimisingSpecLearner(heuristic_manager=hm),
            "guarantee_weakening": OptimisingSpecLearner(heuristic_manager=hm)
        }
        if is_debug:
            recorder = UniqueSpecRecorder(sem_equivalence=False, debug_folder=out_test_dir_name)
        else:
            recorder = UniqueSpecRecorder(sem_equivalence=False)

        # will be set after repairer is constructed
        repairer_ref = []

        def on_new_spec_found(idx, spec, data):
            if repairer_ref:
                save_layered_graph(repairer_ref[0]._om._graph, out_test_dir_name)

        repairer: BFSRepairOrchestrator = BFSRepairOrchestrator(
            learners,
            SpectraGR1Oracle(),
            SpectraDiscriminator(),
            LearningTypeSpecMitigator({
                Learning.ASSUMPTION_WEAKENING: move_one_to_guarantee_weakening,
                Learning.GUARANTEE_WEAKENING: complete_counter_traces
            }),
            om=OrchestrationManagerSyntacticEquivalence(),
            hm=hm,
            recorder=recorder,
            logger=SpecLogger(filename=log_file, on_record=on_new_spec_found)
        )
        repairer_ref.append(repairer)

        repairer.repair_bfs(spec, RepairData(trace, counter_traces=[], learning_type=Learning.ASSUMPTION_WEAKENING))
        new_spec_strings: list[str] = recorder.get_specs()
        save_layered_graph(repairer._om._graph, out_test_dir_name)
        return new_spec_strings
