import re
from collections import defaultdict

from spec_repair.enums import Learning


def assign_equalities(formula_n, variables):
    r"""
    Rewrite bare atoms into Spectra's explicit `name=true` / `name=false` form.

    The boundaries are `\b`, not `[a-z]`. The previous guards - a lookahead of
    `(?!=|[a-z])` and a lookbehind of `(?<![a-z])` - stopped a match running
    into a following *lowercase letter*, but not into an underscore or a digit.
    So any variable whose name is a prefix of another, with `_` or a digit at
    the join, was substituted inside the longer name:

        !hready_counter_val0   ->   hready=false_counter_val0

    which is syntactically valid and semantically nonsense; Spectra then
    rejects it with "Couldn't resolve reference to Referrable
    'false_counter_val0'", pointing nowhere near the cause. AMBA hits this with
    `hready` against `hready_counter_val0`.

    `\b` does not match between a word character and `_` or a digit, so the
    longer name is left alone, while `!hready&`, `!hready)` and `!hready` at
    end-of-string still match. `(?!=)` is kept so an already-assigned
    `name=true` is not rewritten again.
    """
    for var in variables:
        escaped = re.escape(var)
        formula_n = re.sub(rf"!{escaped}\b(?!=)", var + "=false", formula_n)
        formula_n = re.sub(rf"(?<!\w){escaped}\b(?!=)", var + "=true", formula_n)
    return formula_n


def strip_vars(spec, sub=["env", "sys"]):
    return re.findall(r"[" + '|'.join(sub) + r"]\s*boolean\s*(.*)\s*;", '\n'.join(spec))


def make_names_asp_safe(spec: list[str]) -> list[str]:
    """
    ASP/Clingo requires atom (constant) names to start with a lowercase letter
    and contain only word characters - an uppercase-leading identifier is
    silently parsed as a variable instead (e.g. specs carried over from the
    SYNTECH benchmark corpus, like HeadMotor_bwd), while a name containing
    spaces or other punctuation (e.g. a `guarantee -- no pause is eternal`
    label, as used throughout the ColorSort case study) is a hard clingo
    syntax error. Either one silently breaks grounding for the whole
    generated program. Renames every such variable and rule name to a safe
    form, consistently, before any other parsing happens.
    """
    variable_names = [v.strip() for v in strip_vars(spec)]
    rule_names = [
        re.search(r'--\s*(.+)', line).group(1).strip()
        for line in spec if line.find("--") >= 0
    ]
    asp_safe_identifier = re.compile(r'[a-z][a-zA-Z0-9_]*')
    names_needing_renaming = [
        n for n in dict.fromkeys(variable_names + rule_names)
        if n and not asp_safe_identifier.fullmatch(n)
    ]

    taken_names = set(variable_names) | set(rule_names)
    rename_map = {}
    for name in names_needing_renaming:
        safe_name = re.sub(r'[^a-zA-Z0-9_]+', '_', name)
        safe_name = safe_name[0].lower() + safe_name[1:]
        if not safe_name[0].isalpha():
            safe_name = "n_" + safe_name
        suffix = 2
        while safe_name in taken_names and safe_name != name:
            safe_name = f"{safe_name}_v{suffix}"
            suffix += 1
        rename_map[name] = safe_name
        taken_names.add(safe_name)

    for name, safe_name in rename_map.items():
        # \b only makes sense where the name's own edge is a word character -
        # a name ending in punctuation (e.g. a `[...]`-suffixed ColorSort
        # guarantee label) can never satisfy a trailing \b, since that needs a
        # word character on the other side, which a label followed by a
        # newline/EOL never has - silently turning the whole substitution
        # into a no-op instead of raising.
        prefix = r"\b" if re.match(r"\w", name) else ""
        suffix = r"\b" if re.search(r"\w$", name) else ""
        pattern = prefix + re.escape(name) + suffix
        spec = [re.sub(pattern, safe_name, line) for line in spec]
    return spec


def extract_string_within(pattern, line, strip_whitespace=False):
    line = re.compile(pattern).search(line).group(1)
    if strip_whitespace:
        return re.sub(r"\s", "", line)
    return line


