"""
NetworkX DiGraph to HTML Visualization
This script saves a NetworkX DiGraph and generates an interactive HTML visualization
"""

import networkx as nx
import json
import pickle

# ============================================================================
# PART 1: Save NetworkX DiGraph
# ============================================================================

def save_graph_pickle(G, filename='graph.pkl'):
    """
    Save NetworkX graph using pickle (preserves all Python objects)
    
    Args:
        G: NetworkX DiGraph
        filename: Output pickle file path
    """
    with open(filename, 'wb') as f:
        pickle.dump(G, f)
    print(f"Graph saved to {filename} using pickle")


def save_graph_graphml(G, filename='graph.graphml'):
    """
    Save NetworkX graph as GraphML (human-readable XML format)
    
    Args:
        G: NetworkX DiGraph
        filename: Output GraphML file path
    """
    nx.write_graphml(G, filename)
    print(f"Graph saved to {filename} using GraphML")


def save_graph_json(G, filename='graph.json'):
    """
    Save NetworkX graph as JSON (most portable)
    
    Args:
        G: NetworkX DiGraph
        filename: Output JSON file path
    """
    from networkx.readwrite import json_graph
    
    data = json_graph.node_link_data(G)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Graph saved to {filename} using JSON")


# ============================================================================
# PART 2: Load NetworkX DiGraph
# ============================================================================

def load_graph_pickle(filename='graph.pkl'):
    """Load graph from pickle file"""
    with open(filename, 'rb') as f:
        G = pickle.load(f)
    print(f"Graph loaded from {filename}")
    return G


def load_graph_graphml(filename='graph.graphml'):
    """Load graph from GraphML file"""
    G = nx.read_graphml(filename)
    print(f"Graph loaded from {filename}")
    return G


def load_graph_json(filename='graph.json'):
    """Load graph from JSON file"""
    from networkx.readwrite import json_graph
    
    with open(filename, 'r') as f:
        data = json.load(f)
    G = json_graph.node_link_graph(data)
    print(f"Graph loaded from {filename}")
    return G


# ============================================================================
# PART 3: Convert NetworkX DiGraph to HTML Visualization Data
# ============================================================================

def convert_graph_to_vis_data(G):
    """
    Convert NetworkX DiGraph to vis.js format
    
    Args:
        G: NetworkX DiGraph
        
    Returns:
        dict with 'nodes' and 'edges' lists ready for vis.js
    """
    nodes = []
    edges = []
    
    # Convert nodes
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        
        # Build title from either 'title' attribute or all custom attributes
        if 'title' in node_data:
            title = str(node_data['title']).replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        else:
            # Collect all custom attributes
            custom_attrs = []
            for key, value in node_data.items():
                if key not in ['label', 'color', 'shape', 'size']:
                    # Convert newlines to HTML breaks and tabs to spaces
                    value_str = str(value).replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                    custom_attrs.append(f"{key}: {value_str}")
            
            if custom_attrs:
                # Add double line breaks for better spacing
                title = "<br><br>".join(custom_attrs)
            else:
                title = f'Node: {node_id}'
        
        node_obj = {
            'id': str(node_id),
            'label': node_data.get('label', str(node_id)),
            'color': node_data.get('color', '#97c2fc'),
            'shape': node_data.get('shape', 'dot'),
            'size': node_data.get('size', 20),
            '_fullTitle': title  # Store for side panel, but don't show as tooltip
        }
        nodes.append(node_obj)
    
    # Convert edges
    for source, target, edge_data in G.edges(data=True):
        # Build title from either 'title' attribute or all custom attributes
        if 'title' in edge_data:
            edge_title = str(edge_data['title']).replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        else:
            # Collect all custom attributes
            custom_attrs = []
            for key, value in edge_data.items():
                if key not in ['label']:
                    # Convert newlines to HTML breaks and tabs to spaces
                    value_str = str(value).replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                    custom_attrs.append(f"{key}: {value_str}")
            
            if custom_attrs:
                # Add double line breaks for better spacing
                edge_title = "<br><br>".join(custom_attrs)
            else:
                edge_title = f'{source} → {target}'
        
        edge_label = edge_data.get('label', '')
        edge_label = str(edge_label).replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        
        edge_obj = {
            'from': str(source),
            'to': str(target),
            'arrows': 'to',  # DiGraph always has arrows
            '_fullTitle': edge_title,  # Store for side panel, but don't show as tooltip
            'label': edge_label
        }
        edges.append(edge_obj)
    
    return {'nodes': nodes, 'edges': edges}


