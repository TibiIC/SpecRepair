import argparse
import os
import glob
import re
from enum import Enum

import networkx as nx

from typing import Dict, Optional

from spec_repair.util.file_util import read_file
from spec_repair.wrappers.spec import Spec
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.util.graph_util import remove_reflexive_relations, merge_on_bidirectional_edges, \
    remove_transitive_relations


def extract_graph_without_transitivity_relations(graph: nx.DiGraph):
    remove_reflexive_relations(graph)
    remove_transitive_relations(graph, root_node='0')
    merge_on_bidirectional_edges(graph)
    # Renaming process may add reflexive relations back to graph
    remove_reflexive_relations(graph)

    return graph


def generate_graph(all_specs: Dict[int, Spec], graph_type: Optional[GR1FormulaType] = None):
    # Create a directed graph (graph) using networkx
    graph = nx.DiGraph()

    # Iterate through every entry in the selected column
    for this_spec_id, this_spec in all_specs.items():
        for other_spec_id, other_spec in all_specs.items():
            if this_spec.implies(other_spec, graph_type):
                graph.add_edge(str(this_spec_id), str(other_spec_id))
            if this_spec.implied_by(other_spec, graph_type):
                graph.add_edge(str(other_spec_id), str(this_spec_id))

    return extract_graph_without_transitivity_relations(graph)


def generate_tree_from_root(root_spec: Spec, all_other_specs: Dict[int, Spec], graph_type: Optional[GR1FormulaType] = None):
    # Create a directed graph (tree) using networkx
    tree = nx.DiGraph()

    # Iterate through every entry in the selected column
    for spec_id, other_spec in all_other_specs.items():
        if root_spec.implies(other_spec, graph_type):
            tree.add_edge("0", str(spec_id))
        if root_spec.implied_by(other_spec, graph_type):
            tree.add_edge(str(spec_id), "0")

    return tree

def extract_id(file_name: str) -> int:
    match = re.search(r'\d+', file_name)
    if match:
        first_number = match.group()
        return int(first_number)
    else:
        assert False, f"Could not extract id from file name {file_name}"

def visualise_implication_graph_from_specs_at_path(spec_directory_path: str, output_file: str,
                                                   graph_type: Optional[GR1FormulaType]):
    # Use the glob module to find all .spectra files in the specified directory
    spec_abs_paths = glob.glob(os.path.join(spec_directory_path, '*.spectra'))
    spec_abs_paths = [os.path.abspath(file_path) for file_path in spec_abs_paths]

    all_specs: Dict[int, Spec] = {}
    for spec_abs_path in spec_abs_paths:
        spec_id: int = extract_id(os.path.splitext(os.path.basename(spec_abs_path))[0])
        spec_txt: str = read_file(spec_abs_path)
        spec: Spec = Spec(spec_txt)
        all_specs[spec_id] = spec

    graph = generate_graph(all_specs, graph_type)

    # Convert NetworkX graph to Graphviz Digraph
    A = nx.nx_agraph.to_agraph(graph)
    A.node_attr.update(fontsize=24)

    # Find the node with '0' in its label
    target_node_name = None
    for node in graph.nodes():
        if '0' in node.split(','):
            target_node_name = node
            break
    target_node_name = A.get_node(target_node_name)
    target_node_name.attr['penwidth'] = '5'

    # Render the Graphviz AGraph to an image file using Graphviz
    A.draw(output_file, format='png', prog='dot')


def visualise_tree_from_ideal_from_specs_at_path(spec_directory_path: str, output_file: str):
    # Find ideal spec
    ideal_spec_path = f'{spec_directory_path}/0.spectra'

    # Use the glob module to find all .spectra files in the specified directory
    spec_abs_paths = glob.glob(os.path.join(spec_directory_path, '*.spectra'))
    spec_abs_paths = [os.path.abspath(file_path) for file_path in spec_abs_paths]

    # Get the absolute path to the target file
    ideal_spec_absolute_path = os.path.abspath(ideal_spec_path)
    assert (os.path.exists(ideal_spec_absolute_path))

    all_specs: Dict[int, Spec] = {}
    for spec_abs_path in spec_abs_paths:
        spec_id: int = int(os.path.splitext(os.path.basename(spec_abs_path))[0])
        spec_txt: str = read_file(spec_abs_path)
        spec: Spec = Spec(spec_txt)
        all_specs[spec_id] = spec

    del all_specs[0]
    ideal_spec_txt: str = read_file(ideal_spec_absolute_path)
    ideal_spec: Spec = Spec(ideal_spec_txt)

    graph = generate_tree_from_root(ideal_spec, all_specs)
    graph = extract_graph_without_transitivity_relations(graph)

    # Convert NetworkX graph to Graphviz Digraph
    A = nx.nx_agraph.to_agraph(graph)
    A.node_attr.update(fontsize=24)

    # Find the node with '0' in its label
    target_node_name = None
    for node in graph.nodes():
        if '0' in node.split(','):
            target_node_name = node
            break
    target_node_name = A.get_node(target_node_name)
    target_node_name.attr['penwidth'] = '5'

    # Render the Graphviz AGraph to an image file using Graphviz
    A.draw(output_file, format='png', prog='dot')


description = """
TODO: fill up a description for this specification visualiser
"""


class CompareType(Enum):
    ASM = "asm"
    GAR = "gar"
    GR1 = "gr1"

    def __str__(self) -> str:
        return f"{self.value}"

    def to_GR1ExpType(self) -> Optional[GR1FormulaType]:
        match self:
            case CompareType.ASM:
                return GR1FormulaType.ASM
            case CompareType.GAR:
                return GR1FormulaType.GAR
            case CompareType.GR1:
                return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--spec_dir', type=str,
                        required=True,
                        help='Path to the directory with specifications to be compared. All files should be named [0-9]+.spectra')
    parser.add_argument('-o', '--output', type=str,
                        required=False,
                        default="visualisations/new_viz.png",
                        help='Path to the expected output .png file. This is where the tree will be generated.')
    parser.add_argument('-t', '--graph_type', type=CompareType,
                        required=False,
                        default=CompareType.GR1,
                        choices=list(CompareType),
                        help='Type of comparison to be provided [ASM/GAR/GR(1)]. Leave empty for GR(1)')
    args = parser.parse_args()

    current_directory = os.getcwd()
    spec_directory_path = os.path.join(current_directory, args.spec_dir)
    output_file_path = os.path.join(current_directory, args.output)
    graph_type: Optional[GR1FormulaType] = args.graph_type.to_GR1ExpType()
    visualise_implication_graph_from_specs_at_path(spec_directory_path, output_file_path, graph_type)
    # visualise_tree_from_ideal_from_specs_at_path(spec_directory_path, output_file, graph_type)
