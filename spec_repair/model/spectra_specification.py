import copy
import logging
import os
import re
import subprocess
import time
import tempfile
from collections import Counter
from copy import deepcopy
from typing import TypedDict, Optional, TypeVar, List, Set, Any, Callable

import pandas as pd
import spot

from spec_repair.exceptions import EquivalenceUndecided
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
from spec_repair.util.file_util import (generate_temp_filename, read_file_lines,
                                        validate_spectra_file, write_to_file)
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


def _equivalent_via_stdin(left_exp: str, right_exp: str) -> bool:
    """
    `left <-> right` checked without either formula on the command line.

    Same trick as `_implies_via_stdin`: an empty automaton for
    `!(left <-> right)` means the two cannot differ on any word.
    """
    formula = f"!(({left_exp}) <-> ({right_exp}))\n"
    ltl2tgba = _ltlfilt_cmd().replace("ltlfilt", "ltl2tgba")
    autfilt = _ltlfilt_cmd().replace("ltlfilt", "autfilt")
    translate = subprocess.Popen([ltl2tgba, "-F", "-"], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 preexec_fn=_raise_stack_limit)
    check = subprocess.Popen([autfilt, "--is-empty", "--quiet"],
                             stdin=translate.stdout, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, preexec_fn=_raise_stack_limit)
    translate.stdout.close()
    translate.stdin.write(formula.encode("utf-8"))
    translate.stdin.close()
    check.communicate()
    translate_err = translate.stderr.read().decode("utf-8", "replace")
    translate.wait()
    if translate.returncode != 0:
        # Keep the input. A tool that dies on a signal says nothing on stderr,
        # and the formula is the only way to find out why - elevator trace 0
        # crashed ltl2tgba with SIGSEGV here on 2026-08-16.
        dump = _crash_dump_path()
        write_to_file(dump, formula)
        raise Exception(
            f"ltl2tgba failed (exit {translate.returncode}) during the equivalence check.\n"
            f"it said: {translate_err.strip() or '<nothing on stderr>'}\n"
            f"formula ({len(formula)} chars) written to {dump}")
    return check.returncode == 0


# A residue this size is decided in well under a second; past it the
# shortcut stops being a shortcut.
_MAX_RESIDUE_CHARS = 3000


