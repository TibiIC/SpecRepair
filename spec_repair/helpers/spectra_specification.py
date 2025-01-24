import re
from typing import TypedDict, Optional

import pandas as pd

from spec_repair.helpers.spectra_atom import SpectraAtom
from spec_repair.helpers.spectra_formula import SpectraFormula
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType


class FormulaDataPoint(TypedDict):
    name: str
    type: GR1FormulaType
    when: GR1TemporalType
    formula: "SpectraFormula"  # Use the class name as a string for forward declaration


class SpectraSpecification:
    formulas_df: pd.DataFrame = None
    atoms: set[SpectraAtom] = set()

    def __init__(self, spec_txt: str):
        formula_list = []
        spec_lines = spec_txt.splitlines()
        try:
            for i, line in enumerate(spec_lines):
                if line.find("--") >= 0:
                    name: str = re.search(r'--\s*(\S+)', line).group(1)
                    type_txt: str = re.search(r'\s*(asm|assumption|gar|guarantee)\s*--', line).group(1)
                    type: GR1FormulaType = GR1FormulaType.from_str(type_txt)
                    formula_txt: str = re.sub('\s*', '', spec_lines[i + 1])
                    formula: SpectraFormula = SpectraFormula.from_str(formula_txt)
                    when: GR1TemporalType = formula.temp_type
                    formula_list.append([name, type, when, formula])
                else:
                    atom: Optional[SpectraAtom] = SpectraAtom.from_str(line)
                    if atom:
                        self.atoms.add(atom)

        except AttributeError as e:
            raise e

        self.formulas_df = pd.DataFrame(formula_list, columns=["name", "type", "when", "formula"])
