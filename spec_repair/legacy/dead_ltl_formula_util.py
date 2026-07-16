from typing import List, Optional

from py_ltl.formula import LTLFormula, AtomicProposition, Not, Top, Bottom, Eventually, Globally, And, Or, Next, \
    Prev, Until

from spec_repair.util.ltl_formula_util import is_conjunction_of_literals, get_disjuncts_from_disjunction


def is_disjunction_of_conjunctions(f: LTLFormula) -> bool:
    if is_conjunction_of_literals(f):
        return True
    if isinstance(f, Or):
        return is_disjunction_of_conjunctions(f.left) and is_disjunction_of_conjunctions(f.right)
    return False


def is_dnf(f: LTLFormula) -> bool:
    return is_disjunction_of_conjunctions(f)


def get_conjuncts_from_conjunction(conjunction: Optional[LTLFormula]) -> List[LTLFormula]:
    if not conjunction:
        return []
    conjuncts = []
    while isinstance(conjunction, And):
        conjuncts.append(conjunction.right)
        conjunction = conjunction.left
    conjuncts.append(conjunction)
    conjuncts.reverse()
    return conjuncts


def skip_first_temp_op(this_formula: LTLFormula) -> LTLFormula:
    match this_formula:
        case Prev(formula=formula):
            return formula
        case Next(formula=formula):
            return formula
        case Eventually(formula=formula):
            return formula
        case Globally(formula=formula):
            return formula
        case AtomicProposition(name=name, value=value):
            return this_formula
        case Not(_):
            return this_formula
        case Or(_, _):
            return this_formula
        case And(_, _):
            return this_formula
        case Implies(_, _):
            return this_formula
        case Top():
            return this_formula
        case Bottom():
            return this_formula
        case Until(_, _):
            raise ValueError("Until operator not supported anywhere")
        case _:
            raise ValueError(f"Unsupported formula type {type(this_formula)}")


# see journal paper
def is_ilasp_compatible_dnf_structure(disjunction_of_conjunctions) -> bool:
    is_response = False
    if isinstance(disjunction_of_conjunctions, Eventually):
        disjunction_of_conjunctions = disjunction_of_conjunctions.formula
        is_response = True
    conjunctions = get_disjuncts_from_disjunction(disjunction_of_conjunctions)
    for conjunction in conjunctions:
        if isinstance(conjunction, Or):
            return False
        conjuncts = get_conjuncts_from_conjunction(conjunction)
        for conjunct in conjuncts:
            if isinstance(conjunct, Or) or isinstance(conjunct, And) or isinstance(conjunct, Implies):
                return False
            if isinstance(conjunct, Prev) or isinstance(conjunct, Next):
                if is_response:
                    return False
                conjunct = conjunct.formula
            if isinstance(conjunct, Not):
                conjunct = conjunct.formula
            if not isinstance(conjunct, AtomicProposition):
                return False
    return True
