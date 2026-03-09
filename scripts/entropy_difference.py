import spot
import buddy
import networkx as nx
import numpy as np
import itertools
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# ============================================================================
# CORE ENTROPY COMPUTATION (from previous implementation)
# ============================================================================

def entropy_ltl(formula, canonical_aps=None, debug=False):
    """
    Compute the topological entropy of an LTL formula.

    Returns entropy h(L) where prefix growth is approximately λ^n with λ = 2^h.
    """
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

    alphabet_size = 2 ** len(canonical_aps_set)
    free_multiplier = 2 ** len(free_aps)

    if debug:
        print(f"Formula: {formula}")
        print(f"Alphabet size: {alphabet_size}")

    accepting_reachable_states = get_states_reaching_acceptance(aut, debug)

    if len(accepting_reachable_states) == 0:
        return 0.0

    M = build_prefix_matrix(aut, accepting_reachable_states, free_multiplier, debug)

    if M.size == 0:
        spectral_radius = 0.0
    else:
        eigenvalues = np.linalg.eigvals(M)
        spectral_radius = float(np.max(np.abs(eigenvalues)))

    if debug:
        print(f"Spectral radius: {spectral_radius}")

    if spectral_radius <= 0 or alphabet_size <= 1:
        return 0.0

    entropy = float(np.log(spectral_radius) / np.log(alphabet_size))

    return max(0.0, min(1.0, entropy))


def get_states_reaching_acceptance(aut, debug=False):
    """Get all states from which an accepting run is possible."""
    G = nx.DiGraph()
    for state in range(aut.num_states()):
        G.add_node(state)

    for src in range(aut.num_states()):
        for edge in aut.out(src):
            G.add_edge(src, edge.dst)

    sccs = list(nx.strongly_connected_components(G))

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

    if not accepting_states:
        return []

    G_reversed = G.reverse()

    states_reaching_acceptance = set()
    for acc_state in accepting_states:
        visited = set([acc_state])
        queue = [acc_state]

        while queue:
            state = queue.pop(0)
            states_reaching_acceptance.add(state)

            for pred in G_reversed.neighbors(state):
                if pred not in visited:
                    visited.add(pred)
                    queue.append(pred)

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

    result = sorted(list(states_reaching_acceptance & forward_reachable))
    return result


def build_prefix_matrix(aut, states, free_multiplier, debug=False):
    """Build weighted adjacency matrix for prefix counting."""
    n = len(states)
    index_map = {state: i for i, state in enumerate(states)}

    M = np.zeros((n, n))

    for src in states:
        for edge in aut.out(src):
            if edge.dst in states:
                base_weight = count_sat_assignments(edge.cond, aut)
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
# FAIRNESS CONSTRAINT COUNTING
# ============================================================================

def count_fairness_constraints(formula_str: str) -> int:
    """
    Count the number of G F (fairness/justice) constraints in a formula.

    A fairness constraint is a pattern G F ψ (globally, infinitely often ψ).
    """
    try:
        f = spot.formula(formula_str)
    except:
        return 0

    fairness_count = 0

    def count_gf(formula_node):
        nonlocal fairness_count

        if formula_node.kind() == spot.op_G:
            for child in formula_node:
                if child.kind() == spot.op_F:
                    fairness_count += 1
                count_gf(child)
        else:
            for child in formula_node:
                count_gf(child)

    count_gf(f)
    return fairness_count


def extract_fairness_formulas(formula_str: str) -> List[str]:
    """Extract the actual fairness constraint subformulas."""
    try:
        f = spot.formula(formula_str)
    except:
        return []

    fairness_formulas = []

    def extract_gf(formula_node):
        if formula_node.kind() == spot.op_G:
            for child in formula_node:
                if child.kind() == spot.op_F:
                    # Extract what's inside the F
                    for inner_child in child:
                        fairness_formulas.append(str(inner_child))
                extract_gf(child)
        else:
            for child in formula_node:
                extract_gf(child)

    extract_gf(f)
    return fairness_formulas


# ============================================================================
# PERCENTAGE-BASED COMPARISON FRAMEWORK
# ============================================================================

