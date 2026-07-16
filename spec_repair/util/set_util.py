from itertools import combinations


def _candidate_hitting_sets(sets):
    """
    Yield every hitting-set candidate for `sets`, in increasing size order.
    """
    universe = set().union(*sets)  # all elements appearing
    sets = list(sets)
    for size in range(1, len(universe) + 1):
        for combo in combinations(universe, size):
            candidate = set(combo)
            if is_hitting_set(candidate, sets):
                yield candidate


def first_minimal_hitting_set(sets):
    """
    Find the first minimal hitting set for a family of sets.
    `sets` is an iterable of sets (each containing hashable elements).
    Returns a set which hits all input sets, minimal in size.
    """
    for candidate in _candidate_hitting_sets(sets):
        return candidate
    return None  # no hitting set found (should not happen unless input is empty)


def is_hitting_set(candidate, sets):
    return all(candidate & s for s in sets)


def is_minimal(candidate, sets):
    # remove one element at a time and check if still hitting
    for elem in candidate:
        reduced = candidate - {elem}
        if reduced and is_hitting_set(reduced, sets):
            return False
    return True


def all_minimal_hitting_sets(sets):
    sets = list(sets)
    minimal_hitting_sets = []
    for candidate in _candidate_hitting_sets(sets):
        if is_minimal(candidate, sets) and candidate not in minimal_hitting_sets:
            minimal_hitting_sets.append(candidate)
    return minimal_hitting_sets
