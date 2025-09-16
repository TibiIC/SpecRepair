from __future__ import annotations

import random
import re
from collections import defaultdict
from copy import deepcopy
from typing import Optional, List, Set, Tuple

from py_ltl.formula import AtomicProposition

from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.enums import Learning
from spec_repair.helpers.spectra_formula_parser import SpectraFormulaParser
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.heuristics import choose_one_with_heuristic, HeuristicType, random_choice
from spec_repair.ltl_types import CounterStrategy
from spec_repair.special_types import DeadlockAtomSet, DeadlockViolations
from spec_repair.util.ltl_formula_util import satisfies_ltl_formula
from spec_repair.util.spec_util import cs_to_named_cs_traces, trace_replace_name, trace_list_to_asp_form, \
    trace_list_to_ilasp_form, extract_expressions_from_spec, generate_model, run_clingo_raw, run_all_unrealisable_cores
from spec_repair.wrappers.asp_wrappers import run_clingo


class CounterTrace:
    def __init__(self, raw_trace: str, raw_path: str, name: Optional[str] = None):
        self._raw_trace, self._path = raw_trace, raw_path
        self._name = name if name is not None else self._path
        self._is_deadlock = "DEAD" in self._path

    def is_deadlock(self) -> bool:
        return self._is_deadlock

    def get_name(self) -> str:
        return self._name

    def get_raw_trace(self, is_named=True):
        if is_named:
            return trace_replace_name(self._raw_trace, self._path, self._name)
        return self._raw_trace

    def get_asp_form(self, is_named=True):
        raw_asp_form = trace_list_to_asp_form([self.get_raw_trace(is_named=False)])
        if is_named:
            return trace_replace_name(raw_asp_form, self._path, self._name)
        return raw_asp_form

    def get_max_timepoint(self, asp_form: str) -> int:
        timepoints = map(int, re.findall(r"timepoint\((\d+),", asp_form))
        return max(timepoints) if timepoints else 0

    def get_asp_form_awaiting_deadlock(self):
        asp_form = self.get_asp_form()
        max_timepoint = self.get_max_timepoint(asp_form)
        asp_form += f"\n% Extension awaiting deadlock resolution\n"
        asp_form += f"timepoint({max_timepoint + 1},{self._name}).\n"
        asp_form += f"next({max_timepoint + 1},{max_timepoint},{self._name}).\n"
        asp_form += f"\n"
        asp_form += f"1 {{ holds_at(A,{max_timepoint + 1},{self._name}); not_holds_at(A,{max_timepoint + 1},{self._name}) }} 1 :- atom(A).\n\n"
        asp_form += f"atom_set_to(A,true) :- holds_at(A,{max_timepoint + 1},{self._name}), atom(A).\n"
        asp_form += f"atom_set_to(A,false) :- not_holds_at(A,{max_timepoint + 1},{self._name}), atom(A).\n"

        return asp_form

    def get_ilasp_form(self, learning: Learning, is_named=True):
        # TODO: remove "trace_replace_name" as a method for adding the "CS_PATH: self._path" comment to the trace
        return trace_replace_name(trace_list_to_ilasp_form(self.get_asp_form(is_named=is_named), learning), self._path,
                                  self._name)

    def __eq__(self, other: CounterTrace) -> bool:
        return self._raw_trace == other._raw_trace

    def __le__(self, other: CounterTrace) -> bool:
        return self._raw_trace <= other._raw_trace

    def __lt__(self, other: CounterTrace) -> bool:
        return self._raw_trace < other._raw_trace

    def __ge__(self, other: CounterTrace) -> bool:
        return self._raw_trace >= other._raw_trace

    def __gt__(self, other: CounterTrace) -> bool:
        return self._raw_trace > other._raw_trace

    def __hash__(self):
        return hash(self._raw_trace)

    # TODO: Streamline this to be one-two lines maximum
    def __str__(self):
        return f"CounterTrace({self._name}):\nPATH: '{self._path}'\nTrace:\n{self.get_raw_trace()}"

    def print_one_line(self):
        # Dictionary to store states at each time point
        state_dict = defaultdict(dict)

        for s in self.get_raw_trace().split('\n'):
            match = re.search(r'(not_holds_at|holds_at)\((\w+),(\d+),', s)
            if match:
                state, atom, time = match.groups()
                state_dict[time][atom] = '!' if 'not' in state else ''

        # Sort times to maintain order
        sorted_times = sorted(state_dict.keys())

        # Construct the output strings for each time step
        output = []
        for time in sorted_times:
            entities = sorted(state_dict[time].keys())
            time_output = ','.join([f"{state_dict[time][entity]}{entity}" for entity in entities])
            output.append(time_output)

        # Join the time steps with a semicolon
        result = ';'.join(output)
        return f"CT({result})"