def format_spec(spec):
    spec = make_names_asp_safe(spec)
    variables = strip_vars(spec)
    spec = word_sub(spec, "spec", "module")
    spec = word_sub(spec, "alwEv", "GF ( ")
    spec = word_sub(spec, "alw", "G ( ")
    # 'I' is later removed as not real Spectra syntax:
    spec = word_sub(spec, "ini", "I ( ")
    spec = word_sub(spec, "asm", "assumption --")
    spec = word_sub(spec, "gar", "guarantee --")
    # This bit deals with multivalued 'enums'
    spec, new_vars = enumerate_spec(spec)
    for i, line in enumerate(spec):
        words = line.strip("\t").split(" ")
        words = [x for x in words if x != ""]
        # This bit fixes boolean style
        if words and words[0] not in ['env', 'sys', 'spec', 'assumption', 'guarantee', 'module']:
            if len(re.findall(r"\(", line)) == len(re.findall(r"\)", line)) + 1:
                line = line.replace(";", " ) ;")
            # This replaces next(A & B) with next(A) & next(B):
            # line = spread_temporal_operator(line, "next")
            # line = spread_temporal_operator(line, "PREV")
            line = assign_equalities(line, variables + new_vars)
            spec[i] = line
    # This simplifies multiple brackets to single brackets
    # spec = [re.sub(r"\(\s*\((.*)\)\s*\)", r"(\1)", x) for x in spec]
    spec = [remove_trivial_outer_brackets(x) for x in spec]
    return spec


def enumerate_spec(spec):
    new_vars = []
    for i, line in enumerate(spec):
        line = re.sub(r"\s", "", line)
        words = line.split(" ")
        reg = re.search(r"(env|sys){", line)
        if reg:
            # if words[0] in ['env', 'sys'] and line.find("{") >= 0:
            enum = extract_string_within("{(.*)}", line, True).split(",")
            name = extract_string_within("}(.*);", line, True)
            for value in enum:
                pattern = f"{name}\s*=\s*{value}"
                replacement = f"{name}_{value}"
                new_vars.append(replacement)
                spec = [re.sub(pattern, replacement, x) for x in spec]
                pattern = pattern.replace("=", "!=")
                replacement = f"!{replacement}"
                spec = [re.sub(pattern, replacement, x) for x in spec]
            replacement_line = ""
            for var in new_vars:
                replacement_line += reg.group(1) + " boolean " + var + ";\n\n"
            spec[i] = replacement_line
    return spec, new_vars

def split_top_level(expr, sep):
    parts = []
    depth = 0
    start = 0

    for i, c in enumerate(expr):
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif c == sep and depth == 0:
            parts.append(expr[start:i])
            start = i + 1

    parts.append(expr[start:])
    return parts


def extract_balanced(s, start_idx):
    depth = 0
    for i in range(start_idx, len(s)):
        if s[i] == '(':
            depth += 1
        elif s[i] == ')':
            depth -= 1
            if depth == 0:
                return s[start_idx + 1:i], i
    raise ValueError("Unbalanced parentheses")


def flatten_with_op(expr):
    expr = expr.strip()

    # strip redundant parentheses
    while expr.startswith("(") and expr.endswith(")"):
        inner = expr[1:-1].strip()
        if inner.count("(") == inner.count(")"):
            expr = inner
        else:
            break

    depth = 0
    ops = set()

    for c in expr:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif depth == 0 and c in "&|":
            ops.add(c)

    if not ops:
        return None, [expr]

    if len(ops) > 1:
        return None, [expr]

    op = ops.pop()

    parts = []
    depth = 0
    start = 0

    for i, c in enumerate(expr):
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif c == op and depth == 0:
            parts.append(expr[start:i])
            start = i + 1

    parts.append(expr[start:])

    result = []
    for p in parts:
        _, sub = flatten_with_op(p)
        result.extend(sub)

    return op, result

def spread_temporal_operator(line, temporal):
    pattern = temporal + "("
    i = 0
    out = ""

    while i < len(line):
        m = line.find(pattern, i)
        if m == -1:
            out += line[i:]
            break

        out += line[i:m]
        j = m + len(temporal)

        if j >= len(line) or line[j] != '(':
            out += line[m]
            i = m + 1
            continue

        inner, end = extract_balanced(line, j)

        # IMPORTANT: prevent PREV(PREV(...)) explosion
        inner = inner.strip()

        op, atoms = flatten_with_op(inner)

        if op is None:
            rebuilt = f"{temporal}({atoms[0]})"
        else:
            rebuilt = f" {op} ".join(
                f"{temporal}({a.strip()})" for a in atoms
            )

        out += rebuilt
        i = end + 1

    return out

def word_sub(spec: list[str], word: str, replacement: str):
    """
    Takes every expression in a spec and substitute every word in it with another
    :param spec: Specification as list of strings
    :param word: (recurrent) word to be replaced
    :param replacement: Word to replace by
    :return: new_spec.
    """
    return [re.sub(f"\b{word}\b", replacement, x) for x in spec]


def remove_trivial_outer_brackets(output):
    if has_trivial_outer_brackets(output):
        return output[1:-1]
    return output


