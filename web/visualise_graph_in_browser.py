from datetime import datetime

from web.nx_graph_visualizer import load_graph_pickle, generate_html_visualization


def load_and_visualize(pickle_file, output_file='visualization.html'):
    """
    Load a previously saved graph and visualize it
    """
    G = load_graph_pickle(pickle_file)
    generate_html_visualization(G, output_file)

if __name__ == '__main__':
    date = datetime.now().strftime('%Y-%m-%d')
    experiment = 'minepump'
    load_and_visualize(
        f'../tests/test_files/out/repair/{experiment}_{date}/graph.pkl',
        f'visualization_{experiment}_{date}.html'
    )