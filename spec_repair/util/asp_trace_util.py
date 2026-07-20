import re
from typing import List, Set, Tuple, Union

from spec_repair.enums import Learning
from spec_repair.model.spectra_atom import SpectraAtom
from spec_repair.config import PROJECT_PATH
from spec_repair.util.file_util import read_file_lines, write_file, generate_temp_filename, write_to_file, \
    write_trace
from spec_repair.util.formula_string_util import remove_multiple_newlines, extract_all_expressions, spectra_to_DNF, \
    strip_vars
from spec_repair.util.patterns import PRS_REG
from spec_repair.util.subprocess_util import create_cmd, run_subprocess


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
        new_filename = generate_temp_filename('.spectra')
        write_file(new_filename, spec)
        return new_filename
    return output_filename


def create_atom_signature_asp(spec_atoms: Set[SpectraAtom]):
    output = "%---*** Signature  ***---\n\n"
    for atom in sorted(spec_atoms):
        output += f"atom({atom.name}).\n"
    output += "\n\n"
    return output


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
    trace_names: Set[str] = get_trace_names(trace)
    for name in trace_names:
        sub_trace = isolate_trace_of_name(trace, name)

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


def max_timepoint_and_violation_name(trace: List[str]) -> Tuple[int, str]:
    max_timepoint = 0
    for line in trace:
        line = re.sub(r"\s", "", line)
        timepoint = line.split(",")[-2]
        max_timepoint = max(max_timepoint, int(timepoint))
    # TODO: understand why violation name is the last line of the trace
    violation_name = trace[-1].split(",")[-1].replace(").", "")
    return max_timepoint, violation_name


def create_pos_interpretation(ilasp: bool, output: str, trace: List[str], is_infinite: bool,
                              counter_strat: bool) -> str:
    max_timepoint, violation_name = max_timepoint_and_violation_name(trace)
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
    max_timepoint, violation_name = max_timepoint_and_violation_name(trace)
    loop_completion = complete_loop_if_necessary(violation_name, max_timepoint)
    output = f"trace({violation_name}).\n\n"
    output += create_time_fact(max_timepoint + 1, "timepoint", [0, violation_name])
    if not loop_completion:
        output += f"weak_timepoint(weak_t,{violation_name}).\n"
    output += create_time_fact(max_timepoint, "next", [1, 0, violation_name])
    if not loop_completion:
        output += f"next(weak_t,{max_timepoint},{violation_name}).\n"
        output += f"next(weak_t,weak_t,{violation_name}).\n"

    output += loop_completion
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


def complete_loop_if_necessary(violation_name, max_timepoint) -> str:
    states = get_state_numbers(violation_name)
    if not states:
        return ""
    max_state = max(states)
    state_timepoint_diff = max_timepoint - max_state
    match states[-2:]:
        case [s1, s2]:
            if s1 >= s2:
                return f"next({s2 + state_timepoint_diff},{s1 + state_timepoint_diff},{violation_name}).\n"
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


def log_to_asp_trace(lines: str, trace_name: str = "trace_name_0") -> str:
    """
    Converts a runtime log into a workable trace string
    i.e.
    ->
    :param lines: Lines from log file
    :param trace_name: Name of Log
    :return: Trace string
    """
    ret = ""
    for i, line in enumerate(lines.split("\n")):
        ret += log_line_to_asp_trace(line, i, trace_name)
        ret += "\n"
    return ret


def log_line_to_asp_trace(line: str, idx: int = 0, trace_name: str = "trace_name_0") -> str:
    """
    Converts one line from a runtime log into a workable trace string
    i.e.
    ->
    :param line: <highwater:false, methane:false, pump:false, PREV_aux_0:false, Zn:0>
    :param idx: index where log line resides
    :param trace_name:
    :return:     not_holds_at(current,highwater,idx,trace_name).
                 not_holds_at(current,methane,idx,trace_name).
                 not_holds_at(current,pump,idx0,trace_name).
    """
    pairs = extract_string_boolean_pairs(line)
    filtered_pairs = [(key, value == 'true') for key, value in pairs if not key.startswith(('PREV', 'NEXT', 'Zn'))]
    ret = ""
    for env_var, is_true in filtered_pairs:
        ret += f"{'' if is_true else 'not_'}holds_at(current,{env_var},{idx},{trace_name}).\n"

    return ret


