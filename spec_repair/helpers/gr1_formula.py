from collections import defaultdict
from copy import deepcopy
from typing import List, Dict, TypeVar

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.util.spec_util import replace_false_true

from py_ltl.parser import ILTLParser
from py_ltl.formula import AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies


Self = TypeVar('T', bound='SpectraRule')


class GR1Formula:
    def __init__(
            self,
            temp_type: GR1TemporalType,
            antecedent: List[Dict[str, List[str]]],
            consequent: List[Dict[str, List[str]]],
    ):
        self.temp_type = temp_type
        self.antecedent = antecedent
        self.consequent = consequent

    def to_str(self):
        antecedent_str = self.formula_DNF_to_str(self.antecedent, optimise_parantheses=True)
        consequent_str = self.formula_DNF_to_str(self.consequent, optimise_parantheses=True)
        if antecedent_str:
            return f'{self.temp_type}({antecedent_str}->{consequent_str});'
        return f'{self.temp_type}({consequent_str});'

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

    @staticmethod
    def formula_DNF_to_str(parsed_formula: List[Dict[str, List[str]]], optimise_parantheses: bool = False) -> str:
        """
        Encode a parsed formula into a string representation.
        NOTE: encoding will be Spectra-compatible

        Args:
            parsed_formula (List[Dict[str, List[str]]]): The parsed formula to encode.

        Returns:
            str: The encoded formula as a string.
        """
        encoded_formula = []

        for conjunct in parsed_formula:
            encoded_conjunct = []

            for operator, literals in conjunct.items():
                # Encode the operator and literals
                encoded_operator = operator
                encoded_literals = "&".join(literals)
                match encoded_operator:
                    case "eventually":
                        encoded_conjunct.append(f"F({encoded_literals})")
                    case "prev":
                        encoded_conjunct.append(f"PREV({encoded_literals})")
                    case "current":
                        encoded_conjunct.append(encoded_literals)
                    case _:
                        encoded_conjunct.append(f"{encoded_operator}({encoded_literals})")

            # Join the encoded conjunctions by 'or' and add to the list
            encoded_formula.append("&".join(encoded_conjunct))

        if optimise_parantheses:
            return f"{'|'.join(encoded_formula)}"
        else:
            return f"({')|('.join(encoded_formula)})"
