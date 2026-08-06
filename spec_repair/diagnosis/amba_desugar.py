"""
Preprocessor turning AMBA-style Spectra into the boolean+enum subset that
`enum_desugar` already understands.

AMBA (amba_ahb_realizable_amba_ahb_3) uses most of Spectra's surface language at
once - parameterised predicates, arrays, integer-ranged variables, `define`
aliases, quantified formula templates, `forall`, and imported Dwyer patterns.
`enum_desugar` deliberately rejects every one of those. Rather than widen it,
this module lowers them into what it accepts: booleans, `{A,B,C}` enums, and
plain GR(1) formulas. Running the two in sequence gives a specification this
repo's parser can load.

What is lowered, and how:

* `define X := v;`         inlined textually, longest name first so that
                           MASTER_NUM does not partially match MASTER_MAX.
* `boolean[N] v`           becomes `v_0 .. v_{N-1}`; `v[i]` becomes `v_i`.
* `Int(0..N) v`            becomes an enum `{v_val0 .. v_valN}`; `v = k`
                           becomes `v = v_valk`. enum_desugar then encodes it
                           as ceil(log2)-style indicators like any other enum.
* `predicate p(T a): body` inlined at each call site with arguments substituted.
* `asm N{Int(0..M) i}: f`  one formula per value of `i`, named `N_0 .. N_M`.
* `forall i in Int(a..b)`  conjunction over the concrete range.
* `pRespondsToS(p, s)`     `G(p -> F(s))`. The pattern file also gives a 2-state
                           monitor for it, but this repo's parser handles the
                           response pattern natively, so the direct form is both
                           smaller and closer to how every other case study is
                           written.
* `pBecomesTrue_between`   expanded to the 3-state monitor from
  `QandR(p, q, r)`         DwyerPatterns.spectra, with a fresh state variable per
                           call site. Its doc comment states the LTL as
                           `G(!(q & !r) | ((p & !r) V (!r | (p & !r))))`, using
                           the release operator, which GR(1) has no direct form
                           for - but the pattern body already *is* the GR(1)
                           encoding (initial state, safety transition relation,
                           justice condition), so nothing needs inventing.

A monitor instantiated for an assumption emits assumption-side formulas, and one
instantiated for a guarantee emits guarantee-side formulas: the state it
introduces belongs to whichever player is obliged to satisfy the pattern.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

_DEFINE_RE = re.compile(r'^\s*define\s+(\w+)\s*:=\s*(.+?)\s*;\s*$', re.M)
_TYPE_ALIAS_RE = re.compile(r'^\s*type\s+(\w+)\s*=\s*\{([^}]*)\}\s*;\s*$', re.M)
_ARRAY_DECL_RE = re.compile(r'^\s*(env|sys)\s+boolean\[(\d+)\]\s+(\w+)\s*;\s*$', re.M)
_INT_DECL_RE = re.compile(r'^\s*(env|sys)\s+Int\((\d+)\.\.(\d+)\)\s+(\w+)\s*;\s*$', re.M)
_PREDICATE_RE = re.compile(
    r'^\s*predicate\s+(\w+)\s*\(([^)]*)\)\s*:\s*(.+?)\s*;\s*$', re.M | re.S)
_TEMPLATE_HEADER_RE = re.compile(
    r'^\s*(asm|gar|assumption|guarantee)\s+(\w+)\s*\{\s*Int\((\d+)\.\.(\d+)\)\s+(\w+)\s*\}\s*:\s*(.+?)\s*;\s*$',
    re.M | re.S)
_PLAIN_NAMED_RE = re.compile(
    r'^\s*(asm|gar|assumption|guarantee)\s+(\w+)\s*:\s*(.+?)\s*;\s*$', re.M | re.S)
_PLAIN_ANON_RE = re.compile(
    r'^\s*(asm|gar|assumption|guarantee)\s+(?!\w+\s*[:{])(.+?)\s*;\s*$', re.M | re.S)
_FORALL_RE = re.compile(r'forall\s+(\w+)\s+in\s+Int\((\d+)\.\.(\d+)\)\s*\.')


@dataclass
class AmbaLowerResult:
    text: str | None
    reason: str | None = None
    notes: List[str] = field(default_factory=list)


def _inline_defines(text: str) -> Tuple[str, Dict[str, str]]:
    defines = {m.group(1): m.group(2) for m in _DEFINE_RE.finditer(text)}
    text = _DEFINE_RE.sub('', text)
    # Longest first: MASTER_NUM must not be matched as MASTER_MAX's prefix, and
    # a define whose body mentions another define needs the inner one resolved.
    for _ in range(len(defines) + 1):
        for name in sorted(defines, key=len, reverse=True):
            body = defines[name]
            # A bare integer must stay bare: MASTER_NUM -> 3, not (3), or every
            # downstream regex expecting `boolean[3]` / `Int(0..2)` stops
            # matching. Anything else is parenthesised to keep precedence.
            replacement = body if re.fullmatch(r'\d+', body.strip()) else f'({body})'
            text = re.sub(rf'\b{re.escape(name)}\b', replacement, text)
    return text, defines


def _expand_arrays(text: str) -> Tuple[str, Dict[str, int]]:
    arrays: Dict[str, int] = {}
    for kind, size, name in _ARRAY_DECL_RE.findall(text):
        arrays[name] = int(size)

    def decl_replacement(m: re.Match) -> str:
        kind, size, name = m.group(1), int(m.group(2)), m.group(3)
        return "\n".join(f"{kind} boolean {name}_{i};" for i in range(size))

    text = _ARRAY_DECL_RE.sub(decl_replacement, text)
    return text, arrays


def _substitute_array_indices(text: str, arrays: Dict[str, int]) -> str:
    """
    `v[3]` -> `v_3`. Deliberately separate from declaration expansion and run
    late: at declaration time the index is still the bound variable of a
    template or forall (`hbusreq[i]`), and only becomes a literal once those
    have been expanded.
    """
    for name in arrays:
        text = re.sub(rf'\b{re.escape(name)}\s*\[\s*(\d+)\s*\]', rf'{name}_\1', text)
    return text


def _ints_to_enums(text: str) -> Tuple[str, Dict[str, Tuple[int, int]]]:
    ints: Dict[str, Tuple[int, int]] = {}
    for kind, lo, hi, name in _INT_DECL_RE.findall(text):
        ints[name] = (int(lo), int(hi))

    def decl_replacement(m: re.Match) -> str:
        kind, lo, hi, name = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        # Value names carry no variable prefix: enum_desugar's
        # indicator_name already prefixes with the variable, and
        # `<var>_val<k>` here produced `hmaster_hmaster_val0`.
        values = ",".join(f"val{v}" for v in range(lo, hi + 1))
        return f"{kind} {{{values}}} {name};"

    text = _INT_DECL_RE.sub(decl_replacement, text)
    return text, ints


def _substitute_int_values(text: str, ints: Dict[str, Tuple[int, int]]) -> str:
    """
    `v = 3` -> `v = v_val3`. Late, like array indices: until templates and
    forall have been expanded the right-hand side is still a bound variable,
    and predicate inlining leaves it parenthesised as `v = (0)`.
    """
    for name in ints:
        text = re.sub(rf'\b{re.escape(name)}\s*(!?=)\s*\(\s*(\d+)\s*\)', rf'{name}\1\2', text)
        text = re.sub(rf'\b{re.escape(name)}\s*(!?=)\s*(\d+)\b',
                      lambda m: f'{m.group(0).split(m.group(1))[0]}{m.group(1)}val{m.group(2)}', text)
    return text


def _inline_predicates(text: str) -> str:
    """
    A parameter's own type may contain parentheses - `Int(0..2) master` - so the
    parameter list has to be scanned for balance rather than matched with
    [^)]*, which stops at the first ')' and silently leaves the call site
    un-inlined.
    """
    predicates: Dict[str, Tuple[List[str], str]] = {}
    while True:
        m = re.search(r'^[ \t]*predicate\s+(\w+)\s*\(', text, re.M)
        if not m:
            break
        name = m.group(1)
        depth, j = 1, m.end()
        while depth:
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
            j += 1
        params_text = text[m.end():j - 1]
        rest = text[j:]
        body_m = re.match(r'\s*:\s*(.+?);', rest, re.S)
        if not body_m:
            break
        param_names = [p.strip().split()[-1] for p in _split_top_level(params_text, ',') if p.strip()]
        predicates[name] = (param_names, re.sub(r'\s+', '', body_m.group(1)))
        text = text[:m.start()] + rest[body_m.end():]

    for name, (param_names, body) in predicates.items():
        call_re = re.compile(rf'\b{re.escape(name)}\s*\(')
        while True:
            m = call_re.search(text)
            if not m:
                break
            depth, j = 1, m.end()
            while depth:
                if text[j] == '(':
                    depth += 1
                elif text[j] == ')':
                    depth -= 1
                j += 1
            args = [a.strip() for a in _split_top_level(text[m.end():j - 1], ',')]
            expanded = body
            for param, arg in zip(param_names, args):
                expanded = re.sub(rf'\b{re.escape(param)}\b', f'({arg})', expanded)
            text = text[:m.start()] + f'({expanded})' + text[j:]
    return text


def _split_top_level(text: str, sep: str) -> List[str]:
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def _boolean_equality_to_iff(body: str, bool_vars: List[str]) -> str:
    """
    `a = next(b)` is boolean equivalence, not an enum comparison.

    Spectra lets `=` stand for `<->` between booleans, and AMBA uses it for
    frame conditions like `hgrant[i] = next(hgrant[i])` ("the grant does not
    change"). This repo's formula parser only accepts `=` against a value, so
    the operand is rewritten to `<->`, which enum_desugar's _desugar_iff then
    expands. Only fires when the right-hand side is a next(...)/PREV(...)
    expression, so genuine enum comparisons like `hburst=BURST4` are untouched.
    """
    for var in sorted(bool_vars, key=len, reverse=True):
        pattern = re.compile(rf'\b{re.escape(var)}\s*=\s*(next|prev|PREV)\(')
        while True:
            m = pattern.search(body)
            if not m:
                break
            depth, j = 1, m.end()
            while depth:
                if body[j] == '(':
                    depth += 1
                elif body[j] == ')':
                    depth -= 1
                j += 1
            rhs = body[m.end() - len(m.group(1)) - 1:j]
            body = body[:m.start()] + f"(({var})<->({rhs}))" + body[j:]
    return body


_TEMPORAL_PREFIX_RE = re.compile(r'^(GF|G|F)\s+(.*)$', re.S)


def _scope_temporal_prefix(body: str) -> str:
    """
    `G phi -> psi` means `G(phi -> psi)`, not `(G phi) -> psi`.

    Spectra scopes a leading temporal operator over the entire formula, and the
    alternative reading is not even meaningful here: AMBA's G10 would say "if
    !hready holds at every step, then !start at the second step", rather than
    the intended "whenever !hready, then !start next". Only fires when the
    operator is followed by whitespace - `G(...)` is already scoped.
    """
    m = _TEMPORAL_PREFIX_RE.match(body.strip())
    if not m:
        return body
    return f"{m.group(1)}({m.group(2).strip()})"


def _expand_forall(formula: str) -> str:
    """`forall i in Int(a..b) . body` -> conjunction of body with i bound."""
    while True:
        m = _FORALL_RE.search(formula)
        if not m:
            return formula
        var, lo, hi = m.group(1), int(m.group(2)), int(m.group(3))
        rest = formula[m.end():]
        # The quantifier's body runs to the end of the enclosing parenthesis.
        depth, j = 0, 0
        while j < len(rest):
            if rest[j] == '(':
                depth += 1
            elif rest[j] == ')':
                if depth == 0:
                    break
                depth -= 1
            j += 1
        body, tail = rest[:j], rest[j:]
        conjuncts = [re.sub(rf'\b{re.escape(var)}\b', str(v), body) for v in range(lo, hi + 1)]
        formula = formula[:m.start()] + "(" + "&".join(f"({c})" for c in conjuncts) + ")" + tail


_COUNTER_ARITH_NOTE = (
    "hready_counter arithmetic expanded over its concrete 0..4 domain: "
    "`next(c) = c + 1` becomes a disjunction of (c=k & next(c)=k+1), and "
    "`c < 4` a disjunction of the values below 4. Saturation at the top of the "
    "range is left to the specification's own guards, which already case-split "
    "on `c = 4` separately."
)


def _expand_int_arithmetic(text: str, ints: Dict[str, Tuple[int, int]]) -> Tuple[str, List[str]]:
    """
    Lower comparisons and increments over an Int-ranged variable into
    disjunctions over its concrete domain, before it becomes an enum.

    Only the forms AMBA actually uses are handled, and anything else is left
    alone rather than guessed at - an unrecognised arithmetic form will fail
    loudly later in enum substitution instead of being silently mistranslated.
    """
    notes: List[str] = []
    for name, (lo, hi) in ints.items():
        # next(v) = v + 1
        pattern = re.compile(rf'next\(\s*{re.escape(name)}\s*\)\s*=\s*{re.escape(name)}\s*\+\s*1\b')
        if pattern.search(text):
            disjuncts = "|".join(
                f"({name}={k}&next({name}={k + 1}))" for k in range(lo, hi))
            text = pattern.sub(f"({disjuncts})", text)
            notes.append(_COUNTER_ARITH_NOTE)
        # next(v) = v  (unchanged)
        pattern = re.compile(rf'next\(\s*{re.escape(name)}\s*\)\s*=\s*{re.escape(name)}\b(?!\s*[+\-])')
        if pattern.search(text):
            disjuncts = "|".join(f"({name}={k}&next({name}={k}))" for k in range(lo, hi + 1))
            text = pattern.sub(f"({disjuncts})", text)
        # v < k  /  v <= k  /  v > k  /  v >= k
        for op, keep in ((r'<', lambda v, k: v < k), (r'<=', lambda v, k: v <= k),
                         (r'>', lambda v, k: v > k), (r'>=', lambda v, k: v >= k)):
            pattern = re.compile(rf'\b{re.escape(name)}\s*{op}\s*(\d+)\b')

            def replace(m: re.Match, _keep=keep) -> str:
                k = int(m.group(1))
                values = [v for v in range(lo, hi + 1) if _keep(v, k)]
                if not values:
                    return "false"
                return "(" + "|".join(f"{name}={v}" for v in values) + ")"

            text = pattern.sub(replace, text)
        # next(v) = k  ->  next(v = k), the spelling enum_desugar recognises
        text = re.sub(rf'next\(\s*{re.escape(name)}\s*\)\s*=\s*(\w+)\b',
                      rf'next({name}=\1)', text)
    return text, notes


def _expand_templates(text: str) -> str:
    """`asm N{Int(a..b) i}: f;` -> one named formula per value of i."""
    def replacement(m: re.Match) -> str:
        keyword, name, lo, hi, var, body = (
            m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5), m.group(6))
        out = []
        for v in range(lo, hi + 1):
            bound = re.sub(rf'\b{re.escape(var)}\b', str(v), body)
            out.append(f"{keyword} {name}_{v}: {bound};")
        return "\n".join(out)

    return _TEMPLATE_HEADER_RE.sub(replacement, text)


_RESPONDS_TO_RE = re.compile(r'\bpRespondsToS\s*\(')
_BECOMES_TRUE_RE = re.compile(r'\bpBecomesTrue_betweenQandR\s*\(')


def _expand_responds_to(formula: str) -> str:
    """pRespondsToS(p, s) -> G(p -> F(s)), the form this repo parses natively."""
    while True:
        m = _RESPONDS_TO_RE.search(formula)
        if not m:
            return formula
        depth, j = 1, m.end()
        while depth:
            if formula[j] == '(':
                depth += 1
            elif formula[j] == ')':
                depth -= 1
            j += 1
        args = [a.strip() for a in _split_top_level(formula[m.end():j - 1], ',')]
        if len(args) != 2:
            raise ValueError(f"pRespondsToS expects 2 arguments, got {args}")
        formula = formula[:m.start()] + f"G(({args[0]})->F({args[1]}))" + formula[j:]


def _expand_becomes_true(formula: str, keyword: str, name: str,
                         counter: List[int]) -> Tuple[str, List[str], List[str]]:
    """
    pBecomesTrue_betweenQandR(p, q, r) -> the 3-state monitor from
    DwyerPatterns.spectra, with a state variable unique to this call site.

    The pattern's doc comment gives the LTL with a release operator, which GR(1)
    cannot express directly - but the pattern body is already the GR(1)
    encoding, so this transcribes it rather than deriving anything. The monitor
    is emitted on the same side as the formula that invoked it: an assumption's
    monitor constrains the environment, a guarantee's the system.
    """
    m = _BECOMES_TRUE_RE.search(formula)
    if not m:
        return formula, [], []
    depth, j = 1, m.end()
    while depth:
        if formula[j] == '(':
            depth += 1
        elif formula[j] == ')':
            depth -= 1
        j += 1
    args = [a.strip() for a in _split_top_level(formula[m.end():j - 1], ',')]
    if len(args) != 3:
        raise ValueError(f"pBecomesTrue_betweenQandR expects 3 arguments, got {args}")
    p, q, r = args

    counter[0] += 1
    state = f"btq_state_{counter[0]}"
    side = "env" if keyword in ("asm", "assumption") else "sys"
    decls = [f"{side} {{S0,S1,S2}} {state};"]

    s0, s1, s2 = f"{state}=S0", f"{state}=S1", f"{state}=S2"
    n0, n1, n2 = f"next({state}=S0)", f"next({state}=S1)", f"next({state}=S2)"
    transition = (
        f"(({s0})&((!({q})&!({p}))|(({q})&({r}))|(!({r})&({p}))|(!({q})&({r})&({p})))&{n0})"
        f"|(({s0})&(({q})&!({r})&!({p}))&{n1})"
        f"|(({s1})&(!({r})&({p}))&{n0})"
        f"|(({s1})&(!({r})&!({p}))&{n1})"
        f"|(({s1})&({r})&{n2})"
        f"|(({s2})&{n2})"
    )
    formulas = [
        f"{keyword} {name}_monitor_init: {s0};",
        f"{keyword} {name}_monitor_safety: G({transition});",
        f"{keyword} {name}_monitor_justice: GF(({s0})|({s1}));",
    ]
    # The call site itself is discharged entirely by the monitor.
    remainder = (formula[:m.start()] + "true" + formula[j:]).strip()
    return remainder, decls, formulas


def _strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'^\s*import\s*"[^"]*"\s*;?\s*$', '', text, flags=re.M)
    return text


def lower_amba_text(raw_text: str) -> AmbaLowerResult:
    """
    Lower an AMBA-style file into the boolean+enum subset `enum_desugar` takes.

    Emits `assumption -- name` / `guarantee -- name` headers with the body on
    the following line, which is the only shape enum_desugar's header regex
    accepts - AMBA's own `asm NAME: formula;` one-liner is not.
    """
    notes: List[str] = []
    text = _strip_comments(raw_text)

    module = re.search(r'^\s*module\s+(\w+)', text, re.M)
    if not module:
        return AmbaLowerResult(None, "no module declaration found")

    type_aliases = _TYPE_ALIAS_RE.findall(text)

    text, _ = _inline_defines(text)
    text, arrays = _expand_arrays(text)
    text = _inline_predicates(text)
    text = _expand_templates(text)

    ints: Dict[str, Tuple[int, int]] = {}
    for kind, lo, hi, name in _INT_DECL_RE.findall(text):
        ints[name] = (int(lo), int(hi))
    text, arith_notes = _expand_int_arithmetic(text, ints)
    notes.extend(dict.fromkeys(arith_notes))
    text, _ = _ints_to_enums(text)

    decl_lines: List[str] = []
    bool_vars: List[str] = []
    for line in text.splitlines():
        if re.match(r'^\s*(env|sys)\b', line):
            decl_lines.append(line.strip())
            bm = re.match(r'^\s*(?:env|sys)\s+boolean\s+(\w+)\s*;', line)
            if bm:
                bool_vars.append(bm.group(1))
    for alias, values in type_aliases:
        decl_lines.insert(0, f"type {alias} = {{{values}}};")

    # Collect formulas: named one-liners first, then anonymous ones.
    collected: List[Tuple[str, str, str]] = []
    anon = {"asm": 0, "gar": 0, "assumption": 0, "guarantee": 0}
    for m in _PLAIN_NAMED_RE.finditer(text):
        collected.append((m.group(1), m.group(2), m.group(3)))
    consumed = {m.group(0) for m in _PLAIN_NAMED_RE.finditer(text)}
    for m in _PLAIN_ANON_RE.finditer(text):
        if m.group(0) in consumed:
            continue
        keyword = m.group(1)
        anon[keyword] += 1
        collected.append((keyword, f"{keyword}_anon_{anon[keyword]}", m.group(2)))

    if not collected:
        return AmbaLowerResult(None, "no assumption/guarantee formulas found")

    monitor_counter = [0]
    out_formulas: List[Tuple[str, str, str]] = []
    try:
        for keyword, name, body in collected:
            # forall before whitespace stripping: its syntax is
            # `forall i in Int(a..b) .` and the regex needs those spaces.
            body = _expand_forall(body)
            body = _scope_temporal_prefix(body)
            body = _substitute_array_indices(body, arrays)
            body = _substitute_int_values(body, ints)
            body = _boolean_equality_to_iff(body, bool_vars)
            body = re.sub(r'\s+', '', body)
            body = _expand_responds_to(body)
            while _BECOMES_TRUE_RE.search(body):
                body, decls, extra = _expand_becomes_true(
                    body, keyword, name, monitor_counter)
                decl_lines.extend(decls)
                for e in extra:
                    em = _PLAIN_NAMED_RE.match(e)
                    out_formulas.append((em.group(1), em.group(2), em.group(3)))
            if body.strip() not in ("", "true"):
                out_formulas.append((keyword, name, body))
    except ValueError as e:
        return AmbaLowerResult(None, f"formula rewrite failed: {e}")

    keyword_to_full = {"asm": "assumption", "assumption": "assumption",
                       "gar": "guarantee", "guarantee": "guarantee"}
    lines = [f"module {module.group(1)}", ""]
    lines.extend(dict.fromkeys(decl_lines))
    lines.append("")
    for keyword, name, body in out_formulas:
        lines.append(f"{keyword_to_full[keyword]} -- {name}")
        lines.append(f"\t{body};")
        lines.append("")
    return AmbaLowerResult("\n".join(lines), notes=notes)
