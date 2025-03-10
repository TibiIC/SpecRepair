from collections import deque
from typing import Deque, Tuple, Any, Dict

from spec_repair.components.idiscriminator import IDiscriminator
from spec_repair.components.ilearner import ILearner
from spec_repair.components.imittigator import IMittigator
from spec_repair.components.ioracle import IOracle
from spec_repair.components.ispecification import ISpecification
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.heuristic_manager import HeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.recorders.recorder import Recorder
from spec_repair.helpers.recorders.unique_recorder import UniqueRecorder


class OrchestrationManager:
    def __init__(self):
        self._stack: Deque[CandidateRepairNode] = deque()
        self._visited_nodes: Recorder[CandidateRepairNode] = Recorder()

    def initialise_learning_tasks(self, spec, trace):
        root_node = CandidateRepairNode(spec, trace, [], Learning.ASSUMPTION_WEAKENING)
        self._visited_nodes.add(root_node)
        self._stack.append(root_node)

    def enqueue_new_tasks(self, node, new_spec, counter_strategy):
        pass

    def has_next(self):
        pass

    def get_next(self) -> Tuple[ISpecification, Any]:
        next_node = self._stack.popleft()
        return next_node.spec, next_node.get_data()


class BFSRepairOrchestrator:
    def __init__(
            self,
            learners: Dict[str, ILearner],
            oracle: IOracle,
            discriminator: IDiscriminator,
            mittigator: IMittigator,
            orchestration_manager: OrchestrationManager,
            heuristic_manager: HeuristicManager = NoFilterHeuristicManager(),
            recorder: Recorder[ISpecification] = UniqueRecorder()
    ):
        self._learners = learners
        self._oracle = oracle
        self._discriminator = discriminator
        self._mittigator = mittigator
        self._om = orchestration_manager
        self._hm = heuristic_manager
        self._recorder = recorder
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
            learning_strategy: str = self._discriminator.get_learning_strategy(spec, data)
            learner = self._learners[learning_strategy]
            new_specs = learner.learn_new(spec, data)
            if not new_specs:
                alternate_tasks = self._mittigator.prepare_alternative_learning_tasks(spec, data)
                for alt_spec, alt_data in alternate_tasks:
                    self._om.enqueue_new_tasks(alt_spec, alt_data)
            else:
                for new_spec in new_specs:
                    counter_arguments = self._oracle.is_valid_or_counter_arguments(new_spec)
                    if not counter_arguments:
                        self._recorder.add(new_spec)
                    else:
                        for counter_argument in counter_arguments:
                            self._om.enqueue_new_tasks(new_spec, data, counter_argument)

        return self._recorder.get_specs()
