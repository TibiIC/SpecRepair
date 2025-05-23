from py_ltl.formula import LTLFormula, Globally, Implies, AtomicProposition, Not, Top, Bottom, Eventually, And, Or


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
    # Temporal operators and others we don't convert to DNF:
    # Return as-is or raise
    return f


def normalize_to_pattern(formula: LTLFormula) -> LTLFormula:
    # If already matches one of the three, done
    if is_g_dnf_implies_dnf(formula):
        return formula
    if is_g_dnf_implies_fdnf(formula):
        return formula
    if is_gf_dnf(formula):
        return formula

    # Otherwise, we must convert

    # Example heuristic:
    # If formula is of form G(...), transform inside
    if isinstance(formula, Globally):
        inner = formula.formula
        if isinstance(inner, Implies):
            lhs_dnf = to_dnf(inner.left)
            rhs = inner.right
            # if rhs can be turned into Eventually(DNF), do so
            if isinstance(rhs, Eventually):
                rhs_dnf = to_dnf(rhs.formula)
                return Globally(Implies(lhs_dnf, Eventually(rhs_dnf)))
            else:
                rhs_dnf = to_dnf(rhs)
                return Globally(Implies(lhs_dnf, rhs_dnf))
        else:
            # convert to GF(DNF)
            inner_dnf = to_dnf(inner)
            return Globally(Eventually(inner_dnf))

    # Otherwise just convert whole formula to GF(DNF)
    return Globally(Eventually(to_dnf(formula)))