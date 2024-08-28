import copy
import operator
import re
from functools import reduce
from typing import Set, Dict, Union, List, Optional

import pandas as pd

from spec_repair.enums import Learning, When, ExpType
from spec_repair.heuristics import choose_one_with_heuristic, manual_choice, HeuristicType
from spec_repair.ltl import CounterStrategy, spectra_to_df
from spec_repair.old.patterns import PRS_REG, FIRST_PRED, ALL_PREDS
from spec_repair.config import PROJECT_PATH, FASTLAS
from spec_repair.old.specification_helper import strip_vars, assign_equalities
from spec_repair.util.file_util import read_file_lines, write_file


def pRespondsToS_substitution(output_filename):
    spec = read_file_lines(output_filename)
    found = False
    for i, line in enumerate(spec):
        line = line.strip("\t|\n|;")
        if PRS_REG.search(line):
            found = True
            s = re.search(r"G\(([^-]*)", line).group(1)
            p = re.search(r"F\((.*)", line).group(1)
            if p[-2:] == "))":
                p = p[0:-2]
            else:
                print("Trouble extracting p from: " + line)
                exit(1)
                # return "No_file_written:" + line
            replacement = "\tpRespondsToS(" + s + "," + p + ");\n"
            spec[i] = replacement
    if found:
        spec.append(''.join(read_file_lines(f"{PROJECT_PATH}/files/pRespondsToS.txt")))
        new_filename = output_filename.replace(".spectra", "_patterned.spectra")
        write_file(new_filename, spec)
        return new_filename
    return output_filename


# TODO: toggle "sorted" off when performance optimised
def create_signature(spec_df: pd.DataFrame):
    variables = extract_variables(spec_df)
    output = "%---*** Signature  ***---\n\n"
    for var in sorted(variables):
        output += f"atom({var}).\n"
    output += "\n\n"
    return output


def extract_variables(spec_df: pd.DataFrame) -> List[str]:
    antecedents: list[list[str]] = spec_df['antecedent'].tolist()
    consequents: list[list[str]] = spec_df['consequent'].tolist()

    elems: list[str] = reduce(operator.concat, antecedents + consequents, [])
    all_elems = "|".join(elems)
    variables = re.findall(r"\([^,]*,([^,]*)", all_elems)
    return list(dict.fromkeys(variables))


class CSTraces:
    trace: str
    raw_trace: str
    is_deadlock: bool

    def __init__(self, trace, raw_trace, is_deadlock):
        self.trace = trace
        self.raw_trace = raw_trace
        self.is_deadlock = is_deadlock


def cs_to_cs_trace(cs: CounterStrategy, cs_name: str, heuristic: HeuristicType) -> CSTraces:
    trace_name_dict: dict[str, str] = cs_to_named_cs_traces(cs)
    cs_trace_raw, cs_trace_path = choose_one_with_heuristic(list(trace_name_dict.items()), heuristic)
    cs_trace = trace_replace_name(cs_trace_raw, cs_trace_path, cs_name)
    is_deadlock = "DEAD" in cs_trace_path
    return CSTraces(cs_trace, cs_trace_raw, is_deadlock)


def cs_to_named_cs_traces(cs: CounterStrategy) -> dict[str, str]:
    start = "INI"
    output = ""
    trace_name_dict: dict[str, str] = {}
    extract_trace(cs, output, start, 0, "ini", trace_name_dict)

    return trace_name_dict


def trace_replace_name(trace: str, old_name: str, new_name: str) -> str:
    reg = re.compile(rf"\b{old_name}\b")
    trace = reg.sub(new_name, trace)
    trace = re.sub(rf"(trace\({new_name})", rf"% CS_Path: {old_name}\n\n\1", trace)
    return trace


# TODO: generate multiple counter-strategies
def create_cs_traces(ilasp, learning_type: Learning, cs_list: List[CounterStrategy]) \
        -> Dict[str, CSTraces]:
    count = 0
    traces_dict: dict[str, CSTraces] = {}
    for lines in cs_list:
        trace_name_dict = cs_to_named_cs_traces(lines)
        cs_trace, cs_trace_path = choose_one_with_heuristic(list(trace_name_dict.items()), manual_choice)
        cs_trace_list = [cs_trace]
        # TODO: make it clear that a single trace/name pair is created for each element in the list
        trace, trace_names = create_trace(cs_trace_list, ilasp=ilasp, counter_strat=True,
                                          learning_type=learning_type)
        replacement = rf"counter_strat_{count}"
        for name in trace_names:
            trace = trace_replace_name(trace, name, replacement)
        count += 1
        # Add trace to counter-strat collection:
        is_deadlock = "DEAD" in cs_trace_path
        traces_dict[replacement] = CSTraces(trace, cs_trace, is_deadlock)

    return traces_dict


