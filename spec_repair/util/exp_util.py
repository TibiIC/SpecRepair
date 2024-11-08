import re
from typing import List

from spec_repair.enums import Learning
from spec_repair.helpers.adaptation_learned import AdaptationLearned


def split_expression_to_raw_components(exp: str) -> List[str]:
    exp_components: List[str] = exp.split("->")
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


def eventualise_consequent_assumption(line: List[str]):
    antecedent = line[0]
    consequent = line[1]
    consequent_without_temporal = extract_contents_of_temporal(consequent)
    ev_consequent = re.sub(r'^(.*?)(;)?$', r'F(\1)\2', consequent_without_temporal)
    output = antecedent + "->" + ev_consequent
    return '\t' + output + "\n"


def extract_adaptation_from_rule(rule: str) -> AdaptationLearned:
    # 1. Extract the function name at the beginning ("antecedent_exception")
    function_name = re.search(r'^(\w+)\(', rule)
    function_name = function_name.group(1) if function_name else None

    # 2. Extract the first argument of the function ("assumption2_1")
    first_argument = re.search(r'^\w+\((\w+)', rule)
    first_argument = first_argument.group(1) if first_argument else None

    # 3. Extract the number in the second argument (0 in this case)
    second_argument_number = re.search(r'^\w+\(\w+,\s*(\d+)', rule)
    second_argument_number = int(second_argument_number.group(1)) if second_argument_number else None

    # 4. Extract the first and third arguments of each "timepoint_of_op" function
    timepoint_op_args = re.findall(r'timepoint_of_op\((\w+),[^,]*,(\w+)', rule)
    # Create a dictionary to map each variable to its corresponding operator
    variable_to_operator = {var: op for op, var in timepoint_op_args}

    # Step 5: Extract both "holds_at" and "not_holds_at" calls with first and second arguments
    holds_at_args = re.findall(r'(not_)?holds_at\((\w+),\s*(\w+)', rule)

    # Construct atom string with truth values and replaced variables
    replaced_holds_at_args = [
        (
            variable_to_operator.get(arg2, arg2),
            f"{atom}={'false' if prefix == 'not_' else 'true'}"
        )
        for prefix, atom, arg2 in holds_at_args
    ]

    return AdaptationLearned(
        type=function_name,
        name_expression=first_argument,
        disjunction_index=second_argument_number,
        atom_temporal_operators=replaced_holds_at_args
    )
