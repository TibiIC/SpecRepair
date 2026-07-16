from itertools import combinations


def all_minimum_hitting_sets(sets):
    universe = set().union(*sets)  # all elements appearing
    sets = list(sets)
    minimal_hitting_sets = []

    # Try hitting sets of increasing size
    for size in range(1, len(universe) + 1):
        if not minimal_hitting_sets:
            for combo in combinations(universe, size):
                candidate = set(combo)
                # Check if candidate hits all sets
                if all(candidate & s for s in sets):
                    minimal_hitting_sets.append(candidate)
        else:
            break
    return minimal_hitting_sets
