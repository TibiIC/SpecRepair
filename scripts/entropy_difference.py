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

    Args:
        formula_str: LTL formula string

    Returns:
        Number of G F patterns in the formula
    """
    try:
        f = spot.formula(formula_str)
    except:
        return 0

    fairness_count = 0

    def count_gf(formula_node):
        nonlocal fairness_count

        if formula_node.kind() == spot.op_G:
            # Check if any child is F (making this a G F pattern)
            for child in formula_node:
                if child.kind() == spot.op_F:
                    fairness_count += 1
                # Continue recursing into other children
                count_gf(child)
        else:
            # Recurse into all children
            for child in formula_node:
                count_gf(child)

    count_gf(f)
    return fairness_count


def extract_fairness_formulas(formula_str: str) -> List[str]:
    """
    Extract the actual fairness constraint subformulas.

    Args:
        formula_str: LTL formula string

    Returns:
        List of fairness constraint strings (the ψ in G F ψ)
    """
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
            differentiator_note = "\n  ⚠️  Note: Entropy is equal, comparison based on fairness constraints"

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

    Args:
        formula: LTL formula string
        canonical_aps: Canonical set of atomic propositions

    Returns:
        SpecificationMetrics with entropy, branching factor, and fairness count
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

    Uses LEXICOGRAPHIC ordering:
    1. First by branching factor (entropy) - measures per-step freedom
    2. Then by fairness constraints (if entropy is equal) - measures liveness restrictions

    This answers: "Which weakened spec is better (closer to original)?"

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
    # Negative = removed fairness constraints (more permissive)
    # Positive = added fairness constraints (less permissive)
    fairness_diff_1 = spec1.fairness_count - orig.fairness_count
    fairness_diff_2 = spec2.fairness_count - orig.fairness_count

    # Absolute difference in percentage points
    abs_diff = abs(increase_2_percent - increase_1_percent)

    # Relative significance
    if min(abs(increase_1), abs(increase_2)) > 0.001:
        significance = abs_diff / 100 / min(abs(increase_1), abs(increase_2))
    else:
        # If increases are very small, difference is always significant
        significance = float('inf') if abs_diff > 0.01 else 0.0

    # LEXICOGRAPHIC COMPARISON
    # First try to distinguish by entropy, then by fairness

    ENTROPY_EPSILON = 0.5  # Consider entropies equal if within 0.5 percentage points

    if abs_diff < ENTROPY_EPSILON:
        # Entropy is essentially equal - use fairness as tiebreaker
        primary_differentiator = "fairness"

        # For fairness: FEWER constraints = MORE permissive
        # (removing G F makes the spec weaker/more permissive)
        abs_fairness_diff_1 = abs(fairness_diff_1)
        abs_fairness_diff_2 = abs(fairness_diff_2)

        if abs_fairness_diff_1 < abs_fairness_diff_2:
            closer = 1  # Spec 1 changed fairness less
        elif abs_fairness_diff_1 > abs_fairness_diff_2:
            closer = 2  # Spec 2 changed fairness less
        else:
            # Same fairness change, pick arbitrarily
            closer = 1

        # More permissive = removed more fairness OR added less fairness
        if fairness_diff_1 < fairness_diff_2:
            more_permissive = 1  # Spec 1 has fewer fairness constraints
        elif fairness_diff_1 > fairness_diff_2:
            more_permissive = 2  # Spec 2 has fewer fairness constraints
        else:
            # Same fairness, use entropy
            more_permissive = 1 if increase_1 > increase_2 else 2
    else:
        # Entropy is different - use that as primary differentiator
        primary_differentiator = "entropy"

        # Closer = smaller change in entropy
        closer = 1 if abs(increase_1) < abs(increase_2) else 2

        # More permissive = larger increase in entropy
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

    Returns them ranked by proximity to original (lexicographic: entropy, then fairness).

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

        results.append((spec_formula, increase_percent, fairness_diff, spec.branching_factor))

    # Sort lexicographically: first by entropy increase, then by fairness change
    results.sort(key=lambda x: (abs(x[1]), abs(x[2])))

    return results


# ============================================================================
# TESTING FRAMEWORK
# ============================================================================

def test_fairness_counting():
    """Test that fairness constraint counting works correctly."""
    print("=" * 70)
    print("TEST: Fairness Constraint Counting")
    print("=" * 70)

    test_cases = [
        ("G a", 0, "No fairness"),
        ("G F a", 1, "One fairness constraint"),
        ("(G F a) & (G F b)", 2, "Two fairness constraints"),
        ("G (a -> F b)", 0, "Response pattern, not G F"),
        ("(G a) & (G F b)", 1, "Invariant + one fairness"),
        ("(G F a) & (G F b) & (G F c)", 3, "Three fairness constraints"),
    ]

    print("\nTesting fairness counting:")
    for formula, expected_count, description in test_cases:
        count = count_fairness_constraints(formula)
        status = "✓" if count == expected_count else "✗"
        print(f"{status} {formula:<30} → {count} fairness ({description})")
        assert count == expected_count, f"Expected {expected_count}, got {count}"

    print("\n✓ All fairness counting tests passed!\n")


def test_basic_metrics():
    """Test that basic metrics are computed correctly."""
    print("=" * 70)
    print("TEST: Basic Metrics Computation")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    # Test 1: Most restrictive spec
    metrics = compute_metrics("G a", canonical_aps)
    print(f"\nTest 1: G a")
    print(metrics)
    assert metrics.entropy >= 0, "Entropy should be non-negative"
    assert metrics.branching_factor >= 1, "Branching factor should be >= 1"
    assert metrics.fairness_count == 0, "G a has no fairness constraints"

    # Test 2: With fairness
    metrics2 = compute_metrics("G F a", canonical_aps)
    print(f"\nTest 2: G F a")
    print(metrics2)
    assert metrics2.fairness_count == 1, "G F a has one fairness constraint"

    # Test 3: Multiple fairness
    metrics3 = compute_metrics("(G F a) & (G F b)", canonical_aps)
    print(f"\nTest 3: (G F a) & (G F b)")
    print(metrics3)
    assert metrics3.fairness_count == 2, "Should have two fairness constraints"

    print("\n✓ All basic metric tests passed!\n")


def test_fairness_tiebreaking():
    """Test that fairness correctly breaks ties when entropy is equal."""
    print("=" * 70)
    print("TEST: Fairness Tiebreaking")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    # Key test: Same entropy, different fairness
    result = compare_specifications(
        phi_original="G (a & !b)",
        phi_1="G a",  # No fairness added
        phi_2="(G a) & (G F b)",  # Fairness added
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

    # Spec 1 should be closer (fewer constraints)
    assert result.closer_to_original == 1, "Spec 1 should be closer (no fairness added)"

    # Spec 1 should be more permissive (no fairness restrictions)
    assert result.more_permissive == 1, "Spec 1 should be more permissive (no fairness)"

    # Should use fairness as differentiator
    assert result.primary_differentiator == "fairness", "Should use fairness to break tie"

    print("✓ Fairness tiebreaking test passed!\n")


def test_pairwise_comparison():
    """Test comparing two specs against an original."""
    print("=" * 70)
    print("TEST: Pairwise Comparison")
    print("=" * 70)

    canonical_aps = ['a', 'b']

    # Scenario 1: Different entropy
    result1 = compare_specifications(
        phi_original="G (a & !b)",
        phi_1="G a",
        phi_2="G (a | b)",
        canonical_aps=canonical_aps
    )

    print("\nScenario 1: Different entropy")
    print(result1.summary())

    assert result1.increase_2_percent > result1.increase_1_percent, \
        "Spec 2 should be more permissive"
    assert result1.closer_to_original == 1, "Spec 1 should be closer"
    assert result1.primary_differentiator == "entropy", "Should use entropy"

    print("✓ Pairwise comparison tests passed!\n")


def test_multiple_spec_ranking():
    """Test ranking multiple weakened specifications."""
    print("=" * 70)
    print("TEST: Multiple Specification Ranking")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    original = "G (a & !b & !c)"

    weakened = [
        "G a",  # Allow b,c to vary
        "G (a | b)",  # Allow more
        "G (a & !b)",  # Only allow c to vary
        "G F a",  # Liveness
        "(G a) & (G F b)",  # Same entropy as "G a" but with fairness
        "G (a | b | c)",  # Very permissive
    ]

    ranked = compare_multiple_weakened_specs(original, weakened, canonical_aps)

    print(f"\nOriginal: {original}")
    print("\nWeakened specifications ranked by proximity to original:")
    print(f"{'Rank':<6} {'Increase':<12} {'Fairness':<10} {'Branching':<12} {'Formula'}")
    print("-" * 85)

    for rank, (formula, increase_pct, fairness_diff, branching) in enumerate(ranked, 1):
        fairness_str = f"{fairness_diff:+d}" if fairness_diff != 0 else "0"
        print(f"{rank:<6} {increase_pct:>10.2f}% {fairness_str:>8} {branching:>10.4f}  {formula}")

    # Verify "G a" comes before "(G a) & (G F b)" due to fairness
    ga_idx = next(i for i, (f, _, _, _) in enumerate(ranked) if f == "G a")
    ga_gfb_idx = next(i for i, (f, _, _, _) in enumerate(ranked) if f == "(G a) & (G F b)")

    assert ga_idx < ga_gfb_idx, \
        "'G a' should rank before '(G a) & (G F b)' (same entropy, less fairness)"

    print("\n✓ Multiple spec ranking test passed!\n")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("=" * 70)
    print("TEST: Edge Cases")
    print("=" * 70)

    canonical_aps = ['a', 'b']

    # Edge case 1: Comparing identical specs
    result = compare_specifications(
        phi_original="G a",
        phi_1="G a",
        phi_2="G a",
        canonical_aps=canonical_aps
    )

    print("\nEdge Case 1: Identical specifications")
    print(f"Increase 1: {result.increase_1_percent:.4f}%")
    print(f"Increase 2: {result.increase_2_percent:.4f}%")
    print(f"Difference: {result.abs_difference_points:.4f} points")

    assert abs(result.increase_1_percent) < 0.01, "Identical spec should have ~0% increase"
    assert abs(result.abs_difference_points) < 0.01, "Difference should be ~0"

    # Edge case 2: Adding vs removing fairness
    result2 = compare_specifications(
        phi_original="G F a",
        phi_1="G a",  # Removed fairness (more permissive)
        phi_2="(G F a) & (G F b)",  # Added fairness (less permissive)
        canonical_aps=canonical_aps
    )

    print("\nEdge Case 2: Removing vs adding fairness")
    print(f"Spec 1 fairness change: {result2.fairness_diff_1}")
    print(f"Spec 2 fairness change: {result2.fairness_diff_2}")

    assert result2.fairness_diff_1 == -1, "Spec 1 should have removed 1 fairness"
    assert result2.fairness_diff_2 == +1, "Spec 2 should have added 1 fairness"

    print("\n✓ Edge case tests passed!\n")


def run_all_tests():
    """Run the complete test suite."""
    print("\n" + "=" * 70)
    print("RUNNING COMPLETE TEST SUITE")
    print("=" * 70 + "\n")

    test_fairness_counting()
    test_basic_metrics()
    test_fairness_tiebreaking()
    test_pairwise_comparison()
    test_multiple_spec_ranking()
    test_edge_cases()

    print("=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Demonstrate the framework with realistic examples."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Practical Usage")
    print("=" * 70)

    canonical_aps = ['a', 'b', 'c']

    # Example 1: Comparing two repair candidates
    print("\nExample 1: Same entropy, different fairness")
    print("-" * 70)

    result = compare_specifications(
        phi_original="G (a & b)",
        phi_1="G a",  # Relax b requirement
        phi_2="(G a) & (G F b)",  # Relax b but add fairness
        canonical_aps=canonical_aps
    )

    print(result.summary())

    # Example 2: Ranking multiple candidates
    print("\nExample 2: Ranking multiple weakening candidates")
    print("-" * 70)

    original = "G (a & !b)"
    candidates = [
        "G a",
        "G (a | b)",
        "G F a",
        "(G a) & (G F b)",
        "(G a) & (G F c)"
    ]

    ranked = compare_multiple_weakened_specs(original, candidates, canonical_aps)

    print(f"\nOriginal spec: {original}")
    print("\nCandidates ranked by proximity to original:\n")
    print(f"{'Rank':<6} {'Increase':<12} {'Fairness':<10} {'Formula'}")
    print("-" * 60)
    for rank, (formula, increase_pct, fairness_diff, _) in enumerate(ranked, 1):
        fairness_str = f"{fairness_diff:+d}" if fairness_diff != 0 else "0"
        print(f"{rank:<6} {increase_pct:>10.2f}% {fairness_str:>8}  {formula}")


if __name__ == "__main__":
    run_all_tests()
    example_usage()