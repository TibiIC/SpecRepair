import networkx as nx
from pyvis.network import Network

from web.nx_graph_visualizer import load_graph_pickle, generate_html_visualization


def load_and_visualize(pickle_file, output_file='visualization.html'):
    """
    Load a previously saved graph and visualize it
    """
    G = load_graph_pickle(pickle_file)
    generate_html_visualization(G, output_file)

if __name__ == '__main__':
    load_and_visualize(
        '../tests/test_files/out/repair/traffic_single_2026-02-16/graph.pkl',
        'visualization_traffic_single.html'
    )