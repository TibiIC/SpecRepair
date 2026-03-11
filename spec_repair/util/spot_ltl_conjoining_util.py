import spot
from spot import formula as F
from itertools import product as iproduct


def get_disjuncts(f):
    """Flatten an Or-formula into a list of its disjuncts."""
    if f.kindstr() == "Or":
        return list(f)
    return [f]


def get_conjuncts(f):
    """Flatten an And-formula into a list of its conjuncts."""
    if f.kindstr() == "And":
        return list(f)
    return [f]


def negate(f):
    return F.Not(f)


def find_common_antecedent_literals(clauses):
    """
    Each clause is a disjunction: !a1 & !a2 & ... | consequent_literals
    Find literals that appear negated in ALL clauses — these form the antecedent.
    e.g. '!h | m | Xp' and '!h | !p | Xp' both contain '!h', so 'h' is the antecedent.
    """
    # Get disjuncts of each clause
    clause_disjuncts = [set(str(d) for d in get_disjuncts(c)) for c in clauses]

    # Common disjuncts across all clauses
    common = clause_disjuncts[0].intersection(*clause_disjuncts[1:])

    # Among common disjuncts, pick the negated-AP ones as antecedent candidates
    # (i.e. things of the form !x where x is an AP or temporal formula)
    antecedent_strs = {d for d in common if d.startswith("!")}

    return antecedent_strs


def absorb_dnf_terms(dnf_terms):
    """
    Remove redundant terms from DNF using absorption:
    if term_j implies term_i, then term_i absorbs term_j (drop term_j).
    spot.contains(a, b) means b => a.
    """
    if len(dnf_terms) <= 1:
        return dnf_terms

    result = list(dnf_terms)
    changed = True
    while changed:
        changed = False
        for i in range(len(result)):
            for j in range(len(result)):
                if i == j:
                    continue
                # spot.contains(result[i], result[j]) means result[j] => result[i]
                # i.e. result[i] absorbs result[j], so drop result[j]
                if spot.contains(result[i], result[j]):
                    result.pop(j)
                    changed = True
                    break
            if changed:
                break
    return result


def cnf_to_dnf_formulas(conjuncts):
    clause_lists = [get_disjuncts(c) for c in conjuncts]

    dnf_terms = []
    for combo in iproduct(*clause_lists):
        term = F.And(list(combo))
        simplified = spot.simplify(term)
        if str(simplified) != "0":
            dnf_terms.append(simplified)

    if not dnf_terms:
        return F("0")

    # Apply absorption before building the Or
    dnf_terms = merge_complementary_terms(dnf_terms)
    dnf_terms = absorb_dnf_terms(dnf_terms)
    result = F.Or(dnf_terms) if len(dnf_terms) > 1 else dnf_terms[0]
    return spot.simplify(result)


def formulas_are_complementary(li_str, lj_str):
    """Check if two formula strings are logical negations of each other."""
    fi = F(li_str)
    fj = F(lj_str)
    # fi and fj are complementary if fi implies !fj and fj implies !fi
    # In SPOT: spot.contains(a, b) means b => a (b is contained in a)
    return (spot.contains(F.Not(fj), fi) and spot.contains(F.Not(fi), fj))


def merge_complementary_terms(dnf_terms):
    """
    Merge pairs of DNF terms that differ in exactly one complementary literal:
    (a & !b) | (a & b) -> a
    """
    result = list(dnf_terms)
    changed = True
    while changed:
        changed = False
        for i in range(len(result)):
            for j in range(i + 1, len(result)):
                ti = get_conjuncts(result[i])
                tj = get_conjuncts(result[j])
                if len(ti) != len(tj):
                    continue
                si = set(str(x) for x in ti)
                sj = set(str(x) for x in tj)
                only_in_i = si - sj
                only_in_j = sj - si
                if len(only_in_i) == 1 and len(only_in_j) == 1:
                    li = only_in_i.pop()
                    lj = only_in_j.pop()
                    if formulas_are_complementary(li, lj):
                        common = [x for x in ti if str(x) in sj]
                        merged = F.And(common) if len(common) > 1 else (common[0] if common else F("1"))
                        result.pop(j)
                        result.pop(i)
                        result.insert(i, spot.simplify(merged))
                        changed = True
                        break
            if changed:
                break
    return result


def rewrite_as_G_ant_to_dnf(formula_str):
    """
    Rewrite a conjunction of G-formulas into G(antecedent -> DNF_consequent) form.
    """
    original = spot.formula(formula_str)
    simplified = spot.simplify(original)
    print("SPOT simplified:", simplified)

    assert simplified.kindstr() == "G", f"Expected G(...), got: {simplified}"
    body = simplified[0]
    clauses = get_conjuncts(body)
    print("Clauses:", [str(c) for c in clauses])

    # --- Find common antecedent literals ---
    antecedent_strs = find_common_antecedent_literals(clauses)
    print("Common antecedent literals (negated):", antecedent_strs)

    # --- Strip antecedent from each clause to get consequent disjuncts ---
    consequent_clauses = []
    for clause in clauses:
        disjuncts = get_disjuncts(clause)
        remaining = [d for d in disjuncts if str(d) not in antecedent_strs]
        consequent_clauses.append(F.Or(remaining) if len(remaining) > 1 else remaining[0])

    print("Consequent clauses (still CNF):", [str(c) for c in consequent_clauses])

    # --- Convert consequent CNF -> DNF ---
    consequent_dnf = cnf_to_dnf_formulas(consequent_clauses)
    print("Consequent DNF:", consequent_dnf)

    # --- Reconstruct antecedent (strip the '!') ---
    antecedent_parts = [spot.simplify(F.Not(F(s))) for s in antecedent_strs]
    antecedent = F.And(antecedent_parts) if len(antecedent_parts) > 1 else antecedent_parts[0]

    # --- Build final formula ---
    # Simplify consequent in context of the implication first,
    # to collapse e.g. (a&!b)|(a&b) -> a, without letting SPOT
    # flatten the implication into a disjunction
    simplified_consequent = spot.simplify(
        spot.formula(f"({str(antecedent)}) -> ({str(consequent_dnf)})")
    )
    # simplified_consequent may itself be an Implies, or collapsed further
    # Re-extract if it's still an implication, otherwise use as-is
    if simplified_consequent.kindstr() == "Implies":
        consequent_dnf = simplified_consequent[1]
    else:
        # SPOT simplified the whole implication to something atomic - use consequent_dnf as-is
        # but try once more with direct simplification
        consequent_dnf = spot.simplify(consequent_dnf)

    result = F.G(F.Implies(antecedent, consequent_dnf))
    print("\nResult:", result)

    # --- Verify ---
    assert spot.are_equivalent(original, result), "ERROR: rewritten formula is not equivalent!"
    print("Equivalence verified ✓")
    return result