def _split_top_level(formula: str) -> Optional[tuple]:
    """
    `formula` as (operator, operands) split at the outermost operator.

    Recognises the two shapes this module builds: a whole specification is
    `(assumptions) -> (guarantees)`, and each side is a conjunction. Returns
    None for anything else, which simply means no shortcut is attempted.
    """
    f = formula.strip()
    depth, arrows, ands = 0, [], []
    i = 0
    while i < len(f):
        ch = f[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and f.startswith("->", i):
            arrows.append(i)
            i += 1
        elif depth == 0 and ch == "&":
            ands.append(i)
        i += 1
    if len(arrows) == 1:
        return "->", [f[:arrows[0]].strip(), f[arrows[0] + 2:].strip()]
    if arrows:
        return None                      # nested implications: not our shape
    if ands:
        parts, prev = [], 0
        for j in ands:
            parts.append(f[prev:j].strip())
            prev = j + 1
        parts.append(f[prev:].strip())
        return "&", [p for p in parts if p]
    if f.startswith("(") and f.endswith(")"):
        inner = _split_top_level(f[1:-1])
        return inner
    return None


def _equivalent_by_structure(left_exp: str, right_exp: str, depth: int = 0) -> bool:
    """
    True when the two formulas can be *proved* equivalent structurally.

    Sound and one-directional: a False result means "not proved", never "not
    equivalent", so the exact check still runs. It never decides equivalence
    wrongly, and it only ever saves work.

    Two reductions, both standard:

    * `A1 -> B1` and `A2 -> B2` are equivalent if `A1 == A2` and `B1 == B2`.
      Each side is far smaller than the implication, and a whole-specification
      comparison is exactly this shape.
    * `C & L` and `C & R` are equivalent if `L == R`. The shared conjuncts are
      usually nearly all of them: on the genbuf pair that held gpu08 for 23
      hours, the guarantee sides share 105 of 108 conjuncts, so the residue is
      3 conjuncts of 342 characters rather than 7.6KB.

    The converse of neither holds - a shared context can mask a difference - so
    failure here proves nothing.
    """
    if left_exp.strip() == right_exp.strip():
        return True
    if depth > 3:
        return False
    left = _split_top_level(left_exp)
    right = _split_top_level(right_exp)
    if not left or not right or left[0] != right[0]:
        return False
    op, left_parts, right_parts = left[0], left[1], right[1]

    if op == "->":
        # Structural proof only. Falling back to an exact check per side would
        # defeat the point: the guarantee side of a specification is nearly the
        # whole formula, so that check costs about what the one being avoided
        # costs.
        return all(_equivalent_by_structure(a, b, depth + 1)
                   for a, b in zip(left_parts, right_parts))

    left_set, right_set = set(left_parts), set(right_parts)
    if left_set == right_set:
        return True                      # same conjuncts, any order
    left_only = [p for p in left_parts if p not in right_set]
    right_only = [p for p in right_parts if p not in left_set]
    if not left_only or not right_only or not (left_set & right_set):
        # One side subsumes the other, or nothing is shared. `C` versus `C & R`
        # is equivalent exactly when C implies R, which is not what this
        # answers, so say nothing.
        return False
    residue_left, residue_right = "&".join(left_only), "&".join(right_only)
    if max(len(residue_left), len(residue_right)) > _MAX_RESIDUE_CHARS:
        # The residue is no longer small enough to be obviously cheap, and this
        # shortcut exists only to be cheap.
        return False
    return _are_equivalent_exact(residue_left, residue_right)


def are_equivalent(left_exp: str, right_exp: str) -> bool:
    """
    Equivalence of two formulas, cheaply where possible and exactly otherwise.

    The structural shortcut runs first: it can only ever prove equivalence, and
    when it cannot, `_are_equivalent_exact` gives the exact answer.
    """
    if _equivalent_by_structure(left_exp, right_exp):
        return True
    return _are_equivalent_exact(left_exp, right_exp)


def _are_equivalent_exact(left_exp: str, right_exp: str) -> bool:
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
    if (len(left_exp.encode("utf-8")) > _MAX_ARG_BYTES
            or len(right_exp.encode("utf-8")) > _MAX_ARG_BYTES):
        return _equivalent_via_stdin(left_exp, right_exp)
    cmd = [_ltlfilt_cmd(), "-c", "-f", left_exp, LTLFiltOperation.EQUIVALENT.flag(), right_exp]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                         stderr=subprocess.PIPE, preexec_fn=_raise_stack_limit)
    try:
        stdout_bytes, stderr_bytes = p.communicate(timeout=_equiv_timeout())
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        raise EquivalenceUndecided(
            f"ltlfilt did not decide equivalence within "
            f"{_equiv_timeout()}s ({len(left_exp)} and {len(right_exp)} "
            f"characters).") from None
    output = stdout_bytes.decode("utf-8")
    reg = re.search(r"([01])\n", output)
    if not reg:
        raise Exception(
            f"ltlfilt failed (exit {p.returncode}) during the equivalence check.\n"
            f"ltlfilt said: {stderr_bytes.decode('utf-8', 'replace').strip() or '<nothing on stderr>'}\n"
            f"left:\n{left_exp}\nright:\n{right_exp}")
    return reg.group(1) == "1"


_LTLFILT_ENV = "SPEC_REPAIR_LTLFILT"
_EQUIV_TIMEOUT_ENV = "SPEC_REPAIR_EQUIV_TIMEOUT"


