"""
Parser for the Strix HOA (Hanoi Omega Automata) counter-strategy format.

When a specification is unrealizable, Strix outputs the environment's winning
counter-strategy as an HOA automaton.  Example:

    HOA: v1
    tool: "strix" "21.0.0"
    States: 4
    Start: 0
    AP: 3 "methane" "highwater" "pump"
    controllable-AP: 0 1
    acc-name: all
    Acceptance: 0 t
    --BODY--
    State: 0 "[0]"
    [(!(0 | 1)) & (!2)] 1
    [(!(0 | 1)) & (2)] 2
    State: 1 "[1]"
    [(!(1 | !0)) & (t)] 3
    State: 2 "[2]"
    [(t) & (t)] 2
    State: 3 "[3]"
    [(0 & 1) & (t)] 2
    --END--

AP / controllable-AP mapping
----------------------------
In Strix's HOA counter-strategy output the ``controllable-AP`` header lists
the indices of the APs that the *counter-strategy controller* (i.e. the
**environment**) decides.  These therefore map to the ``inputs`` field of
``CSTransition``.  The remaining (non-controllable) APs are what the
**system** picks and map to ``outputs``.

This is consistent with the Spectra counter-strategy invariant: transitions
from the same source state share identical inputs but may differ in outputs.

Guard enumeration
-----------------
HOA transition guards are symbolic boolean formulas over AP indices, using
``t`` (tautology), integer literals, ``!`` (negation), ``&`` (conjunction),
and ``|`` (disjunction).  An unconstrained AP (appearing as ``t``) ranges
over both ``true`` and ``false``.  Each guard is fully enumerated into one
concrete ``CSTransition`` per satisfying assignment.

Trap / DEAD states
------------------
A state whose every outgoing transition loops back to itself is a *trap* state
— the environment keeps the system stuck forever.  Such states are renamed
``"DEAD"`` and are not expanded further (matching ``CounterStrategy``'s
``dead_state`` sentinel).  If multiple trap states exist, they all receive the
``"DEAD"`` label.
"""

from __future__ import annotations

import re
from itertools import product

from spec_repair.model.counter_strategy import CounterStrategy, CSTransition


# ── Boolean formula AST ───────────────────────────────────────────────────────

class _Expr:
    def evaluate(self, assignment: dict[int, bool]) -> bool:
        raise NotImplementedError


class _True(_Expr):
    def evaluate(self, _: dict[int, bool]) -> bool:
        return True


class _False(_Expr):
    def evaluate(self, _: dict[int, bool]) -> bool:
        return False


class _AP(_Expr):
    def __init__(self, idx: int):
        self.idx = idx

    def evaluate(self, assignment: dict[int, bool]) -> bool:
        return assignment[self.idx]


class _Not(_Expr):
    def __init__(self, child: _Expr):
        self.child = child

    def evaluate(self, assignment: dict[int, bool]) -> bool:
        return not self.child.evaluate(assignment)


class _And(_Expr):
    def __init__(self, left: _Expr, right: _Expr):
        self.left, self.right = left, right

    def evaluate(self, assignment: dict[int, bool]) -> bool:
        return self.left.evaluate(assignment) and self.right.evaluate(assignment)


class _Or(_Expr):
    def __init__(self, left: _Expr, right: _Expr):
        self.left, self.right = left, right

    def evaluate(self, assignment: dict[int, bool]) -> bool:
        return self.left.evaluate(assignment) or self.right.evaluate(assignment)


# ── Tokeniser + recursive-descent parser ─────────────────────────────────────

