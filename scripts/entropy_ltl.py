import spot
import numpy as np


def language_entropy_rate(formula: str, max_len: int = 20):
    """
    Compute approximate Shannon entropy rate h(L) of an LTL formula.

    Args:
        formula: LTL formula string
        max_len: maximum length of sequences to enumerate (approximation)
    Returns:
        entropy_rate: approximate bits per step
    """
    f = spot.formula(formula)
    aut = spot.translate(f, 'complete')

    n_states = aut.num_states()
    # Initialize DP table: C[k, s] = # words of length k from state s
    C = np.zeros((max_len + 1, n_states))

    # Length 0 words: count as 1
    C[0, :] = 1

    # Build transition list
    succ = [[] for _ in range(n_states)]
    for s in range(n_states):
        for t in aut.out(s):
            succ[s].append(t.dst)

    # DP recurrence
    for k in range(max_len):
        for s in range(n_states):
            for t in succ[s]:
                C[k + 1, s] += C[k, t]

    # Sum words from initial state(s)
    init_state = aut.get_init_state_number()
    W_le_n = sum(C[k, init_state] for k in range(1, max_len + 1))

    # Entropy rate approximation
    h = np.log2(W_le_n) / max_len
    return h


# -----------------------------
# Testing
# -----------------------------
def test_ltl_language_entropy_rate():
    formulas = [
        ("G(a)", "Globally a"),
        ("F(a)", "Eventually a"),
        ("G(a -> F(b))", "If a then eventually b"),
        ("G(F(a))", "a infinitely often"),
        ("a U b", "a until b"),
    ]

    print("Shannon entropy rate of LTL formulas (bits per step):")
    for formula, desc in formulas:
        h = language_entropy_rate(formula)
        print(f"Formula: {formula} ({desc}), Entropy rate ~ {h:.3f}")


if __name__ == "__main__":
    test_ltl_language_entropy_rate()