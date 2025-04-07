from collections import defaultdict
from copy import deepcopy
from functools import reduce
from typing import List, Dict, TypeVar, Optional

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.util.spec_util import replace_false_true

from py_ltl.parser import ILTLParser
from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Prev, Globally, Eventually, Implies

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
                if self.antecedent is None:
                    first_temp_op, first_atom_assignment = adaptation.atom_temporal_operators[0]
                    first_atom_assignment = replace_false_true(first_atom_assignment)
                    self.antecedent = self.generate_literal(first_atom_assignment, first_temp_op)
                    for op, atom in adaptation.atom_temporal_operators[1:]:
                        atom = replace_false_true(atom)
                        new_disjunct = self.generate_literal(atom, op)
                        self.antecedent = Or(self.antecedent, new_disjunct)
                else:
                    disjuncts = self.get_disjuncts_from_DNF(self.antecedent)
                    disjunct = disjuncts[adaptation.disjunction_index]
                    disjuncts.remove(disjunct)
                    for op, atom in adaptation.atom_temporal_operators:
                        atom = replace_false_true(atom)
                        new_disjunct = self.generate_literal(atom, op)
                        new_disjunct = And(deepcopy(disjunct), new_disjunct)
                        disjuncts.append(new_disjunct)
                    self.antecedent = self.disjoin_all(disjuncts)
            case "consequent_exception":
                ops_in_consequent = {op for disjunct in self.consequent for op in disjunct}
                if "eventually" in ops_in_consequent:
                    for disjunct in deepcopy(self.antecedent):
                        self.antecedent.remove(disjunct)
                        for op, atom in adaptation.atom_temporal_operators:
                            new_disjunct = deepcopy(disjunct)
                            new_disjunct[op].append(replace_false_true(atom))
                            self.antecedent.append(new_disjunct)
                else:
                    new_disjunct = defaultdict(list)
                    for op, atom in adaptation.atom_temporal_operators:
                        new_disjunct[op].append(atom)
                    self.consequent.insert(0, new_disjunct)
            case "ev_temp_op":
                new_consequent = []
                op = "eventually"
                if not self.antecedent or self.antecedent == [defaultdict(list)]:
                    self.temp_type = GR1TemporalType.JUSTICE
                    op = "current"
                for disjunct in self.consequent:
                    all_conjuncts = [conjunct for conjuncts in disjunct.values() for conjunct in conjuncts]
                    new_disjunct = defaultdict(list)
                    new_disjunct[op] = all_conjuncts
                    new_consequent.append(new_disjunct)
                self.consequent = new_consequent

            case _:
                raise ValueError(f"Unsupported temporal type: {self.temp_type}")

    @staticmethod
    def get_disjuncts_from_DNF(dnf_formula: LTLFormula) -> List[LTLFormula]:
        disjunction = dnf_formula
        disjuncts = []
        while isinstance(disjunction, Or):
            disjuncts.append(disjunction.right)
            disjunction = disjunction.left
        disjuncts.append(disjunction)
        disjuncts.reverse()
        return disjuncts

    @staticmethod
    def disjoin_all(formulas: list[LTLFormula]) -> LTLFormula:
        if not formulas:
            raise ValueError("Cannot disjoin an empty list of formulas")
        return reduce(lambda a, b: Or(a, b), formulas)

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
