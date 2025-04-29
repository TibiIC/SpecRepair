from collections import defaultdict
from copy import deepcopy
from functools import reduce
from typing import List, Dict, TypeVar, Optional

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.util.formula_util import disjoin_all, get_disjuncts_from_disjunction
from spec_repair.util.spec_util import replace_false_true

from py_ltl.parser import ILTLParser
from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Prev, Globally, Eventually, \
    Implies, Top, Bottom

Self = TypeVar('T', bound='SpectraRule')


class GR1Formula:
    def __init__(
            self,
            temp_type: GR1TemporalType,
            antecedent: Optional[LTLFormula],
            consequent: LTLFormula
    ):
        self.temp_type = temp_type
        self.antecedent = antecedent
        self.consequent = consequent
        # TODO: create separate parser for ILASP output. for now use this
        self.ilasp_parser = SpectraFormulaParser()

    @staticmethod
    def from_str(formula: str, parser: ILTLParser) -> Self:
        """
        Parse a formula from a Spectra file into a SpectraFormula object.

        Args:
            formula (str): The input formula to parse.

        Returns:
            GR1Formula: A SpectraFormula object containing the parsed formula.
        """
        parsed = parser.parse(formula)
        if not isinstance(parsed, Globally):
            temp_type = GR1TemporalType.INITIAL
        else:
            parsed = parsed.formula
            if isinstance(parsed, Eventually):
                temp_type = GR1TemporalType.JUSTICE
                parsed = parsed.formula
            else:
                temp_type = GR1TemporalType.INVARIANT
        if isinstance(parsed, Implies):
            antecedent = parsed.left
            consequent = parsed.right
        else:
            antecedent = None
            consequent = parsed

        return GR1Formula(temp_type, antecedent, consequent)

    def to_str(self, formatter: ILTLFormatter) -> str:
        if self.antecedent is None:
            implication = self.consequent
        else:
            implication = Implies(self.antecedent, self.consequent)
        match self.temp_type:
            case GR1TemporalType.INITIAL:
                return implication.format(formatter=formatter)
            case GR1TemporalType.INVARIANT:
                return Globally(implication).format(formatter=formatter)
            case GR1TemporalType.JUSTICE:
                return Globally(Eventually(implication)).format(formatter=formatter)
            case _:
                raise ValueError(f"Unsupported temporal type: {self.temp_type}")

    def integrate(self, adaptation: Adaptation):
        match adaptation.type:
            case "antecedent_exception":
                self._integrate_antecedent_exception(adaptation)
            case "consequent_exception":
                if isinstance(self.consequent, Eventually):
                    # TODO: remove possibility of consequent
                    # exception when eventually consequent
                    adaptation.disjunction_index = 0 # Placeholder. TODO: remove
                    self._integrate_antecedent_exception(adaptation)
                else:
                    self._integrate_consequent_exception(adaptation)
            case "ev_temp_op":
                self.consequent = self.remove_temporal_operators(self.consequent)
                if not self.antecedent:
                    self.temp_type = GR1TemporalType.JUSTICE
                else:
                    self.consequent = Eventually(self.consequent)

            case _:
                raise ValueError(f"Unsupported temporal type: {self.temp_type}")

    def _integrate_consequent_exception(self, adaptation: Adaptation):
        first_temp_op, first_atom_assignment = adaptation.atom_temporal_operators[0]
        new_disjunct = self.generate_literal(first_atom_assignment, first_temp_op)
        for op, atom in adaptation.atom_temporal_operators[1:]:
            new_disjunct = And(new_disjunct, self.generate_literal(atom, op))
        self.consequent = Or(self.consequent, new_disjunct)

    def _integrate_antecedent_exception(self, adaptation: Adaptation):
        if self.antecedent is None:
            first_temp_op, first_atom_assignment = adaptation.atom_temporal_operators[0]
            first_atom_assignment = replace_false_true(first_atom_assignment)
            self.antecedent = self.generate_literal(first_atom_assignment, first_temp_op)
            for op, atom in adaptation.atom_temporal_operators[1:]:
                atom = replace_false_true(atom)
                new_disjunct = self.generate_literal(atom, op)
                self.antecedent = Or(self.antecedent, new_disjunct)
        else:
            disjuncts = get_disjuncts_from_disjunction(self.antecedent)
            disjunct = disjuncts[adaptation.disjunction_index]
            disjuncts.remove(disjunct)
            for op, atom in adaptation.atom_temporal_operators:
                atom = replace_false_true(atom)
                new_disjunct = self.generate_literal(atom, op)
                new_disjunct = And(deepcopy(disjunct), new_disjunct)
                disjuncts.append(new_disjunct)
            self.antecedent = disjoin_all(disjuncts)

    def generate_literal(self, atom, op):
        new_disjunct = self.ilasp_parser.parse(atom)
        match op:
            case "current":
                pass
            case "eventually":
                raise ValueError("eventually operator not supported in antecedent")
            case "next":
                new_disjunct = Next(new_disjunct)
            case "prev":
                new_disjunct = Prev(new_disjunct)
            case _:
                raise ValueError(f"Unsupported temporal operator: {op}")
        return new_disjunct

    @staticmethod
    def remove_temporal_operators(this_formula: LTLFormula) -> LTLFormula:
        match this_formula:
            case AtomicProposition(name=name, value=value):
                return this_formula
            case Not(formula=formula):
                return Not(GR1Formula.remove_temporal_operators(formula))
            case And(left=lhs, right=rhs):
                return And(
                    left=GR1Formula.remove_temporal_operators(lhs),
                    right=GR1Formula.remove_temporal_operators(rhs)
                )
            case Or(left=lhs, right=rhs):
                return Or(
                    left=GR1Formula.remove_temporal_operators(lhs),
                    right=GR1Formula.remove_temporal_operators(rhs)
                )
            case Implies(left=lhs, right=rhs):
                return Implies(
                    left=GR1Formula.remove_temporal_operators(lhs),
                    right=GR1Formula.remove_temporal_operators(rhs)
                )
            case Next(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Prev(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Eventually(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Globally(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Top():
                return Top()
            case Bottom():
                return Bottom()
            case _:
                raise NotImplementedError(f"Removing temporal operators not implemented for: {type(this_formula)}")
