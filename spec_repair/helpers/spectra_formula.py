from typing import List, Dict

from spec_repair.ltl_types import GR1TemporalType


class SpectraFormula:
    def __init__(
            self,
            temp_type: GR1TemporalType,
            antecedent: List[Dict[str, List[str]]],
            consequent: List[Dict[str, List[str]]],
    ):
        self.temp_type = temp_type
        self.antecedent = antecedent
        self.consequent = consequent