def create_trace(violation_file: Union[str, List[str]], ilasp=False, counter_strat=False,
                 learning_type=Learning.ASSUMPTION_WEAKENING):
    # This is for starting with unrealizable spec - an experiment
    if violation_file == "":
        return ""
    if type(violation_file) is not list:
        trace = read_file_lines(violation_file)
    else:
        trace = violation_file
    trace = re.sub("\n+", "\n", '\n'.join(trace)).split("\n")
    output = "%---*** Violation Trace ***---\n\n"
    trace_names: Set[str] = set(map(lambda match: match.group(1),
                                    filter(None,
                                           map(lambda line: re.search(r",\s*([^,]*)\)\.", line),
                                               trace)
                                           )
                                    )
                                )
    for name in trace_names:
        reg = re.compile(re.escape(name))
        sub_trace = list(filter(reg.search, trace))

        # TODO: understand infinite traces & use to rework counter-strategy trees
        # TODO: replace is_infinite with Sx->Sy->Sx->Sy and not "DEAD" in name
        is_infinite = bool(re.search("ini_S\d", name))
        # This is for making counter strategies positive when guarantee weakening:
        if learning_type == Learning.GUARANTEE_WEAKENING:
            pos_int = False
        else:
            pos_int = counter_strat
        output = create_pos_interpretation(ilasp, output, sub_trace, is_infinite, pos_int)
    if counter_strat:
        return output, trace_names
    else:
        return output


def create_pos_interpretation(ilasp: bool, output: str, trace: List[str], is_infinite: bool,
                              counter_strat: bool) -> str:
    max_timepoint = 0
    for line in trace:
        line = re.sub(r"\s", "", line)
        timepoint = line.split(",")[-2]
        max_timepoint = max(max_timepoint, int(timepoint))
    # TODO: understand why violation name is the last line of the trace
    violation_name = trace[-1].split(",")[-1].replace(").", "")
    if is_infinite:
        states = violation_name.split("_")
        state_count = [states.count(i) for i in states]
        if 2 in state_count:
            loop = state_count.index(2)
        else:
            is_infinite = False
    if ilasp and not counter_strat:
        output += "#pos({entailed(" + violation_name + ")},{},{\n"
    if ilasp and counter_strat:
        output += "#pos({},{entailed(" + violation_name + ")},{\n"
    output += f"trace({violation_name}).\n\n"
    output += create_time_fact(max_timepoint + 1, "timepoint", [0, violation_name])
    output += create_time_fact(max_timepoint, "next", [1, 0, violation_name])
    if is_infinite:
        output += create_time_fact(1, "next", [loop, max_timepoint, violation_name])
    output += '\n' + '\n'.join(trace) + '\n'
    if ilasp:
        output += "\n}).\n\n"
    return output


def trace_list_to_ilasp_form(asp_trace: str, learning: Learning) -> str:
    output = "%---*** Violation Trace ***---\n\n"
    asp_trace = asp_trace.split('\n')
    individual_traces = get_individual_traces(asp_trace)
    for trace in individual_traces:
        output += trace_single_asp_to_ilasp_form(trace, learning)
    return output


def trace_list_to_asp_form(traces: List[str]) -> str:
    output = "%---*** Violation Trace ***---\n\n"
    traces = remove_multiple_newlines(traces)
    individual_traces = get_individual_traces(traces)
    for trace in individual_traces:
        output += trace_single_to_asp_form(trace)
    return output


def get_individual_traces(traces: List[str]) -> List[List[str]]:
    """
    There may be multiple states of traces of different names.
    We isolate them based on their names
    """
    individual_traces = []
    trace_names: Set[str] = get_trace_names(traces)
    for name in trace_names:
        sub_trace = isolate_trace_of_name(traces, name)
        individual_traces.append(sub_trace)
    return individual_traces