def cts_from_cs(cs: CounterStrategy, cs_id: Optional[int] = None) -> list[CounterTrace]:
    trace_name_dict: dict[str, str] = dict(sorted(cs_to_named_cs_traces(cs).items()))

    return [CounterTrace(raw_trace, raw_path, f"counter_strat_{cs_id}_{ct_id}" if cs_id is not None else None)
            for ct_id, (raw_trace, raw_path) in enumerate(trace_name_dict.items())]


def ct_from_cs(cs: CounterStrategy, heuristic: HeuristicType, cs_id: Optional[int] = None) -> CounterTrace:
    return choose_one_with_heuristic(cts_from_cs(cs, cs_id), heuristic)


# CODE BELOW DEALS WITH DEADLOCK COMPLETION
def complete_ct_from_ct(ct: CounterTrace, spec: list[str], entailed_list: list[str],
                        heuristic: HeuristicType = random_choice) -> CounterTrace:
    return choose_one_with_heuristic(complete_cts_from_ct(ct, spec, entailed_list), heuristic)


def complete_cts_from_ct(ct: CounterTrace, spec: ISpecification, entailed_list: list[str]) -> list[CounterTrace]:
    if ct.is_deadlock() and ct.get_name() in entailed_list:
        assignments = find_all_possible_deadlock_completion_assignments(ct, spec)
        complete_cts = [complete_ct_with_deadlock_assignment(ct, assignment) for assignment in assignments]
        unique_complete_cts = list(dict.fromkeys(complete_cts))
        return unique_complete_cts

    return [ct]


# TODO: rework this to not force breakings on guarantees outside of unrealisable cores
def find_all_possible_deadlock_completion_assignments(ct: CounterTrace, spec: SpectraSpecification) -> List[List[AtomicProposition]]:
    asp = NewSpecEncoder.encode_ASP_deadlock_extension(spec, ct)
    out = run_clingo(asp, n_models=0)
    assignments = extract_answers("\n".join(out))
    if not assignments:
        raise ValueError("Not possible to complete the deadlock! There is no valid assignment that may "
                         "continue the trace. Some error must have occurred!")
    unrealisable_cores = get_unrealisable_core_expression_names(spec)
    possible_assignments = [(atom_assignments, violated_expressions) for atom_assignments, violated_expressions in assignments if violated_expressions.issubset(unrealisable_cores)]
    sorted_possible_assignments = sorted(possible_assignments, key=lambda x: len(x[0]))
    # TODO: introduce heuristic to enforce specific violation
    return [atom_assignments for atom_assignments, _ in sorted_possible_assignments]



def get_unrealisable_core_expression_names(spec: SpectraSpecification) -> Set[str]:
    unrealisable_cores = run_all_unrealisable_cores(spec.to_str(is_to_compile=True))
    return set().union(*unrealisable_cores)


def extract_answers(clingo_output: str) -> List[Tuple[List[AtomicProposition], Set[str]]]:
    answers = {}
    current_answer = None

    for line in clingo_output.splitlines():
        # Detect start of an Answer block
        match = re.match(r"Answer:\s+(\d+)", line)
        if match:
            current_answer = int(match.group(1))
            answers[current_answer] = (list(), set())
            continue

        # Collect atoms for current answer
        if current_answer is not None:
            line = line.strip()
            if line and not line.startswith(("SATISFIABLE", "Models", "Calls", "Time", "CPU Time")):
                atom_set_to = DeadlockAtomSet.pattern.match(line)
                if atom_set_to:
                    atom_name = atom_set_to.group(DeadlockAtomSet.ATOM_NAME)
                    atom_value = atom_set_to.group(DeadlockAtomSet.ATOM_VALUE).lower() == "true"
                    answers[current_answer][0].append(AtomicProposition(name=atom_name, value=atom_value))
                else:
                    violation_holds = DeadlockViolations.pattern.match(line)
                    if violation_holds:
                        violated_exp_name = violation_holds.group(DeadlockViolations.VIOLATED_EXP_NAME)
                        answers[current_answer][1].add(violated_exp_name)

    return list(answers.values())