def extract_string_boolean_pairs(line):
    """
    Get all pairs of strings and booleans of form 'name:val'
    :param line:
    :return:
    """
    pattern = r"\b([a-zA-Z_][\w]*):(\btrue\b|\bfalse\b)"
    pairs = re.findall(pattern, line)
    return pairs


def generate_trace_asp(strong_spec_file, ideal_spec_file, trace_file):
    try:
        old_trace = read_file_lines(trace_file)
    except FileNotFoundError:
        old_trace = []
    asp_restrictions = compose_old_traces(old_trace)

    trace = {}

    initial_expressions, prevs, primed_expressions, unprimed_expressions, variables \
        = extract_expressions_from_file(ideal_spec_file, counter_strat=True)
    initial_expressions_s, prevs_s, primed_expressions_s, unprimed_expressions_s, variables_s \
        = extract_expressions_from_file(strong_spec_file, counter_strat=True)

    # Must-hold side gets the ideal spec's own guarantees. Using the strong
    # (mutated) spec's guarantees here would force the trace to satisfy
    # whatever stronger guarantee is under test, making it impossible to
    # ever witness a violation of a strengthened guarantee.
    ie_g, prevs_g, pe_g, upe_g, v_g = extract_expressions_from_file(ideal_spec_file, guarantee_only=True)
    initial_expressions += ie_g
    primed_expressions += pe_g
    unprimed_expressions += upe_g

    # Must-violate side gets the strong spec's guarantees too, so a trace
    # that violates a strengthened guarantee (while still honouring the
    # strengthened assumptions) counts as a genuine violation, not just
    # assumption violations. When guarantees are unmutated (strong ==
    # ideal), these duplicate the guarantees just pinned true on the
    # must-hold side above, so they can never be the ones that fail here -
    # falling back to today's assumption-only-violation behaviour exactly.
    ie_g_s, prevs_g_s, pe_g_s, upe_g_s, v_g_s = extract_expressions_from_file(strong_spec_file, guarantee_only=True)
    initial_expressions_s += ie_g_s
    primed_expressions_s += pe_g_s
    unprimed_expressions_s += upe_g_s

    expressions = primed_expressions + unprimed_expressions
    neg_expressions = primed_expressions_s + unprimed_expressions_s

    variables = [var for var in variables if not re.search("prev|next", var)]

    # Lowercasing PREV in expressions
    expressions = [re.sub(r"PREV\((!*)([^\|^\(]*)\)", r"\1prev_\2", x) for x in expressions]
    neg_expressions = [re.sub(r"PREV\((!*)([^\|^\(]*)\)", r"\1prev_\2", x) for x in neg_expressions]
    # Removing braces around next function args (`next(sth)` -> `next_sth`)
    expressions = [re.sub(r"next\((!*)([^\|^\(]*)\)", r"\1next_\2", x) for x in expressions]
    neg_expressions = [re.sub(r"next\((!*)([^\|^\(]*)\)", r"\1next_\2", x) for x in neg_expressions]

    one_point_exp = [re.sub(r"(" + '|'.join(variables) + r")", r"prev_\1", x) for x in
                     unprimed_expressions + initial_expressions]
    expressions += one_point_exp
    expressions += [re.sub(r"(" + '|'.join(variables) + r")", r"next_\1", x) for x in unprimed_expressions]
    neg_one_point_exp = [re.sub(r"(" + '|'.join(variables) + r")", r"prev_\1", x) for x in
                         unprimed_expressions_s + initial_expressions_s]
    neg_expressions += neg_one_point_exp
    neg_expressions += [re.sub(r"(" + '|'.join(variables) + r")", r"next_\1", x) for x in unprimed_expressions_s]

    expressions += two_period_primed_expressions(primed_expressions, variables)
    neg_expressions += two_period_primed_expressions(primed_expressions_s, variables)

    # Can it be done with one time point?
    state, violation = generate_model(one_point_exp,
                                      neg_one_point_exp,
                                      variables, scratch=True,
                                      asp_restrictions=asp_restrictions)
    if state is not None and len(neg_one_point_exp) > 0:
        trace[0] = [re.sub(r"prev_", "", var) for var in state[0] if re.search("prev_", var)]
        write_trace(trace, trace_file)
        return trace_file, violation

    # Can it be done with two time points?
    two_point_exp = [x for x in expressions if not re.search("next", x)]
    two_point_neg_exp = [x for x in neg_expressions if not re.search("next", x)]
    state, violation = generate_model(two_point_exp,
                                      two_point_neg_exp, variables, scratch=True,
                                      asp_restrictions=asp_restrictions)
    if state is not None and len(two_point_neg_exp) > 0:
        trace[0] = [re.sub(r"prev_", "", var) for var in state[0] if re.search("prev_", var)]
        trace[1] = [var for var in state[0] if not re.search("prev_|next_", var)]
        write_trace(trace, trace_file)
        return trace_file, violation

    # Can it be done with three time points?
    state, violation = generate_model(expressions, neg_expressions, variables, scratch=True,
                                      asp_restrictions=asp_restrictions)
    if state is None or len(neg_expressions) == 0:
        return None, None
    trace[0] = [re.sub(r"prev_", "", var) for var in state[0] if re.search("prev_", var)]
    trace[1] = [var for var in state[0] if not re.search("prev_|next_", var)]
    trace[2] = [re.sub(r"next_", "", var) for var in state[0] if re.search("next_", var)]
    write_trace(trace, trace_file)
    return trace_file, violation


