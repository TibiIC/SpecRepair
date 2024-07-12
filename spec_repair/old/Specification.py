import copy
import csv
import os
import random
import re
import subprocess
import time
from timeout_decorator import timeout, TimeoutError
from itertools import product
from statistics import median
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd

from spec_repair import config
from spec_repair.exceptions import LearningException
from spec_repair.special_types import EventuallyConsequentRule
from spec_repair.util.exp_util import eventualise_consequent
from spec_repair.util.list_util import re_line_spec
from spec_repair.wrappers.asp_wrappers import run_ILASP_raw
from spec_repair.old.case_study_translator import realizable
from spec_repair.util.spec_util import pRespondsToS_substitution, create_trace, CSTraces, extract_trace, \
    extract_string_within, expressions_df_to_str, format_spec, extract_df_content, illegal_assignments, integrate_rule
from spec_repair.config import PATH_TO_CLI, PRINT_CS, FASTLAS, RESTORE_FIRST_HYPOTHESIS, \
    PROJECT_PATH
from spec_repair.enums import When, ExpType, Learning
from spec_repair.heuristics import choose_one_with_heuristic, manual_choice, HeuristicType
from spec_repair.ltl import spectra_to_df, filter_expressions_of_type
from spec_repair.old.patterns import PRS_REG, FIRST_PRED, ALL_PREDS
from spec_repair.old.specification_helper import run_subprocess, strip_vars, CASE_STUDY_FINALS
from spec_repair.old.util_titus import extract_expressions, generate_model, \
    extract_all_expressions, run_clingo_raw, extract_all_expressions_spot
from spec_repair.util.file_util import is_file_format, generate_filename, generate_random_string, \
    generate_temp_filename, read_file_lines, write_file


def format_name(spectra_file):
    return generate_filename(spectra_file, "_formatted.spectra")


def check_format(spectra_file):
    # TODO: ensure input file is well formatted
    return True
    # names required for assumptions/guarantees
    # no nesting of next/prev
    # no next/prev in liveness


def create_signature_from_file(spectra_file):
    variables = strip_vars(read_file_lines(spectra_file))
    output = "%---*** Signature  ***---\n\n"
    for var in variables:
        output += "atom(" + var + ").\n"
    output += "\n\n"
    return output


def has_extension(file_path, target_extension) -> bool:
    _, extension = os.path.splitext(file_path)
    return extension.lower() == target_extension.lower()


# TODO: Move to ASP wrappers
# TODO: Make it throw the error it returns on bad returns (i.e. syntax errors)
# TODO: check if spectra_file provided should be original version or fixed version
# TODO: don't rename inside of function, provide exact file names and assert their existence
def run_clingo(clingo_file, return_violated_traces=False, exp_type="assumption"):
    assert has_extension(clingo_file, ".lp")
    if not return_violated_traces:
        print("Running Clingo to aid debugging")
    # This assumes my filepath and using WSL
    output = run_clingo_raw(clingo_file)
    output = output.split("\n")
    for i, line in enumerate(output):
        if len(line) > 100:
            output[i] = '\n'.join(line.split(" "))

    answer_set = generate_temp_filename(".answer_set")
    if return_violated_traces:
        return list(filter(re.compile(rf"violation_holds\(|{exp_type}\(|entailed\(").search, output))
    else:
        output = '\n'.join(output)
        write_file(answer_set, output)
        print(f"See file for output: {answer_set}")


# TODO: ASK TITUS why return pRespondsToS too,
#  and why change value in spectra_to_DataFrame?
def gr_one_type(formula):
    '''
    :param formula:
    :return: pRespondsToS, when
    '''
    formula = re.sub('\s*', '', formula)
    eventually = re.search(r"^GF", formula)
    pRespondsToS = PRS_REG.search(formula)
    initially = not re.search(r"^G", formula)
    if eventually:
        when = When.EVENTUALLY
    elif initially:
        when = When.INITIALLY
    elif pRespondsToS:
        when = When.EVENTUALLY
    else:
        when = When.ALWAYS
    return pRespondsToS, when


def drop_all(end_file):
    if not re.search("normalised", end_file):
        print("file not normalised!")
        exit(1)
    spec = read_file_lines(end_file)
    poss_violates = [i + 1 for i, line in enumerate(spec) if
                     re.search("assumption|ass", line) and re.search(r"G", spec[i + 1]) and not re.search(r"F",
                                                                                                          spec[i + 1])]
    possible_ass = [i + 1 for i, line in enumerate(spec) if
                    re.search("assumption|ass", line) and re.search(r"G|GF", spec[i + 1])]
    possible_gar = [i + 1 for i, line in enumerate(spec) if
                    re.search("guarantee|gar", line) and re.search(r"G|GF", spec[i + 1])]

    possible_lines = possible_ass + possible_gar
    possible_lines = [x for x in possible_lines if x not in poss_violates]
    response = re.compile(r'^\s*G\(([^-]*)->\s*F\((.*)\)\s*\)\s*;')
    liveness = re.compile(r"GF\s*\((.*)\)\s*;")
    justice = re.compile(r"G\s*\(([^F]*)\)\s*;")
    exp = re.compile(r"(G)\s*\(([^F]*)\)\s*;|(GF)\s*\((.*)\)\s*;")

    temporals = [exp.search(spec[n]).group(1) for n in possible_lines if exp.search(spec[n])]
    poss_drops = [exp.search(spec[n]).group(2).split("|") for n in possible_lines if exp.search(spec[n])]
    poss_dr_bool = [[bool(not re.search("next|PREV", i)) for i in x] for x in poss_drops]
    # total_drops = sum([sum(x) for x in poss_dr_bool])
    # all_variations = list(product(*[[True,False] for i in range(total_drops)]))
    all_variations = list(product(*[list(product(*[[y, False] if y else [y] for y in x])) for x in poss_dr_bool]))
    all_rules = [
        ['|'.join([poss_drops[i][j] for j, bool in enumerate(subtup) if not bool]) for i, subtup in enumerate(tup)] for
        tup in all_variations]
    [[temporals[i] + "(" + formula + ");\n" for i, formula in enumerate(x)] for x in all_rules]


def summarize_spec(spectra_file):
    # spectra_file = f"{PROJECT_PATH}/input-files/case-studies/modified-specs/minepump/genuine/minepump_FINAL.spectra"
    spec = read_file_lines(spectra_file)
    e_vars = strip_vars(spec, ["env"])
    s_vars = strip_vars(spec, ["sys"])
    assumptions = extract_all_expressions("assumption", spec)
    guarantees = extract_all_expressions("guarantee", spec)
    live = re.compile(r"^GF")
    safe = re.compile(r"^G[^F]*$")
    init = re.compile(r"^[^G]")
    resp = re.compile(r"^G[^F]*->F")
    regs = [init, safe, live, resp]

    columns = ["Type", "Variables", "Expressions", "Initial", "Safety", "Liveness", "Response", "Max Length (vars)",
               "Median Length (vars)"]
    env = summarize_exps(assumptions, e_vars, s_vars, regs)
    sys = summarize_exps(guarantees, s_vars, e_vars, regs)
    tot = summarize_exps(assumptions + guarantees, s_vars + e_vars, [], regs)
    df = pd.DataFrame([["$\mathcal(E)$"] + env, ["$\mathcal(S)$"] + sys, ["Total"] + tot], columns=columns)
    df.index = df["Type"]
    df = df.drop(columns=["Type"]).T
    return df


def summarize_exps(expressions, vars, other_vars, regs):
    output = [len(vars), len(expressions)]
    for reg in regs:
        output.append(count_reg(expressions, reg))

    if len(expressions) == 0:
        return output + [0, 0]

    exp_lengths = [len(re.findall(r"|".join(vars + other_vars), x)) for x in expressions]
    output.append(max(exp_lengths))
    output.append(median(exp_lengths))
    return output


def count_reg(string_list, reg_expr):
    return sum([bool(reg_expr.search(x)) for x in string_list])


def summarize_case_studies():
    csv_list = [110, 67, 66, 59, 52, 45, 38, 31, 30, 23, 19, 15, 14]
    outfolder = "output-files/results"
    df = None
    for n in csv_list:
        outfile = outfolder + "/output" + str(n) + ".csv"
        results = pd.read_csv(outfile, index_col=0)
        results["run_id"] = n
        if df is None:
            df = results
        else:
            df = pd.concat([df, results], axis=0)
    files = CASE_STUDY_FINALS
    keys = files.keys()
    df["Specification"] = [list(keys)[list(files.values()).index(file)] for file in df.file]
    df["Expressions"] = [re.sub(r"\[|\]|'", "", x) for x in df["types"]]
    df["Result"] = [re.sub(r"SimEnv\.", "", x) for x in df["outcome"]]
    df.to_csv("output-files/examples/output_summary.csv")