# TODO: test prev_pump setting
def last_state(trace, prevs, offset=0):
    prevs = ["prev_" + x if not re.search("prev_", x) else x for x in prevs]
    last_timepoint: int = max(map(int, re.findall(r",(\d*),", trace)))
    if last_timepoint == 0 and offset != 0:
        return ()
    last_timepoint: int = last_timepoint - offset
    absent = re.findall(rf"not_holds_at\((.*),{last_timepoint}", trace)
    atoms = re.findall(rf"holds_at\((.*),{last_timepoint}", trace)
    assignments = [f"!{x}" if x in absent else x for x in atoms]
    if last_timepoint == 0:
        prev_assign = [f"!{x}" for x in prevs]
    else:
        prev_timepoint: int = last_timepoint - 1
        absent = re.findall(rf"not_holds_at\((.*),{prev_timepoint}", trace)
        prev_absent = [f"prev_{x}" for x in absent]
        prev_assign = [f"!{x}" if x in prev_absent else x for x in prevs]
    assignments += prev_assign
    variables = [re.sub(r"!", "", x) for x in assignments]
    assignments = [i for _, i in sorted(zip(variables, assignments))]
    return tuple(assignments)


def complete_ct_with_deadlock_assignment(ct: CounterTrace, assignment: list[AtomicProposition]):
    ct = deepcopy(ct)
    last_timepoint = max(re.findall(r",(\d*),", ct._raw_trace))
    timepoint = str(int(last_timepoint) + 1)
    asp = [f"{'' if atom_value.value else 'not_'}holds_at({atom_value.name},{timepoint},{ct._path})." for atom_value in assignment]
    ct._raw_trace = ct._raw_trace + '\n'.join(asp)
    ct._is_deadlock = False
    return ct


def next_possible_assignments(new_state, primed_expressions_cleaned, primed_expressions_cleaned_s, unprimed_expressions,
                              unprimed_expressions_s, variables):
    unsat_next_exp = unsat_nexts(new_state, primed_expressions_cleaned)

    unsat_next_exp_s = unsat_nexts(new_state, primed_expressions_cleaned_s)

    if unsat_next_exp + unsat_next_exp_s + unprimed_expressions + unprimed_expressions_s == []:
        # Pick random assignment
        vars = [var for var in variables if not re.search("prev_", var)]
        i = random.choice(range(2 ** len(vars)))
        # TODO: check possible differences between i random and i deterministic
        i = 0
        n = "{0:b}".format(i)
        assignments = '0' * (len(vars) - len(n)) + n
        assignments = [int(x) for x in assignments]
        state = ["!" + var if assignments[i] else var for i, var in enumerate(vars)]
        return [state], False
    return generate_model(unsat_next_exp + unprimed_expressions, unsat_next_exp_s + unprimed_expressions_s, variables,
                          force=True)


def unsat_nexts(new_state, primed_expressions_cleaned):
    if new_state == []:
        return []
    unsat_primed_exp = [expression for expression in primed_expressions_cleaned if not satisfies(expression, new_state)]
    output = [next_only(x, new_state) for x in unsat_primed_exp]
    output = [x for x in output if x != ""]
    return output


def next_only(x, new_state):
    disjuncts = x.split("|")
    disjuncts = [sub_next_only(dis) for dis in disjuncts if not no_next(dis)]
    return '|'.join(disjuncts)


def sub_next_only(dis):
    conjuncts = dis.split("&")
    output = '&'.join([re.sub(r"next\(([^\)]*)\)", r"\1", x) for x in conjuncts if re.search("next", x)])
    return re.sub(r"\(|\)", "", output)


def no_next(dis):
    conjuncts = dis.split("&")
    for conjunct in conjuncts:
        if re.search("next", conjunct):
            return False
    return True


def satisfies(expression, state):
    parser = SpectraFormulaParser()
    expression = parser.parse(expression)
    state = [set([atom for atom in state if "!" not in atom])]
    is_sat = satisfies_ltl_formula(expression, state)
    return is_sat