def has_trivial_outer_brackets(output):
    contents = list(parenthetic_contents(output))
    if len(contents) == 1:
        if len(contents[0][1]) == len(output) - 2:
            return True
    return False


def parenthetic_contents(text):
    """Generate parenthesized contents in string as pairs (level, contents)."""
    stack = []
    for i, c in enumerate(text):
        if c == '(':
            stack.append(i)
        elif c == ')' and stack:
            start = stack.pop()
            yield (len(stack), text[start + 1: i])


def remove_multiple_newlines(text):
    return re.sub("\n+", "\n", '\n'.join(text)).split("\n")


def replace_false_true(string):
    return string.replace("false", "__PLACEHOLDER__").replace("true", "false").replace("__PLACEHOLDER__", "true")


def flip_assignments(assignments: list[str]) -> list[str]:
    return [replace_false_true(assignment) for assignment in assignments]


def parse_formula_str(formula: str) -> list[dict[str, list[str]]]:
    """
    Parse a formula consisting of disjunctions and conjunctions of temporal operators.

    Args:
        formula (str): The input formula to parse.

    Returns:
        List[Dict[str, List[str]]]: A list of dictionaries containing operators and their associated literals.
    """
    # Remove any whitespace for easier processing
    formula = formula.replace(" ", "")

    # Split the formula by disjunction (e.g., '|' or '∨')
    disjunctions = formula.split('|')
    parsed_conjunctions = []

    for conjunct in disjunctions:
        conjunct = remove_outer_parentheses(conjunct)
        conjunct_dict = defaultdict(list)

        # Split each conjunct by conjunctions (e.g., '&')
        parts = split_with_outer_parentheses(conjunct)

        for part in parts:
            # Regex to capture "operator(content)"
            match = re.match(r'^(next|prev|PREV|G|F)\((.+)\)', part)

            if match:
                operator = match.group(1)
                operator = "eventually" if operator == "F" else operator
                operator = "prev" if operator == "PREV" else operator
                content = match.group(2)
                # Split content by '&' and add to corresponding operator
                literals = re.split(r'\s*&\s*', content)
                conjunct_dict[operator].extend(literals)
            else:
                # No temporal operator, assume 'current' (no operation)
                literals = re.split(r'\s*&\s*', part.strip("()"))
                conjunct_dict["current"].extend(literals)

        parsed_conjunctions.append(dict(conjunct_dict))

    return parsed_conjunctions


def split_with_outer_parentheses(input_str: str) -> list[str]:
    """
    Split the input string based on operators while considering outer parentheses.

    Args:
        input_str (str): The input string to split.

    Returns:
        List[str]: A list of segments split based on the defined logic.
    """
    # This regex captures '&' not enclosed within parentheses
    pattern = r'\b(next|prev|PREV|F|G)\(([^()]*|[^&]*)*\)|[^()&\s]+'
    segments = [match.group(0) for match in re.finditer(pattern, input_str)]

    # Clean up the segments and filter out empty strings
    return [segment.strip() for segment in segments if segment.strip()]


def remove_outer_parentheses(s):
    s = s.strip()
    # Check if the string starts and ends with parentheses
    if s.startswith('(') and s.endswith(')'):
        return s[1:-1]  # Remove the first and last character
    return s  # Return the original string if conditions are not met


def extract_all_expressions(exp_type, spec):
    search_type = exp_type
    if exp_type in ["asm", "assumption"]:
        search_type = "asm|assumption"
    if exp_type in ["gar", "guarantee"]:
        search_type = "gar|guarantee"
    output = [re.sub(r"\s", "", spec[i + 1]) for i, line in enumerate(spec) if re.search(search_type, line)]
    return output


def spectra_to_DNF(formula):
    prefix = ""
    suffix = ";"
    justice = re.search(r"G\((.*)\);", formula)
    liveness = re.search(r"GF\((.*)\);", formula)
    if justice:
        prefix = "G("
        suffix = ");"
        pattern = justice
    if liveness:
        prefix = "GF("
        suffix = ");"
        pattern = liveness
    if not justice and not liveness:
        non_temporal_formula = formula
    else:
        non_temporal_formula = pattern.group(1)
    parts = non_temporal_formula.split("->")
    if len(parts) == 1:
        return prefix + non_temporal_formula + suffix
    return prefix + '|'.join([negate(parts[0]), parts[1]]) + suffix


