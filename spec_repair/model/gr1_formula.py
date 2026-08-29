from copy import deepcopy
from typing import List, TypeVar, Optional

import spot

from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.helpers.formatters.spot_formula_formatter import SpotFormulaFormatter
from spec_repair.helpers.parsers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.util.ltl_formula_util import normalize_to_pattern, disjoin_all, get_disjuncts_from_disjunction
from spec_repair.util.formula_string_util import replace_false_true

from py_ltl.parser import ILTLParser
from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Next, Prev, Globally, Eventually, \
    Implies, Top, Bottom

Self = TypeVar('T', bound='SpectraRule')


class GR1Formula:
    def __init__(
            self,
            temp_type: GR1TemporalType,
            antecedent: Optional[LTLFormula],
            consequent: LTLFormula
    ):
        self.temp_type = temp_type
        self.antecedent = antecedent
        self.consequent = consequent
        # TODO: create separate parser for ILASP output. for now use this
        self.ilasp_parser = SpectraFormulaParser()
        self.spot_formatter = SpotFormulaFormatter()

    @staticmethod
    def from_str(formula: str, parser: ILTLParser) -> Self:
        """
        Parse a formula from a Spectra file into a SpectraFormula object.

        Args:
            formula (str): The input formula to parse.

        Returns:
            GR1Formula: A SpectraFormula object containing the parsed formula.
        """
        parsed_formula: LTLFormula = parser.parse(formula)
        return GR1Formula.from_ltl_formula(parsed_formula)

    @staticmethod
    def from_ltl_formula(parsed_formula: LTLFormula) -> Self:
        parsed_formula = normalize_to_pattern(parsed_formula)
        temp_type, antecedent, consequent = GR1Formula._from_normal_ltl_formula(parsed_formula)
        return GR1Formula(temp_type, antecedent, consequent)

    @staticmethod
    def _from_normal_ltl_formula(parsed_formula):
        """
        precondition: parsed_formula is in a normal form
        """
        if not isinstance(parsed_formula, Globally):
            temp_type = GR1TemporalType.INITIAL
        else:
            parsed_formula = parsed_formula.formula
            if isinstance(parsed_formula, Eventually):
                temp_type = GR1TemporalType.JUSTICE
                parsed_formula = parsed_formula.formula
            else:
                temp_type = GR1TemporalType.INVARIANT
        if isinstance(parsed_formula, Implies):
            antecedent = parsed_formula.left
            consequent = parsed_formula.right
        else:
            antecedent = None
            consequent = parsed_formula
        return temp_type, antecedent, consequent

    def _normalize(self):
        ltl_formula: LTLFormula = self._to_ltl_formula()
        parsed_formula = normalize_to_pattern(ltl_formula)
        self.temp_type, self.antecedent, self.consequent = GR1Formula._from_normal_ltl_formula(parsed_formula)

    def _to_ltl_formula(self) -> LTLFormula:
        if self.antecedent is None:
            implication = self.consequent
        else:
            implication = Implies(self.antecedent, self.consequent)
        match self.temp_type:
            case GR1TemporalType.INITIAL:
                return implication
            case GR1TemporalType.INVARIANT:
                return Globally(implication)
            case GR1TemporalType.JUSTICE:
                return Globally(Eventually(implication))
            case _:
                raise ValueError(f"Unsupported temporal type: {self.temp_type}")

    def to_ltl_formula(self) -> LTLFormula:
        if self.antecedent is None:
            implication = deepcopy(self.consequent)
        else:
            implication = deepcopy(Implies(self.antecedent, self.consequent))
        match self.temp_type:
            case GR1TemporalType.INITIAL:
                return implication
            case GR1TemporalType.INVARIANT:
                return Globally(implication)
            case GR1TemporalType.JUSTICE:
                return Globally(Eventually(implication))
            case _:
                raise ValueError(f"Unsupported temporal type: {self.temp_type}")

    def to_str(self, formatter: ILTLFormatter) -> str:
        return self.to_ltl_formula().format(formatter)

    def integrate_all(self, adaptations: List[Adaptation]):
        """
        Apply a whole learned solution to this formula.

        Antecedent exceptions are applied together, because their
        `disjunction_index` values all number the *same* antecedent; see
        `_integrate_antecedent_exceptions`. Everything else is order-independent
        and goes through `integrate` one at a time.
        """
        antecedent = [a for a in adaptations if a.type == "antecedent_exception"]
        if antecedent:
            self._integrate_antecedent_exceptions(antecedent)
            self._normalize()
        for adaptation in adaptations:
            if adaptation.type != "antecedent_exception":
                self.integrate(adaptation)

    def integrate(self, adaptation: Adaptation):
        # TODO: move this to adaptation_learned.py
        match adaptation.type:
            case "antecedent_exception":
                self._integrate_antecedent_exception(adaptation)
            case "consequent_exception":
                self._integrate_consequent_exception(adaptation)
            case "ev_temp_op":
                if not self.antecedent:
                    self.temp_type = GR1TemporalType.JUSTICE
                else:
                    self.consequent = Eventually(self.consequent)

            case _:
                raise ValueError(f"Unsupported temporal type: {self.temp_type}")
        self._normalize()

    def _integrate_consequent_exception(self, adaptation: Adaptation):
        first_temp_op, first_atom_assignment = adaptation.atom_temporal_operators[0]
        new_disjunct = self._generate_literal(first_atom_assignment, first_temp_op)
        for op, atom in adaptation.atom_temporal_operators[1:]:
            new_disjunct = And(new_disjunct, self._generate_literal(atom, op))
        if isinstance(self.consequent, Eventually):
            self.consequent = Eventually(Or(self.consequent.formula, new_disjunct))
        else:
            self.consequent = Or(self.consequent, new_disjunct)

    def _integrate_antecedent_exception(self, adaptation: Adaptation):
        self._integrate_antecedent_exceptions([adaptation])

    def _integrate_antecedent_exceptions(self, adaptations: List[Adaptation]):
        """
        Apply every antecedent exception the learner returned, in one pass.

        A learned solution carries one `antecedent_exception` rule per disjunct
        of the antecedent, and each rule's `disjunction_index` numbers the
        disjuncts of the antecedent *as the encoder saw it*. Applying them one
        at a time rewrites the antecedent underneath the indices that have not
        been used yet - narrowing disjunct 0 removes it from the list and
        appends the narrowed version at the end, so index 1 no longer names what
        the learner meant. The disjunct that then goes unguarded is the one the
        violation comes through, which is how a search could record a repair
        that still fails its own trace.

        So the indices are resolved against the untouched antecedent and the new
        antecedent is built once, position by position.
        """
        if self.temp_type == GR1TemporalType.JUSTICE:
            self.temp_type = GR1TemporalType.INVARIANT
            self.consequent = Eventually(self.consequent)

        if self.antecedent is None:
            # No disjuncts to index into: the exception becomes the antecedent.
            for adaptation in adaptations:
                for op, atom in adaptation.atom_temporal_operators:
                    literal = self._generate_literal(replace_false_true(atom), op)
                    self.antecedent = (literal if self.antecedent is None
                                       else Or(self.antecedent, literal))
            return

        original = get_disjuncts_from_disjunction(self.antecedent)
        by_index: dict[int, List[Adaptation]] = {}
        for adaptation in adaptations:
            by_index.setdefault(adaptation.disjunction_index, []).append(adaptation)

        rewritten: List = []
        for index, disjunct in enumerate(original):
            if index not in by_index:
                rewritten.append(disjunct)
                continue
            for adaptation in by_index[index]:
                for op, atom in adaptation.atom_temporal_operators:
                    literal = self._generate_literal(replace_false_true(atom), op)
                    rewritten.append(And(deepcopy(disjunct), literal))
        self.antecedent = disjoin_all(rewritten)

    def _generate_literal(self, atom, op):
        new_disjunct = self.ilasp_parser.parse(atom)
        match op:
            case "current":
                pass
            case "eventually":
                raise ValueError("eventually operator not supported in antecedent")
            case "next":
                new_disjunct = Next(new_disjunct)
            case "prev":
                new_disjunct = Prev(new_disjunct)
            case _:
                raise ValueError(f"Unsupported temporal operator: {op}")
        return new_disjunct

    def __hash__(self):
        antecedent_hash = hash(str(self.antecedent)) if self.antecedent is not None else 0
        return hash((self.temp_type, str(antecedent_hash), hash(str(self.consequent))))

    def __eq__(self, other):
        """
        Semantic equality, through `ltlfilt` in a subprocess.

        It used to call `spot.formula` and `spot.are_equivalent` in *this*
        process. libspot is loaded alongside the JVM by jpype, so a crash in
        `spot::fnode::unique` (SIGSEGV, `si_addr 0x30`) takes the whole run
        down - the same fault that was moved out of `spectra_specification`
        on 2026-08-13 and missed here.

        `merge` compares formulas to detect duplicates, so this ran on every
        merge: elevator trace 0 segfaulted with exit 139 in step 2 on 21
        specifications, and twelve runs failed to merge for the same reason.
        """
        if other is None or not isinstance(other, GR1Formula):
            return NotImplemented
        # Imported here, not at module scope: spectra_specification imports this
        # module, so a top-level import would be circular.
        from spec_repair.model.spectra_specification import are_equivalent
        return are_equivalent(self.to_str(formatter=self.spot_formatter),
                              other.to_str(formatter=self.spot_formatter))

    def __repr__(self):
        return self.to_str(formatter=self.spot_formatter)

    @staticmethod
    def remove_temporal_operators(this_formula: LTLFormula) -> LTLFormula:
        match this_formula:
            case AtomicProposition(name=name, value=value):
                return this_formula
            case Not(formula=formula):
                return Not(GR1Formula.remove_temporal_operators(formula))
            case And(left=lhs, right=rhs):
                return And(
                    left=GR1Formula.remove_temporal_operators(lhs),
                    right=GR1Formula.remove_temporal_operators(rhs)
                )
            case Or(left=lhs, right=rhs):
                return Or(
                    left=GR1Formula.remove_temporal_operators(lhs),
                    right=GR1Formula.remove_temporal_operators(rhs)
                )
            case Implies(left=lhs, right=rhs):
                return Implies(
                    left=GR1Formula.remove_temporal_operators(lhs),
                    right=GR1Formula.remove_temporal_operators(rhs)
                )
            case Next(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Prev(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Eventually(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Globally(formula=formula):
                return GR1Formula.remove_temporal_operators(formula)
            case Top():
                return Top()
            case Bottom():
                return Bottom()
            case _:
                raise NotImplementedError(f"Removing temporal operators not implemented for: {type(this_formula)}")
