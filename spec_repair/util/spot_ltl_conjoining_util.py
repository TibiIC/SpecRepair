import re
import spot
from spot import formula as F
from itertools import product as iproduct
from enum import Enum, auto


# ---------------------------------------------------------------------------
# Formula classification
# ---------------------------------------------------------------------------

class FormulaType(Enum):
    INVARIANT = auto()   # G(DNF -> DNF)
    JUSTICE   = auto()   # GF(...)
    RESPONSE  = auto()   # G(... -> F(...))
    OTHER     = auto()


def classify_formula(formula_str):
    """
    Classify a single (non-conjoined) LTL formula string.
    Encodes PREV before parsing so SPOT can handle it.
    """
    encoded = encode_prev(formula_str)
    f = spot.formula(encoded)

    if f.kindstr() != "G":
        return FormulaType.OTHER

    body = f[0]

    # GF(...) — Justice
    if body.kindstr() == "F":
        return FormulaType.JUSTICE

    # G(... -> F(...)) — Response
    if body.kindstr() == "Implies" and body[1].kindstr() == "F":
        return FormulaType.RESPONSE

    # G(... -> ...) where neither side is F — Invariant candidate
    if body.kindstr() == "Implies":
        antecedent = body[0]
        consequent = body[1]
        _validate_invariant_structure(antecedent, consequent, formula_str)
        return FormulaType.INVARIANT

    return FormulaType.OTHER


def _validate_invariant_structure(antecedent, consequent, original_str):
    """
    Validate that:
    - antecedent contains no X(...) operators
    - consequent contains no PREV(...) — encoded as prev_* atoms
    Raises ValueError if violated.
    """
    def contains_X(f):
        if f.kindstr() == "X":
            return True
        return any(contains_X(c) for c in f)

    def contains_prev(f):
        if f.kindstr() == "ap" and str(f).startswith("prev_"):
            return True
        return any(contains_prev(c) for c in f)

    if contains_X(antecedent):
        raise ValueError(
            f"Invalid invariant: antecedent contains X(...) operator in '{original_str}'"
        )
    if contains_prev(consequent):
        raise ValueError(
            f"Invalid invariant: consequent contains PREV(...) in '{original_str}'"
        )


# ---------------------------------------------------------------------------
# PREV <-> opaque atom translation
# ---------------------------------------------------------------------------

def _prev_to_atom(match):
    inner = match.group(1).strip()
    if inner.startswith("!"):
        return f"prev_not{inner[1:]}"
    return f"prev_{inner}"


def encode_prev(formula_str):
    return re.sub(r'PREV\((!?\w+)\)', _prev_to_atom, formula_str)


def decode_prev(formula_str):
    result = re.sub(r'\bprev_not(\w+)\b', lambda m: f"PREV(!{m.group(1)})", formula_str)
    result = re.sub(r'\bprev_(\w+)\b',    lambda m: f"PREV({m.group(1)})",  result)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_disjuncts(f):
    if f.kindstr() == "Or":
        return list(f)
    return [f]


def get_conjuncts(f):
    if f.kindstr() == "And":
        return list(f)
    return [f]


def find_common_antecedent_literals(clauses):
    clause_disjuncts = [set(str(d) for d in get_disjuncts(c)) for c in clauses]
    common = clause_disjuncts[0].intersection(*clause_disjuncts[1:])
    return {d for d in common if d.startswith("!")}


def absorb_dnf_terms(dnf_terms):
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
                if spot.contains(result[i], result[j]):
                    result.pop(j)
                    changed = True
                    break
            if changed:
                break
    return result


def merge_complementary_terms(dnf_terms):
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
                    fi, fj = F(li), F(lj)
                    if spot.contains(F.Not(fj), fi) and spot.contains(F.Not(fi), fj):
                        common = [x for x in ti if str(x) in sj]
                        merged = (F.And(common) if len(common) > 1
                                  else (common[0] if common else F("1")))
                        result.pop(j)
                        result.pop(i)
                        result.insert(i, spot.simplify(merged))
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
    dnf_terms = merge_complementary_terms(dnf_terms)
    dnf_terms = absorb_dnf_terms(dnf_terms)
    result = F.Or(dnf_terms) if len(dnf_terms) > 1 else dnf_terms[0]
    return spot.simplify(result)


# ---------------------------------------------------------------------------
# Core rewriter (invariant + invariant only)
# ---------------------------------------------------------------------------

def _rewrite_invariant_pair(formula_str):
    """Internal: rewrite a conjunction of exactly two invariants."""
    encoded_str = encode_prev(formula_str)
    original = spot.formula(encoded_str)
    simplified = spot.simplify(original)

    assert simplified.kindstr() == "G", f"Expected G(...), got: {simplified}"
    body = simplified[0]
    clauses = get_conjuncts(body)

    antecedent_strs = find_common_antecedent_literals(clauses)

    consequent_clauses = []
    for clause in clauses:
        disjuncts = get_disjuncts(clause)
        remaining = [d for d in disjuncts if str(d) not in antecedent_strs]
        consequent_clauses.append(
            F.Or(remaining) if len(remaining) > 1 else remaining[0]
        )

    consequent_dnf = cnf_to_dnf_formulas(consequent_clauses)

    antecedent_parts = [spot.simplify(F.Not(F(s))) for s in antecedent_strs]
    antecedent = (F.And(antecedent_parts) if len(antecedent_parts) > 1
                  else antecedent_parts[0])

    simplified_impl = spot.simplify(
        spot.formula(f"({antecedent}) -> ({consequent_dnf})")
    )
    if simplified_impl.kindstr() == "Implies":
        consequent_dnf = simplified_impl[1]
    else:
        consequent_dnf = spot.simplify(consequent_dnf)

    result = F.G(F.Implies(antecedent, consequent_dnf))

    assert spot.are_equivalent(original, result), \
        "ERROR: rewritten formula is not equivalent!"

    return decode_prev(str(result))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def conjoin_and_simplify(formula_a, formula_b):
    """
    Conjoin two LTL formulas and simplify where possible.

    Rules:
    - Invariant + Invariant  -> rewrite as G(ADNF -> CDNF)
    - Invariant + Justice    -> return unchanged as conjunction
    - Invariant + Response   -> return unchanged as conjunction
    - Justice   + Justice    -> return unchanged as conjunction
    - Justice   + Response   -> return unchanged as conjunction
    - Response  + Response   -> rewrite as G(ADNF -> F(CDNF))  [not yet implemented]
    - Anything  + OTHER      -> raise ValueError

    Returns a string.
    """
    type_a = classify_formula(formula_a)
    type_b = classify_formula(formula_b)

    # Reject unclassifiable formulas
    if type_a == FormulaType.OTHER:
        raise ValueError(
            f"Formula A is not a recognised type (Invariant/Justice/Response): '{formula_a}'"
        )
    if type_b == FormulaType.OTHER:
        raise ValueError(
            f"Formula B is not a recognised type (Invariant/Justice/Response): '{formula_b}'"
        )

    # Invariant + Invariant: attempt merge
    if type_a == FormulaType.INVARIANT and type_b == FormulaType.INVARIANT:
        return _rewrite_invariant_pair(f"({formula_a}) && ({formula_b})")

    # All other combinations: return unchanged
    return f"{formula_a} & {formula_b}"

def rewrite_as_G_ant_to_dnf(formula_str):
    """
    Public wrapper around _rewrite_invariant_pair for direct use and testing.
    Accepts a conjunction string of invariant formulas.
    """
    return _rewrite_invariant_pair(formula_str)