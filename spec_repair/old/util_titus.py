import re
import subprocess

from spec_repair.old.case_study_translator import negate, realizable
from spec_repair.enums import SimEnv
from spec_repair.old.specification_helper import strip_vars, create_cmd
from spec_repair.util.file_util import read_file_lines, write_file


def generate_trace_asp(start_file, end_file, trace_file):
    try:
        old_trace = read_file_lines(trace_file)
    except FileNotFoundError:
        old_trace = []
    asp_restrictions = compose_old_traces(old_trace)

    trace = {}

    initial_expressions, prevs, primed_expressions, unprimed_expressions, variables \
        = extract_expressions_from_file(end_file, counter_strat=True)
    initial_expressions_s, prevs_s, primed_expressions_s, unprimed_expressions_s, variables_s \
        = extract_expressions_from_file(start_file, counter_strat=True)

    # To include starting guarantees:
    ie_g, prevs_g, pe_g, upe_g, v_g = extract_expressions_from_file(start_file, guarantee_only=True)
    initial_expressions += ie_g
    primed_expressions += pe_g
    unprimed_expressions += upe_g

    # initial_expressions_sa, prevs_sa, primed_expressions_sa, unprimed_expressions_sa, variables_sa = extract_expressions(
    #     start_file, counter_strat=True)

    # This adds starting guarantees to final assumptions
    # initial_expressions += [x for x in initial_expressions_s if x not in initial_expressions_sa]
    # primed_expressions += [x for x in primed_expressions_s if x not in primed_expressions_sa]
    # unprimed_expressions += [x for x in unprimed_expressions_s if x not in unprimed_expressions_sa]

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


def write_trace(trace, filename):
    try:
        prev = read_file_lines(filename)
        timepoint = int(max(re.findall(r"trace_name_(\d*)", ''.join(prev)))) + 1
    except FileNotFoundError:
        timepoint = 0
    trace_name = "trace_name_" + str(timepoint)
    output = ""
    for timepoint in trace.keys():
        variables = list(trace[timepoint])
        for var in variables:
            if not re.search(r"prev_", var):
                prefix = ""
                if var[0] == "!":
                    prefix = "not_"
                    var = var[1:]
                output += prefix + "holds_at(" + var + "," + str(timepoint) + "," + trace_name + ").\n"
        output += "\n"
    with open(filename, 'a', newline='\n') as file:
        file.write(output)


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
    list_of_prevs = ["PREV\\(" + s + "\\)" for s in variables + ["!" + x for x in variables]]
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
        name = "t" + str(i)
        disjuncts = rule.split(";")
        output += '\n'.join([name + " :- " + x + "." for x in disjuncts])
        output += "\ns" + name + " :- not " + name + ".\n:- s" + name + ".\n"

    # output = '\n'.join([x + "." for x in expressions])
    # output += '\n'
    output += '\n'.join(["{" + var + "}." for var in variables])
    output += '\n'

    neg_expressions = aspify(neg_expressions)
    rules = []
    for i, x in enumerate(neg_expressions):
        name = "rule" + str(i)
        disjuncts = x.split(";")
        output += '\n'.join([name + " :- " + dis + "." for dis in disjuncts]) + "\n"
        # output += name + " :- " + x + ".\n"
        rules.append(name)

    if len(rules) > 0:
        output += ":- " + ','.join(rules) + ".\n"
    output += '\n'.join(["#show " + var + "/0." for var in variables]) + "\n"

    file = "/tmp/temp_asp.lp"
    write_file(file, output)
    clingo_out = run_clingo_raw(file)
    violation = True

    reg = re.search(r"Answer: 1(.*)SATISFIABLE", clingo_out, re.DOTALL)
    if not reg:
        # print(clingo_out)
        # print("Something not right with model generation")
        return None, None
    model = reg.group(1)
    model = re.sub(r"\n", "", model)
    state = model.split(" ")
    [state.append("!" + x) for x in variables if x not in state]
    state = [x for x in state if x != ""]
    return [state], violation


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
    spec = [re.sub(r"(" + vars + ")=true", r"\1", line) for line in spec]
    spec = [re.sub(r"(" + vars + ")=false", r"!\1", line) for line in spec]
    return spec


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


def aspify(expressions):
    # is this first one ok?
    expressions = [re.sub(r"\(|\)", "", x) for x in expressions]
    expressions = [re.sub(r"\|", ";", x) for x in expressions]
    expressions = [re.sub(r"!", " not ", x) for x in expressions]
    expressions = [re.sub(r"&", ",", x) for x in expressions]
    return expressions


def run_clingo_raw(filename) -> str:
    filepath = f"{filename}"
    cmd = create_cmd(['clingo', filepath])
    output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    return output.decode('utf-8')


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


def semantically_identical_spot(to_cmp_file, baseline_file):
    to_cmp_file = re.sub("_patterned\.spectra", ".spectra", to_cmp_file)
    assumption = equivalent_expressions("assumption|asm", to_cmp_file, baseline_file)
    if assumption is None:
        return SimEnv.Invalid
    if not assumption:
        if realizable(to_cmp_file):
            return SimEnv.Realizable
        else:
            # This should never happen:
            return SimEnv.Unrealizable
    guarantee = equivalent_expressions("guarantee|gar", to_cmp_file, baseline_file)
    if guarantee is None:
        print("Guarantees Not Working in Spot:\n" + to_cmp_file)
    if not guarantee:
        return SimEnv.IncorrectGuarantees
    return SimEnv.Success


def equivalent_expressions(exp_type, start_file, end_file):
    start_exp = extract_all_expressions_spot(exp_type, start_file)
    end_exp = extract_all_expressions_spot(exp_type, end_file)
    linux_cmd = ["ltlfilt", "-c", "-f", f"{start_exp}", "--equivalent-to", f"{end_exp}"]
    p = subprocess.Popen(linux_cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.communicate()[0]
    close_file_descriptors_of_subprocess(p)
    output = output.decode('utf-8')
    reg = re.search(r"(\d)\n", output)
    if not reg:
        return None
    result = reg.group(1)
    if result == "0":
        return False
    if result == "1":
        return True
    return None


def close_file_descriptors_of_subprocess(p):
    if p.stdin:
        p.stdin.close()
    if p.stdout:
        p.stdout.close()
    if p.stderr:
        p.stderr.close()


def extract_all_expressions_spot(exp_type, file, return_list=False):
    spec = read_file_lines(file)
    variables = strip_vars(spec)
    spec = simplify_assignments(spec, variables)
    expressions = [re.sub(r"\s", "", spec[i + 1]) for i, line in enumerate(spec) if re.search("^" + exp_type, line)]
    expressions = [shift_prev_to_next(formula, variables) for formula in expressions]
    if any([re.search("PREV", x) for x in expressions]):
        raise Exception("There are still PREVs in the expressions!")
    if return_list:
        return [re.sub(";", "", x) for x in expressions]
    exp_conj = re.sub(";", "", '&'.join(expressions))
    return exp_conj
