import re
from collections import defaultdict
from copy import deepcopy
from typing import TypedDict, Optional, TypeVar, List, Set, Any, Callable

import pandas as pd

from spec_repair.components.interfaces.ispecification import ISpecification
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


class SpectraSpecification(ISpecification):
    _formulas_df: pd.DataFrame = None
    _atoms: Set[SpectraAtom] = set()

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
                        self._atoms.add(atom)

        except AttributeError as e:
            raise e

        self._formulas_df = pd.DataFrame(formula_list, columns=["name", "type", "when", "formula"])

    """
    def filter(self, to_filter: str, by_value: Any, to_get: str) -> List[Any]:
        return self._formulas_df.loc[self._formulas_df[to_filter] == by_value, to_get].tolist()
    """

    def integrate_multiple(self, adaptations: List[Adaptation]):
        for adaptation in adaptations:
            self.integrate(adaptation)

    def integrate(self, adaptation: Adaptation):
        formula = self.get_formula(adaptation.formula_name)
        print("Rule:")
        print(f'\t{formula.to_str()}')
        print("Hypothesis:")
        print(
            f'\t{adaptation.type}({adaptation.formula_name},{adaptation.disjunction_index},{adaptation.atom_temporal_operators})')
        formula.integrate(adaptation)
        print("New Rule:")
        print(f'\t{formula.to_str()}')
        self.replace_formula(adaptation.formula_name, formula)

    def replace_formula(self, formula_name, formula):
        self._formulas_df.loc[self._formulas_df["name"] == formula_name, "formula"] = formula

    def get_formula(self, name: str):
        # Get formula by name
        formula: SpectraFormula = \
            self._formulas_df.loc[self._formulas_df["name"] == name, "formula"].iloc[0]
        return formula

    @staticmethod
    def from_file(spec_file: str) -> Self:
        validate_spectra_file(spec_file)
        spec_txt: str = "".join(format_spec(read_file_lines(spec_file)))
        return SpectraSpecification(spec_txt)

    def get_atoms(self):
        return deepcopy(self._atoms)

    def to_asp(
            self,
            learning_names: Optional[List[str]] = None,
            for_clingo: bool = False,
            is_ev_temp_op: bool = True
    ) -> str:
        if learning_names is None:
            learning_names = []
        formulas_str = ""
        for _, row in self._formulas_df.iterrows():
            formulas_str += self._formula_to_asp_str(row, learning_names, for_clingo, is_ev_temp_op)
        return formulas_str

    def _formula_to_asp_str(self, row, learning_names, for_clingo, is_ev_temp_op):
        if row.when == GR1TemporalType.JUSTICE and row['name'] not in learning_names and not for_clingo:
            return ""
        formula: SpectraFormula = row.formula
        expression_string = f"%{row.type.to_asp()} -- {row['name']}\n"
        expression_string += f"%\t{formula.to_str()}\n\n"
        expression_string += f"{row.type.to_asp()}({row['name']}).\n\n"
        is_exception = (row['name'] in learning_names) and not for_clingo
        ant_exception = is_exception and row['type'] == GR1FormulaType.ASM
        gar_exception = is_exception
        expression_string += propositionalise_antecedent(row, exception=ant_exception)
        expression_string += propositionalise_consequent(row, exception=gar_exception, is_ev_temp_op=is_ev_temp_op)
        return expression_string

    def filter(self, func: Callable[[pd.DataFrame], bool]) -> pd.DataFrame:
        return self._formulas_df.loc[func(self._formulas_df)]


def propositionalise_antecedent(row, exception=False):
    output = ""
    disjunction_of_conjunctions = row.formula.antecedent
    n_root_antecedents = 0
    timepoint = "T" if row['when'] != GR1TemporalType.INITIAL else "0"
    if len(disjunction_of_conjunctions) == 0 and exception:
        disjunction_of_conjunctions = [defaultdict(list)]
    component_body = f"antecedent_holds({row['name']},{timepoint},S):-\n" + \
                     f"\ttrace(S),\n" + \
                     f"\ttimepoint({timepoint},S)"
    for asm_id, disjunct in enumerate(disjunction_of_conjunctions):
        output += component_body
        for i, (temp_op, conjuncts) in enumerate(disjunct.items()):
            output += f",\n{component_end_antecedent(row['name'], temp_op, timepoint, n_root_antecedents + i)}"
        if exception:
            output += f",\n\tnot antecedent_exception({row['name']},{asm_id},{timepoint},S)"
        output += ".\n\n"
        for temp_op, conjuncts in disjunct.items():
            output += root_antecedent_body(row['name'], n_root_antecedents)
            for conjunct in conjuncts:
                conjunct_and_value = conjunct.split("=")
                c = conjunct_and_value[0]
                v = conjunct_and_value[1] == "true"
                output += f",\n\t{'' if v else 'not_'}holds_at({c},T2,S)"
            output += ".\n\n"
            n_root_antecedents += 1

    return output


