from collections import deque
from typing import Deque

from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.heuristic_manager import HeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager


class OrchestrationManager:
    def __init__(self):
        self._stack: Deque[CandidateRepairNode] = deque()
        self._visited_nodes: Recorder[CandidateRepairNode] = Recorder()

    def initialise_learning_tasks(self, spec, trace):
        root_node = CandidateRepairNode(spec, trace, [], Learning.ASSUMPTION_WEAKENING)
        self._visited_nodes.add(root_node)
        self._stack.append(root_node)

    def generate_new_nodes(self, node, new_spec, counter_strategy):
        pass

    def has_next(self):
        pass

    def get_next(self):
        pass


class BFSRepairOrchestrator:
    def __init__(
            self,
            learner: Learner,
            oracle: Oracle,
            orchestration_manager: OrchestrationManager,
            heuristic_manager: HeuristicManager = NoFilterHeuristicManager()
    ):
        self._learner = learner
        self._oracle = oracle
        self._om = orchestration_manager
        self._hm = heuristic_manager
        self._initialise_repair()

    def _initialise_repair(self):
        # Counter for recording counter traces
        self._ct_cnt = 0
        self._hm.reset()

    def repair_bfs(
            self,
            og_spec,
            og_data
    ):
        self._initialise_repair()
        self._om.initialise_learning_tasks(og_spec, og_data)

        while self._om.has_next():
            spec, data = self._om.get_next()
            new_specs = self._learner.learn_new(spec, data)
            for new_spec in new_specs:
                counter_arguments = self._oracle.is_valid_or_counter_arguments(new_spec)
                if not counter_arguments:
                    self._recorder.add(new_spec)
                else:
                    for counter_argument in counter_arguments:
                        self._om.enqueue_new_task(spec, data, new_spec, counter_argument)

        return self._recorder.get_specs()