@dataclass
class SpecificationMetrics:
    """Metrics for a single specification."""
    formula: str
    entropy: float
    branching_factor: float
    alphabet_size: int
    fairness_count: int
    fairness_formulas: List[str]

    def __repr__(self):
        fairness_str = f", fairness={self.fairness_formulas}" if self.fairness_formulas else ""
        return (f"SpecificationMetrics(\n"
                f"  formula='{self.formula}',\n"
                f"  entropy={self.entropy:.4f},\n"
                f"  branching_factor={self.branching_factor:.4f},\n"
                f"  fairness_constraints={self.fairness_count}{fairness_str}\n"
                f")")


@dataclass
class ComparisonResult:
    """Result of comparing two weakened specifications against an original."""
    original: SpecificationMetrics
    spec1: SpecificationMetrics
    spec2: SpecificationMetrics

    # Percentage increases from original (entropy-based)
    increase_1_percent: float
    increase_2_percent: float

    # Fairness differences from original
    fairness_diff_1: int
    fairness_diff_2: int

    # Absolute difference in percentage points
    abs_difference_points: float

    # Relative significance (how significant is the difference?)
    relative_significance: float

    # Which spec is closer to original?
    closer_to_original: int  # 1 or 2

    # Which spec is more permissive?
    more_permissive: int  # 1 or 2

    # Comparison method used
    primary_differentiator: str  # "entropy" or "fairness"

    def summary(self) -> str:
        """Human-readable summary."""
        fairness_note_1 = f" (fairness: {self.spec1.fairness_count})" if self.spec1.fairness_count > 0 else ""
        fairness_note_2 = f" (fairness: {self.spec2.fairness_count})" if self.spec2.fairness_count > 0 else ""

        differentiator_note = ""
        if self.primary_differentiator == "fairness":
            differentiator_note = "\n  ⚠️  Note: Entropy is equal, ranked by fairness (more fairness = more restrictive = closer)"

        return f"""
Comparison Summary:
==================
Original: {self.original.formula}
  Branching factor: {self.original.branching_factor:.4f}
  Fairness constraints: {self.original.fairness_count}

Spec 1: {self.spec1.formula}
  Branching factor: {self.spec1.branching_factor:.4f}{fairness_note_1}
  Increase from original: {self.increase_1_percent:.2f}%
  Fairness change: {self.fairness_diff_1:+d}

Spec 2: {self.spec2.formula}
  Branching factor: {self.spec2.branching_factor:.4f}{fairness_note_2}
  Increase from original: {self.increase_2_percent:.2f}%
  Fairness change: {self.fairness_diff_2:+d}

Difference: {self.abs_difference_points:.2f} percentage points

Relative Significance: {self.relative_significance:.2f}
  (The difference is {self.relative_significance * 100:.1f}% of the smaller increase){differentiator_note}

Conclusion:
  - Spec {self.closer_to_original} is CLOSER to the original
  - Spec {self.more_permissive} is MORE PERMISSIVE
  - Primary differentiator: {self.primary_differentiator}
"""


def compute_metrics(formula: str, canonical_aps: List[str]) -> SpecificationMetrics:
    """
    Compute metrics for a single specification.
    """
    entropy = entropy_ltl(formula, canonical_aps=canonical_aps, debug=False)
    alphabet_size = 2 ** len(canonical_aps)
    branching_factor = alphabet_size ** entropy
    fairness_count = count_fairness_constraints(formula)
    fairness_formulas = extract_fairness_formulas(formula)

    return SpecificationMetrics(
        formula=formula,
        entropy=entropy,
        branching_factor=branching_factor,
        alphabet_size=alphabet_size,
        fairness_count=fairness_count,
        fairness_formulas=fairness_formulas
    )