def propositionalise_consequent(row, exception=False, is_ev_temp_op=True):
    output = ""
    disjunction_of_conjunctions = row.formula.consequent
    n_root_consequents = 0
    timepoint = "T" if row['when'] != GR1TemporalType.INITIAL else "0"
    if len(disjunction_of_conjunctions) == 0 and exception:
        disjunction_of_conjunctions = [defaultdict(list)]
    component_body = f"consequent_holds({row['name']},{timepoint},S):-\n" + \
                     f"\ttrace(S),\n" + \
                     f"\ttimepoint({timepoint},S)"
    for disjunct in disjunction_of_conjunctions:
        output += component_body
        for i, (temp_op, conjuncts) in enumerate(disjunct.items()):
            if row['when'] == GR1TemporalType.JUSTICE:
                temp_op = "eventually"
            output += f",\n{component_end_consequent(row['name'], temp_op, timepoint, n_root_consequents + i)}"
        if "eventually" not in disjunct.keys() and exception and is_ev_temp_op and timepoint == "T":
            output += f",\n\tnot ev_temp_op({row['name']})"
        output += ".\n\n"
        if exception and is_ev_temp_op:
            output += component_body
            for i in range(len(disjunct)):
                output += f",\n{component_end_consequent(row['name'], 'eventually', timepoint, n_root_consequents + i)}"
            output += f",\n\tev_temp_op({row['name']}).\n\n"
        for temp_op, conjuncts in disjunct.items():
            output += root_consequent_body(row['name'], n_root_consequents)
            for conjunct in conjuncts:
                conjunct_and_value = conjunct.split("=")
                c = conjunct_and_value[0]
                v = conjunct_and_value[1] == "true"
                output += f",\n\t{'' if v else 'not_'}holds_at({c},T2,S)"
            output += ".\n\n"
            n_root_consequents += 1

    if exception and row['type'] == "guarantee":
        output += component_body
        output += f",\n\tconsequent_exception({row['name']},{timepoint},S)"
        if is_ev_temp_op:
            output += f",\n\tnot ev_temp_op({row['name']})"
        output += f".\n\n"

    return output


def root_antecedent_body(name, id: int):
    out = f"root_antecedent_holds(OP,{name},{id},T1,S):-\n" + \
          f"\ttrace(S),\n" + \
          f"\ttimepoint(T1,S),\n" + \
          f"\tnot weak_timepoint(T1,S),\n" + \
          f"\ttimepoint(T2,S),\n" + \
          f"\ttemporal_operator(OP),\n" + \
          f"\ttimepoint_of_op(OP,T1,T2,S)"
    return out


def component_end_antecedent(name, temp_op, timepoint, id: int):
    assert temp_op in ["current", "next", "prev"]
    out = f"\troot_antecedent_holds({temp_op},{name},{id},{timepoint},S)"
    return out


def root_consequent_body(name, id: int):
    out = f"root_consequent_holds(OP,{name},{id},T1,S):-\n" + \
          f"\ttrace(S),\n" + \
          f"\ttimepoint(T1,S),\n" + \
          f"\tnot weak_timepoint(T1,S),\n" + \
          f"\ttimepoint(T2,S),\n" + \
          f"\ttemporal_operator(OP),\n" + \
          f"\ttimepoint_of_op(OP,T1,T2,S)"
    return out


def component_end_consequent(name, temp_op, timepoint, id: int):
    assert temp_op in ["current", "next", "prev", "eventually"]
    out = f"\troot_consequent_holds({temp_op},{name},{id},{timepoint},S)"
    return out