def summarize_specs():
    files = {  # f"{PROJECT_PATH}/input-files/examples/Arbiter/Arbiter_FINAL.spectra",
        "Lift": f"{PROJECT_PATH}/input-files/examples/lift_FINAL.spectra",
        "Lift New": f"{PROJECT_PATH}/input-files/examples/lift_FINAL_NEW.spectra",
        "Minepump": f"{PROJECT_PATH}/input-files/case-studies/modified-specs/minepump/genuine/minepump_FINAL.spectra",
        # TODO: Find this file
        "Traffic Single": f"{PROJECT_PATH}/input-files/examples/Traffic/traffic_single_FINAL.spectra",
        "Traffic": f"{PROJECT_PATH}/input-files/examples/Traffic/traffic_updated_FINAL.spectra"}
    keys = files.keys()
    # header = pd.MultiIndex.from_product([list(keys), ["env", "sys", "Total"]], names=["Spec", "Type"])
    # list_of_df = [summarize_spec(file) for file in files.values()]
    # df = pd.concat(list_of_df, axis=1)
    # df.columns = header
    # write_file(df.to_latex(), "latex/summary.txt")

    result_file, n = get_last_results_csv_filename(shift=0)
    results = pd.read_csv(result_file, index_col=0)

    results = results[results["outcome"] != "SimEnv.Invalid"]

    results["Specification"] = [list(keys)[list(files.values()).index(file)] for file in results.file]
    results["Expressions"] = [re.sub(r"\[|\]|'", "", x) for x in results["types"]]
    results["Result"] = [re.sub(r"SimEnv\.", "", x) for x in results["outcome"]]

    lat = results_to_latex(results, rows=["Specification", "Result", "Expressions"])
    # lat = re.sub("rrr","|rrr",lat)
    lat += "\n\n" + results_to_latex(results, rows=["Result"])

    output = "\\usepackage{booktabs}\n\\begin{document}\n\\begin{table}\n\\centering\n" + lat + \
             "\\caption{my table}\n\\label{tab:my_label}\n\\end{table}\n\\end{document}\n"

    write_file("latex/output" + n + ".tex", output)


def results_to_latex(results, rows):
    final_df = results.pivot_table(index=rows, values=["total_time", "n_dropped"],
                                   aggfunc="mean", margins=True)
    count_df = results.pivot_table(index=rows, values=["outcome"],
                                   aggfunc="count", margins=True)
    final_df["total_time"] = final_df["total_time"].round(1)
    final_df["n_dropped"] = final_df["n_dropped"].round(1)
    lat = pd.concat([count_df, final_df], axis=1).to_latex()
    # lat = final_df.to_latex()
    # lat = re.sub(r"(\.\d)\d*\b", r"\1", lat)
    lat = re.sub(r"NaN", "-", lat)
    lat = re.sub(r"total\\_time", "Mean Learning", lat)
    lat = re.sub(r"n\\_dropped", "Mean Number of", lat)
    lat = re.sub(r"(" + rows[-1] + "\s*)&\s*&\s*&\s*", r"\1&&Strengthenings&Time (s)", lat)
    lat = re.sub("outcome", "Count", lat)
    lat = re.sub("& A", r"& $\\phi^\\mathcal{E}$", lat)
    lat = re.sub(",G", r",$\\phi^\\mathcal{S}$", lat)
    return lat


def formatted_mean(lst):
    if len(lst) == 0:
        return "-"
    av = sum(lst) / len(lst)
    return str(round(av, 2))


def extract_last_unrealizable_dropped():
    outfile, n = get_last_results_csv_filename(0)
    df = pd.read_csv(outfile)
    df["outcome"] == "SimEnv.Unrealizable"


def save_results_df(total_df):
    outfile, n = get_last_results_csv_filename()
    total_df.to_csv(outfile)


def get_last_results_csv_filename(shift=1, outfolder="output-files/results"):
    # outfolder = "output-files/results"
    all_files = os.listdir(outfolder)
    reg = re.compile(r"output(\d*).csv")
    if len(all_files) == 0:
        n = '0'
    else:
        last_file = max([int(reg.search(x).group(1)) for x in all_files if reg.search(x)])
        n = str(last_file + shift)
    outfile = outfolder + "/output" + n + ".csv"
    return outfile, n


def results_to_df(results, spectra_file, types, include_prev):
    columns = ["file", "run", "types", "prevs", "n_dropped", "outcome", "total_time", "max_time", "median_time",
               "n_runs"]
    output = []
    for key in results.keys():
        result = results[key]
        if len(result[1]) == 0:
            output.append([spectra_file, key, types, include_prev, result[2], result[0], 0, 0, 0, 0])
        else:
            output.append([spectra_file, key, types, include_prev, result[2], result[0], sum(result[1]), max(result[1]),
                           median(result[1]), len(result[1])])
    df = pd.DataFrame(output, columns=columns)
    return df


def increment_diff(diff, i, line):
    try:
        diff[i][line] += 1
    except KeyError:
        try:
            diff[i][line] = 1
        except KeyError:
            diff[i] = {}
            diff[i][line] = 1


def print_diff(final_spec, diff):
    keys = list(diff.keys())
    for i in keys:
        for line in diff[i].keys():
            final_spec[i] += "\t\t" + str(diff[i][line]) + ":" + line + "\n"
    print(''.join(final_spec))


def wrong_order(spec, final_spec):
    expr = re.compile("assumption -- |guarantee -- ")
    for i, line in enumerate(final_spec):
        if spec[i] != line and expr.search(line):
            return True
    return False


def re_order(spec, final_spec):
    final_ex = extract_expressions_to_dict(final_spec)
    start_ex = extract_expressions_to_dict(spec)
    spec = [x for x in spec if re.search("^sys|^env|^module|^spec", x)]
    for key in final_ex.keys():
        spec.append(str(key))
        spec.append(start_ex[key])
    return spec


def extract_expressions_to_dict(final_spec):
    expr = re.compile("assumption -- |guarantee -- ")
    expressions = {}
    for i, line in enumerate(final_spec):
        if expr.search(line):
            expressions[line] = final_spec[i + 1]
    return expressions


def satisfies(expression, state):
    disjuncts = expression.split("|")
    for disjunct in disjuncts:
        conjuncts = disjunct.split("&")
        if all([conjunct in state for conjunct in conjuncts]):
            return True
    return False


def transitions(state, state_space, primed_expressions, prevs):
    primed_expressions = [re.sub(r"PREV\((!*)([^\|]*)\)", r"\1prev_\2", x) for x in primed_expressions]
    # p_exp = primed_expressions[0]
    # p_exp.split("|")
    forced_expressions = [exp for exp in primed_expressions if
                          not any([variable in state for variable in exp.split("|")])]
    nexts = [re.search(r"next\((.*)\)", variable).group(1) for sublist in [exp.split("|") for exp in forced_expressions]
             for variable in sublist if re.search(r"next\((.*)\)", variable)]
    possible_next_states = [s for s in state_space if all([x in s for x in nexts])]
    new_states = possible_next_states
    for prev in prevs:
        var = re.search(r"prev_(.*)", prev).group(1)
        if "!" + var in state:
            new_states = [s for s in possible_next_states if prev not in s]
        else:
            new_states = [s for s in possible_next_states if prev in s]

    return [state_space.index(x) for x in new_states]


def transitions_jit(state, primed_expressions, unprimed_assignments, prevs):
    raise NotImplementedError("Transitions JIT is not finished and not implemented")

    primed_expressions = [re.sub(r"PREV\((!*)([^\|]*)\)", r"\1prev_\2", x) for x in primed_expressions]
    forced_expressions = [exp for exp in primed_expressions if
                          not any([variable in state for variable in exp.split("|")])]
    nexts = [re.search(r"next\((.*)\)", variable).group(1) for sublist in
             [exp.split("|") for exp in forced_expressions]
             for variable in sublist if re.search(r"next", variable)]
    possible_next_states = [s for s in state_space if all([x in s for x in nexts])]

    for prev in prevs:
        var = re.search(r"prev_(.*)", prev).group(1)
        if "!" + var in state:
            new_states = [s for s in possible_next_states if prev not in s]
        else:
            new_states = [s for s in possible_next_states if prev in s]

    return [state_space.index(x) for x in new_states]