def _equiv_timeout() -> Optional[float]:
    """
    Seconds to allow one equivalence check, from `SPEC_REPAIR_EQUIV_TIMEOUT`.

    Unset or 0 means no limit, which is the historical behaviour and the only
    one that answers exactly. A limit turns a check that would not converge into
    an `EquivalenceUndecided` the caller must handle, rather than a process that
    holds a machine for a day.
    """
    raw = os.environ.get(_EQUIV_TIMEOUT_ENV, "").strip()
    if not raw:
        return None
    seconds = float(raw)
    return seconds if seconds > 0 else None


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


# Linux caps a single argv entry at 128KB (MAX_ARG_STRLEN). Merged
# specifications pass that: conjoining 21 of them produced a formula that
# failed with `OSError: [Errno 7] Argument list too long` on 2026-08-16.
_MAX_ARG_BYTES = 100_000


def _raise_stack_limit() -> None:
    """
    Give the child as much stack as it is allowed.

    Spot's translation recurses over the formula tree, so a deeply nested
    formula overflows the default 8MB stack and the process dies on SIGSEGV
    with nothing on stderr. Merging elevator's 21 solutions produces a formula
    59,004 `X` operators deep, which does exactly that - and the same formula
    translates fine once the stack is raised.

    preexec_fn runs in the child after fork, so this affects only the tool.
    """
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
        if hard != resource.RLIM_INFINITY and soft >= hard:
            return
        resource.setrlimit(resource.RLIMIT_STACK, (hard, hard))
    except Exception:  # noqa: BLE001 - a tighter stack is not worth failing over
        pass


def _crash_dump_path() -> str:
    """
    Somewhere a crashing formula survives.

    `generate_temp_filename` puts files in the run's scratch directory, which is
    swept when the process exits - so the first dump of the formula that kills
    ltl2tgba was gone before it could be read.
    """
    directory = os.environ.get("SPEC_REPAIR_CRASH_DIR", "").strip() or tempfile.gettempdir()
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, f"spec_repair_crash_{os.getpid()}_{time.time_ns()}.ltl")


def _implies_via_stdin(left_exp: str, right_exp: str) -> bool:
    """
    `left -> right` checked without putting either formula on the command line.

    Feeds `!(left -> right)` to `ltl2tgba` on stdin and asks `autfilt` whether
    the automaton is empty: empty means the negation is unsatisfiable, so the
    implication holds. Same verdict as `ltlfilt --imply`, no argv limit.
    """
    formula = f"!(({left_exp}) -> ({right_exp}))\n"
    ltl2tgba = _ltlfilt_cmd().replace("ltlfilt", "ltl2tgba")
    autfilt = _ltlfilt_cmd().replace("ltlfilt", "autfilt")
    translate = subprocess.Popen([ltl2tgba, "-F", "-"], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 preexec_fn=_raise_stack_limit)
    check = subprocess.Popen([autfilt, "--is-empty", "--quiet"],
                             stdin=translate.stdout, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, preexec_fn=_raise_stack_limit)
    translate.stdout.close()
    translate.stdin.write(formula.encode("utf-8"))
    translate.stdin.close()
    check.communicate()
    translate_err = translate.stderr.read().decode("utf-8", "replace")
    translate.wait()
    if translate.returncode != 0:
        dump = _crash_dump_path()
        write_to_file(dump, formula)
        raise Exception(
            f"ltl2tgba failed (exit {translate.returncode}) during the comparison.\n"
            f"it said: {translate_err.strip() or '<nothing on stderr>'}\n"
            f"formula ({len(formula)} chars) written to {dump}")
    return check.returncode == 0


def does_left_imply_right(left_exp: str, right_exp: str) -> bool:
    # TODO: introduce an assertion against ltl_ops which do not exist yet
    if (len(left_exp.encode("utf-8")) > _MAX_ARG_BYTES
            or len(right_exp.encode("utf-8")) > _MAX_ARG_BYTES):
        return _implies_via_stdin(left_exp, right_exp)
    linux_cmd = [_ltlfilt_cmd(), "-c", "-f", f"{left_exp}", "--imply", f"{right_exp}"]
    p = subprocess.Popen(linux_cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                         stderr=subprocess.PIPE, preexec_fn=_raise_stack_limit)
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

