# NetworkX DiGraph to HTML Visualization

Convert your NetworkX DiGraph to an interactive HTML visualization with a side panel for exploring nodes and edges.

## Quick Start

### 1. Basic Usage

```python
import networkx as nx
from nx_graph_visualizer import generate_html_visualization

# Create or load your DiGraph
G = nx.DiGraph()
G.add_node("A", label="Node A", title="Description of A")
G.add_node("B", label="Node B", title="Description of B")
G.add_edge("A", "B", label="connects", title="A connects to B")

# Generate HTML visualization
generate_html_visualization(G, 'output.html', 'My Graph')

# Open output.html in your browser!
```

## Saving and Loading Graphs

### Save your graph

```python
from nx_graph_visualizer import save_graph_pickle, save_graph_json

# Pickle (preserves all Python objects, fastest)
save_graph_pickle(G, 'graph.pkl')

# JSON (human-readable, portable)
save_graph_json(G, 'graph.json')

# GraphML (XML format, compatible with other tools)
save_graph_graphml(G, 'graph.graphml')
```

### Load your graph

```python
from nx_graph_visualizer import load_graph_pickle

G = load_graph_pickle('graph.pkl')
generate_html_visualization(G, 'visualization.html')
```

## Customizing Nodes

You can customize how nodes appear by adding attributes:

```python
G.add_node("node_id",
    label="Display Name",           # Text shown on the node
    title="Detailed description",   # Shows in side panel when clicked
    color="#ff6b6b",                # Hex color code
    size=25,                         # Node size (default: 20)
    shape="dot"                      # Shape: dot, box, circle, etc.
)
```

### Available node shapes:
- `dot` (default)
- `circle`
- `box`
- `ellipse`
- `database`
- `diamond`
- `star`
- `triangle`

### Common colors:
- Red: `#ff6b6b`
- Blue: `#4ecdc4`
- Green: `#95e1d3`
- Purple: `#a29bfe`
- Orange: `#fdcb6e`
- Default: `#97c2fc`

## Customizing Edges

Add attributes to edges for labels and descriptions:

```python
G.add_edge("A", "B",
    label="edge label",             # Text shown on the edge
    title="Detailed description"    # Shows in side panel when clicked
)
```

## Complete Example

```python
import networkx as nx
from nx_graph_visualizer import generate_html_visualization

# Create a directed graph
G = nx.DiGraph()

# Add nodes with custom styling
G.add_node("input", 
    label="Input",
    title="This is the input layer",
    color="#ff6b6b",
    size=30,
    shape="box"
)

G.add_node("process",
    label="Processing",
    title="Data processing happens here",
    color="#4ecdc4",
    size=25
)

G.add_node("output",
    label="Output",
    title="Final result",
    color="#95e1d3",
    size=30,
    shape="box"
)

# Add edges
G.add_edge("input", "process", 
    label="transform",
    title="Input is transformed"
)

G.add_edge("process", "output",
    label="result",
    title="Processing produces output"
)

# Generate visualization
generate_html_visualization(G, 'my_graph.html', 'Data Flow')
```

## Features

- **Interactive**: Click nodes and edges to see details in the side panel
- **Draggable**: Move nodes around to arrange your graph
- **Physics simulation**: Nodes automatically arrange themselves
- **Zoom and pan**: Use mouse wheel to zoom, drag to pan
- **Self-contained**: Generated HTML file works offline

## Files

- `nx_graph_visualizer.py` - Main module with all functions
- `simple_usage.py` - Simple examples to get started
- `README.md` - This file

## Function Reference

### `generate_html_visualization(G, output_file, title)`
Generate interactive HTML visualization from a NetworkX DiGraph.

**Parameters:**
- `G`: NetworkX DiGraph object
- `output_file`: Path for output HTML file (default: 'graph_visualization.html')
- `title`: Title for the visualization (default: 'Network Graph')

### `save_graph_pickle(G, filename)`
Save graph using Python pickle format.

### `save_graph_json(G, filename)`
Save graph as JSON (most portable).

### `save_graph_graphml(G, filename)`
Save graph as GraphML XML.

### `load_graph_pickle(filename)`
Load graph from pickle file.

### `load_graph_json(filename)`
Load graph from JSON file.

### `load_graph_graphml(filename)`
Load graph from GraphML file.

## Tips

1. **Node IDs**: Can be strings or numbers, will be converted to strings internally
2. **Large graphs**: For graphs with 100+ nodes, you may want to disable physics after stabilization
3. **Colors**: Use hex colors (#rrggbb) for best results
4. **Titles**: Add detailed descriptions in the `title` attribute - they appear in the side panel

## Troubleshooting

**Nothing appears in the side panel:**
- Make sure you're clicking directly on nodes or edges
- Check browser console (F12) for errors

**Graph looks messy:**
- Let the physics simulation run for a few seconds
- Try adjusting node sizes and spacing
- Manually drag nodes to better positions

**Edges not showing:**
- Ensure you're using `nx.DiGraph()` not `nx.Graph()`
- Check that edge source and target nodes exist
