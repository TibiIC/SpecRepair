from datetime import datetime

from web.nx_graph_visualizer import load_graph_pickle, generate_html_visualization

from datetime import datetime
import networkx as nx
from web.nx_graph_visualizer import load_graph_pickle, generate_html_visualization


def load_and_visualize_smart(pickle_file, expected_root, output_file='visualization.html'):
    G = load_graph_pickle(pickle_file)

    # Auto-detect if edges are backwards
    if expected_root not in G.nodes():
        expected_root = str(expected_root)  # Try as string

    root_in = G.in_degree(expected_root)
    root_out = G.out_degree(expected_root)

    # If root has incoming but no outgoing → edges are backwards!
    if root_in > 0 and root_out == 0:
        print("🔄 Reversing backwards edges...")
        G = G.reverse(copy=True)  # FLIP ALL EDGES

    generate_html_visualization(
        G, output_file, 'BFS Tree',
        hierarchical=True,
        root_node=expected_root
    )



def load_and_visualize(pickle_file, output_file='visualization.html'):
    G = load_graph_pickle(pickle_file)

    # AUTO-DETECT the root node (node with no incoming edges)
    roots = [n for n in G.nodes() if G.in_degree(n) == 0]
    root_node = roots[0] if roots else list(G.nodes())[0]

    print(f"Root node: {repr(root_node)} (type: {type(root_node).__name__})")

    generate_html_visualization(
        G,
        output_file,
        'BFS Repair Tree',
        hierarchical=True,
        root_node=root_node  # Use the detected root
    )


if __name__ == '__main__':
    # date = datetime.now().strftime('%Y-%m-%d')
    date = '2026-06-03'
    experiment = 'arbiter'
    pickle_file = f'../tests/test_files/out_ssh/repair_syn/{experiment}_{date}/graph.pkl'
    output_file = f'visualization_syn_ssh_{experiment}_{date}.html'
    # Use it:
    load_and_visualize_smart(
        pickle_file,
        #f'../tests/test_files/out/degradation/{experiment}_{date}/graph.pkl',
        expected_root=0,
        output_file=output_file
    )