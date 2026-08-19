from copy import deepcopy
from typing import Tuple, Optional

from py_ltl.formatter import ILTLFormatter
from py_ltl.formula import LTLFormula, AtomicProposition, Not, And, Or, Until, Next, Globally, Eventually, Implies, \
    Prev, Top, Bottom


class SpotFormulaFormatter(ILTLFormatter):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def format_dwyer_response_aware(self, this_formula: LTLFormula, dwyer_index: int=0) -> Tuple[str, int]:
        spot_formula = self.format(this_formula)
        if self._contains_response_pattern(spot_formula):
            spot_formula, dwyer_index = self._apply_dwyer_response_pattern(spot_formula, dwyer_index)
        return spot_formula, dwyer_index

    def format(self, this_formula: LTLFormula) -> str:
        # Never risk modifying the original formula
        this_formula = deepcopy(this_formula)
        spot_formula, shift = self._format(this_formula, shift_in=0)
        return spot_formula

    def _format(self, this_formula: LTLFormula, shift_in: int) -> Tuple[str, int]:
        match this_formula:
            case AtomicProposition(name=name, value=True):
                # shift_out is what this subformula asks the *context* to add,
                # and an atom asks for nothing. Returning shift_in here made the
                # binary cases below compound it - see the note there.
                return self._apply_shift(name, shift_in), 0
            case AtomicProposition(name=name, value=False):
                return self._apply_shift(f"!{name}", shift_in), 0
            case Not(formula=formula):
                inner_formula, new_shift_out = self._format(formula, shift_in)
                return f"!({inner_formula})", new_shift_out
            case And(left=left, right=right):
                # Both sides are evaluated at the same point, so both get the
                # same shift_in. Passing `shift_in + left_shift_out` to the
                # right made the shift double at every binary node: with
                # shift_out for an atom being shift_in itself, a single PREV in
                # a formula of 300 conjuncts compounded to 59,304 X operators
                # and 205,261 characters, which ltl2tgba answers with
                # std::bad_alloc. Whichever side reaches further into the past
                # sets the depth; the shallower side is padded to match.
                lhs, left_shift_out = self._format(left, shift_in)
                rhs, right_shift_out = self._format(right, shift_in)
                depth = max(left_shift_out, right_shift_out)
                lhs = self._apply_shift(lhs, depth - left_shift_out)
                rhs = self._apply_shift(rhs, depth - right_shift_out)
                return f"({lhs} & {rhs})", depth
            case Or(left=left, right=right):
                # Both sides are evaluated at the same point, so both get the
                # same shift_in. Passing `shift_in + left_shift_out` to the
                # right made the shift double at every binary node: with
                # shift_out for an atom being shift_in itself, a single PREV in
                # a formula of 300 conjuncts compounded to 59,304 X operators
                # and 205,261 characters, which ltl2tgba answers with
                # std::bad_alloc. Whichever side reaches further into the past
                # sets the depth; the shallower side is padded to match.
                lhs, left_shift_out = self._format(left, shift_in)
                rhs, right_shift_out = self._format(right, shift_in)
                depth = max(left_shift_out, right_shift_out)
                lhs = self._apply_shift(lhs, depth - left_shift_out)
                rhs = self._apply_shift(rhs, depth - right_shift_out)
                return f"({lhs} | {rhs})", depth
            case Implies(left=left, right=right):
                # Both sides are evaluated at the same point, so both get the
                # same shift_in. Passing `shift_in + left_shift_out` to the
                # right made the shift double at every binary node: with
                # shift_out for an atom being shift_in itself, a single PREV in
                # a formula of 300 conjuncts compounded to 59,304 X operators
                # and 205,261 characters, which ltl2tgba answers with
                # std::bad_alloc. Whichever side reaches further into the past
                # sets the depth; the shallower side is padded to match.
                lhs, left_shift_out = self._format(left, shift_in)
                rhs, right_shift_out = self._format(right, shift_in)
                depth = max(left_shift_out, right_shift_out)
                lhs = self._apply_shift(lhs, depth - left_shift_out)
                rhs = self._apply_shift(rhs, depth - right_shift_out)
                return f"({lhs} -> {rhs})", depth
            case Next(formula=formula):
                inner_formula, new_shift_out = self._format(formula, shift_in)
                return f"X({inner_formula})", new_shift_out
            case Prev(formula=formula):
                # Shift everything in the subformula by +1
                new_formula, new_shift_out = self._format(formula, max(shift_in - 1, 0))
                return new_formula, new_shift_out + 1
            case Eventually(formula=formula):
                inner_formula, new_shift_out = self._format(formula, shift_in)
                return f"F({inner_formula})", new_shift_out
            case Globally(formula=formula):
                inner_formula, new_shift_out = self._format(formula, shift_in)
                return f"G({inner_formula})", new_shift_out
            case Top():
                return "true", shift_in
            case Bottom():
                return "false", shift_in
            case _:
                raise NotImplementedError(f"Spot formatting not implemented for: {type(this_formula)}")

    def _apply_dwyer_response_pattern(self, formula_str: str, dwyer_index: int) -> Tuple[str, int]:
        match = self._match_response_pattern(formula_str)
        if match is None:
            return formula_str, dwyer_index

        start, end, lhs, rhs = match
        replacement = self._DWYER_PLACEHOLDER(dwyer_index, lhs, rhs)
        new_formula_str = formula_str[:start] + replacement + formula_str[end:]
        return new_formula_str, dwyer_index + 1

    def _contains_response_pattern(self, spot_formula: str) -> bool:
        return self._match_response_pattern(spot_formula) is not None

    def _match_response_pattern(self, spot_formula: str) -> Optional[Tuple[int, int, str, str]]:
        """
        Scan for the first true response pattern G((lhs -> F(rhs))) and return
        (start, end, lhs, rhs) of the match, or None if there isn't one.

        Uses balanced-paren matching rather than a flat regex so it isn't
        fooled by lookalikes such as "(G(a) -> F(b))" -- that formula is a
        top-level implication between two *siblings* (G(a) and F(b)), not a
        Globally wrapping an Implies, so it must NOT be treated as a response
        pattern even though it contains the substrings "G(", "->" and "F(".
        It also correctly handles arbitrarily nested lhs/rhs (e.g. compound
        propositions), since it never assumes a fixed number of closing
        parens -- it always matches them.
        """
        search_from = 0
        while True:
            g_idx = spot_formula.find("G(", search_from)
            if g_idx == -1:
                return None

            open_idx = g_idx + 1  # index of the '(' right after 'G'
            try:
                close_idx = self._find_matching_paren(spot_formula, open_idx)
            except ValueError:
                return None  # unbalanced; nothing sane to find

            g_content = spot_formula[open_idx + 1:close_idx]

            # A genuine response pattern requires G(...) to wrap a SINGLE
            # fully-parenthesized Implies, i.e. g_content must itself be
            # exactly "(" + <implies body> + ")" with matching outer parens.
            if g_content.startswith("(") and g_content.endswith(")"):
                inner_close = self._find_matching_paren(g_content, 0) if g_content else -1
                if inner_close == len(g_content) - 1:
                    implies_body = g_content[1:-1]
                    arrow_idx = self._find_top_level_arrow(implies_body)
                    if arrow_idx != -1:
                        lhs = implies_body[:arrow_idx]
                        rhs_part = implies_body[arrow_idx + len(" -> "):]
                        if rhs_part.startswith("F(") and rhs_part.endswith(")"):
                            f_close = self._find_matching_paren(rhs_part, 1)
                            if f_close == len(rhs_part) - 1:
                                rhs = rhs_part[2:-1]
                                return g_idx, close_idx + 1, lhs, rhs

            # Not a response pattern at this G(...) -- keep scanning in case
            # there's another G(...) further along that does qualify.
            search_from = g_idx + 2

    def _find_matching_paren(self, s: str, open_idx: int) -> int:
        """Given the index of an opening '(' in s, return the index of its matching ')'."""
        depth = 0
        for i in range(open_idx, len(s)):
            if s[i] == "(":
                depth += 1
            elif s[i] == ")":
                depth -= 1
                if depth == 0:
                    return i
        raise ValueError(f"Unbalanced parentheses in: {s}")

    def _find_top_level_arrow(self, s: str) -> int:
        """Find the index of the top-level ' -> ' delimiter in s (paren depth 0), or -1."""
        depth = 0
        i = 0
        while i < len(s):
            c = s[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and s[i:i + 4] == " -> ":
                return i
            i += 1
        return -1

    def _apply_shift(self, formula_str: str, shift: int) -> str:
        for _ in range(shift):
            formula_str = f"X({formula_str})"
        return formula_str

    def _DWYER_PLACEHOLDER(self, index: int, lhs: str, rhs: str):
        return f"""\
!dwyer_state_{index} & \
G((!dwyer_state_{index} & (!({lhs}) | (({lhs}) & ({rhs}))) & X(!dwyer_state_{index})) | \
(!dwyer_state_{index} & (({lhs}) & !({rhs})) & X(dwyer_state_{index})) | \
(dwyer_state_{index} & ({rhs}) & X(!dwyer_state_{index})) | \
(dwyer_state_{index} & !({rhs}) & X(dwyer_state_{index}))) & \
GF(!dwyer_state_{index})\
"""

SpotFormulaFormatter.instance = SpotFormulaFormatter()