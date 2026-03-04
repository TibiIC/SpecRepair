import spot
import buddy
import networkx as nx
import numpy as np
import itertools
from typing import List, Set, Optional


# ============================================================================
# CORRECTED ENTROPY COMPUTATION
# ============================================================================

def entropy_ltl(formula, canonical_aps=None, debug=False):
    """
    Compute the topological entropy of an LTL formula.

    CORRECTED: Only count prefixes that can lead to accepting runs.

    Entropy = log(λ) / log(|Σ|)
    where λ is the spectral radius of the adjacency matrix over states
    that can reach an accepting SCC.
    """
    aut = spot.translate(formula, 'Buchi', 'SBAcc', 'Complete')

    # Determine alphabet
    formula_aps = {str(ap) for ap in aut.ap()}

    if canonical_aps is None:
        canonical_aps_set = formula_aps
        free_aps = set()
    else:
        canonical_aps_set = set(canonical_aps)
        free_aps = canonical_aps_set - formula_aps
        extra_aps = formula_aps - canonical_aps_set
        if extra_aps:
            raise ValueError(f"Formula uses APs {extra_aps} not in canonical set {canonical_aps}")

    alphabet_size = 2 ** len(canonical_aps_set)
    free_multiplier = 2 ** len(free_aps)

    if debug:
        print(f"\n{'=' * 70}")
        print(f"FORMULA: {formula}")
        print(f"{'=' * 70}")
        print(f"Formula APs: {formula_aps}")
        print(f"Canonical APs: {canonical_aps_set}")
        print(f"Free APs: {free_aps}")
        print(f"Alphabet size: {alphabet_size}")

    # CRITICAL FIX: Only include states that can reach an accepting state
    accepting_reachable_states = get_states_reaching_acceptance(aut, debug)

    if debug:
        print(f"\nStates that can reach acceptance: {len(accepting_reachable_states)}")
        print(f"States: {accepting_reachable_states}")

    if len(accepting_reachable_states) == 0:
        return 0.0

    # Build weighted adjacency matrix for prefix counting
    M = build_prefix_matrix(aut, accepting_reachable_states, free_multiplier, debug)

    if debug:
        print(f"\nPrefix adjacency matrix ({len(accepting_reachable_states)}x{len(accepting_reachable_states)}):")
        print(M)

    # Compute spectral radius
    if M.size == 0:
        spectral_radius = 0.0
    else:
        eigenvalues = np.linalg.eigvals(M)
        spectral_radius = float(np.max(np.abs(eigenvalues)))

    if debug:
        print(f"\nSpectral radius: {spectral_radius}")

    if spectral_radius <= 0 or alphabet_size <= 1:
        return 0.0

    # Entropy = log(λ) / log(|Σ|)
    entropy = float(np.log(spectral_radius) / np.log(alphabet_size))

    if debug:
        print(f"Entropy: {entropy:.6f}")
        print(f"Interpretation: accepting prefixes grow as ~{spectral_radius:.2f}^n")

    return max(0.0, min(1.0, entropy))


def get_states_reaching_acceptance(aut, debug=False):
    """
    Get all states from which an accepting run is possible.

    This is the CRITICAL fix: we only want to count prefixes that can
    actually lead to acceptance, not prefixes that lead to rejection.

    Algorithm:
    1. Find all accepting SCCs (states with accepting edges)
    2. Find all states from which these accepting SCCs are reachable
    """
    # Step 1: Find accepting states (states in accepting SCCs)
    G = nx.DiGraph()
    for state in range(aut.num_states()):
        G.add_node(state)

    for src in range(aut.num_states()):
        for edge in aut.out(src):
            G.add_edge(src, edge.dst)

    # Get SCCs
    sccs = list(nx.strongly_connected_components(G))

    # Find accepting SCCs
    accepting_states = set()
    for scc in sccs:
        has_accepting_edge = False
        for state in scc:
            for edge in aut.out(state):
                if edge.dst in scc and bool(edge.acc):
                    has_accepting_edge = True
                    break
            if has_accepting_edge:
                break

        if has_accepting_edge:
            accepting_states.update(scc)

    if debug:
        print(f"\nAccepting states (in accepting SCCs): {sorted(accepting_states)}")

    if not accepting_states:
        return []

    # Step 2: Find all states from which accepting states are reachable
    # (backward reachability from accepting states)
    G_reversed = G.reverse()

    states_reaching_acceptance = set()
    for acc_state in accepting_states:
        # BFS backwards from this accepting state
        visited = set([acc_state])
        queue = [acc_state]

        while queue:
            state = queue.pop(0)
            states_reaching_acceptance.add(state)

            for pred in G_reversed.neighbors(state):
                if pred not in visited:
                    visited.add(pred)
                    queue.append(pred)

    # Also need to filter: only keep states reachable FROM the initial state
    initial_state = 0
    forward_reachable = set()
    visited = set([initial_state])
    queue = [initial_state]

    while queue:
        state = queue.pop(0)
        forward_reachable.add(state)

        for succ in G.neighbors(state):
            if succ not in visited:
                visited.add(succ)
                queue.append(succ)

    # Final result: states that are both forward-reachable and can reach acceptance
    result = sorted(list(states_reaching_acceptance & forward_reachable))

    if debug:
        print(f"States reachable from initial: {sorted(forward_reachable)}")
        print(f"States that can reach acceptance: {sorted(states_reaching_acceptance)}")
        print(f"Intersection (valid prefix states): {result}")

    return result