def compose_old_traces(old_trace):
    if old_trace == []:
        return ""
    string = ''.join(old_trace)
    traces = re.findall(r"trace_name_\d*", string)
    traces = list(dict.fromkeys(traces))
    output = "\n"
    for i, name in enumerate(traces):
        assignments = []
        for n in range(3):
            as_name = "as" + str(i) + "_" + str(n)
            assignments += asp_trace_to_spectra(name, string, n)
            output += as_name + " :- " + ','.join(assignments) + ".\n"
            output += ":- " + as_name + ".\n"
    return output


def two_period_primed_expressions(primed_expressions, variables):
    nexts = [x for x in primed_expressions if not re.search("PREV|prev", x)]
    prevs = [x for x in primed_expressions if not re.search("next", x)]
    next2_3 = [re.sub(r"next\((!*)([^\|^\(]*)\)", r"\1next_\2", x) for x in nexts]
    next1_2 = [re.sub("(" + "|".join(variables) + ")", r"prev_\1", x) for x in nexts]
    next1_2 = [re.sub(r"next\((!*)([^\|^\(]*)\)", r"\1next_\2", x) for x in next1_2]
    next1_2 = [re.sub(r"next_prev_", "", x) for x in next1_2]

    prev1_2 = [re.sub(r"PREV\((!*)([^\|^\(]*)\)", r"\1prev_\2", x) for x in prevs]
    prev2_3 = [re.sub("(" + "|".join(variables) + ")", r"next_\1", x) for x in prevs]
    prev2_3 = [re.sub(r"PREV\((!*)([^\|^\(]*)\)", r"\1prev_\2", x) for x in prev2_3]
    prev2_3 = [re.sub(r"prev_next_", "", x) for x in prev2_3]
    return next1_2 + next2_3 + prev1_2 + prev2_3


def extract_expressions_from_file(file, counter_strat=False, guarantee_only=False):
    spec = read_file_lines(file)
    return extract_expressions_from_spec(spec, counter_strat, guarantee_only)