def _spans(formula, keyword):
    """(start, open_paren, close_paren) for each `keyword(...)`, parens balanced."""
    out = []
    for m in re.finditer(re.escape(keyword) + r"\s*\(", formula):
        depth, i = 0, m.end() - 1
        while i < len(formula):
            if formula[i] == "(":
                depth += 1
            elif formula[i] == ")":
                depth -= 1
                if depth == 0:
                    out.append((m.start(), m.end(), i))
                    break
            i += 1
    return out


def shift_prev_to_next(formula, variables):
    """
    Move a formula one timepoint forward, so that no PREV remains.

    Spot has no past-time operators, so a Spectra formula mentioning PREV has to
    be expressed with future operators before ltlfilt or ltl2tgba will look at
    it. A formula reading "x held last step, y holds now, z holds next step" is
    the same statement, one step later, as "x holds now, y next, z the step
    after":

        PREV(x)  ->  x          (was t-1, now t)
        y        ->  X(y)       (was t,   now t+1)
        next(z)  ->  X(X(z))    (was t+1, now t+2)

    Only *bare* occurrences shift. An occurrence already inside `PREV(...)` or
    `next(...)` has its offset set by that operator and must be left alone -
    wrapping those as well is what this function used to do, and on amba a
    single PREV in a formula carrying 300 `next` took it from 300 X operators to
    **59,304**, 205,261 characters. ltl2tgba answers that with std::bad_alloc,
    which is the whole of the "exit 2" and, once earlyoom got there first, the
    "exit -15" failures across the 2026-08-18 post-processing runs.

    The rewrite is linear now: one X per bare occurrence, nothing multiplied.
    """
    if not re.search("PREV", formula):
        return re.sub("next", "X", formula)

    # Regions whose offset is already fixed by an operator; bare occurrences are
    # everything outside them.
    protected = []
    for kw in ("PREV", "next"):
        for start, open_end, close in _spans(formula, kw):
            protected.append((start, close + 1))
    protected.sort()

    all_vars = "|".join(sorted(variables, key=len, reverse=True))
    atom = re.compile(r"!?(" + all_vars + r")\b")

    def shift_bare(text):
        return atom.sub(lambda m: f"X({m.group(0)})", text)

    out, cursor = [], 0
    for start, end in protected:
        if start < cursor:      # nested or overlapping; already covered
            continue
        out.append(shift_bare(formula[cursor:start]))
        out.append(formula[start:end])
        cursor = end
    out.append(shift_bare(formula[cursor:]))
    formula = "".join(out)

    # Now the operators themselves: next(z) gains one step, PREV(x) loses its.
    formula = re.sub(r"next\s*\(", "X(X(", formula)
    for start, open_end, close in reversed(_spans(formula, "X(X")):
        formula = formula[:close + 1] + ")" + formula[close + 1:]
    formula = re.sub(r"PREV\s*\(", "(", formula)
    return formula


def remove_double_outer_brackets(string):
    if string[0:2] == "((" and string[-3:-1] == "))":
        return string[1:-1]
    return string


def negate(string):
    '''
    Assumes precedence of AND (DNF)
    :param string:
    :return:
    '''
    # examples:
    # string1 = 'F(level_1_nest_0)|F(level_1_nest_1)|F(level_1_nest_2)'
    # string2 = "A|B&C"
    # string = "(level_1)W(level_2)"
    if string == "":
        return string
    disjuncts = re.sub(r"\s", "", string).split("|")
    for i, sub_string in enumerate(disjuncts):
        conjuncts = sub_string.split("&")
        conjuncts = ["!" + x for x in conjuncts]
        conjuncts = push_negations(conjuncts)
        # This way we push F's out if they are common
        conjunct = check_first_chars(conjuncts, "conjuncts")
        # conjunct = "|".join(conjuncts)
        if len(conjuncts) > 1 and len(disjuncts) > 1:
            conjunct = "(" + conjunct + ")"
        conjunct = remove_double_outer_brackets(conjunct)
        disjuncts[i] = conjunct
    disjuncts = push_negations(disjuncts)
    # This is if we want to push G's out, which i've decided we don't
    # disjuncts = check_first_chars(disjuncts, "disjuncts")
    # return disjuncts
    output = '&'.join(disjuncts)
    output = remove_trivial_outer_brackets(output)
    return output


def check_first_chars(list, type):
    if len(list) == 1:
        return list[0]
    if type == "conjuncts":
        dist_char = "F"
        join_char = "|"
    if type == "disjuncts":
        dist_char = "G"
        join_char = "&"

    first_chars = [chars[0:2] for chars in list]
    character = first_chars[0]
    if all(character == char for char in first_chars):
        if character in ["X(", dist_char + "("]:
            list = [chars[2:-1] for chars in list]
            output = character[0] + "(" + join_char.join(list) + ")"
            return output
    output = join_char.join(list)
    return output


