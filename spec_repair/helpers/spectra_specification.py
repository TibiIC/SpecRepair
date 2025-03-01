import re
from pathlib import Path
from typing import TypedDict, Optional, TypeVar, List

import pandas as pd

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.spectra_atom import SpectraAtom
from spec_repair.helpers.spectra_formula import SpectraFormula
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.util.file_util import read_file_lines, validate_spectra_file
from spec_repair.util.spec_util import format_spec


class FormulaDataPoint(TypedDict):
    name: str
    type: GR1FormulaType
    when: GR1TemporalType
    formula: "SpectraFormula"  # Use the class name as a string for forward declaration


Self = TypeVar('T', bound='SpectraSpecification')


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

    @staticmethod
    def from_file(spec_file: str) -> Self:
        validate_spectra_file(spec_file)
        spec_txt: str = "".join(format_spec(read_file_lines(spec_file)))
        return SpectraSpecification(spec_txt)

    def integrate_multiple(self, adaptations: List[Adaptation]):
        for adaptation in adaptations:
            self.integrate(adaptation)

    def integrate(self, adaptation: Adaptation):
        formula = self.get_formula(adaptation.formula_name)
        print("Rule:")
        print(f'\t{formula.to_str()}')
        print("Hypothesis:")
        print(f'\t{adaptation.type}({adaptation.formula_name},{adaptation.disjunction_index},{adaptation.atom_temporal_operators})')
        formula.integrate(adaptation)
        print("New Rule:")
        print(f'\t{formula.to_str()}')
        self.replace_formula(adaptation.formula_name, formula)

    def replace_formula(self, formula_name, formula):
        self.formulas_df.loc[self.formulas_df["name"] == formula_name, "formula"] = formula

    def get_formula(self, name: str):
        # Get formula by name
        formula: SpectraFormula = \
        self.formulas_df.loc[self.formulas_df["name"] == name, "formula"].iloc[0]
        return formula
