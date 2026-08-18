import argparse
import os
import glob
import re
import sys
from enum import Enum

import networkx as nx

from typing import Dict, List, Optional, Tuple

from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file
from spec_repair.ltl_types import GR1FormulaType
from spec_repair.util.graph_util import remove_reflexive_relations, merge_on_bidirectional_edges, \
    remove_all_transitive_relations, remove_transitive_relations


def extract_graph_without_transitivity_relations(graph: nx.DiGraph, root_node: Optional[str] = '0'):
    """
    :param root_node: node to start the transitive reduction from. Defaults to
        '0' to preserve the legacy numbered-file behaviour; pass None to reduce
        the whole graph, which is what named/grouped nodes need since there is
        no node called '0' and the graph may have several components.
    """
    remove_reflexive_relations(graph)
    if root_node is None:
        remove_all_transitive_relations(graph)
    else:
        remove_transitive_relations(graph, root_node=root_node)
    merge_on_bidirectional_edges(graph)
    # Renaming process may add reflexive relations back to graph
    remove_reflexive_relations(graph)

    return graph


def generate_graph(all_specs: Dict[int, SpectraSpecification], graph_type: Optional[GR1FormulaType] = None,
                   root_node: Optional[str] = '0'):
    # Create a directed graph (graph) using networkx
    graph = nx.DiGraph()

    # Iterate through every entry in the selected column
    for this_spec_id, this_spec in all_specs.items():
        for other_spec_id, other_spec in all_specs.items():
            if this_spec.implies(other_spec, graph_type):
                graph.add_edge(str(this_spec_id), str(other_spec_id))
            if this_spec.implied_by(other_spec, graph_type):
                graph.add_edge(str(other_spec_id), str(this_spec_id))

    return extract_graph_without_transitivity_relations(graph, root_node=root_node)


def generate_tree_from_root(root_spec: SpectraSpecification, all_other_specs: Dict[int, SpectraSpecification], graph_type: Optional[GR1FormulaType] = None):
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

    all_specs: Dict[int, SpectraSpecification] = {}
    for spec_abs_path in spec_abs_paths:
        spec_id: int = extract_id(os.path.splitext(os.path.basename(spec_abs_path))[0])
        spec_txt: str = read_file(spec_abs_path)
        spec: SpectraSpecification = SpectraSpecification(spec_txt)
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

    all_specs: Dict[int, SpectraSpecification] = {}
    for spec_abs_path in spec_abs_paths:
        spec_id: int = int(os.path.splitext(os.path.basename(spec_abs_path))[0])
        spec: SpectraSpecification = SpectraSpecification.from_file(spec_abs_path)
        all_specs[spec_id] = spec

    del all_specs[0]
    ideal_spec: SpectraSpecification = SpectraSpecification.from_file(ideal_spec_absolute_path)

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


"""
Colour-coding groups of specifications
--------------------------------------

`--group LABEL=PATH` adds every specification at PATH (a .spectra file, or a
directory of them) to the graph under LABEL, and gives that group its own
colour. Cataloguing by folder is what makes this work: each pipeline stage
already writes its output to its own directory, so the directory *is* the type.

Nodes are named `LABEL` for a single-file group and `LABEL_0`, `LABEL_1`, ... for
a directory, so where a node came from is readable straight off the graph.

Equivalent specifications get merged into one node by
merge_on_bidirectional_edges. Such a node is drawn as a rounded "bubble"
containing one coloured box per specification inside it, each keeping its own
group colour - so an equivalence spanning several types stays readable as
exactly that, rather than being flattened into a single colour that belongs to
none of them.
"""

