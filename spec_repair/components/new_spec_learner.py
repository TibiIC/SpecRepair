import re
from copy import copy, deepcopy
from typing import Set, List, Tuple, Optional

import pandas as pd

from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.counter_trace import CounterTrace, complete_cts_from_ct
from spec_repair.components.spec_encoder import SpecEncoder
from spec_repair.enums import Learning
from spec_repair.exceptions import NoViolationException, NoWeakeningException, DeadlockRequiredException, \
    NoAssumptionWeakeningException
from spec_repair.helpers.ilasp_interpreter import ILASPInterpreter
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.heuristics import choose_one_with_heuristic, HeuristicType

from spec_repair.util.spec_util import spectra_to_df
from spec_repair.components.spec_generator import SpecGenerator
from spec_repair.wrappers.asp_wrappers import get_violations, run_ILASP


class NewSpecLearner:
    def __init__(self):
        self.file_generator = SpecGenerator()
        self.spec_encoder = SpecEncoder(self.file_generator)

    def learn_new(
            self,
            spec: SpectraSpecification,
            data: Tuple[list[str], list[CounterTrace], Learning]
    ):
        trace, cts, learning_type = data
        possible_adaptations: List[List[Adaptation]] = self.find_possible_adaptations(spec, trace, cts, learning_type)
        new_specs = [deepcopy(spec).integrate_multiple(adaptations) for adaptations in possible_adaptations]
        return new_specs

    def find_possible_adaptations(self, spec, trace, cts, learning_type) -> List[List[Adaptation]]:
        spec_df: pd.DataFrame = spectra_to_df(spec)
        violations = self.get_spec_violations(spec_df, trace, cts, learning_type)
        ilasp: str = self.spec_encoder.encode_ILASP(spec_df, trace, cts, violations, learning_type)
        output: str = run_ILASP(ilasp)
        adaptations: Optional[List[Tuple[int, List[Adaptation]]]] = ILASPInterpreter.extract_learned_possible_adaptations(output)
        if not adaptations:
            if learning_type == Learning.ASSUMPTION_WEAKENING:
                raise NoAssumptionWeakeningException(
                    f"No {learning_type.exp_type_str()} weakening produces realizable spec (las file UNSAT)"
                )
            else:
                raise NoWeakeningException(
                    f"No {learning_type.exp_type_str()} weakening produces realizable spec (las file UNSAT)")

        useful_adaptations: List[List[Adaptation]] = filter_useful_adaptations(adaptations)
        return useful_adaptations

    def get_spec_violations(self, spec_df, trace, cts, learning_type) -> List[str]:
        asp: str = self.spec_encoder.encode_ASP(spec_df, trace, cts)
        violations = get_violations(asp, exp_type=learning_type.exp_type())
        if not violations:
            raise NoViolationException("Violation trace is not violating!")
        if learning_type == Learning.GUARANTEE_WEAKENING:
            deadlock_required = re.findall(r"entailed\((counter_strat_\d*_\d*)\)", ''.join(violations))
            violation_ct = re.findall(r"violation_holds\([^,]*,[^,]*,\s*(counter_strat_\d+_\d+)", ''.join(violations))
            if deadlock_required and not violation_ct:
                raise DeadlockRequiredException("Violation trace is not violating! Deadlock completion is required.")
        return violations

    def get_all_complete_counter_trace_lists(self, spec, trace, init_cts, learning_type) -> List[List[CounterTrace]]:
        if learning_type == Learning.GUARANTEE_WEAKENING:
            spec_df: pd.DataFrame = spectra_to_df(spec)
            ctss: Set[Tuple[CounterTrace]] = {tuple(init_cts)}
            unchanged = False
            while not unchanged:
                unchanged = True
                for cts in deepcopy(ctss):
                    asp: str = self.spec_encoder.encode_ASP(spec_df, trace, list(cts))
                    violations = get_violations(asp, exp_type=learning_type.exp_type())
                    if not violations:
                        raise NoViolationException("Violation trace is not violating!")
                    deadlock_required = re.findall(r"entailed\((counter_strat_\d*_\d*)\)", ''.join(violations))
                    if deadlock_required:
                        set_cts = set(cts)
                        for i, ct in enumerate(copy(cts)):
                            if ct.is_deadlock() and ct.get_name() in deadlock_required:
                                new_set_cts = copy(set_cts)
                                new_set_cts.remove(ct)
                                ctss |= set([tuple(new_set_cts | {complete_ct}) for complete_ct in
                                             complete_cts_from_ct(ct, spec, deadlock_required)])
                                unchanged = False
                        if not unchanged:
                            ctss.remove(cts)
            return [list(cts) for cts in ctss]
        return [init_cts]

    def integrate_learning_hypothesis(self, spec, learning_hypothesis, learning_type) -> list[str]:
        return self.spec_encoder.integrate_learned_hypothesis(spec, learning_hypothesis, learning_type)


def select_learning_hypothesis(hypotheses: List[List[str]], heuristic: HeuristicType) -> List[str]:
    # TODO: store amount of top_hyp learned
    # TODO: make sure no repeated hypotheses occur
    learning_hyp = choose_one_with_heuristic(hypotheses, heuristic)
    return learning_hyp


def filter_useful_adaptations(potential_adaptations: List[Tuple[int, List[Adaptation]]]) -> List[List[Adaptation]]:
    ev_adaptations = [(score, adaptations) for score, adaptations in potential_adaptations if "ev_temp_op" in [adaptation.type for adaptation in adaptations] ]
    other_adaptations = [(score, adaptations) for score, adaptations in potential_adaptations if "ev_temp_op" not in [adaptation.type for adaptation in adaptations] ]
    top_adaptations = ([adaptations for score, adaptations in other_adaptations if score == min(other_adaptations, key=lambda x: x[0])] +
                       [adaptations for score, adaptations in ev_adaptations if score == min(other_adaptations, key=lambda x: x[0])])
    return top_adaptations


