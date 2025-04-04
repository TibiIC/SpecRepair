from collections import defaultdict
from copy import deepcopy
from typing import List, Dict, TypeVar, Optional

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.util.spec_util import replace_false_true

from py_ltl.parser import ILTLParser
from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies


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
                disjunct = self.antecedent[adaptation.disjunction_index]
                self.antecedent.remove(disjunct)
                for op, atom in adaptation.atom_temporal_operators:
                    new_disjunct = deepcopy(disjunct)
                    new_disjunct[op].append(replace_false_true(atom))
                    self.antecedent.append(new_disjunct)
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