def no_next(dis):
    conjuncts = dis.split("&")
    for conjunct in conjuncts:
        if re.search("next", conjunct):
            return False
    return True


def sub_next_only(dis):
    conjuncts = dis.split("&")
    output = '&'.join([re.sub(r"next\(([^\)]*)\)", r"\1", x) for x in conjuncts if re.search("next", x)])
    return re.sub(r"\(|\)", "", output)


def next_only(x, new_state):
    disjuncts = x.split("|")
    # TODO: seems to be generating things that violate assumptions.
    # disjuncts = [dis for dis in disjuncts if not no_next(dis)]
    # currs = [re.sub(r"next\([^\)]*\)", "", dis) for dis in disjuncts]
    # currs = [re.sub(r"&(\))|(\()&", r"\1",c) for c in currs]
    # currs = [re.sub(r"&&","&",c) for c in currs]
    #
    # [satisfies(c,new_state) for c in currs]

    disjuncts = [sub_next_only(dis) for dis in disjuncts if not no_next(dis)]
    return '|'.join(disjuncts)


# TODO: understand this
def next_possible_assignments(new_state, primed_expressions_cleaned, primed_expressions_cleaned_s, unprimed_expressions,
                              unprimed_expressions_s, variables):
    unsat_next_exp = unsat_nexts(new_state, primed_expressions_cleaned)

    # TODO: VERYFY _s should mean the expressions have to be false in order for the violation to occur
    unsat_next_exp_s = unsat_nexts(new_state, primed_expressions_cleaned_s)

    if unsat_next_exp + unsat_next_exp_s + unprimed_expressions + unprimed_expressions_s == []:
        # Pick random assignment
        vars = [var for var in variables if not re.search("prev_", var)]
        i = random.choice(range(2 ** len(vars)))
        # TODO: replace i with 0 for deadlock - in order to make deterministic
        i = 0
        n = "{0:b}".format(i)
        assignments = '0' * (len(vars) - len(n)) + n
        assignments = [int(x) for x in assignments]
        state = ["!" + var if assignments[i] else var for i, var in enumerate(vars)]
        return [state], False
    return generate_model(unsat_next_exp + unprimed_expressions, unsat_next_exp_s + unprimed_expressions_s, variables,
                          force=True)

    # violation = unsat_next_exp + [negate(x) for x in unsat_next_exp_s]
    # parsed = parse_expr(re.sub(r"!", "~", '&'.join(violation)))
    # sympy.to_cnf(parsed)

    # next_assignments = possible_assignments(unsat_next_exp)
    # filtered_next = [x for x in next_assignments if
    #                  not any([satisfies(negate(expression), list(x)) for expression in unprimed_expressions])]
    #
    # violations = [x for x in next_assignments if
    #               any([satisfies(negate(expression), list(x)) for expression in unprimed_expressions_s])]
    # if len(violations) > 0:
    #     return violations, True
    # violations = [x for x in next_assignments if
    #               any([satisfies(negate(expression), list(x)) for expression in unsat_next_exp_s])]
    # if len(violations) > 0:
    #     return violations, True
    #
    # return filtered_next, False


def unsat_nexts(new_state, primed_expressions_cleaned):
    if new_state == []:
        return []
    unsat_primed_exp = [expression for expression in primed_expressions_cleaned if not satisfies(expression, new_state)]
    output = [next_only(x, new_state) for x in unsat_primed_exp]
    output = [x for x in output if x != ""]
    return output


def product_without_dupl(*args, repeat=1):
    pools = [tuple(pool) for pool in args] * repeat
    result = [[]]
    for pool in pools:
        result = [x + [y] if y not in x else x for x in result for y in pool]  # here we added condition
    result = set(list(map(lambda x: tuple(sorted(x)), result)))  # to remove symmetric duplicates
    for prod in result:
        yield tuple(prod)


def split_conjuncts_and_remove_duplicates(tup):
    output = [item for sublist in [re.sub(r"^\(|\)$", r"", x).split("&") for x in list(tup)] for item in sublist]
    return tuple(dict.fromkeys(output))


def slow_state_space(var_space, unprimed_expressions):
    # TODO: check this?
    start = time.time()
    state_space = []
    assignment_sets = possible_assignments(unprimed_expressions)

    for i in range(2 ** len(var_space)):
        n = "{0:b}".format(i)
        assignments = '0' * (len(var_space) - len(n)) + n
        assignments = [int(x) for x in assignments]
        state = set([var[assignments[i]] for i, var in enumerate(var_space)])
        if any([s.issubset(state) for s in assignment_sets]):
            state_space.append(tuple(state))
        # if all([satisfies(expression, state) for expression in unprimed_expressions]):
        #     state_space.append(tuple(state))
    elapsed = (time.time() - start)
    print("Elapsed time: " + str(round(elapsed, 2)) + "s")
    return state_space


def contradiction(x):
    if len(x) == 0:
        return True
    x = list(dict.fromkeys(x))
    vars = [v.strip("!") for v in x]
    var = max(vars, key=vars.count)
    if len([y for y in vars if y == var]) > 1:
        return True
    return False


def possible_assignments(expressions):
    expressions = [x.split("|") for x in expressions]
    required_assignments = list(product_without_dupl(*expressions))
    required_assignments = [split_conjuncts_and_remove_duplicates(tup) for tup in required_assignments]
    assignment_sets = [set(x) for x in required_assignments if not contradiction(x)]
    return assignment_sets


def extract_transitions(file, assumptions_only=False):
    '''

    :param file:
    :return: state_space, initial_state_space, legal_transitions
    '''
    initial_expressions, prevs, primed_expressions, unprimed_expressions, variables = extract_expressions(file,
                                                                                                          assumptions_only)

    var_space = [[x, "!" + x] for x in variables]
    if len(var_space) < 20:
        state_space = list(product(*var_space))
        state_space = [x for x in state_space if all([satisfies(expression, x) for expression in unprimed_expressions])]
    else:
        state_space = slow_state_space(var_space, unprimed_expressions)

    # assignment_set_initials = possible_assignments(initial_expressions)
    # initial_state_space = [x for x in state_space if
    #                        any([s.issubset(set(x)) for s in assignment_set_initials])]

    initial_state_space = [x for x in state_space if
                           all([satisfies(expression, x) for expression in initial_expressions])]
    legal_transitions = [transitions(state, state_space, primed_expressions, prevs) for state in state_space]
    return state_space, initial_state_space, legal_transitions


def semantically_identical(fixed_spec_file, end_file, assumptions_only):
    start_file = re.sub(r"_patterned", "", fixed_spec_file)
    state_space, initial_state_space, legal_transitions = extract_transitions(end_file, assumptions_only)
    state_space_s, initial_state_space_s, legal_transitions_s = extract_transitions(start_file, assumptions_only)

    if state_space == state_space_s and initial_state_space == initial_state_space_s and legal_transitions == legal_transitions_s:
        return True
    return False


def conjunct_is_false(string, variables):
    for var in variables:
        if re.search("!" + var, string) and re.search(r"[^!]" + var + r"|^" + var, string):
            return True
    return False


def last_state(trace, prevs, offset=0):
    prevs = ["prev_" + x if not re.search("prev_", x) else x for x in prevs]
    last_timepoint = max(re.findall(r",(\d*),", trace))
    if last_timepoint == "0" and offset != 0:
        return ()
    last_timepoint = str(int(last_timepoint) - offset)
    absent = re.findall(r"not_holds_at\((.*)," + last_timepoint, trace)
    atoms = re.findall(r"holds_at\((.*)," + last_timepoint, trace)
    assignments = ["!" + x if x in absent else x for x in atoms]
    if last_timepoint == '0':
        prev_assign = ["!" + x for x in prevs]
    else:
        prev_timepoint = str(int(last_timepoint) - 1)
        absent = re.findall(r"not_holds_at\((.*)," + prev_timepoint, trace)
        prev_assign = ["!" + x if x in absent else x for x in prevs]
    assignments += prev_assign
    variables = [re.sub(r"!", "", x) for x in assignments]
    assignments = [i for _, i in sorted(zip(variables, assignments))]
    return tuple(assignments)


def complete_deadlock_with_assignment(assignment, trace, name):
    end = f",{name})."
    last_timepoint = max(re.findall(r",(\d*),", trace))
    timepoint = str(int(last_timepoint) + 1)
    variables = [s for s in assignment if not re.search("prev_", s)]
    asp = ["not_holds_at(" + v[1:] if re.search("!", v) else "holds_at(" + v for v in variables]
    asp = [x + "," + timepoint + end for x in asp]
    return re.sub(r",[^,]*\)\.", end, trace) + '\n'.join(asp)