def push_negations(disjuncts):
    disjuncts = [re.sub(r"!\((.*)\)W\((.*)\)", r"(!\2)U((!\2)&(!\1))", x) for x in disjuncts]
    disjuncts = [re.sub(r"!\((.*)\)U\((.*)\)", r"(!\2)W((!\2)&(!\1))", x) for x in disjuncts]
    disjuncts = [re.sub(r"!!", r"", x) for x in disjuncts]
    disjuncts = [re.sub(r"!F\(", r"G(!", x) for x in disjuncts]
    disjuncts = [re.sub(r"!G\(", r"F(!", x) for x in disjuncts]
    disjuncts = [re.sub(r"!X\(", r"X(!", x) for x in disjuncts]
    disjuncts = [re.sub(r"!next\(", r"next(!", x) for x in disjuncts]
    disjuncts = [re.sub(r"!PREV\(", r"PREV(!", x) for x in disjuncts]
    disjuncts = [re.sub(r"!\(", r"(!", x) for x in disjuncts]
    disjuncts = [re.sub(r"!!", r"", x) for x in disjuncts]
    return disjuncts


def split_expression_to_raw_components(exp: str) -> list[str]:
    exp_components: list[str] = exp.split("->")
    if len(exp_components) == 1:
        exp = re.sub(r"(G|GF)\(\s*", r"\1(true -> ", exp_components[0])
        exp_components = exp.split("->")
    exp_components = [comp.strip() for comp in exp_components]
    return exp_components


def eventualise_consequent(exp, learning_type: Learning):
    match learning_type:
        case Learning.ASSUMPTION_WEAKENING:
            line = split_expression_to_raw_components(exp)
            return eventualise_consequent_assumption(line)
        case Learning.GUARANTEE_WEAKENING:
            line = split_expression_to_raw_components(exp)
            return eventualise_consequent_assumption(line)
            raise NotImplemented(
                "Not sure yet if we want to weaken guarantees by introducing eventually to their consequent.")
        case _:
            raise ValueError("No such learning type")


def extract_contents_of_temporal(expression: str):
    # Remove "next", "prev", or "X" (case-insensitive) and surrounding parentheses
    return re.sub(r'(?i)(next|prev|X)\s*\(([^)]*)\)|\)$', r'\2', expression)


def eventualise_consequent_assumption(line: list[str]):
    antecedent = line[0]
    consequent = line[1]
    consequent_without_temporal = extract_contents_of_temporal(consequent)
    ev_consequent = re.sub(r'^(.*?)(;)?$', r'F(\1)\2', consequent_without_temporal)
    output = antecedent + "->" + ev_consequent
    return '\t' + output + "\n"


def re_line_spec(spec: list[str]) -> list[str]:
    """
    Move multiple newlines to new elems in list.
    Ensures every separate elem has a newline at the end.
    e.g.: ["Anna\n\n", "\n", "eats\n", "potatoes"]
        -> ["Anna\n", "\n", "\n", "eats\n", "potatoes\n"]
    :param spec: Specification as list of strings
    :return: new_spec: Specification reformatted as explained above
    """
    return [line + '\n' for line in ''.join(spec).split("\n")]


def matching_paren(expr: str, open_index: int) -> int:
    """
    Index of the `)` closing the `(` at `open_index`.

    Counting rather than matching a regex: nesting is the whole difficulty, and
    a regex cannot count. Raises rather than returning -1 - an unbalanced
    formula is a bug in whatever produced it, and silently returning a wrong
    span is how it stays hidden.
    """
    if expr[open_index] != "(":
        raise ValueError(f"No '(' at index {open_index} of {expr!r}")
    depth = 0
    for i in range(open_index, len(expr)):
        if expr[i] == "(":
            depth += 1
        elif expr[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"Unbalanced parentheses in {expr!r}")


def strip_redundant_parens(expr: str) -> str:
    """`((a & b))` -> `a & b`, leaving `(a) & (b)` alone."""
    expr = expr.strip()
    while expr.startswith("(") and matching_paren(expr, 0) == len(expr) - 1:
        expr = expr[1:-1].strip()
    return expr


def split_top_level_implication(expr: str):
    """
    Split `s -> p` at the `->` that is not inside parentheses, or None.

    The top-level one is the only one that separates antecedent from
    consequent; `(a -> b) -> F(c)` has two, and splitting at the first gives
    nonsense.
    """
    depth = 0
    for i, c in enumerate(expr):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == "-" and depth == 0 and expr[i:i + 2] == "->":
            return expr[:i].strip(), expr[i + 2:].strip()
    return None