def isolate_trace_of_name(trace: List[str], name: str):
    """
    There may be multiple states of traces of different names.
    We have the names, now we only need to isolate the specific
    individual trace by its name.
    e.g. names: trace_name_0, ini_S0_S1, ini_S0_S1_S1
    """
    reg = re.compile(re.escape(name))
    sub_trace = list(filter(reg.search, trace))
    return sub_trace


def get_trace_names(trace: List[str]) -> Set[str]:
    return set(map(lambda match: match.group(1),
                   filter(None,
                          map(lambda line: re.search(r",\s*([^,]*)\)\.", line),
                              trace)
                          )
                   )
               )


def trace_single_to_asp_form(trace: List[str]) -> str:
    max_timepoint = 0
    for line in trace:
        line = re.sub(r"\s", "", line)
        timepoint = line.split(",")[-2]
        max_timepoint = max(max_timepoint, int(timepoint))
    # TODO: understand why violation name is the last line of the trace
    violation_name = trace[-1].split(",")[-1].replace(").", "")
    output = f"trace({violation_name}).\n\n"
    output += create_time_fact(max_timepoint + 1, "timepoint", [0, violation_name])
    output += create_time_fact(max_timepoint, "next", [1, 0, violation_name])

    output += complete_loop_if_necessary(violation_name)
    output += '\n' + '\n'.join(trace) + '\n'
    return output


def trace_single_asp_to_ilasp_form(trace: List[str], learning: Learning) -> str:
    """
    Pre: a single trace, with a single name, is provided
    """
    name = get_trace_names(trace).pop()
    raw_pattern = r'ini_(S\d+)_.*'
    cs_pattern = r'counter_strat_\d+'
    is_counter_strat: bool = bool(re.match(raw_pattern, name) or re.match(cs_pattern, name))
    if learning == Learning.ASSUMPTION_WEAKENING and is_counter_strat:
        output = f"#pos({{}},{{entailed({name})}},{{\n"
    else:
        output = f"#pos({{entailed({name})}},{{}},{{\n"
    output += '\n' + '\n'.join(trace) + '\n}).\n'
    return output


def complete_loop_if_necessary(violation_name) -> str:
    states = get_state_numbers(violation_name)
    match states[-2:]:
        case [s1, s2]:
            if s1 >= s2:
                return f"next({s2},{s1},{violation_name}).\n"
    return ""


def get_state_numbers(name: str) -> List[int]:
    """
    Extract numeric values of ini_S1_S2_...SN
    """
    pattern = r'ini_(S\d+)_.*'
    match = re.match(pattern, name)

    if match:
        numbers_list = re.findall(r'\d+', name)
        return [int(num) for num in numbers_list]
    return []


def create_time_fact(max_timepoint, name, param_list=None):
    if param_list is None:
        param_list = []
    output = ""
    for i in range(max_timepoint):
        strings = [str(i + x) if type(x) == int else x for x in param_list]
        output += f"{name}({','.join(strings)}).\n"
    return output


# TODO: replace traces as Dict with a Set[Tuple[str,str]]
def extract_trace(lines, output, start, timepoint, trace_name, traces: Dict[str, str]) -> Optional[str]:
    if len(re.findall(start, trace_name)) > 1 or start == "DEAD":
        output = re.sub("trace_name", trace_name, output)
        return output
    pattern = re.compile("^" + start)
    states = list(filter(pattern.search, lines))
    env = re.compile("{(.*)}\s*/", ).search(states[0]).group(1)
    output += vars_to_asp(env, timepoint)
    for state in states:
        sys = re.compile("/\s*{(.*)}", ).search(state).group(1)
        out_copy = copy.deepcopy(output)
        out_copy += vars_to_asp(sys, timepoint)
        next = extract_string_within("->\s*([^\s]*)\s", state)
        new_trace_name = trace_name + "_" + next
        new_output = extract_trace(lines, out_copy, next, timepoint + 1, new_trace_name, traces)
        if new_output is not None:
            traces[new_output] = new_trace_name


def vars_to_asp(sys, timepoint) -> str:
    vars = re.split(",\s*", sys)
    output = "\n".join([var_to_asp(var, timepoint) for var in vars])
    output += "\n"  # TODO: consider removing this last line
    return output


