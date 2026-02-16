import spot
import buddy
import networkx as nx
import numpy as np
import itertools


def deep_analysis(formula, canonical_aps=['a', 'b', 'c']):
    """Analyze exactly what's happening in the automaton"""
    print(f"\n{'=' * 80}")
    print(f"FORMULA: {formula}")
    print(f"{'=' * 80}")

    aut = spot.translate(formula, 'Buchi', 'SBAcc', 'Complete')

    print(f"States: {aut.num_states()}")
    print(f"Formula APs: {aut.ap()}")

    # Analyze automaton structure
    G = nx.DiGraph()
    for state in range(aut.num_states()):
        G.add_node(state)

    for src in range(aut.num_states()):
        for edge in aut.out(src):
            G.add_edge(src, edge.dst)

    sccs = list(nx.strongly_connected_components(G))
    print(f"\nSCCs: {sccs}")

    # For each SCC, show detailed edge structure
    for i, scc in enumerate(sccs):
        print(f"\n--- SCC {i}: {sorted(scc)} ---")

        # Check if accepting
        has_accepting_edge = False
        for src in scc:
            for edge in aut.out(src):
                if edge.dst in scc and bool(edge.acc):
                    has_accepting_edge = True

        print(f"Has accepting edges: {has_accepting_edge}")

        if not has_accepting_edge:
            continue

        # Show all edges with their conditions
        print("\nEdges in SCC:")
        formula_aps = list(aut.ap())
        num_aps = len(formula_aps)
        bdict = aut.get_dict()

        for src in sorted(scc):
            for edge in aut.out(src):
                if edge.dst in scc:
                    # Find which assignments satisfy this edge
                    satisfying = []
                    for assignment in itertools.product([False, True], repeat=num_aps):
                        valuation = buddy.bddtrue
                        for j, ap in enumerate(formula_aps):
                            var = bdict.varnum(ap)
                            if assignment[j]:
                                valuation = valuation & buddy.bdd_ithvar(var)
                            else:
                                valuation = valuation & buddy.bdd_nithvar(var)

                        if (edge.cond & valuation) != buddy.bddfalse:
                            satisfying.append(assignment)

                    accepting_mark = "✓" if bool(edge.acc) else " "
                    print(f"  [{accepting_mark}] {src} → {edge.dst}: {len(satisfying)} assignments")
                    print(f"      Satisfying: {satisfying}")

        # Compute weighted adjacency matrix
        print("\nWeighted adjacency matrix (formula APs only):")
        scc_list = sorted(list(scc))
        index_map = {state: i for i, state in enumerate(scc_list)}
        n = len(scc_list)
        M = np.zeros((n, n))

        for src in scc:
            for edge in aut.out(src):
                if edge.dst in scc:
                    count = 0
                    for assignment in itertools.product([False, True], repeat=num_aps):
                        valuation = buddy.bddtrue
                        for j, ap in enumerate(formula_aps):
                            var = bdict.varnum(ap)
                            if assignment[j]:
                                valuation = valuation & buddy.bdd_ithvar(var)
                            else:
                                valuation = valuation & buddy.bdd_nithvar(var)
                        if (edge.cond & valuation) != buddy.bddfalse:
                            count += 1
                    M[index_map[src], index_map[edge.dst]] = count

        print(M)
        eigenvalues = np.linalg.eigvals(M)
        rho = np.max(np.abs(eigenvalues))
        print(f"Spectral radius: {rho}")

        # Now with canonical alphabet
        free_aps = set(canonical_aps) - {str(ap) for ap in formula_aps}
        free_multiplier = 2 ** len(free_aps)

        M_canonical = M * free_multiplier
        print(f"\nWeighted adjacency matrix (canonical APs {canonical_aps}):")
        print(f"Free APs: {free_aps}, multiplier: {free_multiplier}")
        print(M_canonical)
        rho_canonical = np.max(np.abs(np.linalg.eigvals(M_canonical)))
        print(f"Spectral radius: {rho_canonical}")

        canonical_size = 2 ** len(canonical_aps)
        dim = np.log(rho_canonical) / np.log(canonical_size)
        print(f"Hausdorff dimension: {dim:.4f}")


if __name__ == '__main__':
    # Analyze both formulas
    deep_analysis("G a", canonical_aps=['a', 'b', 'c'])
    deep_analysis("(G a) & (G F b)", canonical_aps=['a', 'b', 'c'])