def extract_expressions_from_spec(spec: list[str], counter_strat=False, guarantee_only=False):
    variables = strip_vars(spec)
    spec = simplify_assignments(spec, variables)
    assumptions = extract_non_liveness(spec, "assumption")
    guarantees = extract_non_liveness(spec, "guarantee")
    if counter_strat:
        guarantees = []
    if guarantee_only:
        assumptions = []
    prev_expressions = [re.search(r"G\((.*)\);", x).group(1) for x in assumptions + guarantees if
                        re.search(r"PREV", x) and re.search("G", x)]
    list_of_prevs = [f"PREV\\({s}\\)" for s in variables + [f"!{x}" for x in variables]]
    prev_occurances = [re.findall('|'.join(list_of_prevs), exp) for exp in prev_expressions]
    prevs = [item for sublist in prev_occurances for item in sublist]
    prevs = [re.sub(r"PREV\(!*(.*)\)", r"prev_\1", x) for x in prevs]
    prevs = list(dict.fromkeys(prevs))
    variables += prevs
    variables.sort()

    unprimed_expressions = [re.search(r"G\(([^F]*)\);", x).group(1) for x in assumptions + guarantees if
                            not re.search(r"PREV|next", x) and re.search(r"G\s*\(", x)]
    primed_expressions = [re.search(r"G\(([^F]*)\);", x).group(1) for x in assumptions + guarantees if
                          re.search(r"PREV|next", x) and re.search("G", x)]
    initial_expressions = [x.strip(";") for x in assumptions + guarantees if not re.search(r"G\(|GF\(", x)]
    return initial_expressions, prevs, primed_expressions, unprimed_expressions, variables


def extract_non_liveness(spec, exp_type):
    output = extract_all_expressions(exp_type, spec)
    return [spectra_to_DNF(x) for x in output if not re.search("F", x)]


def generate_model(expressions, neg_expressions, variables, scratch=False, asp_restrictions="", force=False):
    if scratch:
        prevs = ["prev_" + var for var in variables]
        nexts = ["next_" + var for var in variables]
        if any([re.search("next", x) for x in expressions + neg_expressions]):
            variables = variables + prevs + nexts
        # TODO: double check regex, ensure it's correct
        elif any([re.search(r"\b" + r"|\b".join(variables), x) for x in expressions + neg_expressions]):
            variables = variables + prevs
        else:
            variables = prevs
        output = asp_restrictions + "\n"
    else:
        output = ""
    expressions = aspify(expressions)
    for i, rule in enumerate(expressions):
        name = f"t{i}"
        disjuncts = [x.strip() for x in rule.split(";")]
        for disjunct in disjuncts:
            output += f"{name} :- {disjunct}.\n"
        output += f"s{name} :- not {name}.\n"
        output += f":- s{name}.\n"

    for variable in variables:
        output += f"{{{variable}}}.\n"

    neg_expressions = aspify(neg_expressions)
    rules = []
    for i, rule in enumerate(neg_expressions):
        name = f"rule{i}"
        disjuncts = [x.strip() for x in rule.split(";")]
        for disjunct in disjuncts:
            output += f"{name} :- {disjunct}.\n"
        rules.append(name)

    if len(rules) > 0:
        output += f":- {','.join(rules)}.\n"
    for var in variables:
        output += f"#show {var}/0.\n"

    file = generate_temp_filename('.lp')
    write_file(file, output)
    clingo_out = run_clingo_raw(file, n_models=0)
    violation = True

    matches = re.findall(r'Answer:\s*\d+(?:.*)?\r?\n([^\r\n]*)', clingo_out)

    if not matches:
        # print(clingo_out)
        # print("Something not right with model generation")
        return None, None
    states = [match.split() for match in matches]
    for state in states:
        [state.append(f"!{x}") for x in variables if x not in state]
    return states, violation


def asp_trace_to_spectra(name, string, n):
    tups = re.findall(r"\b(.*)holds_at\((.*)," + str(n) + "," + name + r"\)", string)
    prefix = ""
    if n == 2:
        prefix = "next_"
    if n == 0:
        prefix = "prev_"
    output = ["not " + prefix + tup[1] if tup[0] == "not_" else prefix + tup[1] for tup in tups]
    return output


def simplify_assignments(spec, variables):
    vars = "|".join(variables)
    spec = [re.sub(rf"({vars})=true", r"\1", line) for line in spec]
    spec = [re.sub(rf"({vars})=false", r"!\1", line) for line in spec]
    return spec


def aspify(expressions):
    # is this first one ok?
    expressions = [re.sub(r"\(|\)", "", x) for x in expressions]
    expressions = [re.sub(r"\|", ";", x) for x in expressions]
    expressions = [re.sub(r"!", " not ", x) for x in expressions]
    expressions = [re.sub(r"&", ",", x) for x in expressions]
    return expressions


def run_clingo_raw(filename, n_models: int = 1) -> str:
    cmd = create_cmd(['clingo', f'--models={n_models}', filename])
    return run_subprocess(cmd)
