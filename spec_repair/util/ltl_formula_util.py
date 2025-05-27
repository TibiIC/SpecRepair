from py_ltl.formula import LTLFormula, Globally, Implies, AtomicProposition, Not, Top, Bottom, Eventually, And, Or


def is_dnf_implies_dnf(f: LTLFormula) -> bool:
    # Check if f is Implies(lhs, rhs) and lhs, rhs are DNF
    if not isinstance(f, Implies):
        return False
    return is_dnf(f.left) and is_dnf(f.right)


def is_gdnf(f: LTLFormula) -> bool:
    # Check if f is Globally(formula) and formula is DNF
    if not isinstance(f, Globally):
        return False
    return is_dnf(f.formula)


def is_g_dnf_implies_dnf(f: LTLFormula) -> bool:
    # Check if f is Globally(Implies(lhs, rhs)) and lhs, rhs are DNF
    if not isinstance(f, Globally):
        return False
    if not isinstance(f.formula, Implies):
        return False
    return is_dnf(f.formula.left) and is_dnf(f.formula.right)


def is_g_dnf_implies_fdnf(f: LTLFormula) -> bool:
    # Check if f is Globally(Implies(lhs, Eventually(rhs))) and lhs, rhs are DNF
    if not isinstance(f, Globally):
        return False
    if not isinstance(f.formula, Implies):
        return False
    if not is_dnf(f.formula.left):
        return False
    if not (isinstance(f.formula.right, Eventually) and is_dnf(f.formula.right.formula)):
        return False
    return True


def is_gf_dnf(f: LTLFormula) -> bool:
    # Check if f is Globally(Eventually(formula)) and formula is DNF
    if not isinstance(f, Globally):
        return False
    if not isinstance(f.formula, Eventually):
        return False
    return is_dnf(f.formula.formula)


def is_literal(f: LTLFormula) -> bool:
    # Literal = atomic prop or negation of atomic prop (maybe true/false too)
    if isinstance(f, AtomicProposition):
        return True
    if isinstance(f, Not) and isinstance(f.formula, AtomicProposition):
        return True
    if isinstance(f, Top) or isinstance(f, Bottom):
        return True
    return False


def is_conjunction_of_literals(f: LTLFormula) -> bool:
    if is_literal(f):
        return True
    if isinstance(f, And):
        return is_conjunction_of_literals(f.left) and is_conjunction_of_literals(f.right)
    return False


def is_disjunction_of_conjunctions(f: LTLFormula) -> bool:
    if is_conjunction_of_literals(f):
        return True
    if isinstance(f, Or):
        return is_disjunction_of_conjunctions(f.left) and is_disjunction_of_conjunctions(f.right)
    return False


def is_dnf(f: LTLFormula) -> bool:
    return is_disjunction_of_conjunctions(f)


def to_dnf(f: LTLFormula) -> LTLFormula:
    # Base cases
    if is_literal(f):
        return f
    if isinstance(f, Not):
        # Push negation inward (De Morgan)
        formula = f.formula
        if isinstance(formula, AtomicProposition) or isinstance(formula, Top) or isinstance(formula, Bottom):
            return f
        if isinstance(formula, Not):
            return to_dnf(formula.formula)
        if isinstance(formula, And):
            return to_dnf(Or(Not(formula.left), Not(formula.right)))
        if isinstance(formula, Or):
            return to_dnf(And(Not(formula.left), Not(formula.right)))
        raise NotImplementedError("Negation push-down for this formula not implemented")
    if isinstance(f, And):
        left = to_dnf(f.left)
        right = to_dnf(f.right)
        # Distribute OR over AND:
        if isinstance(left, Or):
            # (A or B) and C => (A and C) or (B and C)
            return to_dnf(Or(And(left.left, right), And(left.right, right)))
        if isinstance(right, Or):
            # A and (B or C) => (A and B) or (A and C)
            return to_dnf(Or(And(left, right.left), And(left, right.right)))
        return And(left, right)
    if isinstance(f, Or):
        left = to_dnf(f.left)
        right = to_dnf(f.right)
        return Or(left, right)
    if isinstance(f, Implies):
        return to_dnf(Or(Not(f.left), f.right))
    # Temporal operators and others we don't convert to DNF:
    # Return as-is or raise
    return f


def normalize_to_pattern(formula: LTLFormula) -> LTLFormula:
    if is_pattern(formula):
        return formula
    # Otherwise, we must convert
    if isinstance(formula, Globally):
        inner_formula = normalize_inner_formula_to_pattern(formula.formula)
        formula = Globally(inner_formula)
    else:
        formula = normalize_inner_formula_to_pattern(formula)
    # TODO: eventually this should become unnecessary, but for now we need to check again
    if is_pattern(formula):
        return formula
    # Otherwise, raise ValueError
    raise ValueError(f"Formula {formula} cannot be converted to G(F(f)) or G(f→g) form")


def is_pattern(formula: LTLFormula) -> bool:
    # If already matches one of the six, done
    pattern_checks = [
        is_dnf,
        is_dnf_implies_dnf,
        is_gdnf,
        is_g_dnf_implies_dnf,
        is_g_dnf_implies_fdnf,
        is_gf_dnf
    ]

    for check in pattern_checks:
        if check(formula):
            return True
    return False


def normalize_inner_formula_to_pattern(inner):
    if isinstance(inner, Implies):
        lhs_dnf = to_dnf(inner.left)
        rhs = inner.right
        # if rhs can be turned into Eventually(DNF), do so
        if isinstance(rhs, Eventually):
            rhs_dnf = to_dnf(rhs.formula)
            return Implies(lhs_dnf, Eventually(rhs_dnf))
        else:
            rhs_dnf = to_dnf(rhs)
            return Implies(lhs_dnf, rhs_dnf)
    elif isinstance(inner, Eventually):
        inner = inner.formula
        inner_dnf = to_dnf(inner)
        return Eventually(inner_dnf)
    else:
        # convert to GF(DNF)
        inner_dnf = to_dnf(inner)
        return inner_dnf
