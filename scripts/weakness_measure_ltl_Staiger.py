import spot
import buddy
import networkx as nx
import numpy as np
import itertools
from typing import Set, List, Dict, Tuple, Optional


# ============================================================================
# OPTION 3: Canonical Alphabet Tracking
# ============================================================================

def hausdorff_dimension_canonical(formula, canonical_aps=None, debug=False):
    """
    Compute Hausdorff dimension relative to a CANONICAL set of atomic propositions.

    KEY DIFFERENCE from basic algorithm:
    - All formulas are evaluated against the SAME alphabet
    - Free variables (not mentioned in formula) contribute to permissiveness
    - This captures that "G a" is weaker than "G (a & !b)" when both use {a,b}

    Args:
        formula: LTL formula string
        canonical_aps: List of AP names (e.g., ['a', 'b', 'c'])
                      If None, uses only the APs mentioned in the formula
        debug: Print detailed information

    Returns:
        Hausdorff dimension in [0, 1]

    Example:
        With canonical_aps = ['a', 'b']:
        - "G a" → dimension ≈ 0.5 (b is free, so accepts 2 out of 4 letters)
        - "G (a & !b)" → dimension = 0.0 (both constrained, 1 out of 4 letters)
    """
    # Generate automaton
    aut = spot.translate(formula, 'Buchi', 'SBAcc', 'Complete')

    # Determine canonical alphabet
    formula_aps = {str(ap) for ap in aut.ap()}

    if canonical_aps is None:
        # No canonical alphabet specified - use formula's APs only
        canonical_aps_set = formula_aps
        free_aps = set()
    else:
        canonical_aps_set = set(canonical_aps)
        free_aps = canonical_aps_set - formula_aps

        # Validate: formula shouldn't use APs not in canonical set
        extra_aps = formula_aps - canonical_aps_set
        if extra_aps:
            raise ValueError(f"Formula uses APs {extra_aps} not in canonical set {canonical_aps}")

    if debug:
        print(f"\n{'=' * 70}")
        print(f"FORMULA: {formula}")
        print(f"{'=' * 70}")
        print(f"Formula APs: {formula_aps}")
        print(f"Canonical APs: {canonical_aps_set}")
        print(f"Free APs (unconstrained): {free_aps}")
        print(f"Alphabet size: {2 ** len(canonical_aps_set)}")

    # Get SCCs
    sccs = get_strongly_connected_components(aut)

    if debug:
        print(f"\nTotal SCCs: {len(sccs)}")
        print(f"Accepting SCCs: {sum(1 for scc in sccs if is_scc_accepting(aut, scc))}")

    # Get maximal accepting SCCs
    maximal_sccs = get_maximal_accepting_sccs(aut, sccs)

    if debug:
        print(f"Maximal accepting SCCs: {len(maximal_sccs)}")

    if not maximal_sccs:
        return 0.0

    # Compute spectral radius for each maximal SCC
    # KEY DIFFERENCE: Account for free variables in edge weights
    max_rho = 0.0
    for scc in maximal_sccs:
        rho = compute_scc_dimension_canonical(aut, scc, free_aps, debug)
        if debug:
            print(f"  SCC {scc}: spectral radius = {rho}")
        max_rho = max(max_rho, rho)

    if max_rho <= 0:
        return 0.0

    # Compute dimension using CANONICAL alphabet size
    canonical_alphabet_size = 2 ** len(canonical_aps_set)

    if canonical_alphabet_size <= 1:
        return 0.0

    dim = float(np.log(max_rho) / np.log(canonical_alphabet_size))

    if debug:
        print(f"\nMax spectral radius: {max_rho}")
        print(f"Canonical alphabet size: {canonical_alphabet_size}")
        print(f"Hausdorff dimension: {dim}")

    return max(0.0, min(1.0, dim))


