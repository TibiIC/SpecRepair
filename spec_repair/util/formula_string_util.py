import re
from collections import defaultdict

from spec_repair.enums import Learning
from spec_repair.util.specification_helper import strip_vars, assign_equalities


def extract_string_within(pattern, line, strip_whitespace=False):
    line = re.compile(pattern).search(line).group(1)
    if strip_whitespace:
        return re.sub(r"\s", "", line)
    return line


def format_spec(spec):
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
    # This changes names that start with capital letters to lowercase so that ilasp/clingo knows they are not variables.
    spec = [re.sub('--[A-Z]', lambda m: m.group(0).lower(), x) for x in spec]
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


def shift_prev_to_next(formula, variables):
    # Assumes no nesting of next/prev
    # filt = r'PREV\(' + r'|PREV\('.join(variables) + r'|PREV\(!'.join(variables)
    filt = "PREV"
    if not re.search(filt, formula):
        return re.sub("next", "X", formula)
    formula = re.sub("next", "XX", formula)

    all_vars = '|'.join(["!" + var + "|" + var for var in variables])
    # formula = re.sub(r"([^\(^!])(" + all_vars + r")|([^V^X])\((" + all_vars + ")", r"\1X(\2)", formula)
    formula = re.sub(f"([^V^X])\(({all_vars})", r"\1(X(\2)", formula)
    formula = re.sub(f"([^\(^!])({all_vars})", r"\1X(\2)", formula)

    formula = re.sub(r"PREV\((" + all_vars + r")\)", r"\1", formula)
    return formula
    # save this as explanation of above:
    # re.sub(r"([^\(^!])(!highwater|highwater|!pump|pump)|([^V^X])\((!highwater|highwater|!pump|pump)", r"\1X(\2)", formula)
    # use this to test:
    # temp_formula ='G(PREV(pump)&PREV(!methane)&!highwater&methane&!methane&pump->XX(!highwater)&XX(methane));'

    # re.sub(r"([^V^X])\((!pump)", r"\1(X(\2))", formula)


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
