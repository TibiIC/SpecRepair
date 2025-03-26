from collections import deque
from typing import Deque, Tuple, Any, Dict

from spec_repair.components.interfaces.idiscriminator import IDiscriminator
from spec_repair.components.interfaces.ilearner import ILearner
from spec_repair.components.interfaces.imittigator import IMittigator
from spec_repair.components.interfaces.ioracle import IOracle
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.enums import Learning
from spec_repair.helpers.heuristic_managers.iheuristic_manager import IHeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.recorders.recorder import Recorder
from spec_repair.helpers.recorders.unique_recorder import UniqueRecorder


class OrchestrationManager:
    def __init__(self):
        self._stack: Deque[Tuple[ISpecification,Any]] = deque()
        self._visited_nodes: Recorder[Tuple[ISpecification,Any]] = Recorder()

    def _reset(self):
        self._stack.clear()
        self._visited_nodes = Recorder()

    def initialise_learning_tasks(self, spec: ISpecification, data: Any):
        self._reset()
        self.enqueue_new_tasks(spec, data)

    def enqueue_new_tasks(self, spec: ISpecification, data: Any):
        node: Tuple[Any, Any] = (spec, data)
        self._stack.append(node)
        self._visited_nodes.add(node)

    def has_next(self) -> bool:
        return bool(self._stack)

    def get_next(self) -> Tuple[ISpecification, Any]:
        return self._stack.popleft()


class BFSRepairOrchestrator:
    def __init__(
            self,
            learners: Dict[str, ILearner],
            oracle: IOracle,
            discriminator: IDiscriminator,
            mittigator: IMittigator,
            orchestration_manager: OrchestrationManager,
            heuristic_manager: IHeuristicManager = NoFilterHeuristicManager(),
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
            og_spec: ISpecification,
            og_data: Any
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
                    counter_examples = self._oracle.is_valid_or_counter_arguments(new_spec)
                    if not counter_examples:
                        self._recorder.add(new_spec)
                    else:
                        for counter_example in counter_examples:
                            new_data = self._mittigator.add_counter_example_to_data(data, counter_example)
                            self._om.enqueue_new_tasks(new_spec, new_data)
