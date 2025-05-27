from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, \
    Prev, Top, Bottom


class SpotFormatter(ILTLFormatter):
    def format(self, this_formula: LTLFormula, shift: int = 0) -> str:
        match this_formula:
            case AtomicProposition(name=name, value=True):
                return self._apply_shift(name, shift)
            case AtomicProposition(name=name, value=False):
                return self._apply_shift(f"!{name}", shift)
            case Not(formula=formula):
                return self._apply_shift(f"!({self.format(formula, 0)})", shift)
            case And(left=left, right=right):
                return self._apply_shift(
                    f"({self.format(left, 0)} && {self.format(right, 0)})", shift)
            case Or(left=left, right=right):
                return self._apply_shift(
                    f"({self.format(left, 0)} || {self.format(right, 0)})", shift)
            case Implies(left=left, right=right):
                return self._apply_shift(
                    f"({self.format(left, 0)} -> {self.format(right, 0)})", shift)
            case Next(formula=formula):
                return self.format(formula, shift + 1)
            case Prev(formula=formula):
                # Shift everything in the subformula by +1
                return self.format(formula, shift + 1)
            case Eventually(formula=formula):
                return self._apply_shift(f"F({self.format(formula, 0)})", shift)
            case Globally(formula=formula):
                return self._apply_shift(f"G({self.format(formula, 0)})", shift)
            case Top():
                return self._apply_shift("true", shift)
            case Bottom():
                return self._apply_shift("false", shift)
            case _:
                raise NotImplementedError(f"Spot formatting not implemented for: {type(this_formula)}")

    def _apply_shift(self, formula_str: str, shift: int) -> str:
        for _ in range(shift):
            formula_str = f"X({formula_str})"
        return formula_str
