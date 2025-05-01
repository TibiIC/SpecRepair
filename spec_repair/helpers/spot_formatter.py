from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, \
    Prev, Top, Bottom

class SpotFormatter(ILTLFormatter):
    def format(self, this_formula: LTLFormula) -> str:
        match this_formula:
            case AtomicProposition(name=name, value=True):
                return name
            case AtomicProposition(name=name, value=value):
                return f"{name} = {str(value).lower()}"
            case Not(formula=formula):
                return f"!({self.format(formula)})"
            case And(left=left, right=right):
                return f"({self.format(left)} && {self.format(right)})"
            case Or(left=left, right=right):
                return f"({self.format(left)} || {self.format(right)})"
            case Implies(left=left, right=right):
                return f"({self.format(left)} -> {self.format(right)})"
            case Next(formula=formula):
                return f"X({self.format(formula)})"
            case Prev(formula=formula):
                return f"Y({self.format(formula)})"  # Spot uses 'Y' for previous
            case Eventually(formula=formula):
                return f"F({self.format(formula)})"
            case Globally(formula=formula):
                return f"G({self.format(formula)})"
            case Top():
                return "true"
            case Bottom():
                return "false"
            case _:
                raise NotImplementedError(f"Spot formatting not implemented for: {type(this_formula)}")