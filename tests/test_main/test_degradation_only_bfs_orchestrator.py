import os
import pickle
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
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import write_to_file
from spec_repair.util.mittigation_strategies import complete_counter_traces
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
            leaf_node.attr['color'] = 'red'
    target_node= A.get_node(target_node_name)
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
            SpectraGR1Oracle(),
            SpectraDiscriminator(),
            LearningTypeSpecMitigator({
                Learning.GUARANTEE_WEAKENING: complete_counter_traces
            }),
            om = OrchestrationManagerSemanticEquivalence(),
            hm = NoFilterHeuristicManager(),
            recorder = recorder,
            logger = SpecLogger(filename=log_file)
        )
        # Getting all possible repairs
        repairer.repair_bfs(spec, RepairData("", counter_traces=[], learning_type=Learning.GUARANTEE_WEAKENING))
        new_spec_strings: list[str] = [spec.to_str() for spec in recorder.get_all_values()]
        for i, new_spec in enumerate(new_spec_strings):
            write_to_file(f"{out_test_dir_name}/{case_study_name}_fix_{i}.spectra", new_spec)
        graph = repairer._om._graph
        save_layered_graph(graph, out_test_dir_name)
        return new_spec_strings