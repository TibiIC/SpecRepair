import re
from collections import defaultdict
from copy import deepcopy
from typing import TypedDict, Optional, TypeVar, List, Set, Any, Callable

import pandas as pd

from build.lib.spec_repair.ltl import LTLFormula
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.asp_exception_formatter import ASPExceptionFormatter
from spec_repair.helpers.asp_formula_formatter import ASPFormulaFormatter
from spec_repair.helpers.spectra_atom import SpectraAtom
from spec_repair.helpers.gr1_formula import GR1Formula
from spec_repair.helpers.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType
from spec_repair.util.file_util import read_file_lines, validate_spectra_file
from spec_repair.util.formula_util import get_temp_op, get_disjuncts_from_disjunction, get_conjuncts_from_conjunction, \
    skip_first_temp_op, is_ilasp_compatible_dnf_structure
from spec_repair.util.spec_util import format_spec

from py_ltl.formula import AtomicProposition, Not, Eventually

class FormulaDataPoint(TypedDict):
    name: str
    type: GR1FormulaType
    when: GR1TemporalType
    formula: "GR1Formula"  # Use the class name as a string for forward declaration


Self = TypeVar('T', bound='SpectraSpecification')


class SpectraSpecification(ISpecification):
    def __init__(self, spec_txt: str):
        self._formulas_df: pd.DataFrame = None
        self._atoms: Set[SpectraAtom] = set()
        self._parser = SpectraFormulaParser()
        self._formater = SpectraFormulaFormatter()
        self._asp_formatter = ASPExceptionFormatter()
        formula_list = []
        spec_lines = spec_txt.splitlines()
        try:
            for i, line in enumerate(spec_lines):
                if line.find("--") >= 0:
                    name: str = re.search(r'--\s*(\S+)', line).group(1)
                    type_txt: str = re.search(r'\s*(asm|assumption|gar|guarantee)\s*--', line).group(1)
                    type: GR1FormulaType = GR1FormulaType.from_str(type_txt)
                    formula_txt: str = re.sub('\s*', '', spec_lines[i + 1])
                    formula: GR1Formula = GR1Formula.from_str(formula_txt, self._parser)
                    when: GR1TemporalType = formula.temp_type
                    formula_list.append([name, type, when, formula])
                else:
                    atom: Optional[SpectraAtom] = SpectraAtom.from_str(line)
                    if atom:
                        self._atoms.add(atom)

        except AttributeError as e:
            raise e

        self._formulas_df = pd.DataFrame(formula_list, columns=["name", "type", "when", "formula"])

    def integrate_multiple(self, adaptations: List[Adaptation]):
        for adaptation in adaptations:
            self.integrate(adaptation)
        return self

    def integrate(self, adaptation: Adaptation):
        formula = self.get_formula(adaptation.formula_name)
        print("Rule:")
        print(f'\t{formula.to_str(self._formater)}')
        print("Hypothesis:")
        print(
            f'\t{adaptation.type}({adaptation.formula_name},{adaptation.disjunction_index},{adaptation.atom_temporal_operators})')
        formula.integrate(adaptation)
        print("New Rule:")
        print(f'\t{formula.to_str(self._formater)}')
        self.replace_formula(adaptation.formula_name, formula)

    def replace_formula(self, formula_name, formula):
        self._formulas_df.loc[self._formulas_df["name"] == formula_name, "formula"] = formula

    def get_formula(self, name: str):
        # Get formula by name
        formula: GR1Formula = \
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
            formulas_str += "\n\n"
        return formulas_str

    def _formula_to_asp_str(self, row, learning_names, for_clingo, is_ev_temp_op):
        if row.when == GR1TemporalType.JUSTICE and row['name'] not in learning_names and not for_clingo:
            return ""
        formula: GR1Formula = row.formula
        expression_string = f"%{row.type.to_asp()} -- {row['name']}\n"
        expression_string += f"%\t{formula.to_str(self._formater)}\n\n"
        expression_string += f"{row.type.to_asp()}({row['name']}).\n\n"
        is_exception = (row['name'] in learning_names) and not for_clingo
        ant_exception = is_exception and row['type'] == GR1FormulaType.ASM
        gar_exception = is_exception and row['type'] == GR1FormulaType.GAR
        ev_exception = is_exception and is_ev_temp_op
        self._asp_formatter.is_antecedent_exception = ant_exception
        self._asp_formatter.is_consequent_exception = gar_exception
        self._asp_formatter.is_eventually_exception = ev_exception
        expression_string += row.formula.to_str(self._asp_formatter).replace("{name}", row['name'])
        return expression_string

    def filter(self, func: Callable[[pd.DataFrame], bool]) -> pd.DataFrame:
        return self._formulas_df.loc[func(self._formulas_df)]

    def extract_sub_specification(self, func: Callable[[pd.DataFrame], bool]) -> Any:
        sub_spec = deepcopy(self)
        sub_spec._formulas_df = deepcopy(self.filter(func))
        return sub_spec

    def to_str(self):
        """
        Convert the specification to a string representation.
        """
        spec_str = ""
        for atom in sorted(self._atoms):
            spec_str += f"{atom.atom_type} {atom.value_type} {atom.name};\n"
        spec_str += "\n\n"

        for _, row in self._formulas_df.iterrows():
            spec_str += f"{row['type'].to_str()} -- {row['name']}\n"
            spec_str += f"{row['formula'].to_str(self._formater)}\n\n"
        return spec_str

    def __deepcopy__(self, memo):
        new_spec = SpectraSpecification("")
        new_spec._formulas_df = self._formulas_df.copy(deep=True)
        for col in new_spec._formulas_df.columns:
            if new_spec._formulas_df[col].dtype == 'O':  # Object dtype means it might contain class instances
                new_spec._formulas_df[col] = new_spec._formulas_df[col].apply(lambda x: deepcopy(x, memo))
        new_spec._atoms = deepcopy(self._atoms, memo)
        return new_spec


