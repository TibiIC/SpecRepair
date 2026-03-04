# Let's see this numerically

import numpy as np

# L₁: Prefixes grow as 2^n (full binary tree)
def prefixes_L1(n):
    return 2**n

# L₂: Prefixes grow as 1.5^n * sin(n) (oscillating)
def prefixes_L2(n):
    return int((1.5**n) * (1 + 0.3 * np.sin(n)))

# Raw ratio
print("Raw ratios:")
for n in [5, 10, 15, 20, 25, 30]:
    ratio = prefixes_L1(n) / prefixes_L2(n)
    print(f"n={n:2d}: {ratio:.4f}")

# Entropy ratio
print("\nEntropy difference:")
for n in [5, 10, 15, 20, 25, 30]:
    h1 = np.log(prefixes_L1(n)) / n
    h2 = np.log(prefixes_L2(n)) / n
    diff = h1 - h2
    print(f"n={n:2d}: {diff:.4f}")