from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, Prev, Top, Bottom

class SpectraFormulaFormatter(ILTLFormatter):
    def format(self, formula: LTLFormula) -> str:
        match formula:
            case AtomicProposition(name=name, value=value):
                return f"{name}={str(value).lower()}"
            case Not(formula=formula):
                return f"!({self.format(formula)})"
            case And(left=lhs, right=rhs):
                return f"({self.format(lhs)}&{self.format(rhs)})"
            case Or(left=lhs, right=rhs):
                return f"({self.format(lhs)}|{self.format(rhs)})"
            case Implies(left=lhs, right=rhs):
                return f"({self.format(lhs)}->{self.format(rhs)})"
            case Next(formula=formula):
                return f"next({self.format(formula)})"
            case Prev(formula=formula):
                return f"prev({self.format(formula)})"
            case Eventually(formula=formula):
                return f"F({self.format(formula)})"
            case Globally(formula=formula):
                if isinstance(formula, Eventually):
                    return f"G{self.format(formula)}"
                return f"G({self.format(formula)})"
            case Top():
                return "true"
            case Bottom():
                return "false"
            case _:
                raise NotImplementedError(f"Formatter not implemented for: {type(formula)}")