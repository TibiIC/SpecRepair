import re
from copy import copy, deepcopy
from typing import Set, Optional, List, Tuple

import pandas as pd

from spec_repair.helpers.counter_trace import CounterTrace, complete_cts_from_ct
from spec_repair.components.spec_encoder import SpecEncoder
from spec_repair.config import FASTLAS
from spec_repair.enums import Learning
from spec_repair.exceptions import NoViolationException, NoWeakeningException, DeadlockRequiredException, \
    NoAssumptionWeakeningException
from spec_repair.helpers.heuristic_managers.iheuristic_manager import IHeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.heuristics import choose_one_with_heuristic, HeuristicType, first_choice

from spec_repair.util.spec_util import spectra_to_df
from spec_repair.wrappers.asp_wrappers import get_violations, run_ILASP


class SpecLearner:
    def __init__(self, heuristic_manager: IHeuristicManager = NoFilterHeuristicManager()):
        self._hm = heuristic_manager
        self.spec_encoder = SpecEncoder(self._hm)

    def set_heuristic_manager(self, heuristic_manager: IHeuristicManager):
        self._hm = heuristic_manager
        self.spec_encoder.set_heuristic_manager(heuristic_manager)

    def learn_weaker_spec(
            self,
            spec: list[str],
            trace: List[str],
            cts: List[CounterTrace],
            learning_type: Learning,
            heuristic: HeuristicType = first_choice
    ) -> Optional[list[str]]:
        ctss: List[List[CounterTrace]] = self.get_all_complete_counter_trace_lists(spec, trace, cts, learning_type)
        # TODO: split the heuristics in a manager class
        complete_cts: List[CounterTrace] = choose_one_with_heuristic(ctss, first_choice)
        hypotheses = self.find_weakening_hypotheses(spec, trace, complete_cts, learning_type)
        learning_hypothesis = select_learning_hypothesis(hypotheses, heuristic)
        return self.integrate_learning_hypothesis(spec, learning_hypothesis, learning_type)

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

    def find_weakening_hypotheses(self, spec, trace, cts, learning_type) -> Optional[List[List[str]]]:
        spec_df: pd.DataFrame = spectra_to_df(spec)
        asp: str = self.spec_encoder.encode_ASP(spec_df, trace, cts)
        violations = get_violations(asp, exp_type=learning_type.exp_type())
        if not violations:
            raise NoViolationException("Violation trace is not violating!")
        if learning_type == Learning.GUARANTEE_WEAKENING:
            deadlock_required = re.findall(r"entailed\((counter_strat_\d*_\d*)\)", ''.join(violations))
            violation_ct = re.findall(r"violation_holds\([^,]*,[^,]*,\s*(counter_strat_\d+_\d+)", ''.join(violations))
            if deadlock_required and not violation_ct:
                raise DeadlockRequiredException("Violation trace is not violating! Deadlock completion is required.")
        ilasp: str = self.spec_encoder.encode_ILASP(spec_df, trace, cts, violations, learning_type)
        output: str = run_ILASP(ilasp)
        hypotheses = get_hypotheses(output)
        if not hypotheses:
            if learning_type == Learning.ASSUMPTION_WEAKENING:
                raise NoAssumptionWeakeningException(
                    f"No {learning_type.exp_type_str()} weakening produces realizable spec (las file UNSAT)"
                )
            else:
                raise NoWeakeningException(
                    f"No {learning_type.exp_type_str()} weakening produces realizable spec (las file UNSAT)")
        return filter_useful_learning_hypotheses(hypotheses)

    def integrate_learning_hypothesis(self, spec, learning_hypothesis, learning_type) -> list[str]:
        return self.spec_encoder.integrate_learned_hypothesis(spec, learning_hypothesis, learning_type)


def select_learning_hypothesis(hypotheses: List[List[str]], heuristic: HeuristicType) -> List[str]:
    # TODO: store amount of top_hyp learned
    # TODO: make sure no repeated hypotheses occur
    learning_hyp = choose_one_with_heuristic(hypotheses, heuristic)
    return learning_hyp


def filter_useful_learning_hypotheses(hypotheses):
    all_hyp = hypotheses[1:]
    ev_hyp = [hyp[1:] for hyp in all_hyp if "ev_temp_op" in hyp[1]]
    all_other_hyp = [hyp for hyp in all_hyp if "ev_temp_op" not in hyp[1]]
    scores = [int(re.search(r"score (\d*)", hyp[0]).group(1)) for hyp in all_other_hyp if
              re.search(r"score (\d*)", hyp[0])]
    top_hyp = [hyp[1:] for i, hyp in enumerate(all_other_hyp) if scores[i] == min(scores)] + ev_hyp
    return top_hyp


def get_hypotheses(output: str) -> Optional[List[List[str]]]:
    if re.search("UNSATISFIABLE", ''.join(output)):
        return None
    if re.search(r"1 \(score 0\)", ''.join(output)):
        raise NoViolationException("Learning problem is trivially solvable. "
                                   "If spec is not realisable, we have a learning error.")

    if FASTLAS:
        output = re.sub(r"time\(V\d*\)|trace\(V\d*\)", "", output)
        output = re.sub(r" ,", "", output)
        output = re.sub(r", \.", ".", output)
        output = re.sub(r"\), ", "); ", output)
        hypotheses = [re.sub(r"b'|'", "", output).split("\n")]
    else:
        hypotheses = [part.split("\n") for part in ''.join(output).split("%% Solution ")]
    return hypotheses
