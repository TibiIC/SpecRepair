"""
Simple example of how to visualize your NetworkX DiGraph
"""

import networkx as nx
from nx_graph_visualizer import generate_html_visualization, save_graph_pickle, load_graph_pickle


# ============================================================================
# METHOD 1: Direct visualization from your existing graph
# ============================================================================

def visualize_my_graph():
    """
    Replace this with your actual graph creation code
    """
    # Your existing code that creates G
    G = nx.DiGraph()
    
    # Example: Add your nodes and edges here
    G.add_node(1, label="Start", title="Starting point of the process")
    G.add_node(2, label="Process", title="Processing step")
    G.add_node(3, label="End", title="Final output")
    
    G.add_edge(1, 2, label="step1", title="First transformation")
    G.add_edge(2, 3, label="step2", title="Final transformation")
    
    # Generate HTML visualization
    generate_html_visualization(G, 'my_visualization.html', 'My Graph Title')
    
    print("Done! Open my_visualization.html in your browser")


# ============================================================================
# METHOD 2: Save graph, then load and visualize later
# ============================================================================

def save_my_graph():
    """
    Save your graph for later use
    """
    # Your graph creation code
    G = nx.DiGraph()
    # ... add nodes and edges ...
    
    # Save it
    save_graph_pickle(G, 'my_saved_graph.pkl')


def load_and_visualize():
    """
    Load a previously saved graph and visualize it
    """
    G = load_graph_pickle('my_saved_graph.pkl')
    generate_html_visualization(G, 'visualization_from_saved.html')


# ============================================================================
# METHOD 3: Customize node colors and properties
# ============================================================================

def visualize_with_custom_styling():
    """
    Example with custom node colors, sizes, and shapes
    """
    G = nx.DiGraph()
    
    # Add nodes with custom styling
    G.add_node("input", 
               label="Input Layer",
               title="Data input node",
               color="#ff6b6b",  # Red
               size=30,
               shape="box")
    
    G.add_node("hidden1",
               label="Hidden 1", 
               title="First hidden layer",
               color="#4ecdc4",  # Teal
               size=25,
               shape="dot")
    
    G.add_node("hidden2",
               label="Hidden 2",
               title="Second hidden layer", 
               color="#4ecdc4",
               size=25,
               shape="dot")
    
    G.add_node("output",
               label="Output Layer",
               title="Final output",
               color="#95e1d3",  # Light green
               size=30,
               shape="box")
    
    # Add edges with labels
    G.add_edge("input", "hidden1", label="w1", title="Weight connection 1")
    G.add_edge("input", "hidden2", label="w2", title="Weight connection 2")
    G.add_edge("hidden1", "output", label="w3", title="Weight connection 3")
    G.add_edge("hidden2", "output", label="w4", title="Weight connection 4")
    
    generate_html_visualization(G, 'styled_graph.html', 'Neural Network Structure')
    print("Styled graph created! Open styled_graph.html")


# ============================================================================
# RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("Choose an example to run:")
    print("1. Basic visualization")
    print("2. Save and load graph")
    print("3. Custom styling example")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        visualize_my_graph()
    elif choice == "2":
        save_my_graph()
        load_and_visualize()
    elif choice == "3":
        visualize_with_custom_styling()
    else:
        print("Invalid choice. Running all examples...")
        visualize_my_graph()
        visualize_with_custom_styling()
