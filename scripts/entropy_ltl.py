import spot
import math


def ltl_entropy(formula: str) -> float:
    """
    Compute an approximate Shannon entropy for an LTL formula using
    the automaton transitions, without using spot.word or accepting_word().
    """
    f = spot.formula(formula)
    aut = spot.translate(f, 'deterministic', 'complete')  # deterministic automaton

    n = aut.num_states()
    if n == 0:
        return 0.0

    # assign uniform probability for each outgoing transition from each state
    entropy = 0.0
    for s in range(n):
        succ = list(aut.out(s))
        k = len(succ)
        if k == 0:
            continue
        p = 1.0 / k
        # contribution of this state to entropy = sum(-p*log2(p) for each outgoing edge)
        entropy += k * (-p * math.log2(p))
    return entropy


# -----------------------------
# Testing
# -----------------------------
def test_ltl_entropy():
    formulas = [
        ("G(a)", "Globally a"),
        ("F(a)", "Eventually a"),
        ("G(a -> F(b))", "If a then eventually b"),
        ("G(F(a))", "a infinitely often"),
        ("a U b", "a until b"),
    ]

    for formula, desc in formulas:
        ent = ltl_entropy(formula)
        print(f"Formula: {formula} ({desc}), Entropy ~ {ent:.3f}")


if __name__ == "__main__":
    test_ltl_entropy()