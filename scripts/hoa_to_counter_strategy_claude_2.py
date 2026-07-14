"""
General HOA -> Spectra counter-strategy extractor.

Strix, when a spec is UNREALIZABLE, returns a HOA automaton that is a
winning strategy *for the environment*: `controllable-AP` lists the
propositions the counter-strategy itself picks (the original spec's ENV
inputs); every other proposition (the original spec's SYS outputs) is
universally quantified over, which is why you typically see one outgoing
edge per possible system response.

This module:
  1. Parses that HOA text generically (no hard-coded AP names/counts).
  2. Expands every edge label into concrete (env_move, sys_move, target)
     triples for however many APs the automaton actually has.
  3. Restricts the automaton to the "restricted game": a system that
     obeys its own safety guarantees will never pick a sys_move that
     violates them, so those edges are dropped.
  4. Classifies what's left into the two kinds of real counter-strategy:
       - DEADLOCK: a reachable state + env move where *every* remaining
         sys_move (across every edge available at that env move) breaks
         a safety guarantee -> the system would need contradictory
         actions.
       - INFINITE LOOP: a reachable cycle that is safety-consistent
         forever, so a system stuck in it can satisfy safety but never
         make progress (never revisits/achieves the justice goal).
  5. Emits the loop portion as Spectra-style `INI -> S0 {..} / {..};`
     lines, and reports the deadlock states/moves separately.

The system's safety/initial GUARANTEES are *not* present in the HOA file
(they live in the original GR(1) spec), so they're supplied by you as
formula strings such as:

    "highwater=true -> next(pump=true)"
    "methane=true  -> next(pump=false)"
    "pump=false"                              # initial

Supported formula syntax: identifiers, `=true` / `=false` (defaults to
`=true` if omitted, i.e. `pump` means `pump=true`), `!`, `&`, `|`, `->`,
parentheses, and `next(...)`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Optional, Tuple

Assignment = Dict[str, bool]
DEAD = "DEAD"


# ======================================================================
# 1. HOA parsing
# ======================================================================

@dataclass
class HOA:
    ap_names: List[str]
    controllable_idx: List[int]                    # ENV props of the original spec
    start: str
    edges: Dict[str, List[Tuple[str, str]]]         # state -> [(label, target), ...]


def parse_hoa(text: str) -> HOA:
    ap_names: List[str] = []
    controllable_idx: List[int] = []
    start: Optional[str] = None
    edges: Dict[str, List[Tuple[str, str]]] = {}
    in_body = False
    cur_state: Optional[str] = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("AP:"):
            ap_names = re.findall(r'"([^"]*)"', line)
        elif line.startswith("controllable-AP:"):
            controllable_idx = [int(n) for n in re.findall(r"\d+", line.split(":", 1)[1])]
        elif line.startswith("Start:"):
            start = line.split(":", 1)[1].strip()
        elif line == "--BODY--":
            in_body = True
        elif line == "--END--":
            in_body = False
        elif in_body and line.startswith("State:"):
            m = re.match(r'State:\s*(\S+)', line)
            if m:
                cur_state = m.group(1)
                edges.setdefault(cur_state, [])
        elif in_body and line.startswith("["):
            m = re.match(r'\[(.*)\]\s*(\S+)', line)
            if m and cur_state is not None:
                edges[cur_state].append((m.group(1), m.group(2)))

    if not ap_names or start is None:
        raise ValueError("Could not parse AP list / Start state from HOA text.")

    return HOA(ap_names, controllable_idx, start, edges)


# ======================================================================
# 2. Edge-label evaluator (labels reference APs by index: 0,1,2,... plus t/f)
# ======================================================================

def _tokenize_edge_label(s: str) -> List[str]:
    return re.findall(r't\b|f\b|\d+|[!&|()]', s)


def _eval_edge_label(tokens: List[str], a: Dict[int, bool]) -> bool:
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def consume():
        v = tokens[pos[0]]
        pos[0] += 1
        return v

    def expr():
        return or_()

    def or_():
        v = and_()
        while peek() == '|':
            consume()
            v = v or and_()
        return v

    def and_():
        v = not_()
        while peek() == '&':
            consume()
            v = v and not_()
        return v

    def not_():
        if peek() == '!':
            consume()
            return not atom()
        return atom()

    def atom():
        t = peek()
        if t == '(':
            consume()
            v = expr()
            consume()  # ')'
            return v
        consume()
        if t == 't':
            return True
        if t == 'f':
            return False
        return a[int(t)]

    return expr()


def expand_hoa(hoa: HOA):
    """Expand every (state, label, target) edge into concrete
    (env_move, sys_move, target) triples, for as many APs as the
    automaton actually declares."""
    n = len(hoa.ap_names)
    env_idx = list(hoa.controllable_idx)
    sys_idx = [i for i in range(n) if i not in env_idx]

    by_state: Dict[str, List[Tuple[Assignment, Assignment, str]]] = {}
    for state, label_edges in hoa.edges.items():
        seen = set()
        out: List[Tuple[Assignment, Assignment, str]] = []
        for label, tgt in label_edges:
            tokens = _tokenize_edge_label(label)
            for vals in product([False, True], repeat=n):
                a = dict(enumerate(vals))
                if not _eval_edge_label(tokens, a):
                    continue
                env = {hoa.ap_names[i]: a[i] for i in env_idx}
                sysd = {hoa.ap_names[i]: a[i] for i in sys_idx}
                key = (tuple(sorted(env.items())), tuple(sorted(sysd.items())), tgt)
                if key in seen:
                    continue
                seen.add(key)
                out.append((env, sysd, tgt))
        by_state[state] = out
    return by_state, env_idx, sys_idx


# ======================================================================
# 3. Guarantee-formula parser (named vars, next(), ->, &, |, !, =true/=false)
# ======================================================================

_GUARANTEE_TOKEN_RE = re.compile(
    r'next\(|->|=true|=false|[()!&|]|[A-Za-z_][A-Za-z0-9_]*'
)


def _tokenize_guarantee(s: str) -> List[str]:
    return _GUARANTEE_TOKEN_RE.findall(s)


class _GuaranteeParser:
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def parse(self):
        return self.implies()

    def implies(self):
        left = self.or_()
        if self.peek() == '->':
            self.consume()
            return ('implies', left, self.implies())
        return left

    def or_(self):
        left = self.and_()
        while self.peek() == '|':
            self.consume()
            left = ('or', left, self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.peek() == '&':
            self.consume()
            left = ('and', left, self.not_())
        return left

    def not_(self):
        if self.peek() == '!':
            self.consume()
            return ('not', self.not_())
        return self.atom()

    def atom(self):
        t = self.peek()
        if t == '(':
            self.consume()
            node = self.implies()
            self.consume()  # ')'
            return node
        if t == 'next(':
            self.consume()
            node = self.implies()
            self.consume()  # ')'
            return ('next', node)
        name = self.consume()
        value = True
        if self.peek() in ('=true', '=false'):
            value = self.consume() == '=true'
        return ('var', name, value)


def parse_guarantee(formula: str):
    return _GuaranteeParser(_tokenize_guarantee(formula)).parse()


def eval_guarantee(ast, prev: Assignment, curr: Assignment, in_next: bool = False) -> bool:
    kind = ast[0]
    if kind == 'var':
        _, name, value = ast
        ctx = curr if in_next else prev
        return ctx[name] == value
    if kind == 'next':
        return eval_guarantee(ast[1], prev, curr, True)
    if kind == 'not':
        return not eval_guarantee(ast[1], prev, curr, in_next)
    if kind == 'and':
        return eval_guarantee(ast[1], prev, curr, in_next) and eval_guarantee(ast[2], prev, curr, in_next)
    if kind == 'or':
        return eval_guarantee(ast[1], prev, curr, in_next) or eval_guarantee(ast[2], prev, curr, in_next)
    if kind == 'implies':
        return (not eval_guarantee(ast[1], prev, curr, in_next)) or eval_guarantee(ast[2], prev, curr, in_next)
    raise ValueError(f"Unknown node {ast}")


# ======================================================================
# 4. Restricted-game pruning: deadlocks + loops
# ======================================================================

@dataclass
class CounterStrategyResult:
    kept: Dict[Tuple, Tuple[str, Assignment, Assignment, str]]
    env_names: List[str]
    sys_names: List[str]
    start: str
    deadlocks: List[Tuple[str, Assignment]]
    spectra_lines: List[str]


def build_counter_strategy(
    hoa_text: str,
    safety_guarantees: List[str],
    initial_formulas: List[str],
) -> CounterStrategyResult:
    hoa = parse_hoa(hoa_text)
    by_state, env_idx, sys_idx = expand_hoa(hoa)
    env_names = [hoa.ap_names[i] for i in env_idx]
    sys_names = [hoa.ap_names[i] for i in sys_idx]

    guarantee_asts = [parse_guarantee(f) for f in safety_guarantees]
    initial_asts = [parse_guarantee(f) for f in initial_formulas]

    def sys_move_valid(env: Assignment, sysd: Assignment, prev_full: Optional[Assignment], is_initial: bool) -> bool:
        curr = {**env, **sysd}
        if is_initial:
            return all(eval_guarantee(a, curr, curr) for a in initial_asts)
        return all(eval_guarantee(a, prev_full, curr) for a in guarantee_asts)

    kept: Dict[Tuple, Tuple[str, Assignment, Assignment, str]] = {}
    deadlocks: List[Tuple[str, Assignment]] = []
    reported_deadlocks = set()

    def key_of(src, env, sysd, tgt):
        return (src, tuple(sorted(env.items())), tuple(sorted(sysd.items())), tgt)

    def dfs(state: str, prev_full: Optional[Assignment], path: List[str]) -> bool:
        is_initial = prev_full is None
        candidates = by_state.get(state, [])
        any_alive = False

        # Track, per distinct env move offered at this state, whether at
        # least one safety-consistent sys response exists anywhere among
        # the edges that offer that env move.
        env_move_has_valid_response: Dict[tuple, bool] = {}
        for env, _sysd, _tgt in candidates:
            env_move_has_valid_response.setdefault(tuple(sorted(env.items())), False)

        for env, sysd, tgt in candidates:
            env_key = tuple(sorted(env.items()))
            if not sys_move_valid(env, sysd, prev_full, is_initial):
                continue
            env_move_has_valid_response[env_key] = True
            curr_full = {**env, **sysd}

            if tgt in path:
                actual_tgt = tgt
            elif not by_state.get(tgt):
                actual_tgt = DEAD
            else:
                actual_tgt = tgt if dfs(tgt, curr_full, path + [state]) else DEAD

            kept[key_of(state, env, sysd, actual_tgt)] = (state, env, sysd, actual_tgt)
            any_alive = True

        for env_key, has_valid in env_move_has_valid_response.items():
            if not has_valid:
                dl_key = (state, env_key)
                if dl_key not in reported_deadlocks:
                    reported_deadlocks.add(dl_key)
                    deadlocks.append((state, dict(env_key)))

        return any_alive

    dfs(hoa.start, None, [])

    spectra_lines = _to_spectra_lines(kept, hoa.start)

    return CounterStrategyResult(kept, env_names, sys_names, hoa.start, deadlocks, spectra_lines)


# ======================================================================
# 5. Spectra-style output for the loop portion
# ======================================================================

def _to_spectra_lines(kept, start: str) -> List[str]:
    outgoing: Dict[str, List[Tuple[Assignment, Assignment, str]]] = {}
    for src, env, sysd, tgt in kept.values():
        outgoing.setdefault(src, []).append((env, sysd, tgt))

    name = {start: "INI"}
    counter = 0
    seen_states = {start}
    frontier = [start]
    while frontier:
        nxt_frontier = []
        for s in frontier:
            for _env, _sysd, tgt in outgoing.get(s, []):
                if tgt == DEAD or tgt in seen_states:
                    continue
                seen_states.add(tgt)
                name[tgt] = f"S{counter}"
                counter += 1
                nxt_frontier.append(tgt)
        frontier = nxt_frontier

    def fmt(d: Assignment) -> str:
        return "{" + ", ".join(f"{k}:{str(v).lower()}" for k, v in d.items()) + "}"

    lines: List[str] = []
    for s in name:  # insertion order = BFS order, starting with `start`
        for env, sysd, tgt in outgoing.get(s, []):
            if tgt == DEAD:
                continue
            lines.append(f"{name[s]} -> {name[tgt]} {fmt(env)} / {fmt(sysd)};")
    return lines


# ======================================================================
# Demo / self-test
# ======================================================================

if __name__ == "__main__":
    minepump_hoa = """
