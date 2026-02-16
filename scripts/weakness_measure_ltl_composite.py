import spot
import buddy
import networkx as nx
import numpy as np
import itertools
from typing import Set, List, Dict, Tuple, Optional


# ============================================================================
# EXTENDED WEAKNESS MEASURE: Recurrent + Liveness
# ============================================================================

def extract_liveness_constraints(formula_str):
    """
    Identify liveness constraints in the formula.

    Liveness constraints are F (eventually) operators that are NOT
    part of fairness (GF) conditions.

    Returns:
        List of subformulas that are liveness constraints
    """
    # Parse the formula
    formula = spot.formula(formula_str)

    liveness_constraints = []

    def find_f_operators(f, under_g=False):
        """Recursively find F operators that aren't under G"""
        if f.kind_name() == 'F' and not under_g:
            # This is a liveness constraint
            liveness_constraints.append(str(f[0]))
        elif f.kind_name() == 'G':
            # Entering a G operator
            for child in f:
                find_f_operators(child, under_g=True)
        else:
            # Other operators
            for child in f:
                find_f_operators(child, under_g=under_g)

    find_f_operators(formula)
    return liveness_constraints


def compute_reachability_dimension(aut, canonical_aps, debug=False):
    """
    Compute a measure of how constrained the path to accepting states is.

    This captures liveness constraints like "F b" that don't affect
    recurrent behavior but do constrain reachability.

    Returns:
        A value in [0, 1] where:
        - 0.0 = easy to reach accepting states (many paths)
        - 1.0 = hard to reach accepting states (few paths)
    """
    # Find accepting states
    accepting_states = set()
    for state in range(aut.num_states()):
        if bool(aut.state_acc_sets(state)):
            accepting_states.add(state)

    if not accepting_states:
        return 1.0  # No accepting states = impossible to satisfy

    # Build graph
    G = nx.DiGraph()
    for state in range(aut.num_states()):
        G.add_node(state)

    # Add weighted edges
    free_aps = set(canonical_aps) - {str(ap) for ap in aut.ap()}
    free_multiplier = 2 ** len(free_aps)

    for src in range(aut.num_states()):
        for edge in aut.out(src):
            base_weight = count_sat_assignments(edge.cond, aut)
            canonical_weight = base_weight * free_multiplier
            if canonical_weight > 0:
                G.add_edge(src, edge.dst, weight=canonical_weight)

    # Compute: average weight of shortest paths to accepting states
    # High weight = easy to reach, Low weight = hard to reach

    initial_state = 0  # Assume state 0 is initial

    total_paths_weight = 0
    alphabet_size = 2 ** len(canonical_aps)

    for acc_state in accepting_states:
        if nx.has_path(G, initial_state, acc_state):
            # Find the path with maximum product of weights
            # (approximation: use shortest path as proxy)
            try:
                path = nx.shortest_path(G, initial_state, acc_state)
                path_weight = 1.0
                for i in range(len(path) - 1):
                    edge_weight = G[path[i]][path[i + 1]]['weight']
                    path_weight *= (edge_weight / alphabet_size)
                total_paths_weight += path_weight
            except:
                pass

    # Convert to penalty: more paths = less penalty
    if total_paths_weight == 0:
        return 1.0

    # Normalize: penalty is inverse of ease of reaching
    penalty = 1.0 / (1.0 + total_paths_weight)

    return penalty


def weakness_measure_extended(formula, canonical_aps=['a', 'b', 'c'], debug=False):
    """
    Extended weakness measure that captures BOTH recurrent and liveness behavior.

    Returns:
        (recurrent_dimension, liveness_penalty, composite_score)

    Where:
        recurrent_dimension: Hausdorff dimension of the accepting SCC
        liveness_penalty: How hard it is to reach the accepting SCC (0=easy, 1=hard)
        composite_score: Combined measure = recurrent_dimension * (1 - liveness_penalty)

    Examples:
        "G a" → (0.67, ~0, 0.67)         # Easy to reach, moderate recurrent freedom
        "(G a) & (F b)" → (0.67, ~0.2, 0.54)  # Harder to reach, same recurrent freedom
    """
    # Generate automaton
    aut = spot.translate(formula, 'Buchi', 'SBAcc', 'Complete')

    # Extract liveness constraints
    liveness_constraints = extract_liveness_constraints(formula)

    # Compute recurrent dimension (standard Hausdorff dimension)
    recurrent_dim = hausdorff_dimension_canonical(
        formula, canonical_aps=canonical_aps, debug=False
    )

    # Compute liveness penalty
    liveness_penalty = compute_reachability_dimension(aut, canonical_aps, debug=debug)

    # Composite score: dimension discounted by liveness constraints
    composite_score = recurrent_dim * (1 - liveness_penalty)

    if debug:
        print(f"\n{'=' * 70}")
        print(f"FORMULA: {formula}")
        print(f"{'=' * 70}")
        print(f"Liveness constraints found: {liveness_constraints}")
        print(f"Recurrent dimension: {recurrent_dim:.4f}")
        print(f"Liveness penalty: {liveness_penalty:.4f}")
        print(f"Composite score: {composite_score:.4f}")
        print(f"{'=' * 70}")

    return recurrent_dim, liveness_penalty, composite_score


