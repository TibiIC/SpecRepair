"""
Trace the 5-state HOA: verify which transitions survive in the restricted game,
step by step, using the minepump safety guarantees.

Safety guarantees (inner formulas extracted from G(...)):
  G1: highwater=true -> next(pump=true)    [inner: highwater=true -> next(pump=true)]
  G2: methane=true  -> next(pump=false)   [inner: methane=true -> next(pump=false)]
Initial:
  I0: pump=false

At each step we check whether sys is valid given prev_full.
"""
from itertools import product

APs = ["methane", "highwater", "pump"]  # indices 0,1,2
ENV = ["methane", "highwater"]  # controllable → CSTransition.inputs
SYS = ["pump"]  # non-controllable → CSTransition.outputs


# --- simple formula evaluator --------------------------------------------------
def eval_G_inner(inner: str, prev: dict, curr: dict) -> bool:
    """Evaluate inner formula of G(inner) at the prev→curr boundary."""
    # G(highwater=true -> next(pump=true)):
    if inner == "highwater=true -> next(pump=true)":
        return not prev["highwater"] or curr["pump"]
    # G(methane=true -> next(pump=false)):
    if inner == "methane=true -> next(pump=false)":
        return not prev["methane"] or not curr["pump"]
    raise ValueError(f"Unknown formula: {inner}")


def eval_initial(expr: str, curr: dict) -> bool:
    if expr == "pump=false":
        return not curr["pump"]
    raise ValueError(f"Unknown initial formula: {expr}")


safety_formulas = [
    "highwater=true -> next(pump=true)",
    "methane=true -> next(pump=false)",
]
initial_formulas = ["pump=false"]


def is_sys_valid(sys_out, env_out, prev_full, is_initial):
    curr = {**env_out, **sys_out}
    if is_initial:
        return all(eval_initial(f, curr) for f in initial_formulas)
    else:
        return all(eval_G_inner(f, prev_full, curr) for f in safety_formulas)


# --- 5-state HOA raw transitions (already expanded earlier) --------------------
import re as _re
from itertools import product as _product


def expand_hoa(raw):
    """Expand label → list of (env, sys, tgt)."""

    def eval_label(s, a):
        tokens = _re.findall(r't\b|f\b|\d+|[!&|()]', s)
        pos = [0]

        def peek():
            return tokens[pos[0]] if pos[0] < len(tokens) else None

        def consume():
            v = tokens[pos[0]]; pos[0] += 1; return v

        def expr():
            return or_()

        def or_():
            l = and_()
            while peek() == '|': consume(); l = l or and_()
            return l

        def and_():
            l = not_()
            while peek() == '&': consume(); l = l and not_()
            return l

        def not_():
            if peek() == '!': consume(); return not atom()
            return atom()

        def atom():
            t = peek()
            if t == '(': consume(); v = expr(); consume(); return v
            consume()
            if t == 't': return True
            if t == 'f': return False
            return a[int(t)]

        return expr()

    seen = {}
    for src, formula, tgt in raw:
        for vals in _product([False, True], repeat=3):
            a = dict(enumerate(vals))
            if eval_label(formula, a):
                env = {"methane": a[0], "highwater": a[1]}
                sys = {"pump": a[2]}
                key = (src, tuple(sorted(env.items())), tuple(sorted(sys.items())), tgt)
                seen[key] = (env, sys, tgt)

    result = {}
    for (src, env_t, sys_t, tgt), (env, sys, _) in seen.items():
        result.setdefault(src, []).append((env, sys, tgt))
    return result


raw = [
    ('0', '(!(0 | 1)) & (!2)', '1'),
    ('0', '(!(0 | 1)) & (2)', '2'),
    ('1', '(0 & 1) & (!2)', '3'),
    ('1', '(0 & 1) & (2)', '2'),
    ('2', '(t) & (!2)', '3'),
    ('2', '(t) & (2)', '4'),
    ('3', '(t) & (!2)', '3'),
    ('3', '(t) & (2)', '2'),
    ('4', '(!1) & (!2)', '3'),
    ('4', '(!1) & (2)', '4'),
]

by_state = expand_hoa(raw)

# --- DFS pruning ---------------------------------------------------------------
DEAD = "DEAD"
result_transitions = {}


def key_of(src, env, sys, tgt):
    return (src, tuple(sorted(env.items())), tuple(sorted(sys.items())), tgt)


def dfs(state, prev_full, path):
    is_initial = (state == '0')
    candidates = by_state.get(state, [])
    any_alive = False

    for env, sys, tgt in candidates:
        if not is_sys_valid(sys, env, prev_full, is_initial):
            continue
        curr_full = {**env, **sys}

        if tgt in path:
            k = key_of(state, env, sys, tgt)
            result_transitions[k] = (state, env, sys, tgt)
            any_alive = True
        elif not by_state.get(tgt):
            k = key_of(state, env, sys, DEAD)
            result_transitions[k] = (state, env, sys, DEAD)
            any_alive = True
        else:
            tgt_alive = dfs(tgt, curr_full, path + [state])
            actual_tgt = tgt if tgt_alive else DEAD
            k = key_of(state, env, sys, actual_tgt)
            result_transitions[k] = (state, env, sys, actual_tgt)
            any_alive = True

    return any_alive


dfs('0', None, [])

print("=== Restricted-game transitions ===")
for src, env, sys, tgt in result_transitions.values():
    print(f"  {src} → {tgt}  env={env}  sys={sys}")