HOA: v1
tool: "strix" "21.0.0"
States: 5
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
[(0 & 1) & (!2)] 3
[(0 & 1) & (2)] 2
State: 2 "[2]"
[(t) & (!2)] 3
[(t) & (2)] 4
State: 3 "[3]"
[(t) & (!2)] 3
[(t) & (2)] 2
State: 4 "[4]"
[(!1) & (!2)] 3
[(!1) & (2)] 4
--END--
"""

    result = build_counter_strategy(
        minepump_hoa,
        safety_guarantees=[
            "highwater=true -> next(pump=true)",
            "methane=true -> next(pump=false)",
        ],
        initial_formulas=["pump=false"],
    )

    print("=== minepump: env/sys props ===")
    print("ENV:", result.env_names, " SYS:", result.sys_names)

    print("\n=== minepump: restricted-game transitions ===")
    for src, env, sysd, tgt in result.kept.values():
        print(f"  {src} -> {tgt}  env={env}  sys={sysd}")

    print("\n=== minepump: deadlocks (env move, no safe sys response) ===")
    for state, env in result.deadlocks:
        print(f"  state {state}: env forces {env} and every safe pump value is excluded")

    print("\n=== minepump: Spectra-style loop transitions ===")
    for line in result.spectra_lines:
        print(" ", line)

    # ------------------------------------------------------------------
    traffic_hoa = """
