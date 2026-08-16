import copy
import logging
import os
import re
import subprocess
from collections import Counter
from copy import deepcopy
from typing import TypedDict, Optional, TypeVar, List, Set, Any, Callable

import pandas as pd
import spot

from spec_repair.interfaces.ispecification import ISpecification
# from spec_repair.components.oracles.new_spec_oracle import NewSpecOracle
from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.helpers.formatters.asp_exception_formatter import ASPExceptionFormatter
from spec_repair.interfaces.iheuristic_manager import IHeuristicManager
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.model.spectra_atom import SpectraAtom
from spec_repair.model.gr1_formula import GR1Formula
from spec_repair.helpers.formatters.spectra_formula_formatter import SpectraFormulaFormatter
from spec_repair.helpers.parsers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.helpers.formatters.spot_specification_formatter import SpotSpecificationFormatter
from spec_repair.ltl_types import GR1FormulaType, GR1TemporalType, TemporalDialect, LTLFiltOperation
from spec_repair.util.file_util import read_file_lines, validate_spectra_file
from spec_repair.util.ltl_formula_util import get_disjuncts_from_disjunction
from spec_repair.util.formula_string_util import format_spec
from spec_repair.helpers.weakness_measurement.weakness_user_friendly import computeWeakness, Weakness
from spec_repair.exceptions import NameClashException


class FormulaDataPoint(TypedDict):
    name: str
    type: GR1FormulaType
    when: GR1TemporalType
    formula: "GR1Formula"  # Use the class name as a string for forward declaration


Self = TypeVar('T', bound='SpectraSpecification')


class SpectraSpecification(ISpecification):
    _response_pattern = """\
    pattern pRespondsToS(s, p) {
      var { S0, S1} state;

      // initial assignments: initial state
      ini state=S0;

      // safety this and next state
      alw ((state=S0 & ((!s) | (s & p)) & next(state=S0)) |
      (state=S0 & (s & !p) & next(state=S1)) |
      (state=S1 & (p) & next(state=S0)) |
      (state=S1 & (!p) & next(state=S1)));

      // equivalence of satisfaction
      alwEv (state=S0);
    }"""

    def __init__(self, spec_txt: str):
        spec_txt = copy.deepcopy(spec_txt)
        self._formulas_df: pd.DataFrame = pd.DataFrame(columns=["name", "type", "when", "formula"])
        self._module_name: str
        self._atoms: Set[SpectraAtom] = set()
        self._parser = SpectraFormulaParser()
        self._formater = SpectraFormulaFormatter()
        self._asp_formatter = ASPExceptionFormatter()
        spec_lines = spec_txt.splitlines()
        try:
            for i, line in enumerate(spec_lines):
                if line.find("module") >= 0:
                    self._module_name = line.split()[1]
                elif line.find("--") >= 0:
                    name: str = re.search(r'--\s*(.+)', line).group(1)
                    type_txt: str = re.search(r'\s*(asm|assumption|gar|guarantee)\s*--', line).group(1)
                    formula_type: GR1FormulaType = GR1FormulaType.from_str(type_txt)
                    formula_txt: str = re.sub('\s*', '', spec_lines[i + 1])
                    formula: GR1Formula = GR1Formula.from_str(formula_txt, self._parser)
                    self.add_formula(formula, name, formula_type)
                else:
                    atom: Optional[SpectraAtom] = SpectraAtom.from_str(line)
                    if atom:
                        self._atoms.add(atom)

        except AttributeError as e:
            raise e

    def integrate_multiple(self, adaptations: List[Adaptation]):
        for adaptation in adaptations:
            self.integrate(adaptation)
        return self

    def integrate(self, adaptation: Adaptation):
        """
        Apply one learned adaptation to the formula it names.

        Logged as a single line rather than the three-stanza Rule/Hypothesis/New
        Rule block this used to print. That block ran once per adaptation per
        candidate, which on a branching search is thousands of times - it buried
        the events that say where the run actually is, and said nothing a
        before/after pair does not.
        """
        formula = self.get_formula(adaptation.formula_name)
        before = formula.to_str(self._formater)
        formula.integrate(adaptation)
        logging.getLogger(__name__).debug(
            "%s %s: %s -> %s", adaptation.type, adaptation.formula_name,
            before, formula.to_str(self._formater))
        self.replace_formula(adaptation.formula_name, formula)

    def replace_formula(self, formula_name, formula):
        self._formulas_df.loc[self._formulas_df["name"] == formula_name, "formula"] = formula

    def get_formula(self, name: str):
        # Get formula by name
        formula: GR1Formula = \
            self._formulas_df.loc[self._formulas_df["name"] == name, "formula"].iloc[0]
        return formula