def compare_specifications(
        phi_original: str,
        phi_1: str,
        phi_2: str,
        canonical_aps: List[str]
) -> ComparisonResult:
    """
    Compare two weakened specifications against an original.

    CRITICAL ASSUMPTION: Both phi_1 and phi_2 are WEAKENINGS of phi_original
    (i.e., more permissive than the original).

    Ranking logic:
    1. PRIMARY: Lower entropy increase = closer to original (smaller language)
    2. SECONDARY (when entropy tied): MORE fairness = closer to original
       - Because fairness constraints make the spec MORE RESTRICTIVE
       - This brings it back toward the restrictive original

    Args:
        phi_original: Original specification
        phi_1: First weakened specification
        phi_2: Second weakened specification
        canonical_aps: Canonical set of atomic propositions

    Returns:
        ComparisonResult with detailed percentage-based analysis
    """
    # Compute metrics for all three specs
    orig = compute_metrics(phi_original, canonical_aps)
    spec1 = compute_metrics(phi_1, canonical_aps)
    spec2 = compute_metrics(phi_2, canonical_aps)

    # Compute relative increases from original (entropy-based)
    increase_1 = (spec1.branching_factor - orig.branching_factor) / orig.branching_factor
    increase_2 = (spec2.branching_factor - orig.branching_factor) / orig.branching_factor

    increase_1_percent = increase_1 * 100
    increase_2_percent = increase_2 * 100

    # Fairness differences from original
    fairness_diff_1 = spec1.fairness_count - orig.fairness_count
    fairness_diff_2 = spec2.fairness_count - orig.fairness_count

    # Absolute difference in percentage points
    abs_diff = abs(increase_2_percent - increase_1_percent)

    # Relative significance
    if min(abs(increase_1), abs(increase_2)) > 0.001:
        significance = abs_diff / 100 / min(abs(increase_1), abs(increase_2))
    else:
        significance = float('inf') if abs_diff > 0.01 else 0.0

    # COMPARISON LOGIC (FIXED)
    # ========================

    ENTROPY_EPSILON = 0.5  # Consider entropies equal if within 0.5 percentage points

    if abs_diff < ENTROPY_EPSILON:
        # Entropy is tied - use fairness as tiebreaker
        primary_differentiator = "fairness"

        # CRITICAL FIX: For WEAKENINGS of a restrictive original:
        # - More fairness constraints = More restrictive = CLOSER to original
        # - Fewer fairness constraints = More permissive = FURTHER from original
        #
        # Example: G a (original, restrictive)
        #   Solution A: G(a | x)              - entropy +6%, fairness 0
        #   Solution B: (G F a) & G(a | x)    - entropy +6%, fairness 1
        #   → Solution B is CLOSER (fairness makes it more restrictive like original)

        # Closer = MORE fairness (more restrictive, closer to restrictive original)
        if spec1.fairness_count > spec2.fairness_count:
            closer = 1  # Spec 1 has MORE fairness = more restrictive = closer
        elif spec1.fairness_count < spec2.fairness_count:
            closer = 2  # Spec 2 has MORE fairness = more restrictive = closer
        else:
            # Same fairness count - they're equally close
            closer = 1  # Arbitrary choice

        # More permissive = FEWER fairness constraints (less restrictive)
        if spec1.fairness_count < spec2.fairness_count:
            more_permissive = 1
        elif spec1.fairness_count > spec2.fairness_count:
            more_permissive = 2
        else:
            more_permissive = 1  # Arbitrary choice

    else:
        # Entropy is different - use that as primary differentiator
        primary_differentiator = "entropy"

        # Closer = smaller entropy increase (less permissive)
        closer = 1 if abs(increase_1) < abs(increase_2) else 2

        # More permissive = larger entropy increase
        more_permissive = 1 if increase_1 > increase_2 else 2

    return ComparisonResult(
        original=orig,
        spec1=spec1,
        spec2=spec2,
        increase_1_percent=increase_1_percent,
        increase_2_percent=increase_2_percent,
        fairness_diff_1=fairness_diff_1,
        fairness_diff_2=fairness_diff_2,
        abs_difference_points=abs_diff,
        relative_significance=significance,
        closer_to_original=closer,
        more_permissive=more_permissive,
        primary_differentiator=primary_differentiator
    )


def compare_multiple_weakened_specs(
        phi_original: str,
        weakened_specs: List[str],
        canonical_aps: List[str]
) -> List[Tuple[str, float, int, float]]:
    """
    Compare multiple weakened specifications against an original.

    Returns them ranked by proximity to original:
    1. PRIMARY: Entropy increase (ascending = closer)
    2. SECONDARY: Fairness count (descending = more restrictive = closer)

    Args:
        phi_original: Original specification
        weakened_specs: List of weakened specifications
        canonical_aps: Canonical atomic propositions

    Returns:
        List of (formula, percentage_increase, fairness_diff, branching_factor) tuples,
        sorted by proximity to original
    """
    orig = compute_metrics(phi_original, canonical_aps)

    results = []
    for spec_formula in weakened_specs:
        spec = compute_metrics(spec_formula, canonical_aps)
        increase = (spec.branching_factor - orig.branching_factor) / orig.branching_factor
        increase_percent = increase * 100
        fairness_diff = spec.fairness_count - orig.fairness_count

        results.append((spec_formula, increase_percent, fairness_diff, spec.branching_factor, spec.fairness_count))

    # CRITICAL FIX: Sort by proximity to original
    # Primary: Entropy increase (ascending = smaller = closer)
    # Secondary: Fairness count (descending = more restrictive = closer to restrictive original)
    results.sort(key=lambda x: (abs(x[1]), -x[4]))  # Sort by (entropy_increase, -fairness_count)

    # Return without the fairness_count (keep original return signature)
    return [(formula, inc_pct, fair_diff, branch) for formula, inc_pct, fair_diff, branch, _ in results]