UNREALIZABLE
HOA: v1
tool: "strix" "21.0.0"
States: 4
Start: 0
AP: 4 "car" "emergency" "police" "green"
controllable-AP: 0 1 2
acc-name: all
Acceptance: 0 t
--BODY--
State: 0 "[0]"
[(!(2 | !0)) & (!3)] 1
[(!(2 | !0)) & (3)] 2
State: 1 "[1]"
[(!(2 | !0)) & (!3)] 1
[(!(2 | !0)) & (3)] 2
State: 2 "[2]"
[(!(2 | !0)) & (!3)] 3
[(!(2 | !0)) & (3)] 2
State: 3 "[3]"
[(!(2 | !0)) & (!3)] 3
[(!(2 | !0)) & (3)] 2
--END--
"""

    # No extra system safety guarantees supplied here -> pure structural
    # (loop/deadlock) pruning. Plug in real guarantees the same way as
    # for minepump if you have them.
    result2 = build_counter_strategy(traffic_hoa, safety_guarantees=[], initial_formulas=[])

    print("\n\n=== traffic light: env/sys props ===")
    print("ENV:", result2.env_names, " SYS:", result2.sys_names)

    print("\n=== traffic light: Spectra-style loop transitions ===")
    for line in result2.spectra_lines:
        print(" ", line)