# Light fills chosen to stay readable behind black label text. Known stage names
# get a stable colour so graphs from different runs look the same; anything else
# cycles through EXTRA_COLOURS.
GROUP_COLOURS: Dict[str, str] = {
    "strong": "#ffd6a5",
    "ideal": "#caffbf",
    # The trace_violation setup's reference specification, playing the role
    # strong.spectra plays in the strengthened one - hence the same colour.
    "original": "#ffd6a5",
    "trivial": "#ffadad",
    "merged": "#bdb2ff",
    "max_merged": "#9bf6ff",
    "filtered_merged": "#a0c4ff",
}
EXTRA_COLOURS = ["#fdffb6", "#ffc6ff", "#d0d1ff", "#b5e48c", "#f6bd60"]
DEFAULT_COLOUR = "#ffffff"


def _escape(text: str) -> str:
    """Escape text for a Graphviz HTML-like label."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


"""
The legend
----------

`--legend` chooses how the group colours are explained:

  compact (default) - a small swatch table pinned to the bottom-right corner,
                      drawn as the *graph's* label rather than as a node
  full              - the old legend cluster, laid out as part of the graph
  none              - no legend at all

The cluster version was laid out by `dot` alongside the graph, so it competed
with the real nodes for space: its boxes use the same 18-24pt fonts, and the
bubble example is a whole nested table, which on a small graph came out as wide
as everything it was explaining. The compact version is a graph label with
`labelloc=b`/`labeljust=r`, so it is placed after layout, in the corner, and
takes only the strip of canvas it actually occupies. At 8pt with 6px swatches it
is roughly a tenth of the area the cluster used.
"""

LEGEND_STYLES = ("compact", "full", "none")

# Point size for the compact legend. The graph's own nodes are 24pt; keeping the
# legend this much smaller is the entire point of it.
LEGEND_FONT_SIZE = 8
LEGEND_SWATCH_PX = 6


def compact_legend_label(colour_of: Dict[str, str], has_bubbles: bool) -> str:
    """
    A small swatch-per-group table, for use as the graph's own label.

    One row per group: a filled square and the group name. Equivalence bubbles
    get a single line of text rather than a nested table example - the shape is
    self-evident once named, and reproducing it here is what made the old legend
    take so much room.
    """
    rows = [
        f'<TR><TD COLSPAN="2" BORDER="0" ALIGN="LEFT">'
        f'<FONT POINT-SIZE="{LEGEND_FONT_SIZE}"><B>Specification type</B></FONT></TD></TR>'
    ]
    for label, colour in colour_of.items():
        rows.append(
            f'<TR>'
            f'<TD BGCOLOR="{colour}" WIDTH="{LEGEND_SWATCH_PX}" HEIGHT="{LEGEND_SWATCH_PX}" '
            f'FIXEDSIZE="TRUE"></TD>'
            f'<TD BORDER="0" ALIGN="LEFT">'
            f'<FONT POINT-SIZE="{LEGEND_FONT_SIZE}">{_escape(label)}</FONT></TD>'
            f'</TR>'
        )
    if has_bubbles:
        rows.append(
            f'<TR><TD COLSPAN="2" BORDER="0" ALIGN="LEFT">'
            f'<FONT POINT-SIZE="{LEGEND_FONT_SIZE}">'
            f'rounded box = equivalent specifications</FONT></TD></TR>'
        )
    return (f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="1" CELLPADDING="1" '
            f'COLOR="#888888">{"".join(rows)}</TABLE>>')


def bubble_label(members: List[Tuple[str, str]], caption: Optional[str] = None) -> str:
    """
    Build a Graphviz HTML-like label: a rounded "bubble" holding one coloured
    cell per member, so an equivalence spanning several groups keeps every
    group's colour instead of being flattened into one.

    `members` is [(display_name, fill_colour), ...]. The result is wrapped in
    angle brackets, which is how pygraphviz tells an HTML-like label apart from
    an ordinary quoted string.
    """
    cells = "".join(
        f'<TD BGCOLOR="{colour}">{_escape(name)}</TD>' for name, colour in members
    )
    rows = f"<TR>{cells}</TR>"
    if caption:
        rows += (f'<TR><TD COLSPAN="{max(1, len(members))}" BORDER="0">'
                 f'{_escape(caption)}</TD></TR>')
    return (f'<<TABLE BORDER="2" CELLBORDER="1" CELLSPACING="6" CELLPADDING="6" '
            f'STYLE="ROUNDED" COLOR="#555555">{rows}</TABLE>>')


def parse_group_argument(raw: str) -> Tuple[str, str]:
    """Parse a `LABEL=PATH` group argument."""
    if "=" not in raw:
        raise argparse.ArgumentTypeError(
            f"--group expects LABEL=PATH, got '{raw}'")
    label, path = raw.split("=", 1)
    label, path = label.strip(), path.strip()
    if not label or not path:
        raise argparse.ArgumentTypeError(
            f"--group expects a non-empty LABEL and PATH, got '{raw}'")
    return label, path


def load_group_specs(label: str, path: str) -> Dict[str, SpectraSpecification]:
    """
    Load a group's specifications, keyed by node name. Missing paths are skipped
    with a warning rather than aborting: a pipeline run legitimately has nothing
    to show for a stage that produced no specs, and losing the whole graph over
    that is worse than an incomplete one.
    """
    if not os.path.exists(path):
        print(f"WARNING: skipping group '{label}' - no such path: {path}")
        return {}
    if os.path.isfile(path):
        return {label: SpectraSpecification.from_file(path)}

    spec_files = sorted(f for f in os.listdir(path) if f.endswith(".spectra"))
    if not spec_files:
        print(f"WARNING: skipping group '{label}' - no .spectra files in {path}")
        return {}
    return {
        f"{label}_{i}": SpectraSpecification.from_file(os.path.join(path, f))
        for i, f in enumerate(spec_files)
    }


def _members_of_node(
        node_name: str,
        node_to_label: Dict[str, str],
        colour_of: Dict[str, str],
        group_order: Dict[str, int],
) -> List[Tuple[str, str]]:
    """
    The specifications a (possibly merged, comma-joined) node holds, as
    [(node_name, colour), ...] ordered by the order the groups were given on the
    command line so bubbles read consistently across graphs.
    """
    parts = [p.strip() for p in node_name.split(",") if p.strip()]
    parts.sort(key=lambda p: (group_order.get(node_to_label.get(p, ""), len(group_order)), p))
    return [(p, colour_of.get(node_to_label.get(p, ""), DEFAULT_COLOUR)) for p in parts]


def visualise_grouped_implication_graph(
        groups: List[Tuple[str, str]],
        output_file: str,
        graph_type: Optional[GR1FormulaType] = None,
        legend: str = "compact",
) -> None:
    all_specs: Dict[str, SpectraSpecification] = {}
    node_to_label: Dict[str, str] = {}
    colour_of: Dict[str, str] = {}
    group_order: Dict[str, int] = {}
    extra = iter(EXTRA_COLOURS)

    for label, path in groups:
        loaded = load_group_specs(label, path)
        for node_name, spec in loaded.items():
            if node_name in all_specs:
                raise ValueError(f"Duplicate node name '{node_name}'; use distinct group labels.")
            all_specs[node_name] = spec
            node_to_label[node_name] = label
        if loaded and label not in colour_of:
            colour_of[label] = GROUP_COLOURS.get(label) or next(extra, DEFAULT_COLOUR)
            group_order[label] = len(group_order)

    if not all_specs:
        raise ValueError("No specifications found in any group; nothing to draw.")
    print(f"Building implication graph over {len(all_specs)} specification(s) "
          f"in {len(colour_of)} group(s): {', '.join(colour_of)}")

    graph = generate_graph(all_specs, graph_type, root_node=None)

    A = nx.nx_agraph.to_agraph(graph)
    A.node_attr.update(fontsize=24, style="filled", shape="box")

    bubbles = 0
    for node in graph.nodes():
        members = _members_of_node(str(node), node_to_label, colour_of, group_order)
        agraph_node = A.get_node(node)
        if len(members) > 1:
            # Equivalent specifications: one bubble, one coloured box per
            # specification inside it, each keeping its own group's colour.
            agraph_node.attr["shape"] = "none"
            agraph_node.attr["style"] = ""
            agraph_node.attr["label"] = bubble_label(members)
            bubbles += 1
        elif members:
            agraph_node.attr["fillcolor"] = members[0][1]

    if legend == "compact":
        # Drawn as the graph's own label, so `dot` places it after layout in the
        # bottom-right corner instead of reserving space for it among the nodes.
        A.graph_attr["label"] = compact_legend_label(colour_of, bool(bubbles))
        A.graph_attr["labelloc"] = "b"
        A.graph_attr["labeljust"] = "r"
        A.graph_attr["fontsize"] = str(LEGEND_FONT_SIZE)
    elif legend == "full":
        # Legend as its own cluster so it lays out beside the graph, not inside it.
        legend_cluster = A.add_subgraph(name="cluster_legend", label="Specification type", fontsize=20)
        for label, colour in colour_of.items():
            legend_node = f"legend_{label}"
            legend_cluster.add_node(legend_node, label=label, fillcolor=colour,
                                    style="filled", shape="box", fontsize=18)
        if bubbles:
            # Only explain bubbles when the graph actually contains one.
            sample = list(colour_of.items())[:2]
            while len(sample) < 2:
                sample.append(("", DEFAULT_COLOUR))
            legend_cluster.add_node(
                "legend_bubble",
                label=bubble_label([(name or " ", colour) for name, colour in sample],
                                   caption="equivalent specifications"),
                shape="none", style="", fontsize=18)

    os.makedirs(os.path.dirname(os.path.abspath(output_file)) or ".", exist_ok=True)
    A.draw(output_file, format="png", prog="dot")
    print(f"Written graph to: {output_file}")


description = """
Draw the implication graph over one or more groups of Spectra specifications,
colour-coded by group. Give each group as LABEL=PATH, where PATH is a .spectra
file or a directory of them:

  python scripts/visualise_resulting_specs.py -o graph.png \\
      --group strong=input-files/case-studies/spectra/case_study_1/lift/strong.spectra \\
      --group ideal=input-files/case-studies/spectra/case_study_1/lift/ideal.spectra \\
      --group trivial=tests/test_files/out/trivial_solutions/2026-07-27/lift \\
      --group filtered_merged=.../filtered_merged_specs

