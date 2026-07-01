"""
Structured representation of a counter-strategy automaton.

Replaces the legacy `CounterStrategy = list[str]` type alias with a proper
class that makes the automaton graph explicit and traversable.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterator


@dataclass
class CSTransition:
    """
    One edge in a counter-strategy automaton.

    Inputs (environment-controlled APs) are shared across all transitions
    from the same source state in a valid counter-strategy — the environment
    picks a fixed input response for each state. Outputs (system-controlled
    APs) differ between transitions from the same state, capturing the
    system's nondeterministic choices.
    """
    source: str
    target: str
    inputs: dict[str, bool]   # environment-controlled (non-controllable APs)
    outputs: dict[str, bool]  # system-controlled (controllable APs)

    @property
    def assignments(self) -> dict[str, bool]:
        """Combined input + output assignments at this transition."""
        return {**self.inputs, **self.outputs}

    def to_spectra_str(self) -> str:
        """Serialise back to the Spectra counter-strategy string format."""
        def fmt(d: dict[str, bool]) -> str:
            return ", ".join(f"{k}:{'true' if v else 'false'}" for k, v in sorted(d.items()))

        return f"{self.source} -> {self.target} {{{fmt(self.inputs)}}} / {{{fmt(self.outputs)}}};"


class CounterStrategy:
    """
    A counter-strategy automaton: a finite directed graph whose paths from
    the initial state to a dead/sink state represent the environment's
    winning plays.

    Replaces the legacy `list[str]` type alias.  Callers that previously
    iterated over the raw strings should now use `transitions`,
    `transitions_from`, or `all_paths`.
    """

    def __init__(
        self,
        transitions: list[CSTransition],
        initial_state: str = "INI",
        dead_state: str = "DEAD",
    ):
        self._transitions = transitions
        self.initial_state = initial_state
        self.dead_state = dead_state
        self._by_source: dict[str, list[CSTransition]] = defaultdict(list)
        for t in transitions:
            self._by_source[t.source].append(t)

    # ------------------------------------------------------------------
    # Graph accessors
    # ------------------------------------------------------------------

    @property
    def transitions(self) -> list[CSTransition]:
        return list(self._transitions)

    def transitions_from(self, state: str) -> list[CSTransition]:
        return list(self._by_source.get(state, []))

    def all_states(self) -> set[str]:
        states: set[str] = set()
        for t in self._transitions:
            states.add(t.source)
            states.add(t.target)
        return states

    def sink_states(self) -> set[str]:
        """States with no outgoing transitions (natural dead ends)."""
        return self.all_states() - set(self._by_source)

    # ------------------------------------------------------------------
    # Path enumeration
    # ------------------------------------------------------------------

    def all_paths(self) -> list[list[CSTransition]]:
        """
        Return every simple path from `initial_state` to `dead_state`,
        plus paths that terminate at a cycle (the environment forcing an
        infinite loop is also a winning play for liveness properties).

        Each path is an ordered list of CSTransition objects; the sequence
        of states is implicit as [t.source for t in path] + [path[-1].target].
        """
        paths: list[list[CSTransition]] = []
        self._dfs(self.initial_state, [], [], paths)
        return paths

    def _dfs(
        self,
        state: str,
        current_path: list[CSTransition],
        visited: list[str],
        paths: list[list[CSTransition]],
    ) -> None:
        # Terminate: reached dead state or detected a cycle.
        if state == self.dead_state or state in visited:
            if current_path:                 # don't record the trivial empty path
                paths.append(list(current_path))
            return
        for t in self.transitions_from(state):
            self._dfs(t.target, current_path + [t], visited + [state], paths)

    # ------------------------------------------------------------------
    # Winning condition
    # ------------------------------------------------------------------

    def winning_condition(self) -> str:
        """
        Classify how the environment wins:

        - ``"deadlock"``  – every path terminates at the dead state.
        - ``"loop"``      – every path terminates at a cycle (no dead state
                            is ever reached).
        - ``"mixed"``     – some paths deadlock, others loop (rare but valid).
        - ``"unknown"``   – no paths could be extracted (empty automaton).
        """
        paths = self.all_paths()
        if not paths:
            return "unknown"
        has_dead = any(p[-1].target == self.dead_state for p in paths)
        has_loop = any(p[-1].target != self.dead_state for p in paths)
        if has_dead and has_loop:
            return "mixed"
        return "deadlock" if has_dead else "loop"

    def _unique_path_signatures(self) -> list[str]:
        """Return the distinct state-sequences across all paths, e.g. ``['INI_S0_DEAD']``."""
        seen: dict[str, None] = {}  # ordered-set via insertion-order dict
        for path in self.all_paths():
            sig = "_".join([path[0].source] + [t.target for t in path])
            seen[sig] = None
        return list(seen)

    # ------------------------------------------------------------------
    # Structural equality
    # ------------------------------------------------------------------

    def _canonical_form(self) -> list[tuple]:
        """
        A state-name-agnostic representation of the automaton.

        States are renamed in BFS order from ``initial_state``:
        - ``initial_state`` → ``"ini"``
        - ``dead_state``    → ``"dead"``
        - all others        → ``"1"``, ``"2"``, … in first-encounter order

        Each transition is recorded as a 4-tuple::

            (src_canonical_id, dst_canonical_id,
             sorted_inputs_tuple, sorted_outputs_tuple)

        Two ``CounterStrategy`` objects are structurally equivalent iff
        their canonical forms are equal.  Variable names (AP labels) must
        match exactly; only state names are abstracted away.
        """
        state_id: dict[str, str] = {
            self.initial_state: "ini",
            self.dead_state: "dead",
        }
        next_id = [1]

        def get_id(s: str) -> str:
            if s not in state_id:
                state_id[s] = str(next_id[0])
                next_id[0] += 1
            return state_id[s]

        result: list[tuple] = []
        queue: list[str] = [self.initial_state]
        visited: set[str] = {self.initial_state}

        while queue:
            state = queue.pop(0)
            src_id = get_id(state)
            transitions = sorted(
                self.transitions_from(state),
                key=lambda t: (sorted(t.inputs.items()), sorted(t.outputs.items())),
            )
            for t in transitions:
                dst_id = get_id(t.target)
                if t.target not in visited and t.target != self.dead_state:
                    visited.add(t.target)
                    queue.append(t.target)
                result.append((
                    src_id,
                    dst_id,
                    tuple(sorted(t.inputs.items())),
                    tuple(sorted(t.outputs.items())),
                ))

        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CounterStrategy):
            return NotImplemented
        return self._canonical_form() == other._canonical_form()

    def __hash__(self) -> int:
        return hash(tuple(self._canonical_form()))

    # ------------------------------------------------------------------
    # Iteration / convenience
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[CSTransition]:
        return iter(self._transitions)

    def __len__(self) -> int:
        return len(self._transitions)

    def __repr__(self) -> str:
        condition = self.winning_condition()
        sigs = self._unique_path_signatures()
        paths_str = ", ".join(sigs) if sigs else "none"
        return f"CounterStrategy(winning={condition}, paths=[{paths_str}])"

    def to_spectra_list(self) -> list[str]:
        """Round-trip back to the legacy list-of-strings representation."""
        return [t.to_spectra_str() for t in self._transitions]