def generate_html_visualization(G, output_file='graph_visualization.html', title='Network Graph'):
    """
    Generate HTML file with interactive graph visualization
    
    Args:
        G: NetworkX DiGraph
        output_file: Path to output HTML file
        title: Title for the visualization
    """
    
    # Convert graph to vis.js format
    vis_data = convert_graph_to_vis_data(G)
    
    # Create the HTML template with embedded data
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" integrity="sha512-WgxfT5LWjfszlPHXRmBWHkV2eceiWTOBvrKCNbdgDYTHrT2AeLCGbF4sZlZw3UMN3WtL0tGUoIAKsu8mllg/XA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js" integrity="sha512-LnvoEWDFrqGHlHmDD2101OrLcbsfkrzoSpvtSQtxK3RMnRV0eOkhhBN2dXHKRrUU8p2DGRTk35n4O8nWSVe1mQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>

    <style type="text/css">
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Arial, sans-serif;
            overflow: hidden;
        }}

        #mynetwork {{
            position: absolute;
            left: 0;
            top: 0;
            right: 300px;
            height: 100vh;
            background-color: #ffffff;
            border-right: 2px solid #ccc;
            transition: right 0.1s ease;
        }}

        #sidepanel {{
            position: absolute;
            right: 0;
            top: 0;
            width: 300px;
            height: 100vh;
            background: #f8f9fa;
            padding: 20px;
            overflow-y: auto;
            box-shadow: -2px 0 10px rgba(0,0,0,0.1);
            z-index: 1000;
            min-width: 200px;
            max-width: 800px;
        }}

        #resize-handle {{
            position: absolute;
            left: 0;
            top: 0;
            width: 8px;
            height: 100%;
            background: #ccc;
            cursor: col-resize;
            z-index: 1001;
            transition: background 0.2s;
        }}

        #resize-handle:hover {{
            background: #007bff;
        }}

        #sidepanel h3 {{
            margin: 0 0 20px 0;
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
            font-size: 20px;
        }}

        #details {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            min-height: 100px;
        }}

        #details p {{
            margin: 15px 0;
            line-height: 1.8;
            word-wrap: break-word;
        }}

        #details b {{
            color: #007bff;
            display: inline-block;
            min-width: 80px;
        }}

        .placeholder {{
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 40px 20px;
        }}

        #config {{
            display: none;
        }}
    </style>
</head>

