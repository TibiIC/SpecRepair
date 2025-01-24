import re
from typing import TypedDict, Optional

import pandas as pd

from spec_repair.helpers.spectra_formula import SpectraFormula
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType, GR1AtomType
from spec_repair.special_types import GR1Atom


class FormulaDataPoint(TypedDict):
    name: str
    type: GR1FormulaType
    when: GR1TemporalType
    formula: "SpectraFormula"  # Use the class name as a string for forward declaration


class Atom:
    def __init__(self, name: str, value_type: str, atom_type: GR1AtomType):
        self.name = name
        self.value_type = value_type
        self.atom_type = atom_type

    @staticmethod
    def from_str(atom_str: str):
        atom_definition = GR1Atom.pattern.match(atom_str)
        if atom_definition:
            name = atom_definition.group(GR1Atom.NAME)
            value_type = atom_definition.group(GR1Atom.VALUE_TYPE)
            atom_type = atom_definition.group(GR1Atom.ATOM_TYPE)
            return Atom(name, value_type, GR1AtomType.from_str(atom_type))
        return None

    def __str__(self):
        return f"{self.atom_type} {self.value_type} {self.name}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (self.name == other.name and
                self.value_type == other.value_type and
                self.atom_type == other.atom_type)

    def __hash__(self):
        return hash((self.name, self.value_type, self.atom_type))

class SpectraSpecification:
    formulas_df: pd.DataFrame = None
    atoms: set[Atom] = set()

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
                    atom: Optional[Atom] = Atom.from_str(line)
                    if atom:
                        self.atoms.add(atom)

        except AttributeError as e:
            raise e

        self.formulas_df = pd.DataFrame(formula_list, columns=["name", "type", "when", "formula"])
