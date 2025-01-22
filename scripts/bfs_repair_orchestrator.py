from collections import deque
from typing import Deque

from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.heuristic_manager import HeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager


class BFSRepairOrchestrator:
    def __init__(
            self,
            learner: Learner,
            enactor: Enactor,
            oracle: Oracle,
            heuristic_manager: HeuristicManager = NoFilterHeuristicManager()

    ):
        self._learner = learner
        self._oracle = oracle
        self._hm = heuristic_manager
        self.delegate: Optional[RepairOrchestratorDelegate] = None
        self._initialise_repair_variables()

    def _initialise_repair_variables(self):
        # Counter for recording counter traces
        self._ct_cnt = 0
        self._hm.reset()
        self._stack: Deque[CandidateRepairNode] = deque()
        self._visited_nodes: Recorder[CandidateRepairNode] = Recorder()

    def repair_bfs(
            self,
            spec,
            trace
    ):
        self._initialise_repair_variables()
        root_node = CandidateRepairNode(spec, trace, [], Learning.ASSUMPTION_WEAKENING)
        self._visited_nodes.add(root_node)
        self._stack.append(root_node)

        while self._stack:
            node = self._stack.popleft()
            new_specs = self._learner.learn_new(node.spec, node.trace, node.counter_traces, node.learning_type)
            for new_spec in new_specs:
                if self.oracle.is_valid(new_spec):
                    self.delegate.log(new_spec)
                    self._recorder.add(new_spec)
                else:
                    counter_examples = self.oracle.get_counter_examples(new_spec)
                    for counter_example in counter_examples:
                        new_node = CandidateRepairNode(new_spec, counter_example, [], Learning.ASSUMPTION_WEAKENING)
                        if new_node not in self._visited_nodes:
                            self._visited_nodes.add(new_node)
                            self._stack.append(new_node)

        return self._recorder.get_specs()
