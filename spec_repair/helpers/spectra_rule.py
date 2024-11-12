from collections import defaultdict
from typing import List, Dict, TypeVar

from spec_repair.helpers.adaptation_learned import AdaptationLearned
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.special_types import GR1Formula
from spec_repair.util.spec_util import parse_formula_str, replace_false_true

Self = TypeVar('T', bound='SpectraRule')


class SpectraRule:
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

    def integrate(self, adaptation: AdaptationLearned):
        match adaptation.type:
            case "antecedent_exception":
                for op, atom in adaptation.atom_temporal_operators:
                    self.antecedent[adaptation.disjunction_index][op].append(replace_false_true(atom))
            case "consequent_exception":
                new_disjunct = defaultdict(list)
                for op, atom in adaptation.atom_temporal_operators:
                    new_disjunct[op].append(atom)
                self.consequent.insert(0, new_disjunct)
            case _:
                raise ValueError(f"Unsupported temporal type: {self.temp_type}")

    @staticmethod
    def from_str(formula: str) -> Self:
        """
        Parse a formula from a Spectra file into a SpectraFormula object.

        Args:
            formula (str): The input formula to parse.

        Returns:
            SpectraRule: A SpectraFormula object containing the parsed formula.
        """

        temp_op_str = GR1Formula.pattern.match(formula).group(GR1Formula.TEMP_OP)
        match temp_op_str:
            case "G":
                temp_op = GR1TemporalType.INVARIANT
            case "GF":
                temp_op = GR1TemporalType.JUSTICE
            case _:
                temp_op = GR1TemporalType.INITIAL

        formula = GR1Formula.pattern.match(formula).group(GR1Formula.FORMULA)
        # Split the formula by '->'
        parts = formula.split('->')

        if len(parts) == 1:
            antecedent = [defaultdict(list)]
            consequent = parse_formula_str(parts[0])
        else:
            antecedent = parse_formula_str(parts[0])
            consequent = parse_formula_str(parts[1])

        return SpectraRule(temp_op, antecedent, consequent)

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