def build_prefix_matrix(aut, states, free_multiplier, debug=False):
    """
    Build weighted adjacency matrix for prefix counting.

    M[i,j] = number of alphabet letters that enable transition from state i to state j
    """
    n = len(states)
    index_map = {state: i for i, state in enumerate(states)}

    M = np.zeros((n, n))

    for src in states:
        for edge in aut.out(src):
            if edge.dst in states:  # Only count transitions within our state set
                # Count satisfying assignments
                base_weight = count_sat_assignments(edge.cond, aut)

                # Multiply by free variables
                canonical_weight = base_weight * free_multiplier

                if canonical_weight > 0:
                    M[index_map[src], index_map[edge.dst]] += canonical_weight

    return M


def count_sat_assignments(cond, aut):
    """Count how many variable assignments satisfy the BDD condition."""
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
# TESTING
# ============================================================================

def test_individual_formulas():
    """Test individual invariants and justice formulas."""
    print("=" * 70)
    print("TESTING INDIVIDUAL FORMULAS (CORRECTED)")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    test_cases = [
        # Invariants
        ("G a", "Invariant: a always true"),
        ("G (a & !b)", "Invariant: a true, b false"),
        ("G (a | b)", "Invariant: at least one of a,b true"),
        ("G (a -> b)", "Invariant: if a then b"),

        # Justice (Fairness)
        ("G F a", "Justice: a infinitely often"),
        ("G F (a & b)", "Justice: both a and b infinitely often"),
        ("(G F a) & (G F b)", "Justice: a and b each infinitely often"),

        # Response (Dwyer patterns)
        ("G(a -> F b)", "Response: every a followed eventually by b"),
        ("G(a -> X b)", "Response: every a followed immediately by b"),
    ]

    print(f"\nCanonical alphabet: {canonical_aps} (size {2 ** len(canonical_aps)})")
    print(f"\n{'Formula':<30} | {'Entropy':<10} | Description")
    print("-" * 80)

    for formula, description in test_cases:
        entropy_val = entropy_ltl(formula, canonical_aps=canonical_aps, debug=False)
        print(f"{formula:<30} | {entropy_val:<10.4f} | {description}")


def test_conjunctions():
    """Test conjunctions of invariants and justice formulas."""
    print("\n\n" + "=" * 70)
    print("TESTING CONJUNCTIONS (CORRECTED)")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    test_cases = [
        # Invariant + Liveness
        ("G a", "Just invariant"),
        ("(G a) & (F b)", "Invariant + liveness"),

        # Invariant + Justice
        ("G a", "Just invariant"),
        ("(G a) & (G F b)", "Invariant + justice"),

        # Multiple justice conditions
        ("G F a", "One justice"),
        ("(G F a) & (G F b)", "Two justice conditions"),
        ("(G F a) & (G F b) & (G F c)", "Three justice conditions"),

        # Invariant + Multiple justice
        ("(G (a | b)) & (G F a)", "Invariant + one justice"),
        ("(G (a | b)) & (G F a) & (G F b)", "Invariant + two justice"),

        # Response patterns
        ("G(a -> F b)", "Response pattern"),
        ("G(a -> F b) & G(b -> F c)", "Chained responses"),
    ]

    print(f"\nCanonical alphabet: {canonical_aps} (size {2 ** len(canonical_aps)})")
    print(f"\n{'Formula':<45} | {'Entropy':<10} | Description")
    print("-" * 90)

    for formula, description in test_cases:
        entropy_val = entropy_ltl(formula, canonical_aps=canonical_aps, debug=False)
        print(f"{formula:<45} | {entropy_val:<10.4f} | {description}")


def detailed_comparison():
    """Detailed comparison of the problematic cases."""
    print("\n\n" + "=" * 70)
    print("DETAILED COMPARISON: PROBLEMATIC CASES (CORRECTED)")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    cases = [
        "G a",
        "(G a) & (F b)",
        "(G a) & (G F b)",
    ]

    for formula in cases:
        entropy_ltl(formula, canonical_aps=canonical_aps, debug=True)
        print()


if __name__ == "__main__":
    test_individual_formulas()
    test_conjunctions()
    detailed_comparison()