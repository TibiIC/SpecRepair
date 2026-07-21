"""
Automated boolean-desugaring preprocessor for enum-typed Spectra files
(e.g. the SYNTECH15/17/19 academic benchmark corpora), so they can be
loaded by this repo's SpectraSpecification parser without a native
multi-valued-domain implementation. Deliberately narrow in scope: this
mechanically rewrites enum-typed variables into N-1 boolean "indicator"
variables (plus mutual-exclusion constraints to preserve the enum's
one-hot semantics) and fixes the two structural gaps that block real
SYNTECH-style files independent of enums (formula bodies wrapping onto
multiple lines, and bare/unnamed assumption|guarantee|asm|gar headers).

Anything requiring genuinely new modeling capability - predicate/monitor/
counter/weight blocks, Int(...)/array-typed variables, import resolution,
or a custom `pattern` block other than the one known-safe translation
below - is out of scope on purpose and causes the file to be reported as
unsupported rather than guessed at. That's native multi-valued-domain
parser territory, tracked separately.
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Regexes for constructs this desugarer deliberately does not attempt to
# handle - detecting any of these means the file needs the (separate,
# longer-term) native multi-valued-domain parser instead.
_UNSUPPORTED_MARKERS: List[Tuple[str, str]] = [
    (r'\bpredicate\b', "predicate definitions"),
    (r'\bmonitor\s+\w+\s*\{', "monitor blocks"),
    (r'\bimport\s*"', "import directives"),
    (r'\bInt\s*\(', "Int(...) typed variables"),
    (r'(?<!//)\[\s*\d', "array-typed variables"),
    (r'\bdefine\b', "define blocks"),
    (r'\bcounter\s+\w+\s*\(', "counter blocks"),
    (r'^\s*weight\b', "weight declarations"),
]

# The only custom `pattern NAME(...) { ... }` block this desugarer knows
# how to translate - derived by hand (see docs/session-notes) from its
# auxiliary-variable definition: a helper boolean that resets whenever
# `trigger` fires without an immediate `response`, required to hold
# infinitely often. That's exactly the standard LTL response property.
_KNOWN_PATTERN_TRANSLATIONS = {
    "respondsTo": lambda trigger, response: f"G(({trigger})->F({response}))",
}

_HEADER_RE = re.compile(r'^\s*(asm|assumption|gar|guarantee)\b(\s*--\s*(.*))?\s*$')
_TYPE_ALIAS_RE = re.compile(r'^\s*type\s+(\w+)\s*=\s*\{([^}]*)\}\s*;?\s*$')
_INLINE_ENUM_DECL_RE = re.compile(r'^\s*(env|sys)\s*\{([^}]*)\}\s*(\w+)\s*;?\s*$')
_BOOL_DECL_RE = re.compile(r'^\s*(env|sys)\s+boolean\s+(\w+)\s*;?\s*$')
_NAMED_TYPE_DECL_RE = re.compile(r'^\s*(env|sys)\s+(\w+)\s+(\w+)\s*;?\s*$')
_MODULE_RE = re.compile(r'^\s*module\s+(\w+)')
_PATTERN_DEF_RE = re.compile(r'\bpattern\s+(\w+)\s*\(')
_PATTERN_CALL_RE = re.compile(r'\brespondsTo\s*\(')


@dataclass
class EnumVar:
    kind: str  # "env" or "sys"
    values: List[str]

    @property
    def n_indicators(self) -> int:
        return len(self.values) - 1

    def indicator_name(self, var_name: str, value_index: int) -> str:
        return f"{var_name}_{self.values[value_index].lower()}"


@dataclass
class DesugarResult:
    text: Optional[str]
    reason: Optional[str] = None


def strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return '\n'.join(re.sub(r'//.*$', '', line) for line in text.splitlines())


def _find_unsupported_construct(text: str) -> Optional[str]:
    for pattern, label in _UNSUPPORTED_MARKERS:
        if re.search(pattern, text, re.MULTILINE):
            return label
    for name in _PATTERN_DEF_RE.findall(text):
        if name not in _KNOWN_PATTERN_TRANSLATIONS:
            return f"unknown custom pattern {name!r}"
    return None


def _collect_declarations(lines: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, EnumVar], Dict[str, str]]:
    type_aliases: Dict[str, List[str]] = {}
    enum_vars: Dict[str, EnumVar] = {}
    bool_vars: Dict[str, str] = {}
    for line in lines:
        m = _TYPE_ALIAS_RE.match(line)
        if m:
            type_aliases[m.group(1)] = [v.strip() for v in m.group(2).split(",")]
            continue
        m = _INLINE_ENUM_DECL_RE.match(line)
        if m:
            kind, values_txt, name = m.group(1), m.group(2), m.group(3)
            enum_vars[name] = EnumVar(kind, [v.strip() for v in values_txt.split(",")])
            continue
        m = _BOOL_DECL_RE.match(line)
        if m:
            bool_vars[m.group(2)] = m.group(1)
            continue
        m = _NAMED_TYPE_DECL_RE.match(line)
        if m and m.group(2) in type_aliases:
            kind, type_name, name = m.group(1), m.group(2), m.group(3)
            enum_vars[name] = EnumVar(kind, type_aliases[type_name])
            continue
    return type_aliases, enum_vars, bool_vars


def _distribute_next_over_or(formula: str) -> str:
    """
    X(a|b) === Xa|Xb. Rewrites any next(...) span whose top-level content
    (outside nested parens) contains a `|`, into a parenthesised
    disjunction of next(...) over each top-level disjunct. Needed because
    enum-comparison substitution routinely produces next(A|B|C) when a
    `next(var != some_value)` expands to a disjunction of indicators, and
    SpectraFormulaParser's normalize_to_pattern rejects next() wrapping a
    disjunction outright (confirmed - it accepts next() of a literal or a
    conjunction, just not a disjunction).
    """
    result = []
    i = 0
    while i < len(formula):
        m = re.compile(r'\bnext\(').search(formula, i)
        if not m:
            result.append(formula[i:])
            break
        result.append(formula[i:m.start()])
        start = m.end()
        depth = 1
        j = start
        while depth > 0:
            if formula[j] == '(':
                depth += 1
            elif formula[j] == ')':
                depth -= 1
            j += 1
        inner = _push_negation_through_or(formula[start:j - 1])
        parts = _split_top_level(inner, '|')
        if len(parts) > 1:
            distributed = "|".join(f"next({_distribute_next_over_or(p)})" for p in parts)
            result.append(f"({distributed})")
        else:
            result.append(f"next({_distribute_next_over_or(inner)})")
        i = j
    return "".join(result)


def _push_negation_through_or(text: str) -> str:
    """
    !(A|B|C) === !A & !B & !C (De Morgan's). A negated disjunction becomes
    a conjunction this way - already known-supported inside next() -
    instead of needing next() distributed over each disjunct separately.
    """
    m = re.fullmatch(r'!\((.*)\)', text.strip())
    if not m:
        return text
    parts = _split_top_level(m.group(1), '|')
    if len(parts) <= 1:
        return text
    return "(" + " & ".join(f"!({_push_negation_through_or(p)})" for p in parts) + ")"


def _split_top_level(text: str, sep: str) -> List[str]:
    parts = []
    depth = 0
    start = 0
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


def _split_top_level_str(text: str, sep: str) -> List[str]:
    """Like _split_top_level, but sep is a multi-character literal (e.g. '<->')."""
    parts = []
    depth = 0
    start = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif depth == 0 and text.startswith(sep, i):
            parts.append(text[start:i])
            start = i + len(sep)
            i += len(sep)
            continue
        i += 1
    parts.append(text[start:])
    return parts


def _desugar_iff(formula: str) -> str:
    """
    A<->B === (A&B)|(!A&!B). `<->` almost always sits inside the enclosing
    temporal operator's parens (e.g. G(A<->B)), so a plain top-level split
    of the whole formula string sees depth>=1 everywhere and never fires.
    Instead: try a split at this string's own depth 0 first: if it finds
    exactly one `<->`, rewrite and recurse into both sides (to catch any
    further `<->` nested inside their sub-parens); if it finds none,
    recurse into every parenthesised subgroup at this level instead, since
    that's where the operator actually lives. Only binary (one `<->` per
    level) is supported - a chained `A<->B<->C` is reported as unsupported
    rather than guessed at.
    """
    parts = _split_top_level_str(formula, '<->')
    if len(parts) == 2:
        a, b = (_desugar_iff(p) for p in parts)
        return f"(({a})&({b}))|(!({a})&!({b}))"
    if len(parts) > 2:
        raise ValueError(f"chained <-> not supported: {formula}")
    result = []
    i = 0
    n = len(formula)
    while i < n:
        if formula[i] == '(':
            depth = 1
            j = i + 1
            while depth > 0:
                if formula[j] == '(':
                    depth += 1
                elif formula[j] == ')':
                    depth -= 1
                j += 1
            result.append(f"({_desugar_iff(formula[i + 1:j - 1])})")
            i = j
        else:
            result.append(formula[i])
            i += 1
    return "".join(result)


_TEMPORAL_OPERAND_EQ_RE = re.compile(r'\b(next|prev|PREV)\(([A-Za-z_][A-Za-z0-9_]*)\)(!?=)([A-Za-z0-9_]+)')


def _normalize_temporal_operand_equality(formula: str) -> str:
    """
    next(var)=VALUE and next(var)!=VALUE (equality applied to the temporal
    operator's *result*) are used interchangeably with next(var=VALUE) /
    next(var!=VALUE) (equality written *inside* it) across the SYNTECH
    corpus for the same meaning - e.g. `next(spec_stage)=WAIT` alongside
    `PREV(spec_pausing=GO)` in the same ColorSort file. _substitute_enum_
    comparisons only recognises the "inside" spelling (its regex requires
    the var name immediately followed by =/!=), so the "outside" spelling
    silently passes through untouched, leaving a bare unresolved enum var
    name next to a dangling comparison. Rewriting it onto the "inside"
    spelling first means the rest of the pipeline needs no separate case
    for it, and next(...)/prev(...) end up wrapping only a plain boolean
    comparison either way - exactly what the (unmodified) downstream
    boolean-only parser already accepts.
    """
    return _TEMPORAL_OPERAND_EQ_RE.sub(r'\1(\2\3\4)', formula)


def _value_expr(var_name: str, enum_var: EnumVar, value_index: int) -> str:
    """
    Boolean expression for "var_name equals its value_index-th domain
    value": the bare indicator for one of the first n_indicators values, or
    the negated-conjunction-of-all-indicators "else" expression for the one
    remaining value with no indicator of its own.
    """
    if value_index < enum_var.n_indicators:
        return enum_var.indicator_name(var_name, value_index)
    negated = " & ".join(
        f"!{enum_var.indicator_name(var_name, k)}" for k in range(enum_var.n_indicators)
    )
    return f"({negated})"


_ENUM_TO_ENUM_CMP_RE = re.compile(
    r'\b(?:(?P<lop>next|prev|PREV)\((?P<lvar1>[A-Za-z_][A-Za-z0-9_]*)\)|(?P<lvar2>[A-Za-z_][A-Za-z0-9_]*))'
    r'(?P<neq>!?=)'
    r'(?:(?P<rop>next|prev|PREV)\((?P<rvar1>[A-Za-z_][A-Za-z0-9_]*)\)|(?P<rvar2>[A-Za-z_][A-Za-z0-9_]*))'
)


def _substitute_enum_to_enum_comparisons(formula: str, enum_vars: Dict[str, EnumVar]) -> str:
    """
    detect=spec_currentColor, detect!=spec_currentColor, color=next(spec_
    currentColor), next(spec_currentColor)=spec_currentColor: comparing two
    enum-typed variables to each other (optionally with one side wrapped in
    next(...)/prev(...)) rather than comparing one to a literal domain
    value - _substitute_enum_comparisons only handles the latter (it tries
    to match the right-hand identifier against each of the *left* variable's
    own domain values, which silently never fires when the right-hand side
    is itself another enum variable's name). Must run before that function
    and before _normalize_temporal_operand_equality, since a match here
    consumes the whole comparison outright rather than just relocating a
    next(...) wrapper - if left unhandled here first, e.g.
    next(spec_currentColor)=spec_currentColor would get normalized to
    next(spec_currentColor=spec_currentColor) and then silently fail to
    substitute at all, since "spec_currentColor" isn't one of its own
    domain values.

    "var1 = var2" desugars to a disjunction of "both sides pick the same
    shared domain value" - values that exist in only one variable's domain
    can never make the comparison true, so they're simply skipped (matching
    the strong spec's assumption of well-typed enum comparisons where
    var1's and var2's domains are meant to overlap in practice).

    "var1 != var2" is deliberately *not* generated as a negation of that
    disjunction: to_dnf's De Morgan step would turn each equal-value
    conjunct into a 2-literal disjunction, and distributing AND back over
    N such disjuncts is exponential in N - confirmed, a 6-value color enum
    already blows the recursion limit that way. Instead it's generated
    directly as the disjunction of *unequal*-value pairs (any (lv, rv)
    with lv != rv, over the full cross-product of both domains, not just
    shared values - a value unique to one side always makes them unequal
    regardless of what the other side is): already flat EDNF as-is, so
    to_dnf never needs to distribute anything, at the cost of more (but
    only polynomially more, not exponentially) disjuncts.
    """
    def replace(m: re.Match) -> str:
        lvar = m.group("lvar1") or m.group("lvar2")
        rvar = m.group("rvar1") or m.group("rvar2")
        if lvar not in enum_vars or rvar not in enum_vars:
            return m.group(0)
        lop, rop = m.group("lop"), m.group("rop")
        left_enum, right_enum = enum_vars[lvar], enum_vars[rvar]
        is_neq = m.group("neq") == "!="
        value_pairs = (
            [(lv, rv) for lv in left_enum.values for rv in right_enum.values if lv != rv]
            if is_neq
            else [(v, v) for v in left_enum.values if v in right_enum.values]
        )
        if not value_pairs:
            # Equals with no shared values: can never match. Not-equals
            # with no unequal pairs: both domains reduce to the same single
            # value, so they're forced equal, so "not equal" never holds
            # either. Both cases are simply "false".
            return "false"
        disjuncts = []
        for lv, rv in value_pairs:
            left = _value_expr(lvar, left_enum, left_enum.values.index(lv))
            right = _value_expr(rvar, right_enum, right_enum.values.index(rv))
            if lop:
                left = f"{lop}({left})"
            if rop:
                right = f"{rop}({right})"
            disjuncts.append(f"({left}&{right})")
        return "(" + "|".join(disjuncts) + ")"

    return _ENUM_TO_ENUM_CMP_RE.sub(replace, formula)


def _substitute_enum_comparisons(formula: str, enum_vars: Dict[str, EnumVar]) -> str:
    for var_name, enum_var in enum_vars.items():
        for i, value in enumerate(enum_var.values):
            replacement = _value_expr(var_name, enum_var, i)
            eq_pattern = re.compile(rf'\b{re.escape(var_name)}\s*=\s*{re.escape(value)}\b')
            formula = eq_pattern.sub(replacement, formula)
            if i < enum_var.n_indicators:
                neq_replacement = f"!{replacement}"
            else:
                positive = "|".join(
                    enum_var.indicator_name(var_name, k) for k in range(enum_var.n_indicators)
                )
                neq_replacement = f"({positive})"
            neq_pattern = re.compile(rf'\b{re.escape(var_name)}\s*!=\s*{re.escape(value)}\b')
            formula = neq_pattern.sub(neq_replacement, formula)
    return formula


def _substitute_pattern_calls(formula: str) -> str:
    m = _PATTERN_CALL_RE.search(formula)
    while m:
        start = m.end()
        depth = 1
        j = start
        while depth > 0:
            if formula[j] == '(':
                depth += 1
            elif formula[j] == ')':
                depth -= 1
            j += 1
        args_text = formula[start:j - 1]
        args = _split_top_level(args_text, ',')
        if len(args) != 2:
            raise ValueError(f"respondsTo(...) expects 2 arguments, got: {args_text}")
        trigger, response = args[0].strip(), args[1].strip()
        replacement = _KNOWN_PATTERN_TRANSLATIONS["respondsTo"](trigger, response)
        formula = formula[:m.start()] + replacement + formula[j:]
        m = _PATTERN_CALL_RE.search(formula)
    return formula


def _mutual_exclusion_formulas(var_name: str, enum_var: EnumVar) -> List[str]:
    """
    One G(!(a&b)); formula per indicator pair, rather than a single
    G(pair1 & pair2 & ...); conjoining all of them - semantically identical
    (G distributes over & - G(A&B&...) === G(A)&G(B)&...), but a single
    big conjunction of many negated-pair clauses forces to_dnf to fully
    distribute AND over the OR each De Morgan'd clause becomes, which is
    exponential in the number of pairs (confirmed: 10 pairs, from a 6-value
    enum, already blows Python's recursion limit converting it to DNF).
    Splitting per pair means to_dnf only ever sees one tiny 2-literal
    disjunction per formula.
    """
    if enum_var.n_indicators < 2:
        return []
    indicators = [enum_var.indicator_name(var_name, i) for i in range(enum_var.n_indicators)]
    return [
        f"G(!({a}&{b}));"
        for idx, a in enumerate(indicators) for b in indicators[idx + 1:]
    ]


def desugar_spectra_text(raw_text: str) -> DesugarResult:
    text = strip_comments(raw_text)
    unsupported = _find_unsupported_construct(text)
    if unsupported:
        return DesugarResult(None, f"unsupported construct: {unsupported}")

    lines = text.splitlines()
    type_aliases, enum_vars, bool_vars = _collect_declarations(lines)
    if not enum_vars and not bool_vars:
        return DesugarResult(None, "no recognizable env/sys variable declarations found")

    module_name = None
    for line in lines:
        m = _MODULE_RE.match(line)
        if m:
            module_name = m.group(1)
            break
    if not module_name:
        return DesugarResult(None, "no module declaration found")

    formulas: List[Tuple[str, str, str]] = []  # (keyword, name, body)
    unnamed_counters: Dict[str, int] = {}
    seen_names: Dict[str, int] = {}
    i = 0
    n = len(lines)
    while i < n:
        m = _HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue
        keyword = m.group(1)
        name = (m.group(3) or "").strip()
        body_lines = []
        j = i + 1
        while j < n and ';' not in lines[j]:
            if lines[j].strip():
                body_lines.append(lines[j].strip())
            j += 1
        if j >= n:
            return DesugarResult(None, f"formula after '{lines[i].strip()}' has no terminating ';'")
        body_lines.append(lines[j].split(';')[0].strip())
        body = re.sub(r'\s+', '', "".join(body_lines))
        if not name:
            unnamed_counters[keyword] = unnamed_counters.get(keyword, 0) + 1
            name = f"unnamed_{keyword}_{unnamed_counters[keyword]}"
        if name in seen_names:
            # SYNTECH source files sometimes reuse the same descriptive
            # comment as the name for multiple distinct formulas (e.g. every
            # speed-transition rule in ColorSort named "if the speed button
            # is pressed, increase the speed by one level") - harmless as a
            # comment, but SpectraSpecification requires unique formula
            # names, so disambiguate with a counter suffix rather than
            # erroring out on what's really just a naming collision.
            seen_names[name] += 1
            name = f"{name} ({seen_names[name]})"
        else:
            seen_names[name] = 1
        formulas.append((keyword, name, body))
        i = j + 1

    if not formulas:
        return DesugarResult(None, "no assumption/guarantee formulas found")

    try:
        rewritten_formulas = []
        for keyword, name, body in formulas:
            body = _substitute_pattern_calls(body)
            body = _substitute_enum_to_enum_comparisons(body, enum_vars)
            body = _normalize_temporal_operand_equality(body)
            body = _substitute_enum_comparisons(body, enum_vars)
            body = _desugar_iff(body)
            body = _distribute_next_over_or(body)
            rewritten_formulas.append((keyword, name, body))
    except ValueError as e:
        return DesugarResult(None, f"formula rewrite failed: {e}")

    out_lines = [f"module {module_name}", ""]
    for var_name, kind in sorted(bool_vars.items(), key=lambda kv: kv[1]):
        out_lines.append(f"{kind} boolean {var_name};")
    for var_name, enum_var in sorted(enum_vars.items(), key=lambda kv: kv[1].kind):
        for i in range(enum_var.n_indicators):
            out_lines.append(f"{enum_var.kind} boolean {enum_var.indicator_name(var_name, i)};")
    out_lines.append("")

    keyword_to_full = {"asm": "assumption", "assumption": "assumption", "gar": "guarantee", "guarantee": "guarantee"}
    for keyword, name, body in rewritten_formulas:
        out_lines.append(f"{keyword_to_full[keyword]} -- {name}")
        out_lines.append(f"\t{body};")
        out_lines.append("")

    for var_name, enum_var in enum_vars.items():
        mutex_formulas = _mutual_exclusion_formulas(var_name, enum_var)
        formula_keyword = "assumption" if enum_var.kind == "env" else "guarantee"
        for idx, mutex in enumerate(mutex_formulas, start=1):
            base_name = f"{var_name}_mutual_exclusion"
            name = base_name if len(mutex_formulas) == 1 else f"{base_name}_{idx}"
            out_lines.append(f"{formula_keyword} -- {name}")
            out_lines.append(f"\t{mutex}")
            out_lines.append("")

    return DesugarResult("\n".join(out_lines))
