import spot
import buddy
import networkx as nx
import numpy as np
import itertools


def generate_buchi(formula):
    """Generate Büchi automaton from LTL formula using Spot"""
    return spot.translate(formula, 'Buchi', 'SBAcc', 'Complete')


def spot_to_graph(aut):
    """Convert Spot automaton to NetworkX graph"""
    G = nx.DiGraph()

    for state in range(0, aut.num_states()):
        acc_mark = aut.state_acc_sets(state)
        is_accepting = bool(acc_mark)
        G.add_node(state, accepting=is_accepting)

    for src in range(0, aut.num_states()):
        for edge in aut.out(src):
            edge_accepting = bool(edge.acc)
            G.add_edge(src, edge.dst, cond=edge.cond, accepting=edge_accepting)

    return G


def accepting_scc_subgraph(G):
    """Extract subgraph containing only SCCs that have at least one accepting edge"""
    sccs = list(nx.strongly_connected_components(G))
    accepting_nodes = set()

    for scc in sccs:
        has_accepting_edge = False
        for node in scc:
            for _, dst, data in G.out_edges(node, data=True):
                if dst in scc and data.get('accepting', False):
                    has_accepting_edge = True
                    break
            if has_accepting_edge:
                break

        if has_accepting_edge:
            accepting_nodes.update(scc)

    return G.subgraph(accepting_nodes).copy()


def count_sat_assignments(cond, aut):
    """Count how many variable assignments satisfy the BDD condition"""
    ap_list = list(aut.ap())
    num_aps = len(ap_list)

    if num_aps == 0:
        return 1 if cond != buddy.bddfalse else 0

    if cond == buddy.bddfalse:
        return 0
    if cond == buddy.bddtrue:
        return 2 ** num_aps

    bdict = aut.get_dict()
    count = 0

    for assignment in itertools.product([False, True], repeat=num_aps):
        valuation = buddy.bddtrue
        for i, ap in enumerate(ap_list):
            var = bdict.varnum(ap)
            if assignment[i]:
                valuation = valuation & buddy.bdd_ithvar(var)
            else:
                valuation = valuation & buddy.bdd_nithvar(var)

        if (cond & valuation) != buddy.bddfalse:
            count += 1

    return count


def adjacency_matrix_weighted(aut, G):
    """Build weighted adjacency matrix based on transition conditions"""
    nodes = list(G.nodes())
    if len(nodes) == 0:
        return np.array([[]])

    index = {n: i for i, n in enumerate(nodes)}
    M = np.zeros((len(nodes), len(nodes)))

    for src, dst, attr in G.edges(data=True):
        weight = count_sat_assignments(attr["cond"], aut)
        if weight > 0:
            M[index[src], index[dst]] = weight

    return M


def spectral_radius(M):
    """Compute spectral radius (largest eigenvalue magnitude)"""
    if M.size == 0:
        return 0.0
    vals = np.linalg.eigvals(M)
    return float(np.max(np.abs(vals)))


def hausdorff_dimension(formula):
    """
    Compute Hausdorff dimension of the omega-language defined by an LTL formula.

    The dimension is computed as log(ρ) / log(|Σ|) where:
    - ρ is the spectral radius of the weighted adjacency matrix
    - |Σ| is the alphabet size (2^n for n atomic propositions)

    Returns a value in [0, 1] where:
    - 0 indicates a very sparse/restricted language
    - 1 indicates a dense/unrestricted language
    """
    aut = generate_buchi(formula)
    G = spot_to_graph(aut)
    G_acc = accepting_scc_subgraph(G)

    if len(G_acc) == 0:
        return 0.0

    M = adjacency_matrix_weighted(aut, G_acc)
    rho = spectral_radius(M)
    sigma_size = 2 ** len(aut.ap())

    if rho <= 0 or sigma_size <= 1:
        return 0.0

    dim = float(np.log(rho) / np.log(sigma_size))
    return max(0.0, min(1.0, dim))


if __name__ == "__main__":
    # Example usage
    formulas = [
        "G a",
        "G (a | b)",
        "G F a",
        "G(a -> F b)",
        "G(a -> X b)",
    ]

    for formula in formulas:
        dim = hausdorff_dimension(formula)
        print(f"Hausdorff dimension of '{formula}': {dim:.6f}")