class Specification:
    def __init__(self, spectra_file, violation_file, violation_list: Optional[List] = None,
                 include_prev=False, include_next=False, counter_strat_file="", random_hypothesis=True,
                 fixed_spec: Optional[str] = None, heuristic: HeuristicType = manual_choice):
        self.min_solutions = []
        self.realizability_checks = {"assumption": 0, "guarantee": 0}
        self.cs_list = []  # List of lists of CounterStrategies in Spectra form
        self.las = ""
        self.log_line = []
        self.is_realizable = None
        self.max_hypotheses = 10
        self.spectra_file = spectra_file
        self.heuristic = heuristic
        self.file_suffix = generate_random_string(length=10)
        self.las_file = generate_filename(self.spectra_file, f"_{self.file_suffix}.las", True)
        self.lp_file = generate_filename(self.spectra_file, f"_{self.file_suffix}.lp", True)
        if fixed_spec:
            assert (is_file_format(fixed_spec, ".spectra"))
            self.fixed_spec_file = fixed_spec
        else:
            self.fixed_spec_file = generate_filename(self.spectra_file, f"_fixed_{self.file_suffix}.spectra")
        self.include_prev = include_prev
        self.include_next = include_next
        self.violation_file = violation_file
        self.violation_trace = create_trace(self.violation_file)
        self.random_hypothesis = random_hypothesis

        self.fixed_spec_history = []
        self.log_list = []

        self.list_of_hypotheses = ""
        self.hypothesis_log = []
        self.attempted_hypotheses = 0

        if violation_list is None:
            violation_list = []
        self.violation_list = violation_list
        self.guarantee_violation_list = []

        self.counter_strat_file = counter_strat_file
        self.counter_strat_count = 0
        self.cs_trace = ""

        self.background_knowledge = ''.join(read_file_lines(f"{PROJECT_PATH}/files/background_knowledge.txt"))

    def run_assumption_weakening(self):
        learning_type = Learning.ASSUMPTION_WEAKENING
        self.initiate_log_line(learning_type)
        self.encode_ILASP(learning_type)
        if not self.violation_list and \
                not self.calculate_violated_expressions():
            raise LearningException("Violation trace not violating")
        hypothesis = run_ILASP_raw(self.las_file)
        if self.integrate_learned_hypothesis(hypothesis):
            self.check_realizability(learning_type)

    def run_pipeline(self, timeout_value: Optional[int] = None):
        self.absolute_start = time.time()
        self.format_spectra_file()
        self.generate_formula_df_from_spectra()
        self.orig_formula_df = copy.deepcopy(self.formula_df)

        def run_pipeline_with_timeout():
            self.run_assumption_weakening()
            # Guarantee weakening is called recursively

        # Adding timeout to the pipeline, if provided
        if timeout_value:
            run_pipeline_with_timeout = timeout(timeout_value)(run_pipeline_with_timeout)
        try:
            run_pipeline_with_timeout()
        except TimeoutError:
            print(f"Timeout after {timeout_value}s learning time.")
            self.is_realizable = os.path.exists(self.fixed_spec_file) and realizable(self.fixed_spec_file)
            if os.path.exists(self.fixed_spec_file):
                self.log(f"Intermediate (not fixed) specification: {self.fixed_spec_file}", True)
            else:
                self.log(f"No intermediate specification generated.", True)

        elapsed = (time.time() - self.absolute_start)
        print(f"Elapsed time: {round(elapsed, 2)}s")
        self.log_pipeline(elapsed)
        return elapsed

    TEMP: set[Tuple[int, str]] = set()

    # TODO: generate multiple counter-strategies
    def create_cs_traces(self, ilasp, learning_type: Learning) \
            -> Dict[str, CSTraces]:
        count = 0
        traces_dict: dict[str, CSTraces] = {}
        for lines in self.cs_list:
            trace_name_dict = self.counter_strat_to_trace(lines)
            cs_trace, cs_trace_path = choose_one_with_heuristic(list(trace_name_dict.items()), self.heuristic)
            cs_trace_list = [cs_trace]
            # TODO: make it clear that a single trace/name pair is created for each element in the list
            trace, trace_names = create_trace(cs_trace_list, ilasp=ilasp, counter_strat=True,
                                              learning_type=learning_type)
            replacement = r"counter_strat_" + str(count)
            for name in trace_names:
                reg = re.compile(r"\b" + name + r"\b")
                # uniquely rename trace
                trace = reg.sub(replacement, trace)
                # save original trace name
                trace = re.sub(r"(trace\(" + replacement + r")", r"\n% CS_Path: " + name + r"\n\n\1", trace)
            count += 1
            # Add trace to counter-strat collection:
            is_deadlock = "DEAD" in cs_trace_path
            traces_dict[replacement] = CSTraces(trace, cs_trace, is_deadlock)

        return traces_dict

    def initiate_log_line(self, learning_type: Learning):
        start = time.time()
        self.log_line = [self.spectra_file]
        self.log_line.append(start)
        self.log_line.append(str(learning_type))
        self.log_line.append(self.include_prev)
        self.log_line.append(r",".join(self.violation_list))
        return start

    def format_spectra_file(self):
        '''
        Converts Spectra file to standardised format for parsing.\n
        :param spectra_file: Path to Spectra specification.
        :return: Boolean indicating success/failure.
        '''
        self.orig_spec = read_file_lines(self.spectra_file)
        if not check_format(self.orig_spec):
            print("Incorrect Spectra Format. See format_spectra_file for correct format.")
            exit(1)
        self.formatted_file = format_name(self.spectra_file)
        self.formatted_spec = format_spec(self.orig_spec)
        self.fixed_spec = copy.deepcopy(self.formatted_spec)

    def generate_formula_df_from_spectra(self):
        self.formula_df = spectra_to_df(self.fixed_spec)

    def encode_ILASP(self, learning_type=Learning.ASSUMPTION_WEAKENING, for_clingo=False):
        '''
        Converts DataFrame of Spectra expressions into ASP files '.las' for learning with ILASP and '.lp' for debugging.
        Output can be found in the output-files folder.

        Violation trace example can be found here: {PROJECT_PATH}/files/traffic_violation.txt

        :param formula_df: Pandas DataFrame generated by spectra_to_DataFrames.
        :param violation_file: Path to text file containing violation trace.
        :param spectra_file: Path to original Spectra specification.
        '''
        # Generate first Clingo file to find violating assumptions/guarantees
        assumptions = filter_expressions_of_type(self.formula_df, ExpType.ASSUMPTION)
        guarantees = filter_expressions_of_type(self.formula_df, ExpType.GUARANTEE)
        assumption_string = expressions_df_to_str(assumptions, for_clingo=True)
        guarantee_string = expressions_df_to_str(guarantees, for_clingo=True)
        signature = create_signature_from_file(self.spectra_file)
        violation_trace_asp = self.violation_trace
        cs_traces_dict: dict[str, CSTraces] = self.create_cs_traces(False, learning_type)
        cs_trace: str = ''.join([trace_obj.trace for trace_obj in cs_traces_dict.values()])
        self.generate_lp_file(assumption_string, guarantee_string, signature, violation_trace_asp, cs_trace,
                              for_clingo=for_clingo)
        if for_clingo:
            return

        exp_type = learning_type.exp_type_str()
        violations = run_clingo(self.lp_file, return_violated_traces=True, exp_type=exp_type)

        # Complete deadlocks if no violations found (behaviour happens ONLY during guarantee weakening)
        if learning_type == Learning.GUARANTEE_WEAKENING:
            deadlock_required = re.findall(r"entailed\((counter_strat_\d*)\)", ''.join(violations))

            if deadlock_required:
                cs_trace_lp = ""
                for trace_name, trace_obj in cs_traces_dict.items():
                    if trace_obj.is_deadlock and trace_name in deadlock_required:
                        assignment = self.extract_one_possible_deadlock_completion_assignments(trace_obj.raw_trace,
                                                                                               self.fixed_spec_file)
                        trace_obj.raw_trace = complete_deadlock_with_assignment(assignment, trace_obj.raw_trace,
                                                                                trace_name)
                        cs_trace_lp += complete_deadlock_with_assignment(assignment, trace_obj.trace, trace_name)
                self.generate_lp_file(assumption_string, guarantee_string, signature, violation_trace_asp, cs_trace_lp,
                                      for_clingo=for_clingo)

            if len(self.guarantee_violation_list) == 0:
                if not self.extract_unrealizable_cores():
                    self.add_guarantee_violation_list(self.get_all_guarantee_names())
                self.log("Guarantee Violation List:", False)
                for expression in self.guarantee_violation_list:
                    self.log('\t' + expression, False)
            self.calculate_violated_expressions(exp_type="guarantee")
            # self.guarantee_violation_list += [v for v in violated_relevant_exp if v not in self.guarantee_violation_list]

        ill_assign: dict = illegal_assignments(self.formula_df, violations, "")

        mode_declaration = self.create_mode_bias(learning_type, ill_assign)
        # TODO: understand where/why this trace is being used
        violation_trace_ilasp = create_trace(self.violation_file, ilasp=True)
        cs_trace = ""
        for trace_name, trace_obj in cs_traces_dict.items():
            # TODO: make it clear that a single trace/name pair is created for each element in the list
            trace, trace_names = create_trace([trace_obj.raw_trace], ilasp=True, counter_strat=True,
                                              learning_type=learning_type)
            for name in trace_names:
                reg = re.compile(r"\b" + name + r"\b")
                # uniquely rename trace
                replacement = trace_name
                trace = reg.sub(replacement, trace)
                # save original trace name
                trace = re.sub(r"(trace\(" + replacement + r")", r"\n% CS_Path: " + name + r"\n\n\1", trace)
            cs_trace += trace
        if PRINT_CS:
            print(cs_trace)

        background_knowledge = self.background_knowledge

        if FASTLAS:
            background_knowledge = re.sub("==", "=", self.background_knowledge)
            max_timepoint = max([int(x) for x in re.findall(r"timepoint\((\d*),", violation_trace_ilasp + cs_trace)])
            for i in range(max_timepoint + 1):
                violation_trace_ilasp += "time(" + str(i) + ").\n"

        match learning_type:
            case Learning.ASSUMPTION_WEAKENING:
                expressions_for_weakening = expressions_df_to_str(assumptions, self.violation_list)
            case Learning.GUARANTEE_WEAKENING:
                expressions_for_weakening = expressions_df_to_str(guarantees, self.guarantee_violation_list)
            case _:
                raise ValueError(f"There should only be Assumption and Guarantee weakenings, not {learning_type}")

        self.las = mode_declaration + background_knowledge + \
                   expressions_for_weakening + signature + violation_trace_ilasp + cs_trace
        if not for_clingo:
            write_file(self.las_file, self.las)

    def generate_lp_file(self, assumptions: str, guarantees: str, signature: str, violation_trace, cs_trace,
                         for_clingo: bool):
        '''
        Generate the contents of the .lp file to be run in Clingo.
        Running this file will generate the violations that hold, given the problem statement
        :param assumptions: GR(1) assumptions, provided as a string in the form of Clingo-compatible statements
        :param guarantees: GR(1) guarantees, provided as a string in the form of Clingo-compatible statements
        :param signature: LTL atoms used in expressions (e.g. methane, highwater, pump, etc.)
        :param violation_trace: Trace which violated the original GR(1) specification
        :param cs_trace: Traces from counter-strategies, which are supposed to violate current specification
        :param for_clingo: TODO (idk)
        :return:
        '''
        lp = self.generate_lp(assumptions, cs_trace, for_clingo, guarantees, signature, violation_trace)
        write_file(self.lp_file, lp)

    def extract_one_possible_deadlock_completion_assignments(self, trace, file):
        file = re.sub("_patterned", "", file)
        initial_expressions, prevs, primed_expressions, unprimed_expressions, variables = extract_expressions(file,
                                                                                                              counter_strat=True)
        initial_expressions_s, prevs_s, primed_expressions_s, unprimed_expressions_s, variables_s = extract_expressions(
            file, guarantee_only=True)
        primed_expressions_cleaned = [re.sub(r"PREV\((!*)([^\|^\(]*)\)", r"\1prev_\2", x) for x in primed_expressions]
        primed_expressions_cleaned_s = [re.sub(r"PREV\((!*)([^\|^\(]*)\)", r"\1prev_\2", x) for x in
                                        primed_expressions_s]
        final_state = last_state(trace, prevs)
        assignments, is_violating = next_possible_assignments(final_state, primed_expressions_cleaned,
                                                              primed_expressions_cleaned_s, unprimed_expressions,
                                                              unprimed_expressions_s, variables)
        if assignments is None:
            raise ValueError("Not possible to complete the deadlock! There is no valid assignment that may "
                             "continue the trace. Some error must have occurred!")
        assignment = choose_one_with_heuristic(assignments, self.heuristic)
        return assignment

    def generate_lp(self, assumptions, cs_trace, for_clingo, guarantees, signature, violation_trace):
        lp = self.background_knowledge + \
             assumptions + \
             guarantees + \
             signature + \
             violation_trace + \
             cs_trace
        if not for_clingo:
            elements_to_show_list: list[str] = ["violation_holds/3", "assumption/1", "guarantee/1", "entailed/1"]
            elements_to_show: str = "\n\n".join(f"#show {element}." for element in elements_to_show_list)
            lp += f"\n\n{elements_to_show}\n"
        return lp

    def integrate_learned_hypothesis(self, hypothesis, learning_type=Learning.ASSUMPTION_WEAKENING):
        '''
        Integrates learned hypothesis into formatted spectra file.

        The first body of the learned rule will be negated and added as conjunct to the antecedent of the rule. For all
        further bodies of the learned rule (if any) they are negated and then added to the antecedent of copies of the
        original rule.

        For example:\n
        original rule:......... A -> B                  \n
        learned hyp:......... C & D                     \n
        negated hyp:....... !C | !D                     \n
        new rule:............... A & (!C | !D) -> B     \n
        translation p1:..... A & !C -> B                \n
        translation p2:..... A & !D -> B                \n

        :return: Path to fixed Spectra specification.
        '''
        if re.search("UNSATISFIABLE", ''.join(hypothesis)):
            if self.attempted_hypotheses == 0:
                print(".las file is UNSAT\nAre the trace atoms labelled correctly?")
                return False
            if learning_type == Learning.ASSUMPTION_WEAKENING:
                self.log(
                    "\nNo assumption weakening produces realizable spec (las file UNSAT)\nMoving to Guarantee Weakening",
                    True)
                self.run_guarantee_weakening(initiate=True)
            else:
                self.log("\nNo guarantee weakening produces realizable spec (las file UNSAT)\nTerminating.", True)
            return

        if FASTLAS:
            hypothesis = re.sub(r"time\(V\d*\)|trace\(V\d*\)", "", hypothesis)
            hypothesis = re.sub(r" ,", "", hypothesis)
            hypothesis = re.sub(r", \.", ".", hypothesis)
            hypothesis = re.sub(r"\), ", "); ", hypothesis)
            hypotheses = [re.sub(r"b'|'", "", hypothesis).split("\n")]
        else:
            hypotheses = [part.split("\n") for part in ''.join(hypothesis).split("%% Solution ")]
        self.most_recent_applied_hypotheses = []

        if len(hypotheses) > 0:
            if FASTLAS:
                nth_hyp = hypotheses[0]
                if self.list_of_hypotheses.find(''.join(nth_hyp)) > 0:
                    print("repeated hypothesis found")
            else:
                # Possible to select one of best at random, but not necessary i think
                all_hyp = hypotheses[1:]
                scores = [int(re.search(r"score (\d*)", x[0]).group(1)) for x in all_hyp if
                          re.search(r"score (\d*)", x[0])]
                top_hyp = [x[1:] for i, x in enumerate(all_hyp) if scores[i] == min(scores)]
                self.min_solutions.append(len(top_hyp))
                if any([self.list_of_hypotheses.find(''.join(x)) > 0 for x in top_hyp]):
                    print("repeated hypothesis found")
                top_hyp = [x for x in top_hyp if self.list_of_hypotheses.find(''.join(x)) < 0]
                if len(top_hyp) == 0:
                    top_hyp = [x for x in all_hyp if self.list_of_hypotheses.find(''.join(x)) < 0]
                if len(top_hyp) == 0:
                    if learning_type == Learning.ASSUMPTION_WEAKENING:
                        self.log("\nMoving to Guarantee Weakening", True)
                        self.run_guarantee_weakening(initiate=True)
                    else:
                        # self.log("Repeated Rule Found:\n\t" + ''.join(nth_hyp), True)
                        self.log("No New Hypotheses Found", True)
                        self.log("\nTerminating.", True)
                        # self.run_guarantee_weakening(initiate=False)
                    return
                nth_hyp = choose_one_with_heuristic(top_hyp, self.heuristic)
            self.list_of_hypotheses += ''.join(nth_hyp)
            self.attempted_hypotheses += 1
        elif learning_type == Learning.ASSUMPTION_WEAKENING:
            print("No hypotheses: reverting to Guarantee Weakening")
            self.run_guarantee_weakening(initiate=True)
            return False
        elif learning_type == Learning.GUARANTEE_WEAKENING:
            print("No hypotheses: ending learning procedure.")
            return False
        # TODO: consider rule without "exception" (i.e. consequent_holds :- root_consequent_holds)
        rules: list[str] = list(filter(re.compile("_exception|root_consequent_").search, nth_hyp))
        if len(rules) == 0:
            print("\nNothing learned")
            self.encode_ILASP(learning_type, for_clingo=True)
            run_clingo(clingo_file=self.lp_file)
            return False
        else:
            self.log("Rule:", print_out=True)
        spec = copy.deepcopy(self.formatted_spec)
        line_list = []
        rule_list = []
        output_list = []
        for rule in rules:
            if EventuallyConsequentRule.pattern.match(rule):
                self.process_new_eventually_exception(learning_type, line_list, output_list, rule, rule_list, spec)
            else:  # either antecedent or consequent exception
                self.process_new_rule_exception(learning_type, line_list, output_list, rule, rule_list, spec)
        self.log_line.append('\\n'.join(line_list))
        self.log_line.append('\\n'.join(rule_list))
        self.log_line.append('\\n'.join(output_list))

        spec = [re.sub(r"\bI\b\s*\(", "(", line) for line in spec]
        spec = re_line_spec(spec)
        self.fixed_spec = spec
        # Added spec to df because las file is now regenerated often: removed this because we should be learning from
        # original file until we move to guarantee weakening. Guarantee weakening does do this on first run.
        # self.spectra_to_DataFrames()
        self.fixed_spec_history.append(spec)
        write_file(self.fixed_spec_file, spec)
        # TODO: never is self.formula_df updated!!!
        return True

    def process_new_rule_exception(self, learning_type, line_list, output_list, rule, rule_list, spec):
        name = FIRST_PRED.search(rule).group(1)
        self.hypothesis_log.append(rule)
        self.most_recent_applied_hypotheses.append(rule)
        rule_split = rule.replace("\n", "").split(":-")
        if learning_type == Learning.ASSUMPTION_WEAKENING:
            body = rule_split[1].split("; ")
        else:
            body = [rule_split[1]]
        # body = rule_split[1].split("; ")
        for i, line in enumerate(spec):
            if re.search(name + r"\b", line):
                j = i + 1
        line = spec[j].strip("\n")
        self.log(line, print_out=True)
        line_list.append(line)
        self.log("Hypothesis:", print_out=True)
        self.log('\t' + rule, print_out=True)
        rule_list.append(rule)
        line = spec[j].split("->")
        if len(line) == 1:
            arrow = ""
            line = re.sub(r"(G|GF)\(\s*", r"\1( -> ", line[0])
            line = line.split("->")
            if len(line) == 1:
                line = re.sub(r"\(", r"( ->", line[0])
                line = line.split("->")
        else:
            arrow = "->"
        for i, conjunct in enumerate(body):
            output = integrate_rule(arrow, conjunct, learning_type, line)
            if i == 0:
                spec[j] = output
                if output == "\n":
                    spec[j - 1] = ""
            else:
                string_out = spec[j - 1].replace(name, name + str(i)) + output
                spec.append(string_out)
            self.log("New Rule:", print_out=True)
            self.log(output.strip("\n"), print_out=True)
            output_list.append(output.strip("\n"))

    def process_new_eventually_exception(self, learning_type, line_list, output_list, rule, rule_list, spec):
        name = ALL_PREDS.search(rule).group(1).split(',')[1].strip()
        self.hypothesis_log.append(rule)
        self.most_recent_applied_hypotheses.append(rule)
        for i, line in enumerate(spec):
            if re.search(name + r"\b", line):
                j = i + 1
        line = spec[j].strip("\n")
        self.log(line, print_out=True)
        line_list.append(line)
        self.log("Hypothesis:", print_out=True)
        self.log('\t' + rule, print_out=True)
        rule_list.append(rule)
        output = eventualise_consequent(line, learning_type)
        spec[j] = output
        self.log("New Rule:", print_out=True)
        self.log(output.strip("\n"), print_out=True)
        output_list.append(output.strip("\n"))

    def extract_unrealizable_cores(self):
        """
        Extracted runnable jar from cores.ExploreCores from
        https://github.com/jringert/spectra-tutorial/blob/main/D2_counter-strategy/src/cores/ExploreCores.java
        \nHad to edit file, so it takes input from args.\n
        :return: True if cores found, False otherwise.
        """
        path_to_jar = f"{PROJECT_PATH}/spectra_unrealizable_cores.jar"
        cmd = ['java', '-jar', path_to_jar, pRespondsToS_substitution(self.fixed_spec_file), '--jtlv']
        output = run_subprocess(cmd)
        core_found = re.compile("at lines <([^>]*)>").search(output)
        names = []
        if core_found:
            line_nums = [x for x in core_found.group(1).split(" ") if x != ""]
        else:
            line_nums = ['']
        if line_nums != ['']:
            print("\nUnrealizable core:")
            for line in line_nums:
                name = extract_string_within(r"--\s*([^:^\s]*)", self.fixed_spec[int(line) - 1])
                print(name)
                print(line + ":" + self.fixed_spec[int(line)])
                names.append(name)
            self.guarantee_violation_list = names
            self.calculate_violated_expressions(exp_type="guarantee")
            return True
        else:
            print("\nNo Unrealizable Core Found.")
            return False

    def check_realizability(self, learning_type, disable_log=False):
        '''
        Checks realizability of Spectra file using Spectra CLI (Command Line Interface).\n
        Download from\nhttps://github.com/SpectraSynthesizer/spectra-cli\n
        Generates a Counter-Strategy in unrealizable.\n
        NB: Old Spectra format must be used. i.e. G rather than alw.\n
        :param fixed_spec: path to fixed spectra file
        '''
        file = pRespondsToS_substitution(self.fixed_spec_file)
        cmd = ['java', '-jar', PATH_TO_CLI, '-i', file, '--counter-strategy', '--jtlv']
        output = run_subprocess(cmd)
        # TODO: check for failure in cmd here! (NEXT & PREV "cannot prime primed variables")
        if learning_type == Learning.ASSUMPTION_WEAKENING:
            self.realizability_checks["assumption"] += 1
        else:
            self.realizability_checks["guarantee"] += 1
        if re.search("Result: Specification is unrealizable", output):
            self.is_realizable = False
            if not disable_log:
                self.log("Unrealizable", True)
                self.log_line.append("unrealizable")
                self.log_line.append(time.time())
                self.save_line_to_log(is_realizable=False)
            output = str(output).split("\n")
            counter_strategy = list(
                filter(re.compile(r"\s*->\s*[^{]*{[^}]*").search, output))  # IR: Spectra Representation
            self.cs_list += [counter_strategy]
            # self.counter_strat_to_partial_interpretation(counter_strategy, learning_type)
            if PRINT_CS:
                print('\n'.join(counter_strategy))
            match learning_type:
                case Learning.GUARANTEE_WEAKENING:
                    self.run_guarantee_weakening()
                case Learning.ASSUMPTION_WEAKENING:
                    self.run_assumption_weakening()
                case _:
                    raise NotImplementedError("No logic for such learning type exists yet!")

        elif re.search("Result: Specification is realizable", output):
            self.is_realizable = True
            if not disable_log:
                self.log("Realizable: success.", True)
                self.log_line.append("realizable")
                self.log_line.append(time.time())
                self.save_line_to_log(is_realizable=True)

                self.log(f"Fixed specification: {self.fixed_spec_file}", True)
            return
        else:
            raise Exception(output)

    def counter_strat_to_trace(
            self,
            lines: Optional[List[str]] = None
    ) -> Dict[str, str]:
        if lines is None:
            lines = read_file_lines(self.counter_strat_file)
        start = "INI"
        output = ""
        trace_name_dict: dict[str, str] = {}
        # TODO: ASK TITUS what is the relationship between low caps "ini" and "ini_S" infinite traces?
        extract_trace(lines, output, start, 0, "ini", trace_name_dict)

        return trace_name_dict

    # TODO: Find way to make output signature customisable (REGEX maybe?)
    def create_mode_bias(self, learning_type, ill_assign):
        head = "antecedent_exception"
        legal_next = "env_atom"
        next_type = ""
        in_bias = ""
        spec = self.fixed_spec

        if learning_type == Learning.GUARANTEE_WEAKENING:
            head = "consequent_exception"
            legal_next = "usable_atom"
            next_type = "_weak"

        output = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n" \
                 "%% Mode Declaration\n" \
                 "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n" \
                 f"#modeh({head}(const(expression_v), var(time), var(trace))).\n"

        # Learning rule for weakening to justice rule
        if config.WEAKENING_TO_JUSTICE:
            output += f"#modeh(consequent_holds(eventually,const(expression_v), var(time), var(trace))).\n"

        restriction = ", (positive)"
        if FASTLAS:
            restriction = ""
            in_bias = "in_"
        if config.WEAKENING_TO_JUSTICE:
            output += f"#modeb(1,root_consequent_holds(eventually, const(expression_v), var(time), var(trace)){restriction}).\n"
        output += f"#modeb(2,holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)){restriction}).\n"
        output += f"#modeb(2,not_holds_at(const(temp_op_v), const(usable_atom), var(time), var(trace)){restriction}).\n"

        # TODO: see how changes affect
        if self.include_next:
            output += f"#modeb(2,holds_at(next, const({legal_next}), var(time), var(trace)){restriction}).\n"
            output += f"#modeb(2,not_holds_at(next, const({legal_next}), var(time), var(trace)){restriction}).\n"
            if learning_type == Learning.ASSUMPTION_WEAKENING:
                for variable in strip_vars(spec, ["env"]):
                    if FASTLAS:
                        output += f"env_atom({variable}).\n"
                    else:
                        output += f"#constant(env_atom,{variable}).\n"

        for variable in strip_vars(spec):
            if FASTLAS:
                output += f"usable_atom({variable}).\n"
            else:
                output += f"#constant(usable_atom,{variable}).\n"

        for temp_op in ["current", "next", "prev", "eventually"]:
            if FASTLAS:
                output += "temp_op_v(" + temp_op + ").\n"
            else:
                output += "#constant(temp_op_v," + temp_op + ").\n"

        # This determines which rules can be weakened.
        if not self.violation_list:
            expression_names = self.formula_df.loc[self.formula_df["type"] == "assumption"]["name"]
        else:
            expression_names = self.violation_list

        if learning_type == Learning.GUARANTEE_WEAKENING:
            expression_names = self.guarantee_violation_list

        for name in expression_names:
            if FASTLAS:
                output += "expression_v(" + name + ").\n"
            else:
                output += "#constant(expression_v, " + name + ").\n"

        output += f"#bias(\"\n"
        output += f":- constraint.\n"
        output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).\n"
        output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(not_holds_at(_,_,V3,V4)), (V3, V4) != (V1, V2).\n"

        # The below would be true when learning a rule like A :- B,C. , but not A :- B;C. Not sure how to
        # distinguish, but the rules we learn seem to be disjunct bodies mostly.
        # Added back in because the ';' actually means and, it turns out
        output += f":- {in_bias}body(holds_at(eventually,_,V1,_)), {in_bias}body(holds_at(eventually,_,V2,_)), V1 != V2.\n"

        if not self.include_next:
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(holds_at(next,_,_,_)).\n"
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(not_holds_at(next,_,_,_)).\n"
        if not self.include_prev:
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(holds_at(prev,_,_,_)).\n"
            output += f":- {in_bias}head({head}(_,V1,V2)), {in_bias}body(not_holds_at(prev,_,_,_)).\n"

        for name in expression_names:
            when = extract_df_content(self.formula_df, name, extract_col="when")
            if name in ill_assign.keys():
                restricted_assignments = ill_assign[name]
                restricted_assignments = [re.sub("_next", next_type + "_next", x) for x in restricted_assignments]
            else:
                restricted_assignments = []

            if when != When.EVENTUALLY:
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(eventually,_,_,_)).\n"
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(eventually,_,_,_)).\n"
                for assignment in restricted_assignments:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body({assignment}).\n"

            if when == When.EVENTUALLY:
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(current,_,_,_)).\n"
                output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(current,_,_,_)).\n"
                restricted_assignments = [re.sub("V1,V2", "_,_,_", x) for x in restricted_assignments]
                for assignment in restricted_assignments:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body({assignment}).\n"
                if self.include_prev:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(prev,_,_,_)).\n"
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(prev,_,_,_)).\n"
                if self.include_next:
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(holds_at(next,_,_,_)).\n"
                    output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body(not_holds_at(next,_,_,_)).\n"

        # This is making sure we don't learn a body that is already in our rule.
        for name in expression_names:
            antecedent_list = extract_df_content(self.formula_df, name, extract_col=re.sub(r"_exception", "", head))
            for antecedents in antecedent_list:
                if antecedents != "":
                    antecedents = antecedents.split(",\n\t")
                    for fact in antecedents:
                        fact = fact.replace("T,S)", "V1,V2)")
                        output += f":- {in_bias}head({head}({name},V1,V2)), {in_bias}body({fact}).\n"

        if config.WEAKENING_TO_JUSTICE:
            output += f":- {in_bias}head({head}(_,_,_)), {in_bias}body(root_consequent_holds(_,_,_,_)).\n"
            output += f":- {in_bias}head(consequent_holds(_,_,_,_)), {in_bias}body(holds_at(_,_,_,_)).\n"
            output += f":- {in_bias}head(consequent_holds(_,_,_,_)), {in_bias}body(not_holds_at(_,_,_,_)).\n"
            output += f":- {in_bias}head(consequent_holds(eventually,E1,V1,V2)), {in_bias}body(root_consequent_holds(eventually,E2,V3,V4)), (E1,V1,V2) != (E2,V3,V4).\n"

        # Prevents repeated hypotheses which is possible (due to prev at time point zero - possibly should be using a weak prev for antecedent...)
        if FASTLAS:
            for old_hyp in [x for x in self.list_of_hypotheses.split(".") if x != ""]:
                reg = re.search("(.*) :- (.*)", old_hyp)
                if not reg:
                    print("huh?")
                h = reg.group(1)
                b = reg.group(2).split(";")
                output += ":- in_head(" + h + "), " + ','.join(
                    ['in_body(' + x + ")" for x in b]) + ", #count{X : in_body(X)} = " + str(len(b)) + ".\n"

        output += "\").\n\n"
        return output

    # def extract_df_content(self, name, extract_col):
    #     try:
    #         idx = self.formula_df.index[self.formula_df["name"] == name].tolist()[0]
    #     except IndexError:
    #         print("Cannot find name:\t'" + name + "'\n\nIn specification expression names:\n")
    #         print(self.formula_df["name"])
    #         exit(1)
    #     extracted_item = self.formula_df[extract_col].iloc[idx]
    #     return extracted_item

    # TODO: refactor logging
    def generate_csv_with_header(self, log_path):
        column_names = ["file", "start_time", "type", "allow_prev", "expressions", "rule", "hypothesis", "new_rule",
                        "outcome", "end_time", "duration_s", "overall_duration_s"]
        if not os.path.exists(log_path):
            with open(log_path, "w") as f:
                f.write(",".join(column_names) + "\n")

    def save_line_to_log(self, is_realizable):
        log_path = f"{PROJECT_PATH}/logs/specification_log_{self.file_suffix}.csv"
        # TODO: refactor logging
        self.generate_csv_with_header(log_path)
        with open(log_path) as log_file:
            first_line = log_file.readline()
        columns = first_line.strip("\n").split(",")
        start_time_col = columns.index("start_time")
        end_time_col = columns.index("end_time")

        start_time = self.log_line[start_time_col]
        end_time = self.log_line[end_time_col]
        if is_realizable:
            overall_duration = end_time - self.absolute_start
        else:
            overall_duration = ""
        duration = end_time - start_time
        self.log_line.append(duration)
        self.log_line.append(overall_duration)

        for i, item in enumerate(self.log_line):
            if i in [start_time_col, end_time_col]:
                item = time.asctime(time.localtime(item))
            item = str(item)
            self.log_line[i] = item

        with open(log_path, 'a', newline="") as log_file:
            log = csv.writer(log_file)
            log.writerow(self.log_line)

    def log_pipeline(self, elapsed):
        output = "Timestamp:\t\t" + time.asctime() + "\n"
        output += ("Original File:\t" + self.spectra_file + "\n")
        output += "PREV bodies:\t"
        output += "included\n" if self.include_prev else "excluded\n"

        # output += "Strengthening:\t"
        # output += "weaken again with counter-strategy\n" if self.strengthen_via_weaken \
        #     else "via antecedent_strengthen\n"

        output += "Assumptions set for weakening:\n"
        for assumption in self.violation_list:
            output += "\t\t\t\t" + assumption + "\n"

        output += "Learned rules:\n"
        for text in self.log_list:
            output += "\t\t\t\t" + text + "\n"

        # for hypothesis in self.hypothesis_log:
        #     output += "\t\t\t\t" + hypothesis + "\n"

        output += ("Elapsed Time:\t" + str(round(elapsed, 2)) + "S\n\n")
        with open(f"{PROJECT_PATH}/logs/specification_log_{self.file_suffix}.txt", 'a') as log:
            log.write(output)

    def restore_first_hypothesis(self):
        if not RESTORE_FIRST_HYPOTHESIS:
            return
        self.log("\nReverting to:", True)
        hypothesis = self.hypothesis_log[len(self.hypothesis_log) - self.attempted_hypotheses]
        self.log('\t' + hypothesis, True)
        # print(self.hypothesis_log[len(self.hypothesis_log) - self.attempted_hypotheses])
        for i in range(self.attempted_hypotheses - 1):
            self.fixed_spec_history.pop()
        spec = self.fixed_spec_history[len(self.fixed_spec_history) - 1]
        self.fixed_spec = spec
        write_file(self.fixed_spec_file, spec)

    def run_guarantee_weakening(self, initiate=False):
        learning_type = Learning.GUARANTEE_WEAKENING
        self.initiate_log_line(learning_type)
        # This is so that the guarantee stage runs including our learned assumptions
        if initiate:
            self.restore_first_hypothesis()
            self.attempted_hypotheses = 0
            counter_strategy = generate_counter_strat(pRespondsToS_substitution(self.fixed_spec_file))
            if not counter_strategy:
                raise Exception(
                    f"Specification at {self.fixed_spec_file} is realisable! No counter-strategy can be found!")
            self.cs_list = [counter_strategy]
        # TODO: figure out necessity of formatted_spec vs fixed_spec only
        self.formatted_spec = copy.deepcopy(self.fixed_spec)
        self.generate_formula_df_from_spectra()
        self.encode_ILASP(learning_type)
        self.log_line.pop()
        self.log_line.append(r",".join(self.guarantee_violation_list))

        # self.add_counter_strats_to_las_file()
        hypothesis = run_ILASP_raw(self.las_file)
        if self.integrate_learned_hypothesis(hypothesis, learning_type):
            self.check_realizability(learning_type)

    def add_guarantee_violation_list(self, guarantee_violation_list):
        self.guarantee_violation_list = guarantee_violation_list

    def get_all_guarantee_names(self):
        return self.formula_df["name"].loc[self.formula_df["type"] == "guarantee"].to_list()

    def log(self, output, print_out):
        if print_out:
            print(output)
        self.log_list.append(output)

    def calculate_violated_expressions(self, exp_type="assumption"):
        # self.format_spectra_file()
        # self.spectra_to_DataFrames()
        # self.encode_ILASP()
        violations = run_clingo(self.lp_file, return_violated_traces=True, exp_type=exp_type)

        v = re.findall(r"violation_holds\(\b([^,^\)]*)", ''.join(violations))
        a = re.findall(exp_type + r"\(\b([^,^\)]*)", ''.join(violations))
        violation_list = list(dict.fromkeys([x for x in v if x in a]))
        if len(violation_list) == 0:
            return False
        # violation_list = [item for sublist in [FIRST_PRED.findall(x) for x in violations] for item in sublist]
        # assumptions = re.findall(r"\bassumption\((.*)\)\b", violations)
        # # violation_list = [FIRST_PRED.search(x).group(1) for x in violations]
        # violation_list = list(dict.fromkeys(violation_list))
        if exp_type == "assumption":
            self.violation_list = violation_list
            self.encode_ILASP()
        else:
            self.guarantee_violation_list += [x for x in violation_list if x not in self.guarantee_violation_list]
        return True