def compute_scc_dimension_canonical(aut, scc, free_aps, debug=False):
    """
    Compute spectral radius for an SCC, accounting for FREE variables.

    KEY INSIGHT:
    - If an edge accepts k assignments over the formula's APs
    - And there are n free APs (not in formula)
    - Then the edge actually accepts k * 2^n letters in the canonical alphabet

    Example:
        Formula: "G a", canonical APs: {a, b}
        Edge condition: "a" (accepts when a=true)
        - Over formula APs {a}: accepts 1 assignment (a=true)
        - Free APs: {b}
        - In canonical alphabet {a,b}: accepts 1 * 2^1 = 2 letters
          (a=true,b=false) and (a=true,b=true)
    """
    scc_list = sorted(list(scc))
    index_map = {state: i for i, state in enumerate(scc_list)}
    n = len(scc_list)

    # Free variable multiplier: each free variable doubles the accepting letters
    free_multiplier = 2 ** len(free_aps)

    if debug and free_aps:
        print(f"\n  Free variable multiplier: {free_multiplier} (from {len(free_aps)} free APs)")

    # Build weighted adjacency matrix
    M = np.zeros((n, n))

    for src in scc:
        for edge in aut.out(src):
            if edge.dst in scc:
                # Count satisfying assignments over formula's APs
                base_weight = count_sat_assignments(edge.cond, aut)

                # Multiply by free variable factor to get true weight in canonical alphabet
                canonical_weight = base_weight * free_multiplier

                if canonical_weight > 0:
                    M[index_map[src], index_map[edge.dst]] = canonical_weight

                if debug and canonical_weight > 0:
                    print(f"    Edge {src}→{edge.dst}: base={base_weight}, "
                          f"canonical={canonical_weight}")

    if debug:
        print(f"\n  Adjacency matrix:")
        print(f"  {M}")

    # Compute spectral radius
    if M.size == 0:
        return 0.0

    eigenvalues = np.linalg.eigvals(M)
    rho = float(np.max(np.abs(eigenvalues)))

    return rho


# ============================================================================
# Helper functions (same as before)
# ============================================================================

def get_strongly_connected_components(aut):
    """Get all SCCs of the automaton."""
    G = nx.DiGraph()
    for state in range(aut.num_states()):
        G.add_node(state)

    for src in range(aut.num_states()):
        for edge in aut.out(src):
            G.add_edge(src, edge.dst)

    sccs = list(nx.strongly_connected_components(G))
    return sccs


def is_scc_accepting(aut, scc):
    """Check if SCC contains at least one accepting edge."""
    for src in scc:
        for edge in aut.out(src):
            if edge.dst in scc and bool(edge.acc):
                return True
    return False


def get_maximal_accepting_sccs(aut, sccs):
    """Get maximal (terminal) accepting SCCs."""
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
    """Count satisfying assignments for a BDD condition."""
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
# COMPARISON: Standard vs Canonical Alphabet
# ============================================================================

def compare_approaches(formula, canonical_aps=['a', 'b', 'c']):
    """Compare standard approach vs canonical alphabet approach."""
    print(f"\n{'=' * 70}")
    print(f"FORMULA: {formula}")
    print(f"{'=' * 70}")

    # Standard approach (no canonical alphabet)
    dim_standard = hausdorff_dimension_canonical(formula, canonical_aps=None, debug=False)
    print(f"\nStandard (formula APs only): {dim_standard:.4f}")

    # Canonical alphabet approach
    dim_canonical = hausdorff_dimension_canonical(formula, canonical_aps=canonical_aps, debug=True)

    print(f"\n{'=' * 70}")
    print(f"COMPARISON:")
    print(f"  Standard:  {dim_standard:.4f}")
    print(f"  Canonical: {dim_canonical:.4f}")
    print(f"  Difference: {dim_canonical - dim_standard:.4f}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    print("=" * 70)
    print("DEMONSTRATING THE DIFFERENCE: Option 1 vs Option 3")
    print("=" * 70)

    # The key test case that motivated this change
    compare_approaches("G a", canonical_aps=['a', 'b'])
    compare_approaches("G (a & !b)", canonical_aps=['a', 'b'])

    print("\n\n" + "=" * 70)
    print("COMPREHENSIVE COMPARISON")
    print("=" * 70)

    test_cases = [
        "G a",
        "(G a) & (G F b)",
        "G (a & !b)",
        "G (a | b)",
        "G F a",
        "F a",
        "G(a -> F b)",
        "G(a -> X b)",
        "(G F a) & (G F b)",
        "G((a & !b) | (!a & b))",
    ]

    canonical_aps = ['a', 'b', 'c']

    print(f"\nCanonical alphabet: {canonical_aps}")
    print(f"Alphabet size: {2 ** len(canonical_aps)} = 8 letters\n")
    print(f"{'Formula':<30} | {'Standard':<10} | {'Canonical':<10} | {'Diff'}")
    print("-" * 70)

    for formula in test_cases:
        dim_std = hausdorff_dimension_canonical(formula, canonical_aps=None)
        dim_can = hausdorff_dimension_canonical(formula, canonical_aps=canonical_aps)
        diff = dim_can - dim_std
        print(f"{formula:<30} | {dim_std:<10.4f} | {dim_can:<10.4f} | {diff:+.4f}")