# TODO: make it count the amount of conjunctions with different temporal operators (max=3/disjunct)
    def get_max_disjuncts_in_antecedent(self) -> int:
        """
        Get the maximum number of conjunctions in the antecedent of any formula.
        """
        max_disjuncts = 0
        for _, row in self._formulas_df.iterrows():
            if row['type'] == GR1FormulaType.ASM:
                formula = row.formula
                antecedent = formula.antecedent
                disjuncts = get_disjuncts_from_disjunction(antecedent)
                max_disjuncts = max(max_disjuncts, len(disjuncts))
        return max_disjuncts

    @staticmethod
    def from_file(spec_file: str) -> Self:
        validate_spectra_file(spec_file)
        spec_txt: str = "".join(format_spec(read_file_lines(spec_file)))
        return SpectraSpecification(spec_txt)

    @staticmethod
    def from_str(spec_text: str) -> Self:
        spec_txt: str = "".join(format_spec(spec_text.splitlines(keepends=True)))
        return SpectraSpecification(spec_txt)

    def get_atoms(self):
        return deepcopy(self._atoms)

    def to_formatted_string(
            self,
            formatter
    ) -> str:
        return formatter.format(self)

    def to_asp(
            self,
            learning_names: Optional[List[str]] = None,
            for_clingo: bool = False,
            hm: IHeuristicManager = NoFilterHeuristicManager()
    ) -> str:
        if learning_names is None:
            learning_names = []
        formulas_str = ""
        for _, row in self._formulas_df.iterrows():
            formulas_str += self._formula_to_asp_str(row, learning_names, for_clingo, hm)
            formulas_str += "\n\n"
        return formulas_str

    def _formula_to_asp_str(self, row, learning_names, for_clingo, hm: IHeuristicManager):
        if row.when == GR1TemporalType.JUSTICE and row['name'] not in learning_names and not for_clingo:
            return ""
        formula: GR1Formula = row.formula
        expression_string = f"%{row.type.to_asp()} -- {row['name']}\n"
        expression_string += f"%\t{formula.to_str(self._formater)}\n\n"
        expression_string += f"{row.type.to_asp()}({row['name']}).\n\n"
        is_exception = (row['name'] in learning_names) and not for_clingo
        ant_exception = is_exception and hm.is_enabled("ANTECEDENT_WEAKENING")
        gar_exception = is_exception and hm.is_enabled("CONSEQUENT_WEAKENING")
        ev_exception = is_exception and hm.is_enabled("INVARIANT_TO_RESPONSE_WEAKENING")
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

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.to_str()

    def to_str(self, is_to_compile: bool = False,
               dialect: "TemporalDialect" = None) -> str:
        """
        Convert the specification to a string representation.

        `dialect` chooses how the always-operators are spelled - see
        TemporalDialect. It rewrites only the operator that begins a formula,
        so a `G` inside an expression, or a variable whose name starts with
        one, is untouched.
        """
        dialect = dialect or TemporalDialect.default()
        spec_str = f"module {self._module_name}\n\n"
        for atom in sorted(self._atoms):
            spec_str += f"{atom.atom_type} {atom.value_type} {atom.name};\n"
        spec_str += "\n\n"

        self._formater.is_response_pattern = is_to_compile

        for _, row in self._formulas_df.iterrows():
            spec_str += f"{row['type'].to_str()} -- {row['name']}\n"
            spec_str += f"\t{row['formula'].to_str(self._formater)};\n\n"

        if is_to_compile and "pRespondsToS" in spec_str:
            spec_str += self._response_pattern
        self._formater.is_response_pattern = False
        if dialect is not TemporalDialect.G:
            # GF before G, or `GF(` would be rewritten to `alw F(`.
            spec_str = re.sub(r"(?m)^(\s*)GF\(", rf"\1{dialect.justice}(", spec_str)
            spec_str = re.sub(r"(?m)^(\s*)G\(", rf"\1{dialect.invariant}(", spec_str)
        return spec_str

    def __deepcopy__(self, memo):
        new_spec = SpectraSpecification("")
        new_spec._module_name = self._module_name
        new_spec._formulas_df = self._formulas_df.copy(deep=True)
        for col in new_spec._formulas_df.columns:
            if new_spec._formulas_df[col].dtype == 'O':  # Object dtype means it might contain class instances
                new_spec._formulas_df[col] = new_spec._formulas_df[col].apply(lambda x: deepcopy(x, memo))
        new_spec._atoms = deepcopy(self._atoms, memo)
        return new_spec

    def __hash__(self) -> int:
        """
        Generate a hash for the specification based on its module name and formulas.
        """
        return hash((self._module_name, tuple(self._formulas_df.itertuples(index=False, name=None))))

    def __eq__(self, other) -> bool:
        return (self.equivalent_to(other, GR1FormulaType.ASM)
                and
                self.equivalent_to(other, GR1FormulaType.GAR))

    def __ne__(self, other) -> bool:
        # Define the not equal comparison
        return not self.__eq__(other)

    def __le__(self, other):
        """
        Check if this specification is equivalent to or implies the other specification.
        """
        return self.equivalent_to(other) or self.implies(other)

    def __lt__(self, other):
        """
        Check if this specification implies the other specification.
        """
        return self.implies(other)

    def __ge__(self, other):
        """
        Check if this specification is equivalent to or is implied by the other specification.
        """
        return self.equivalent_to(other) or self.implied_by(other)

    def __gt__(self, other):
        """
        Check if this specification is implied by the other specification.
        """
        return self.implied_by(other)

    def is_trivial_true(self, formula_type: Optional[GR1FormulaType]=None) -> bool:
        return self.is_equivalent_to_spot("G(true)", formula_type)

    def is_trivial_false(self, formula_type: Optional[GR1FormulaType]=None) -> bool:
        return self.is_equivalent_to_spot("G(false)", formula_type)

    def equivalent_to(self, other, formula_type: Optional[GR1FormulaType] = None) -> bool:
        f1 = self.to_formatted_string(SpotSpecificationFormatter(formula_type))
        f2 = other.to_formatted_string(SpotSpecificationFormatter(formula_type))
        return are_equivalent(f1, f2)

    def implies(self, other, formula_type: Optional[GR1FormulaType] = None) -> bool:
        f1 = self.to_formatted_string(SpotSpecificationFormatter(formula_type))
        f2 = other.to_formatted_string(SpotSpecificationFormatter(formula_type))
        return does_left_imply_right(f1, f2)

    def implied_by(self, other, formula_type: Optional[GR1FormulaType] = None) -> bool:
        return other.implies(self, formula_type)

    def is_equivalent_to_spot(self, formula: str, formula_type: Optional[GR1FormulaType]):
        f1 = self.to_formatted_string(SpotSpecificationFormatter(formula_type))
        return are_equivalent(f1, formula)

    def get_weakness(self, type: GR1FormulaType = GR1FormulaType.ASM) -> Weakness:
        """
        Calculate weakness measure between two specifications based on Davide Cavezza's paper
        "A Weakness Measure for GR(1) Formulae". This method implements the quantitative
        weakness relation where a higher value indicates a weaker (more permissive) specification.
        The measure is calculated by comparing the traces accepted by both specifications.

        Args:
            type: The type of formulas to compare (assumptions or guarantees)

        Returns:
            Tuple containing:
                - float: First component of the weakness measure (entropy-based)
                - float: Second component of the weakness measure (Hausdorff distance-based)
                - int: Third component indicating total number of traces
                - float: Third component of the weakness measure (Hausdorff distance-based on Fairness formulas)
        """

        formatter = SpotSpecificationFormatter(type, not_initial=True)
        this_spot: str = self.to_formatted_string(formatter)
        signature: List[str] = [atom.name for atom in self.get_atoms()]
        return computeWeakness(this_spot, signature)

    def add_formula(self, new_formula: GR1Formula, name: str, formula_type: GR1FormulaType):
        when: GR1TemporalType = new_formula.temp_type
        # Check if a formula with the same name, type, and when already exists
        existing = self._formulas_df[
            (self._formulas_df['name'] == name)
            ]

        if not existing.empty:
            raise NameClashException(
                f"Formula with name '{name}', type '{formula_type}', and temporal type '{when}' already exists"
            )

        new_row = pd.DataFrame([[name, formula_type, when, new_formula]], columns=["name", "type", "when", "formula"])
        self._formulas_df = pd.concat([self._formulas_df, new_row], ignore_index=True)

    def rename_formula(self, old_name: str, new_name: str):
        # Check if old_name exists
        existing_old = self._formulas_df[self._formulas_df['name'] == old_name]
        if existing_old.empty:
            raise ValueError(f"Formula with name '{old_name}' does not exist")

        # Check if new_name would create a clash
        existing_new = self._formulas_df[self._formulas_df['name'] == new_name]
        if not existing_new.empty:
            raise NameClashException(f"Formula with name '{new_name}' already exists")

        # Update the name
        self._formulas_df.loc[self._formulas_df['name'] == old_name, 'name'] = new_name

    def remove_formula(self, name: str):
        # Check if formula exists
        existing = self._formulas_df[self._formulas_df['name'] == name]
        if existing.empty:
            raise ValueError(f"Formula with name '{name}' does not exist")

        # Remove the formula
        self._formulas_df = self._formulas_df[self._formulas_df['name'] != name].reset_index(drop=True)

    def merge(self, other: Self) -> Self:
        """
        Merge this specification with another specification.
        Returns a new specification containing all distinct formulas from both specifications.

        - If name and formula are identical, skip the duplicate
        - If names clash but formulas differ, rename both with counter suffix (name_0, name_1)

        Args:
            other: The specification to merge with this one

        Returns:
            A new merged specification
        """
        merged_spec = deepcopy(self)

        # Track all formula names and their formulas for clash detection
        name_to_formulas: dict[str, list[tuple[GR1Formula, GR1FormulaType, GR1TemporalType, str]]] = {}


        # Collect all existing names from both specifications for clash detection
        all_existing_names: Set[str] = set()
        for _, row in merged_spec._formulas_df.iterrows():
            all_existing_names.add(row['name'])
        for _, row in other._formulas_df.iterrows():
            all_existing_names.add(row['name'])


        # Helper function to generate unique name
        def generate_unique_name(base_name: str, counter: int) -> str:
            while True:
                candidate = f"{base_name}_{counter}"
                if candidate not in all_existing_names:
                    all_existing_names.add(candidate)
                    return candidate
                counter += 1


        # Collect formulas from the current specification
        for _, row in merged_spec._formulas_df.iterrows():
            name: str = row['name']
            if name not in name_to_formulas:
                name_to_formulas[name] = []
            name_to_formulas[name].append((row['formula'], row['type'], row['when'], 'self'))

        # Helper function to check if equivalent formula already exists
        def has_equivalent_formula(target_formula: GR1Formula, target_type: GR1FormulaType) -> bool:
            for formulas_list in name_to_formulas.values():
                for existing_formula, existing_type, _, _ in formulas_list:
                    if existing_type == target_type and existing_formula == target_formula:
                        return True
            return False

        # Process formulas from the other specification
        for _, row in other._formulas_df.iterrows():
            name = row['name']
            formula = row['formula']
            formula_type = row['type']
            when = row['when']

            # Skip if an equivalent formula with the same type already exists
            if has_equivalent_formula(formula, formula_type):
                continue

            if name not in name_to_formulas:
                # No clash, add directly
                name_to_formulas[name] = [(formula, formula_type, when, 'other')]
            else:
                # Check if identical formula with same name already exists
                is_duplicate = False
                for existing_formula, existing_type, existing_when, _ in name_to_formulas[name]:
                    if (existing_formula == formula and
                            existing_type == formula_type and
                            existing_when == when):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    # Name clash with different formula
                    name_to_formulas[name].append((formula, formula_type, when, 'other'))

        # Rebuild the specification with renamed formulas where needed
        merged_spec._formulas_df = pd.DataFrame(columns=["name", "type", "when", "formula"])

        for base_name, formulas_list in name_to_formulas.items():
            if len(formulas_list) == 1:
                # No clash, use original name
                formula, formula_type, when, _ = formulas_list[0]
                new_row = pd.DataFrame([[base_name, formula_type, when, formula]],
                                       columns=["name", "type", "when", "formula"])
                merged_spec._formulas_df = pd.concat([merged_spec._formulas_df, new_row], ignore_index=True)
            else:
                # Multiple formulas with same name, rename with counter
                for idx, (formula, formula_type, when, _) in enumerate(formulas_list):
                    new_name = generate_unique_name(base_name, idx)
                    new_row = pd.DataFrame([[new_name, formula_type, when, formula]],
                                                   columns=["name", "type", "when", "formula"])
                    merged_spec._formulas_df = pd.concat([merged_spec._formulas_df, new_row], ignore_index=True)

        # Merge atoms from both specifications
        merged_spec._atoms = self._atoms.union(other._atoms)

        return merged_spec