def to_seconds(t):
    return time.mktime(time.strptime(t))


def recursively_search(case_study, folder, exclusions=["genuine"]):
    folders = [os.path.join(folder, x) for x in os.listdir(folder) if x not in exclusions]
    files = [x for x in folders if not os.path.isdir(x)]
    sub_folders = [folder for folder in folders if folder not in files]
    for file in files:
        if file.find(case_study) >= 0:
            return file
    if len(sub_folders) == 0:
        return "file_not_found"
    for sub_folder in sub_folders:
        file_out = recursively_search(case_study, sub_folder)
        if file_out != "file_not_found":
            return file_out


def extract_nth_violation(trace_file, n):
    traces = read_file_lines(trace_file)
    trace = [x for x in traces if re.search("trace_name_" + str(n), x)]
    if len(trace) == 0:
        return ""
    temp_file = re.sub("auto_violation", "auto_violation_temp", trace_file)
    write_file(temp_file, trace)
    return temp_file


def contains_contradictions(start_file, exp_type):
    start_file = re.sub("_patterned\.spectra", ".spectra", start_file)
    start_exp = extract_all_expressions_spot(exp_type, start_file)
    linux_cmd = ["ltlfilt", "-f", f"{start_exp}", "--simplify"]
    output = subprocess.Popen(linux_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    output = output.decode('utf-8')
    reg = re.search(r"(\d)\n", output)
    if not reg:
        return False
    result = reg.group(1)
    return result == "0"


def get_start_files(name):  # , cap):
    output = {}
    for folder in ["temporal"]:
        long_folder = f"{PROJECT_PATH}/input-files/strengthened/" + folder
        files = os.listdir(long_folder)

        rel_files = re.findall(name + r"_dropped\d*\.spectra", '\n'.join(files))
        # if len(rel_files) > cap:
        #     rel_files = rel_files[:cap]
        for file in rel_files:
            output[long_folder + "/" + file] = folder
    return output


def n_trivial_guarantees(file):
    gar = extract_all_expressions_spot("guarantee|gar", file, True)
    count = 0
    for exp in gar:
        linux_cmd = "ltlfilt -f '" + exp + "' --simplify"
        output = \
            subprocess.Popen(["wsl"], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE).communicate(
                input=linux_cmd.encode())[0]
        reg = re.search(r"b'(\d)\\n'", str(output))
        if reg and reg.group(1) == str(1):
            count += 1
    return count


def fix_df():
    df = pd.read_csv("../../output-files/examples/latest_rq_results.csv")
    np.isnan(df["temporals"])
    new_set = [np.isnan(x) for x in df["temporals"]]
    df_upper = df.loc[[not x for x in new_set]]
    df_lower = df.loc[new_set]

    df_lower = df_lower.drop(columns="Unnamed: 0.1")
    col_names = list(df_lower.columns)
    new_cols = col_names[1:] + ["REMOVE"]
    df_lower.columns = new_cols
    df_lower = df_lower.drop(columns="REMOVE")

    df_upper = df_upper.drop(columns=["Unnamed: 0.1", "Unnamed: 0"])

    output = pd.concat([df_lower, df_upper], axis=0)
    output.to_csv("output-files/examples/latest_rq_results.csv")


def reformat_latex_table_rq(perf_string, key="Count"):
    perf_string = re.sub(r"Case-Study[\s&]*\\*\n", "", perf_string)
    perf_string = re.sub(r"\{\}(\s*&\s*" + key + ")", r"Case-Study\1", perf_string)
    # perf_string = re.sub(r"\{\}(\s*&\s*Mean)", r"Case-Study\1", perf_string)
    perf_string = re.sub("REMOVE", " ", perf_string)
    return perf_string


def shrink_latex_table_width(perf_string):
    perf_string = re.sub(r"\n\\begin\{tabular\}", r"\n\\resizebox{\\textwidth}{!}{%\n\\begin{tabular}", perf_string)
    perf_string = re.sub(r"\n\\end\{tabular\}", r"\n\\end{tabular}\n}", perf_string)
    return perf_string


def generate_counter_strat(spec_file) -> Optional[List[str]]:
    cmd = ['java', '-jar', PATH_TO_CLI, '-i', spec_file, '--counter-strategy', '--jtlv']
    output = run_subprocess(cmd)
    if re.search("Result: Specification is unrealizable", output):
        output = str(output).split("\n")
        counter_strategy = list(filter(re.compile(r"\s*->\s*[^{]*{[^}]*").search, output))
        if PRINT_CS:
            print('\n'.join(counter_strategy))
        return counter_strategy
    elif re.search("FileNotFoundException", output):
        raise Exception(f"File {spec_file} doesn't exist!")
    elif re.search("Error:", output):
        raise Exception(output)

    return None