def var_to_asp(var, timepoint) -> str:
    parts = var.split(":")
    suffix = ""
    if parts[1] == "false":
        suffix = "not_"
    params = [parts[0], str(timepoint), "trace_name"]
    return f"{suffix}holds_at({','.join(params)})."


def extract_string_within(pattern, line, strip_whitespace=False):
    line = re.compile(pattern).search(line).group(1)
    if strip_whitespace:
        return re.sub(r"\s", "", line)
    return line


def expressions_df_to_str(expressions: pd.DataFrame, learning_names: Optional[List[str]] = None,
                          for_clingo=False) -> str:
    if learning_names is None:
        learning_names = []
    expression_string = ""
    for _, line in expressions.iterrows():
        # This removes alwEv's unless they are being learned:
        expression_string += expression_to_str(line, learning_names, for_clingo)
    return expression_string


def expression_to_str(line: pd.Series, learning_names: list[str], for_clingo: bool) -> str:
    if line.when == When.EVENTUALLY and line['name'] not in learning_names and not for_clingo:
        return ""
    expression_string = f"%{line['type']} -- {line['name']}\n"
    expression_string += f"%\t{line['formula']}\n\n"
    expression_string += f"{line['type']}({line['name']}).\n\n"
    is_exception = (line['name'] in learning_names) and not for_clingo
    ant_exception = is_exception and line['type'] == str(ExpType.ASSUMPTION)
    gar_exception = is_exception and line['type'] == str(ExpType.GUARANTEE)
    expression_string += propositionalise_formula(line, "antecedent", ant_exception)
    expression_string += propositionalise_formula(line, "consequent", gar_exception)
    return expression_string


def get_temp_op(rule: str) -> str:
    """
    Extracts the first argument of the "holds_at" expression.
    On error (generally means string is empty), returns the
    "current" temporal operator.
    @param rule:
    @return:
    """
    try:
        return re.search(r"holds_at\((\w+)(,\w+)*\)", rule).group(1)
    except AttributeError:
        return "current"


def propositionalise_formula(line, component_type, exception=False):
    output = ""
    rules = line[component_type]
    timepoint = "T" if line['when'] != When.INITIALLY else "0"
    if len(rules) == 0:
        rules = [""]
    rule = rules[0]
    temp_op = get_temp_op(rule)
    first_arg = f"{temp_op}," if component_type == "consequent" else ""
    component_body = f"{component_type}_holds({first_arg}{line['name']},{timepoint},S):-\n" + \
                     f"\ttrace(S),\n" + \
                     f"\ttimepoint({timepoint},S)"
    if component_type == "consequent":
        output += component_body
        output += f",\n{component_end_consequent(line, temp_op, timepoint)}.\n\n"
    for rule in rules:
        if component_type != "consequent":
            output += component_body
        elif component_type == "consequent":
            output += root_consequent_body(line, timepoint)
        if rule != "":
            if component_type == "consequent":
                op_rule = re.sub(temp_op, r"OP", rule)
                output += f",\n\t{op_rule}"
            elif component_type != "consequent":
                output += f",\n\t{rule}"

        if exception and component_type != "consequent":
            output += f",\n\tnot antecedent_exception({line['name']},{timepoint},S)"
        output += ".\n\n"
        if exception and component_type == "consequent":
            output += root_consequent_body(line, timepoint)
            output += f",\n\tconsequent_exception({line['name']},{timepoint},S).\n"

    return output


def root_consequent_body(line, timepoint):
    root_consequent_body = f"root_consequent_holds(OP,{line['name']},{timepoint},S):-\n" + \
                           f"\ttrace(S),\n" + \
                           f"\ttimepoint({timepoint},S),\n" + \
                           f"\ttemporal_operator(OP)"
    return root_consequent_body


def component_end_consequent(line, temp_op, timepoint):
    out = f"\troot_consequent_holds({temp_op},{line['name']},{timepoint},S)"
    if temp_op != "eventually":
        out += f",\n\tnot ev_temp_op({line['name']})"
    return out


def get_assumptions_and_guarantees_from(start_file) -> pd.DataFrame:
    spec: List[str] = format_spec(read_file_lines(start_file))
    spec_df: pd.DataFrame = spectra_to_df(spec)
    return spec_df


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
        if words[0] not in ['env', 'sys', 'spec', 'assumption', 'guarantee', 'module']:
            if len(re.findall(r"\(", line)) == len(re.findall(r"\)", line)) + 1:
                line = line.replace(";", " ) ;")
            # This replaces next(A & B) with next(A) & next(B):
            line = spread_temporal_operator(line, "next")
            line = spread_temporal_operator(line, "PREV")
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