def are_equivalent(left_exp: str, right_exp: str) -> bool:
    """
    Equivalence through `ltlfilt`, in a subprocess, never in this process.

    `spot.formula()` interns formula nodes, and on a large formula that
    interning segfaults - `spot::fnode::unique`, SIGSEGV, si_addr 0x30, a null
    dereference. Because `import spot` loads libspot into *this* process,
    alongside the JVM, the crash takes the whole run with it: amba's trace 3
    lost a six-hour repair at the merge, and the same frame killed runs during
    the sweeps.

    A subprocess cannot do that. If ltlfilt dies, one comparison fails and the
    caller sees an exception it can handle, which is exactly how
    `does_left_imply_right` has always worked - equivalence simply never
    followed suit.
    """
    cmd = [_ltlfilt_cmd(), "-c", "-f", left_exp, LTLFiltOperation.EQUIVALENT.flag(), right_exp]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout_bytes, stderr_bytes = p.communicate()
    output = stdout_bytes.decode("utf-8")
    reg = re.search(r"([01])\n", output)
    if not reg:
        raise Exception(
            f"ltlfilt failed (exit {p.returncode}) during the equivalence check.\n"
            f"ltlfilt said: {stderr_bytes.decode('utf-8', 'replace').strip() or '<nothing on stderr>'}\n"
            f"left:\n{left_exp}\nright:\n{right_exp}")
    return reg.group(1) == "1"