# ============================================================================
# TESTING FRAMEWORK
# ============================================================================

def test_fairness_tiebreaking_fixed():
    """Test the FIXED fairness tiebreaking logic."""
    print("=" * 70)
    print("TEST: Fixed Fairness Tiebreaking (Weakenings)")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    # Key test: Same entropy, different fairness
    # Original is RESTRICTIVE, both specs weaken it
    # The one with MORE fairness should be CLOSER
    result = compare_specifications(
        phi_original="G (a & !b)",
        phi_1="G a",  # Weakens safety, no fairness (more permissive)
        phi_2="(G a) & (G F b)",  # Weakens safety, adds fairness (less permissive)
        canonical_aps=canonical_aps
    )

    print("\nComparing specs with SAME entropy but DIFFERENT fairness:")
    print(result.summary())

    # Both should have same entropy increase
    assert abs(result.increase_1_percent - result.increase_2_percent) < 1.0, \
        "Entropy increases should be very similar"

    # Fairness should be different
    assert result.fairness_diff_1 == 0, "Spec 1 should have no fairness change"
    assert result.fairness_diff_2 == 1, "Spec 2 should have +1 fairness"

    # FIXED: Spec 2 should be closer (more fairness = more restrictive = closer to restrictive original)
    assert result.closer_to_original == 2, "Spec 2 should be closer (has fairness constraint)"

    # Spec 1 should be more permissive (no fairness restrictions)
    assert result.more_permissive == 1, "Spec 1 should be more permissive (no fairness)"

    # Should use fairness as differentiator
    assert result.primary_differentiator == "fairness", "Should use fairness to break tie"

    print("✓ FIXED fairness tiebreaking test passed!\n")


def run_all_tests():
    """Run the complete test suite."""
    print("\n" + "=" * 70)
    print("RUNNING COMPLETE TEST SUITE (WITH FIX)")
    print("=" * 70 + "\n")

    test_fairness_tiebreaking_fixed()

    print("=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()

    # Re-run the arbiter example with the fix
    print("\n\n" + "=" * 80)
    print("RE-RUNNING ARBITER EXAMPLE WITH FIX")
    print("=" * 80)

    canonical_aps = ['a', 'g1', 'g2', 'r1', 'r2']
    original = "G a"

    solutions = {
        0: "G F a",
        1: "G(a | (!g1 & !r1))",
        6: "G(a | (!g1 & !g2 & !r1 & !r2))",
        7: "(G F a) & G(a | (!g1 & !g2 & !r1 & !r2))"
    }

    all_solutions = list(solutions.values())
    ranked = compare_multiple_weakened_specs(original, all_solutions, canonical_aps)

    print(f"\n{'Rank':<6} {'Increase':<12} {'Fairness':<10} {'Branching':<12} {'Solution'}")
    print("-" * 80)

    for rank, (formula, increase_pct, fairness_diff, branching) in enumerate(ranked, 1):
        sol_id = next(k for k, v in solutions.items() if v == formula)
        fairness_str = f"{fairness_diff:+d}" if fairness_diff != 0 else "0"
        print(f"{rank:<6} {increase_pct:>10.2f}% {fairness_str:>8} {branching:>10.4f}  Solution {sol_id}")

    print("\n" + "=" * 80)
    print("EXPECTED RANKING (with fix):")
    print("  1. Solution 7 (6.25%, +1 fairness) ← CLOSEST (fairness makes it restrictive)")
    print("  2. Solution 6 (6.25%, 0 fairness)")
    print("  3. Solution 1 (25%, 0 fairness)")
    print("  4. Solution 0 (100%, +1 fairness) ← FURTHEST")
    print("=" * 80)