def spread_temporal_operator(line, temporal):
    pattern = r"(!)?" + temporal + r"\(([^\)]*)(&|\|)\s*"
    replacement = temporal + r"(\1\2) \3 \1" + temporal + "("
    while re.search(pattern, line):
        line = re.sub(pattern, replacement, line)
    line = re.sub("!" + temporal + r"\(", temporal + "(!", line)
    return line


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


# TODO: Revisit when optimising
def illegal_assignments(spec_df: pd.DataFrame, violations, trace):
    illegals = dict()
    # Violations needs to contain some values
    if trace == "" or not violations:
        return illegals
    expression_names: List[str] = re.findall(r"[assumption|guarantee]\(([^\)^,]*)\)", violations[0])
    for exp_name in expression_names:
        when = extract_df_content(spec_df, exp_name, "when")
        violated_timepoints = re.findall(r"violation_holds\(" + exp_name + r",(\d*),([^\)]*)\)", violations[0])
        preds: List[str] = []
        for vt in violated_timepoints:
            preds += extract_predicates(vt, trace)
        if when == when.EVENTUALLY:
            preds: List[str] = [re.sub(r"at_next\(|at_prev\(|at\(", "at_eventually(", x) for x in preds]
        preds = list(dict.fromkeys(preds))
        preds = [re.sub(r"\.", "", x) for x in preds]
        negs = [x[4:] if re.search(r"^not_", x) else "not_" + x for x in preds]
        illegals[exp_name] = negs
        # illegals[exp_name] = [x for x in negs if x not in preds]
    return illegals


def extract_df_content(formula_df: pd.DataFrame, name: str, extract_col: str):
    try:
        extracted_item = formula_df.loc[formula_df["name"] == name, extract_col].iloc[0]
        return extracted_item
    except IndexError:
        print(f"Cannot find name:\t'{name}'\n\nIn specification expression names:\n")
        print(formula_df["name"])
        exit(1)


def extract_predicates(vt, trace):
    trace_list = trace.split("\n")
    unprimed_preds = extract_preds_at(trace_list, vt, 0)
    prev_preds = extract_preds_at(trace_list, vt, -1)
    next_preds = extract_preds_at(trace_list, vt, 1)
    return unprimed_preds + prev_preds + next_preds


def extract_preds_at(trace_list, vt, offset):
    timepoint_string = "," + str(int(vt[0]) + offset) + "," + vt[1]
    swap = ""
    if offset == -1:
        swap = "_prev"
    if offset == 1:
        swap = "_next"
    preds = [re.sub(r"at\(", "at" + swap + "(", x) for x in trace_list if re.search(r"_.*" + timepoint_string, x)]
    return [re.sub(timepoint_string, ",V1,V2", x) for x in preds]


def remove_multiple_newlines(text):
    return re.sub("\n+", "\n", '\n'.join(text)).split("\n")


def replace_false_true(string):
    return string.replace("false", "__PLACEHOLDER__").replace("true", "false").replace("__PLACEHOLDER__", "true")


def flip_assignments(assignments: list[str]) -> list[str]:
    return [replace_false_true(assignment) for assignment in assignments]


def integrate_rule(arrow, conjunct, learning_type, line):
    conjunct = re.sub("\s", "", conjunct)
    facts = conjunct.split(";")
    if FASTLAS:
        facts = [x for x in facts if x != ""]
    assignments = extract_assignments_from_facts(facts, learning_type)

    is_eventually_consequent = "eventually" not in conjunct and bool(re.match(r"^F\(.+\)", line[-1]))
    if learning_type == Learning.ASSUMPTION_WEAKENING or is_eventually_consequent:
        assignments = flip_assignments(assignments) if is_eventually_consequent else assignments
        return integrate_antecedent(assignments, line, facts)

    if learning_type == Learning.GUARANTEE_WEAKENING:
        return integrate_consequent(arrow, assignments, facts, line)