_LTLFILT_ENV = "SPEC_REPAIR_LTLFILT"


def _ltlfilt_cmd() -> str:
    """
    Which `ltlfilt` to run. `SPEC_REPAIR_LTLFILT=/path/to/ltlfilt` overrides.

    Stock Spot is compiled with a ceiling of 32 acceptance sets, and a whole-GR1
    comparison exceeds it as soon as a specification carries enough liveness:
    `ltlfilt: Too many acceptance sets used.  The limit is 32.`, exit 2. That is
    what stopped the `gr1` implication graphs for amba trace 0 and lift traces 2
    and 3 on 2026-08-16, while `asm` and `gar` stayed under the ceiling and drew
    fine.

    Spot's own advice is to recompile, so /vol/bitbucket/tg4018/spot-maxacc is
    2.14.5 built with `--enable-max-accsets=128`. Point this at it - and at its
    lib directory on LD_LIBRARY_PATH - to draw those graphs.
    """
    return os.environ.get(_LTLFILT_ENV, "").strip() or "ltlfilt"


def does_left_imply_right(left_exp: str, right_exp: str) -> bool:
    # TODO: introduce an assertion against ltl_ops which do not exist yet
    linux_cmd = [_ltlfilt_cmd(), "-c", "-f", f"{left_exp}", "--imply", f"{right_exp}"]
    p = subprocess.Popen(linux_cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_bytes, stderr_bytes = p.communicate()
    output: str = stdout_bytes.decode('utf-8')
    reg = re.search(r"([01])\n", output)
    if not reg:
        # ltlfilt's own message, not just "unexpected output". Three separate
        # failures hid behind the old wording in one day: an ltlfilt/libspot ABI
        # mismatch (exit 127), Spot's 32 acceptance-set ceiling (exit 2), and a
        # third still being diagnosed. Each cost an investigation that the first
        # line of stderr would have answered.
        raise Exception(
            f"ltlfilt failed (exit {p.returncode}) during the comparison.\n"
            f"ltlfilt said: {stderr_bytes.decode('utf-8', 'replace').strip() or '<nothing on stderr>'}\n"
            f"left:\n{left_exp}\nright:\n{right_exp}",
        )
    result = reg.group(1)
    return result == "1"