def hausdorff_dimension_canonical(formula, canonical_aps=None, debug=False):
    """Standard canonical Hausdorff dimension (from previous implementation)"""
    aut = spot.translate(formula, 'Buchi', 'SBAcc', 'Complete')

    formula_aps = {str(ap) for ap in aut.ap()}

    if canonical_aps is None:
        canonical_aps_set = formula_aps
        free_aps = set()
    else:
        canonical_aps_set = set(canonical_aps)
        free_aps = canonical_aps_set - formula_aps
        extra_aps = formula_aps - canonical_aps_set
        if extra_aps:
            raise ValueError(f"Formula uses APs {extra_aps} not in canonical set")

    sccs = get_strongly_connected_components(aut)
    maximal_sccs = get_maximal_accepting_sccs(aut, sccs)

    if not maximal_sccs:
        return 0.0

    max_rho = 0.0
    for scc in maximal_sccs:
        rho = compute_scc_dimension_canonical(aut, scc, free_aps, False)
        max_rho = max(max_rho, rho)

    if max_rho <= 0:
        return 0.0

    canonical_alphabet_size = 2 ** len(canonical_aps_set)
    if canonical_alphabet_size <= 1:
        return 0.0

    dim = float(np.log(max_rho) / np.log(canonical_alphabet_size))
    return max(0.0, min(1.0, dim))


def compute_scc_dimension_canonical(aut, scc, free_aps, debug=False):
    """Compute spectral radius accounting for free variables"""
    scc_list = sorted(list(scc))
    index_map = {state: i for i, state in enumerate(scc_list)}
    n = len(scc_list)

    free_multiplier = 2 ** len(free_aps)
    M = np.zeros((n, n))

    for src in scc:
        for edge in aut.out(src):
            if edge.dst in scc:
                base_weight = count_sat_assignments(edge.cond, aut)
                canonical_weight = base_weight * free_multiplier
                if canonical_weight > 0:
                    M[index_map[src], index_map[edge.dst]] = canonical_weight

    if M.size == 0:
        return 0.0

    eigenvalues = np.linalg.eigvals(M)
    return float(np.max(np.abs(eigenvalues)))


# Helper functions (same as before)
def get_strongly_connected_components(aut):
    G = nx.DiGraph()
    for state in range(aut.num_states()):
        G.add_node(state)
    for src in range(aut.num_states()):
        for edge in aut.out(src):
            G.add_edge(src, edge.dst)
    return list(nx.strongly_connected_components(G))


def is_scc_accepting(aut, scc):
    for src in scc:
        for edge in aut.out(src):
            if edge.dst in scc and bool(edge.acc):
                return True
    return False


def get_maximal_accepting_sccs(aut, sccs):
    accepting_sccs = [scc for scc in sccs if is_scc_accepting(aut, scc)]
    scc_graph = nx.DiGraph()
    scc_map = {}

    for i, scc in enumerate(sccs):
        scc_graph.add_node(i)
        for state in scc:
            scc_map[state] = i

    for i, scc in enumerate(sccs):
        for src in scc:
            for edge in aut.out(src):
                dst_scc = scc_map[edge.dst]
                if dst_scc != i:
                    scc_graph.add_edge(i, dst_scc)

    maximal_sccs = []
    accepting_indices = {sccs.index(scc) for scc in accepting_sccs}

    for scc in accepting_sccs:
        scc_idx = sccs.index(scc)
        is_maximal = True
        for target_idx in accepting_indices:
            if target_idx != scc_idx:
                if nx.has_path(scc_graph, scc_idx, target_idx):
                    is_maximal = False
                    break
        if is_maximal:
            maximal_sccs.append(scc)

    return maximal_sccs


def count_sat_assignments(cond, aut):
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


# ============================================================================
# DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    canonical_aps = ['a', 'b', 'c']

    print("=" * 70)
    print("EXTENDED WEAKNESS MEASURE")
    print("Captures BOTH recurrent behavior AND liveness constraints")
    print("=" * 70)

    test_cases = [
        ("G a", "No liveness constraints"),
        ("(G a) & (F b)", "Must eventually satisfy b"),
        ("G (a & !b)", "Strict safety"),
        ("F a", "Pure liveness"),
        ("G F a", "Fairness"),
        ("G(a -> F b)", "Response property"),
    ]

    print(f"\nCanonical alphabet: {canonical_aps}\n")
    print(f"{'Formula':<25} | {'Recurrent':<10} | {'Liveness':<10} | {'Composite':<10} | Description")
    print("-" * 95)

    for formula, description in test_cases:
        rec_dim, live_pen, composite = weakness_measure_extended(
            formula, canonical_aps=canonical_aps, debug=False
        )
        print(f"{formula:<25} | {rec_dim:<10.4f} | {live_pen:<10.4f} | {composite:<10.4f} | {description}")

    print("\n" + "=" * 70)
    print("DETAILED COMPARISON: G a vs (G a) & (F b)")
    print("=" * 70)

    weakness_measure_extended("G a", canonical_aps=canonical_aps, debug=True)
    weakness_measure_extended("(G a) & (F b)", canonical_aps=canonical_aps, debug=True)