def propositionalise_antecedent(row, exception=False):
    output = ""
    disjunction_of_conjunctions: LTLFormula = row.formula.antecedent
    n_root_antecedents = 0
    timepoint = "T" if row['when'] != GR1TemporalType.INITIAL else "0"
    component_body = f"antecedent_holds({row['name']},{timepoint},S):-\n" + \
                     f"\ttrace(S),\n" + \
                     f"\ttimepoint({timepoint},S)"
    disjuncts = get_disjuncts_from_disjunction(disjunction_of_conjunctions)
    if not disjuncts:
        disjuncts = [None]
    for asm_id, disjunct in enumerate(disjuncts):
        output += component_body
        op_conjunction: List[LTLFormula] = get_conjuncts_from_conjunction(disjunct)
        for i, op_conjunct in enumerate(op_conjunction):
            output += f",\n{component_end_antecedent(row['name'], get_temp_op(op_conjunct), timepoint, n_root_antecedents + i)}"
        if exception:
            output += f",\n\tnot antecedent_exception({row['name']},{asm_id},{timepoint},S)"
        output += ".\n\n"
        for op_conjunct in op_conjunction:
            output += root_antecedent_body(row['name'], n_root_antecedents)
            conjunction: LTLFormula = skip_first_temp_op(op_conjunct)
            conjunction: List[LTLFormula] = get_conjuncts_from_conjunction(conjunction)
            for conjunct in conjunction:
                v = False
                if isinstance(conjunct, Not):
                    conjunct = conjunct.formula
                    v = True
                assert isinstance(conjunct, AtomicProposition)
                c = conjunct.name
                v = v ^ conjunct.value # flip conjunct.value if it is negated
                output += f",\n\t{'' if v else 'not_'}holds_at({c},T2,S)"
            output += ".\n\n"
            n_root_antecedents += 1

    return output


def propositionalise_consequent(row, exception=False, is_ev_temp_op=True):
    output = ""
    disjunction_of_conjunctions: LTLFormula = row.formula.consequent
    assert is_ilasp_compatible_dnf_structure(disjunction_of_conjunctions)
    n_root_consequents = 0
    timepoint = "T" if row['when'] != GR1TemporalType.INITIAL else "0"
    component_body = f"consequent_holds({row['name']},{timepoint},S):-\n" + \
                     f"\ttrace(S),\n" + \
                     f"\ttimepoint({timepoint},S)"
    if isinstance(disjunction_of_conjunctions, Eventually):
        disjunction_of_conjunctions = disjunction_of_conjunctions.formula
        temp_op = "eventually"
    disjuncts: List[LTLFormula] = get_disjuncts_from_disjunction(disjunction_of_conjunctions)
    for disjunct in disjuncts:
        output += component_body
        op_conjunction: List[LTLFormula] = get_conjuncts_from_conjunction(disjunct)
        for i, op_conjunct in enumerate(op_conjunction):
            temp_op = get_temp_op(op_conjunct)
            if row['when'] == GR1TemporalType.JUSTICE:
                temp_op = "eventually"
            output += f",\n{component_end_consequent(row['name'], temp_op, timepoint, n_root_consequents + i)}"
        # TODO: cook up better way of checking whether a temporal operator is present in a formula
        if "eventually" not in output and exception and is_ev_temp_op and timepoint == "T":
            output += f",\n\tnot ev_temp_op({row['name']})"
        output += ".\n\n"
        if exception and is_ev_temp_op:
            output += component_body
            for i in range(len(op_conjunction)):
                output += f",\n{component_end_consequent(row['name'], 'eventually', timepoint, n_root_consequents + i)}"
            output += f",\n\tev_temp_op({row['name']}).\n\n"
        for op_conjunct in op_conjunction:
            output += root_consequent_body(row['name'], n_root_consequents)
            conjunction: LTLFormula = skip_first_temp_op(op_conjunct)
            conjunction: List[LTLFormula] = get_conjuncts_from_conjunction(conjunction)
            for conjunct in conjunction:
                v = False
                if isinstance(conjunct, Not):
                    conjunct = conjunct.formula
                    v = True
                assert isinstance(conjunct, AtomicProposition)
                c = conjunct.name
                v = v ^ conjunct.value  # flip conjunct.value if it is negated
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
