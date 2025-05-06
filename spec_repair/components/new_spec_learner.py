import re
from copy import copy, deepcopy
from typing import Set, List, Tuple, Optional

import pandas as pd

from spec_repair.components.interfaces.ilearner import ILearner
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.helpers.adaptation_learned import Adaptation
from spec_repair.helpers.counter_trace import CounterTrace, complete_cts_from_ct
from spec_repair.enums import Learning
from spec_repair.exceptions import NoViolationException, NoWeakeningException, DeadlockRequiredException, \
    NoAssumptionWeakeningException
from spec_repair.helpers.heuristic_managers.iheuristic_manager import IHeuristicManager
from spec_repair.helpers.ilasp_interpreter import ILASPInterpreter
from spec_repair.helpers.spectra_specification import SpectraSpecification
from spec_repair.heuristics import choose_one_with_heuristic, HeuristicType

from spec_repair.wrappers.asp_wrappers import get_violations, run_ILASP


class NewSpecLearner(ILearner):
    def __init__(self, heuristic_manager: IHeuristicManager):
        self.spec_encoder = NewSpecEncoder(heuristic_manager)

    def learn_new(
            self,
            spec: SpectraSpecification,
            data: Tuple[list[str], list[CounterTrace], Learning, list[SpectraSpecification]]
    ) -> List[SpectraSpecification]:
        trace, cts, learning_type, spec_history = data
        try:
            possible_adaptations: List[List[Adaptation]] = self.find_possible_adaptations(spec, trace, cts, learning_type)
            new_specs = [deepcopy(spec).integrate_multiple(adaptations) for adaptations in possible_adaptations]
            return new_specs
        except NoWeakeningException as e:
            print(f"Weakening failed: {e}")
            return []
        except NoViolationException as e:
            print(f"Weakening failed: {e}")
            return []
        except DeadlockRequiredException as e:
            print(f"Weakening failed: {e}")
            return []

    def find_possible_adaptations(self, spec: SpectraSpecification, trace, cts, learning_type) -> List[List[Adaptation]]:
        violations = self.get_spec_violations(spec, trace, cts, learning_type)
        ilasp: str = self.spec_encoder.encode_ILASP(spec, trace, cts, violations, learning_type)
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

    def get_spec_violations(self, spec: SpectraSpecification, trace, cts, learning_type) -> List[str]:
        asp: str = self.spec_encoder.encode_ASP(spec, trace, cts)
        violations = get_violations(asp, exp_type=learning_type.exp_type())
        if not violations:
            raise NoViolationException("Violation trace is not violating!")
        if learning_type == Learning.GUARANTEE_WEAKENING:
            deadlock_required = re.findall(r"entailed\((counter_strat_\d*_\d*)\)", ''.join(violations))
            violation_ct = re.findall(r"violation_holds\([^,]*,[^,]*,\s*(counter_strat_\d+_\d+)", ''.join(violations))
            if deadlock_required and not violation_ct:
                raise DeadlockRequiredException("Violation trace is not violating! Deadlock completion is required.")
        return violations

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
    top_adaptations = ([adaptations for score, adaptations in other_adaptations if score == min(other_adaptations, key=lambda x: x[0])[0]] +
                       [adaptations for score, adaptations in ev_adaptations if score == min(ev_adaptations, key=lambda x: x[0])[0]])
    return top_adaptations