The legacy single-directory mode (-s/--spec_dir) still works and is unchanged.
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('-s', '--spec_dir', type=str,
                      help='Legacy mode: one directory of specifications, all named [0-9]+.spectra')
    mode.add_argument('-g', '--group', type=parse_group_argument, action='append', dest='groups',
                      metavar='LABEL=PATH',
                      help='A colour-coded group of specifications; repeat for each type')
    parser.add_argument('-o', '--output', type=str,
                        required=False,
                        default="visualisations/new_viz.png",
                        help='Path to the expected output .png file. This is where the tree will be generated.')
    parser.add_argument('-t', '--graph_type', type=CompareType,
                        required=False,
                        default=CompareType.GR1,
                        choices=list(CompareType),
                        help='Type of comparison to be provided [ASM/GAR/GR(1)]. Leave empty for GR(1)')
    parser.add_argument('--legend', choices=list(LEGEND_STYLES), default="compact",
                        help='Legend style for grouped mode: compact (small, bottom-right corner; '
                             'default), full (the larger legend cluster), or none')
    args = parser.parse_args(argv)

    graph_type: Optional[GR1FormulaType] = args.graph_type.to_GR1ExpType()
    output_file_path = os.path.abspath(args.output)

    if args.groups:
        visualise_grouped_implication_graph(args.groups, output_file_path, graph_type,
                                            legend=args.legend)
    else:
        spec_directory_path = os.path.abspath(args.spec_dir)
        visualise_implication_graph_from_specs_at_path(spec_directory_path, output_file_path, graph_type)
    return 0


if __name__ == '__main__':
    sys.exit(main())