def _tokenize(s: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            tokens.append(s[i:j])
            i = j
        elif c in ('!', '&', '|', '(', ')', 't', 'f'):
            tokens.append(c)
            i += 1
        else:
            i += 1  # skip unexpected characters
    return tokens


class _FormulaParser:
    """Recursive-descent parser for HOA boolean guard formulas."""

    def __init__(self, tokens: list[str]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> str | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _consume(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def parse(self) -> _Expr:
        return self._or()

    def _or(self) -> _Expr:
        left = self._and()
        while self._peek() == '|':
            self._consume()
            left = _Or(left, self._and())
        return left

    def _and(self) -> _Expr:
        left = self._unary()
        while self._peek() == '&':
            self._consume()
            left = _And(left, self._unary())
        return left

    def _unary(self) -> _Expr:
        if self._peek() == '!':
            self._consume()
            return _Not(self._unary())   # allow chained !! (double negation)
        return self._primary()

    def _primary(self) -> _Expr:
        tok = self._peek()
        if tok == '(':
            self._consume()              # '('
            expr = self._or()
            self._consume()              # ')'
            return expr
        self._consume()
        if tok == 't':
            return _True()
        if tok == 'f':
            return _False()
        return _AP(int(tok))            # AP index literal


def _parse_guard(guard_str: str) -> _Expr:
    return _FormulaParser(_tokenize(guard_str)).parse()


def _enumerate_satisfying(guard: _Expr, ap_count: int) -> list[dict[int, bool]]:
    """Return every {ap_index: bool} assignment that satisfies *guard*."""
    return [
        {i: bits[i] for i in range(ap_count)}
        for bits in product((False, True), repeat=ap_count)
        if guard.evaluate({i: bits[i] for i in range(ap_count)})
    ]


# ── HOA parser ────────────────────────────────────────────────────────────────

# Raw automaton types (before name mapping)
_RawTransitions = dict[int, list[tuple[str, int]]]   # state → [(guard, target)]


class StrixCSParser:
    """
    Parses a Strix HOA counter-strategy string into a ``CounterStrategy``.

    Usage::

        cs = StrixHOAParser.from_str(strix_stdout)
    """

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_str(cls, text: str) -> CounterStrategy:
        """Parse the full Strix HOA output string into a ``CounterStrategy``."""
        lines = text.splitlines()
        ap_names, controllable_indices, start_idx = cls._parse_header(lines)
        raw = cls._parse_body_raw(lines)
        return cls._build_counter_strategy(raw, ap_names, controllable_indices, start_idx)

    # ------------------------------------------------------------------ #
    # Header parsing                                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def _parse_header(
        cls, lines: list[str]
    ) -> tuple[list[str], set[int], int]:
        """
        Extract from the HOA header:
        - ordered list of AP names
        - set of controllable AP indices (→ inputs in CSTransition)
        - index of the start state
        """
        ap_names: list[str] = []
        controllable: set[int] = set()
        start_idx: int = 0

        for line in lines:
            if line.startswith('--BODY--'):
                break
            if line.startswith('AP:'):
                # AP: 3 "methane" "highwater" "pump"
                ap_names = re.findall(r'"([^"]+)"', line)
            elif line.startswith('controllable-AP:'):
                # controllable-AP: 0 1
                indices = line.split(':', 1)[1].split()
                controllable = {int(x) for x in indices if x.strip()}
            elif line.startswith('Start:'):
                start_idx = int(line.split(':', 1)[1].strip())

        return ap_names, controllable, start_idx

    # ------------------------------------------------------------------ #
    # Body parsing                                                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def _parse_body_raw(cls, lines: list[str]) -> _RawTransitions:
        """
        Parse the ``--BODY--`` section into a raw adjacency structure:
        ``{state_index: [(guard_string, target_index), ...]]}``.
        """
        in_body = False
        current_state: int | None = None
        raw: _RawTransitions = {}

        for line in lines:
            stripped = line.strip()
            if stripped == '--BODY--':
                in_body = True
                continue
            if stripped == '--END--':
                break
            if not in_body:
                continue

            state_m = re.match(r'State:\s*(\d+)', stripped)
            if state_m:
                current_state = int(state_m.group(1))
                raw[current_state] = []
                continue

            # Transition: [guard] target
            trans_m = re.match(r'\[([^\]]*)\]\s*(\d+)', stripped)
            if trans_m and current_state is not None:
                guard_str = trans_m.group(1).strip()
                target = int(trans_m.group(2))
                raw[current_state].append((guard_str, target))

        return raw

    # ------------------------------------------------------------------ #
    # State naming                                                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def _identify_trap_states(cls, raw: _RawTransitions) -> set[int]:
        """
        A *trap* state has at least one outgoing transition and every one of
        them loops back to itself.  Such states are the HOA equivalent of the
        Spectra ``DEAD`` sentinel: once reached, the system cannot escape.
        """
        return {
            state
            for state, transitions in raw.items()
            if transitions and all(target == state for _, target in transitions)
        }

    @classmethod
    def _build_name_map(
        cls,
        raw: _RawTransitions,
        start_idx: int,
        trap_states: set[int],
    ) -> dict[int, str]:
        """
        Assign human-readable names to HOA state indices:
        - start state     → ``"INI"``
        - trap states     → ``"DEAD"``
        - remaining states → ``"S0"``, ``"S1"``, … (sorted by index)
        """
        name_map: dict[int, str] = {start_idx: "INI"}
        for s in trap_states:
            name_map[s] = "DEAD"

        counter = 0
        for s in sorted(raw.keys()):
            if s not in name_map:
                name_map[s] = f"S{counter}"
                counter += 1

        return name_map

    # ------------------------------------------------------------------ #
    # CounterStrategy construction                                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def _build_counter_strategy(
        cls,
        raw: _RawTransitions,
        ap_names: list[str],
        controllable_indices: set[int],
        start_idx: int,
    ) -> CounterStrategy:
        n = len(ap_names)
        trap_states = cls._identify_trap_states(raw)
        name_map = cls._build_name_map(raw, start_idx, trap_states)

        transitions: list[CSTransition] = []

        for state_idx, trans_list in raw.items():
            src_name = name_map[state_idx]
            if src_name == "DEAD":
                # Trap-state self-loops carry no counter-strategy information.
                continue

            for guard_str, target_idx in trans_list:
                target_name = name_map.get(target_idx, f"S{target_idx}")
                guard = _parse_guard(guard_str)
                satisfying = _enumerate_satisfying(guard, n)

                for assignment in satisfying:
                    inputs = {
                        ap_names[i]: assignment[i]
                        for i in range(n)
                        if i in controllable_indices
                    }
                    outputs = {
                        ap_names[i]: assignment[i]
                        for i in range(n)
                        if i not in controllable_indices
                    }
                    transitions.append(CSTransition(
                        source=src_name,
                        target=target_name,
                        inputs=inputs,
                        outputs=outputs,
                    ))

        return CounterStrategy(transitions, initial_state="INI", dead_state="DEAD")