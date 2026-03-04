from entropy_difference import *

# Define the canonical alphabet
canonical_aps = ['a', 'g1', 'g2', 'r1', 'r2']

# Original and solutions
original = "G a"

solutions = {
    0: "G F a",
    1: "G(a | (!g1 & !r1))",
    2: "G(a | (!g1 & !r2))",
    3: "G(a | (!g1 & !g2))",
    4: "G(a | (!g2 & !r1))",
    5: "G(a | (!g2 & !r2))",
    6: "G(a | (!g1 & !g2 & !r1 & !r2))",
    7: "(G F a) & G(a | (!g1 & !g2 & !r1 & !r2))"
}

print("="*80)
print("COMPARING REPAIR SOLUTIONS")
print("="*80)
print(f"\nOriginal: {original}")
print(f"Canonical APs: {canonical_aps}")
print(f"Alphabet size: {2**len(canonical_aps)} = 32 letters\n")

# Compute metrics for all solutions
print("="*80)
print("INDIVIDUAL METRICS")
print("="*80)

original_metrics = compute_metrics(original, canonical_aps)
print(f"\nOriginal: {original}")
print(original_metrics)

solution_metrics = {}
for sol_id, sol_formula in solutions.items():
    metrics = compute_metrics(sol_formula, canonical_aps)
    solution_metrics[sol_id] = metrics
    print(f"\nSolution {sol_id}: {sol_formula}")
    print(metrics)

# Rank all solutions
print("\n" + "="*80)
print("RANKING ALL SOLUTIONS BY PROXIMITY TO ORIGINAL")
print("="*80)

all_solutions = list(solutions.values())
ranked = compare_multiple_weakened_specs(original, all_solutions, canonical_aps)

print(f"\n{'Rank':<6} {'Increase':<12} {'Fairness':<10} {'Branching':<12} {'Solution'}")
print("-" * 95)

for rank, (formula, increase_pct, fairness_diff, branching) in enumerate(ranked, 1):
    # Find which solution this is
    sol_id = next(k for k, v in solutions.items() if v == formula)
    fairness_str = f"{fairness_diff:+d}" if fairness_diff != 0 else "0"
    print(f"{rank:<6} {increase_pct:>10.2f}% {fairness_str:>8} {branching:>10.4f}  Solution {sol_id}")

# Detailed pairwise comparisons
print("\n" + "="*80)
print("DETAILED PAIRWISE COMPARISONS")
print("="*80)

# Compare Solutions 1-5 (similar structure)
print("\n" + "-"*80)
print("Group 1: Solutions 1-5 (G(a | !xi & !yi) patterns)")
print("-"*80)

for i in range(1, 6):
    result = compare_specifications(original, solutions[1], solutions[i], canonical_aps)
    if i > 1:
        print(f"\nSolution 1 vs Solution {i}:")
        print(f"  Entropy difference: {result.abs_difference_points:.4f} points")
        print(f"  Closer to original: Solution {result.closer_to_original}")
        print(f"  Primary differentiator: {result.primary_differentiator}")

# Compare Solution 6 vs 7 (with and without fairness)
print("\n" + "-"*80)
print("Group 2: Solution 6 vs 7 (With/Without Fairness)")
print("-"*80)

result_6_7 = compare_specifications(original, solutions[6], solutions[7], canonical_aps)
print(result_6_7.summary())

# Compare Solution 0 (GF a) vs others
print("\n" + "-"*80)
print("Solution 0 (G F a) vs Best Safety-only Solution")
print("-"*80)

# Find best safety-only solution (1-6)
best_safety_id = min(range(1, 7),
                     key=lambda i: (abs(solution_metrics[i].branching_factor - original_metrics.branching_factor),
                                   abs(solution_metrics[i].fairness_count - original_metrics.fairness_count)))

result_0_best = compare_specifications(original, solutions[0], solutions[best_safety_id], canonical_aps)
print(f"\nSolution 0 (G F a) vs Solution {best_safety_id} ({solutions[best_safety_id]}):")
print(result_0_best.summary())

# Analysis summary
print("\n" + "="*80)
print("ANALYSIS SUMMARY")
print("="*80)

print(f"""
Original Specification: {original}
  - Branching factor: {original_metrics.branching_factor:.4f}
  - Fairness constraints: {original_metrics.fairness_count}

Key Findings:

1. SOLUTION GROUPS:
   - Solutions 1-5: Similar safety relaxations (G(a | !xi & !yi))
   - Solution 6: Maximum safety relaxation (all variables)
   - Solution 0: Pure liveness (G F a)
   - Solution 7: Hybrid (safety + liveness)

2. CLOSEST TO ORIGINAL:
   - Solution {ranked[0][0]} is closest
   - Increase: {ranked[0][1]:.2f}%
   - This represents the MINIMAL WEAKENING

3. MOST PERMISSIVE:
   - Solution {ranked[-1][0]} is most permissive
   - Increase: {ranked[-1][1]:.2f}%
   - This represents the MAXIMAL WEAKENING

4. FAIRNESS IMPACT:
   - Solutions with G F constraints: {[k for k, v in solution_metrics.items() if v.fairness_count > 0]}
   - These add liveness requirements which constrain infinite behavior
   - Even with same entropy, fairness makes specs LESS permissive
""")

# Recommendation based on metrics
print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

print(f"""
If you want the MINIMAL change from original:
  → Choose: Solution {[k for k, v in solutions.items() if v == ranked[0][0]][0]}
  → This adds only {ranked[0][1]:.1f}% more behavior

If you want to balance safety and liveness:
  → Consider: Solution 7 (combines safety relaxation + fairness)
  → Note: Fairness constraint makes it LESS permissive than pure safety

If solutions 1-5 have similar metrics:
  → The choice depends on SEMANTIC considerations (which variables matter)
  → All have similar quantitative impact: ~{ranked[0][1]:.0f}% increase
""")