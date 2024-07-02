from collections import deque
from copy import copy
from typing import Optional, Deque

from spec_repair.builders.spec_recorder import SpecRecorder
from spec_repair.components.counter_trace import CounterTrace
from spec_repair.components.spec_learner import SpecLearner
from spec_repair.components.spec_oracle import SpecOracle
from spec_repair.enums import Learning
from spec_repair.heuristics import first_choice
from spec_repair.special_types import StopHeuristicType
from spec_repair.wrappers.spec import Spec


class RepairNode:
    def __init__(
            self,
            spec: list[str],
            ct_list: Optional[any],
            learning_choice: str,
            learning_type: Learning
    ):
        self.spec = spec
        self.ct_list = ct_list
        self.learning_hypothesis = learning_choice
        self.learning_type = learning_type


class BacktrackingRepairOrchestrator:
    def __init__(self, learner: SpecLearner, oracle: SpecOracle):
        self._learner = learner
        self._oracle = oracle
        self._ct_cnt = 0

    # Reimplementation of the highest level abstraction code
    def repair_spec_bfs(
            self,
            spec: list[str],
            trace: list[str],
            stop_heuristic: StopHeuristicType = lambda a, g: True
    ) -> SpecRecorder:
        stack: Deque[RepairNode] = deque()
        unique_specs = SpecRecorder()
        hypotheses = self._learner.find_weakening_hypotheses(spec, trace, [], Learning.ASSUMPTION_WEAKENING)
        for hypothesis in hypotheses:
            stack.append(RepairNode(spec, [], hypothesis, Learning.ASSUMPTION_WEAKENING))

        while stack:
            repair_node = stack.pop()
            new_spec = self._learner.integrate_learning_hypothesis(repair_node.spec, repair_node.learning_hypothesis, repair_node.learning_type)
            cs = self._oracle.synthesise_and_check(new_spec)
            if not cs:
                unique_specs.add(Spec(''.join(new_spec)))
            else:
                ct_list = copy(repair_node.ct_list)
                ct_list.append(self.ct_from_cs(cs))
                hypotheses = self._learner.find_weakening_hypotheses(spec, trace, ct_list, repair_node.learning_type)
                for hypothesis in hypotheses:
                    stack.append(RepairNode(spec, ct_list, hypothesis, repair_node.learning_type))

        return unique_specs

    def ct_from_cs(self, cs: list[str]) -> CounterTrace:
        ct_name = f"counter_strat_{self._ct_cnt}"
        self._ct_cnt += 1
        return CounterTrace(cs, heuristic=first_choice, name=ct_name)