<body>
    <div id="mynetwork"></div>
    
    <div id="sidepanel">
        <div id="resize-handle"></div>
        <h3>Details Panel</h3>
        <div id="details">
            <p class="placeholder">Click on a node or edge to view details</p>
        </div>
    </div>

    <div id="config"></div>

    <script type="text/javascript">
        console.log("Script starting...");

        // Graph data from NetworkX
        var nodes = new vis.DataSet({json.dumps(vis_data['nodes'], indent=8)});

        var edges = new vis.DataSet({json.dumps(vis_data['edges'], indent=8)});

        // Create network
        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            nodes: {{
                font: {{
                    size: 16
                }}
            }},
            nodes: {{
                font: {{
                    size: 16
                }}
            }},
            edges: {{
                font: {{
                    size: 12,
                    align: 'middle'
                }},
                color: {{
                    inherit: true
                }},
                smooth: {{
                    enabled: true,
                    type: "dynamic"
                }}
            }},
            interaction: {{
                dragNodes: true,
                hover: false,
                tooltipDelay: 300,
                hideEdgesOnDrag: false,
                hideNodesOnDrag: false
            }},
            nodes: {{
                font: {{
                    size: 16
                }}
            }},
            physics: {{
                enabled: true,
                stabilization: {{
                    enabled: true,
                    iterations: 1000
                }}
            }}
        }};

        var network = new vis.Network(container, data, options);

        console.log("Network created");

        // Node click handler
        network.on("click", function(params) {{
            console.log("Click event:", params);
            
            var detailsDiv = document.getElementById("details");
            
            if (params.nodes.length > 0) {{
                // Node was clicked
                var nodeId = params.nodes[0];
                var nodeData = nodes.get(nodeId);
                
                console.log("Node clicked:", nodeId, nodeData);
                
                detailsDiv.innerHTML = `
                    <h4 style="color: #007bff; margin-top: 0; margin-bottom: 15px;">Node Selected</h4>
                    <p><b>ID:</b> ${{nodeData.id}}</p>
                    <p><b>Label:</b> ${{nodeData.label}}</p>
                    <p><b>Shape:</b> ${{nodeData.shape}}</p>
                    <p><b>Color:</b> <span style="display:inline-block; width:20px; height:20px; background:${{nodeData.color}}; border:1px solid #999; vertical-align:middle;"></span></p>
                    <hr style="margin: 15px 0;">
                    <div style="white-space: normal;"><b>Description:</b><br>${{nodeData._fullTitle || 'No description'}}</div>
                `;
            }} 
            else if (params.edges.length > 0) {{
                // Edge was clicked
                var edgeId = params.edges[0];
                var edgeData = edges.get(edgeId);
                
                console.log("Edge clicked:", edgeId, edgeData);
                
                detailsDiv.innerHTML = `
                    <h4 style="color: #28a745; margin-top: 0; margin-bottom: 15px;">Edge Selected</h4>
                    <p><b>From:</b> ${{edgeData.from}}</p>
                    <p><b>To:</b> ${{edgeData.to}}</p>
                    <p><b>Label:</b> ${{edgeData.label || 'None'}}</p>
                    <p><b>Direction:</b> ${{edgeData.arrows || 'None'}}</p>
                    <hr style="margin: 15px 0;">
                    <div style="white-space: normal;"><b>Description:</b><br>${{edgeData._fullTitle || 'No description'}}</div>
                `;
            }}
            else {{
                // Empty space clicked
                console.log("Empty space clicked");
                detailsDiv.innerHTML = '<p class="placeholder">Click on a node or edge to view details</p>';
            }}
        }});

        console.log("Event listeners attached");

        // ============================================================
        // RESIZABLE SIDE PANEL
        // ============================================================
        const resizeHandle = document.getElementById('resize-handle');
        const sidepanel = document.getElementById('sidepanel');
        const mynetwork = document.getElementById('mynetwork');
        let isResizing = false;

        resizeHandle.addEventListener('mousedown', function(e) {{
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        }});

        document.addEventListener('mousemove', function(e) {{
            if (!isResizing) return;
            
            const windowWidth = window.innerWidth;
            const newWidth = windowWidth - e.clientX;
            
            // Constrain width between min and max
            if (newWidth >= 200 && newWidth <= 800) {{
                sidepanel.style.width = newWidth + 'px';
                mynetwork.style.right = newWidth + 'px';
                
                // Redraw network to fit new dimensions
                if (network) {{
                    network.fit();
                }}
            }}
        }});

        document.addEventListener('mouseup', function() {{
            if (isResizing) {{
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }}
        }});
    </script>
</body>
</html>"""
    
    # Write HTML file
    with open(output_file, 'w') as f:
        f.write(html_template)
    
    print(f"HTML visualization generated: {output_file}")
    print(f"Open {output_file} in your web browser to view the graph")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Create a sample DiGraph
    print("=" * 70)
    print("Creating example NetworkX DiGraph...")
    print("=" * 70)
    
    G = nx.DiGraph()
    
    # Add nodes with attributes
    G.add_node("A", label="Node A", title="This is node A - the start", color="#ff6b6b", size=25)
    G.add_node("B", label="Node B", title="This is node B - middle layer", color="#4ecdc4", size=25)
    G.add_node("C", label="Node C", title="This is node C - another middle", color="#4ecdc4", size=25)
    G.add_node("D", label="Node D", title="This is node D - the end", color="#95e1d3", size=25)
    
    # Add edges with attributes
    G.add_edge("A", "B", label="flow", title="A influences B")
    G.add_edge("A", "C", label="flow", title="A influences C")
    G.add_edge("B", "D", label="result", title="B leads to D")
    G.add_edge("C", "D", label="result", title="C leads to D")
    
    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Save the graph in different formats
    print("\n" + "=" * 70)
    print("Saving graph in multiple formats...")
    print("=" * 70)
    
    save_graph_pickle(G, 'my_graph.pkl')
    save_graph_json(G, 'my_graph.json')
    save_graph_graphml(G, 'my_graph.graphml')
    
    # Generate HTML visualization
    print("\n" + "=" * 70)
    print("Generating HTML visualization...")
    print("=" * 70)
    
    generate_html_visualization(G, 'my_graph_visualization.html', 'My Network Graph')
    
    # Example 2: Load and visualize a saved graph
    print("\n" + "=" * 70)
    print("Loading graph from pickle and creating visualization...")
    print("=" * 70)
    
    loaded_graph = load_graph_pickle('my_graph.pkl')
    generate_html_visualization(loaded_graph, 'loaded_graph_visualization.html', 'Loaded Graph')
    
    print("\n" + "=" * 70)
    print("DONE! Open the HTML files in your browser to view the graphs")
    print("=" * 70)