def integrate_antecedent(assignments, line, facts):
    next_assignments = [x for i, x in enumerate(assignments) if re.search("next", facts[i])]
    cur_assignments = [x for x in assignments if x not in next_assignments]
    orig_ant = re.search(r"(G\(|GF\()(.*)$", line[0])
    if orig_ant:
        op = orig_ant.group(1)
        head = orig_ant.group(2)
    else:
        op = ""
        head = line[0]
    disjuncts = get_disjuncts(head)
    amended_disjuncts = []
    for disjunct in disjuncts:
        conjuncts = get_conjuncts(disjunct)
        next_conjuncts = [x for x in conjuncts if re.search("next", x)] + next_assignments
        cur_conjuncts = [x for x in conjuncts if x not in next_conjuncts] + cur_assignments

        antecedent = ""
        if cur_conjuncts:
            antecedent += conjunct_assignments(cur_conjuncts)
        if cur_conjuncts and next_conjuncts:
            antecedent += "&"
        if next_conjuncts:
            antecedent += f"next({conjunct_assignments(next_conjuncts)})"
        amended_disjuncts.append(antecedent)
    antecedent_total = op + disjunct_assignments(amended_disjuncts)
    consequent = line[1]
    output = antecedent_total + "->" + consequent
    # This is in case there was no antecedent to start with:
    output = re.sub(r"\(\s*&", "(", output)
    output = re.sub(r"\(\s*\|", "(", output)
    output = re.sub(r"\(\s*->", "(", output)
    output = re.sub(r"->\s*\|", "->", output)
    if assignments == [] and FASTLAS:
        return '\n'
    return '\t' + output + "\n"


def integrate_consequent(arrow, assignments, facts, line):
    antecedent = line[0]
    end_line = line[1]
    next_assignments = [x for i, x in enumerate(assignments) if re.search("next", facts[i])]
    ev_assignments = [x for i, x in enumerate(assignments) if re.search("eventually", facts[i])]
    cur_assignments = [x for x in assignments if x not in ev_assignments and x not in next_assignments]
    cur = conjunct_assignments(cur_assignments)
    next = conjunct_assignments(next_assignments)
    ev = conjunct_assignments(ev_assignments)
    # This is for pRespondsToS patterns:
    respond = re.search(r"F\(([^)]*)\)", end_line)
    if respond:
        ev = f"F({disjunct_assignments([ev, respond.group(1)])})"
        end_line = end_line.replace(f"F({respond.group(1)})", '', 1)
    elif re.search(r"GF\(", antecedent):
        ev_old = end_line.replace(");", "")
        ev = disjunct_assignments([ev, ev_old])
        end_line = end_line.replace(ev_old, '', 1)
    # This is for next patterns:
    respond = re.search(r"next\(([^)]*)\)", end_line)
    if respond:
        next = f"next({disjunct_assignments([next, respond.group(1)])})"
        end_line = end_line.replace(f"next({respond.group(1)})", '', 1)
    elif next:
        next = f"next({next})"
    end_line = end_line.replace("\n", "", 1)
    end_line = end_line.replace(");", "", 1)
    cur = disjunct_assignments([cur] + get_disjuncts(end_line))
    consequent = disjunct_assignments([cur, next, ev])
    output = f"\t{antecedent}{arrow}{consequent});"
    if assignments == [] and FASTLAS:
        return '\n'
    return output + "\n"


def extract_assignments_from_facts(facts, learning_type):
    assignments = []
    for fact in facts:
        temp_op = FIRST_PRED.search(fact).group(1)
        all_atoms = ALL_PREDS.search(fact).group(1)
        atom = all_atoms.split(',')[1].strip()
        # Don't flip if it is consequent_exception
        make_true = fact[0:4] == "not_"
        if learning_type == Learning.GUARANTEE_WEAKENING:
            make_true = not make_true
        # The reason it is this way around is that we need to negate whatever is learned
        if make_true:
            value = "true"
        else:
            value = "false"
        atom_assignment = atom + "=" + value

        assignments.append(atom_assignment)
    return assignments


def get_conjuncts(disjunct: str):
    return disjunct.split("&")


def get_disjuncts(conjunct: str):
    return conjunct.split("|")


def conjunct_assignments(assignments):
    assignments = [assignment for assignment in assignments if assignment != ""]
    output = '&'.join(assignments)
    return output


def disjunct_assignments(assignments):
    assignments = [assignment for assignment in assignments if assignment != ""]
    output = '|'.join(assignments)
    return output
