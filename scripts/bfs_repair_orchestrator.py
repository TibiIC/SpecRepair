from typing import Any, Dict

from spec_repair.components.interfaces.idiscriminator import IDiscriminator
from spec_repair.components.interfaces.ilearner import ILearner
from spec_repair.components.interfaces.imitigator import IMitigator
from spec_repair.components.interfaces.ioracle import IOracle
from spec_repair.components.interfaces.ispecification import ISpecification
from spec_repair.helpers.heuristic_managers.iheuristic_manager import IHeuristicManager
from spec_repair.helpers.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.helpers.orchestration_managers.orchestration_manager import OrchestrationManager
from spec_repair.helpers.recorders.irecorder import IRecorder
from spec_repair.helpers.recorders.unique_recorder import UniqueRecorder


class BFSRepairOrchestrator:
    def __init__(
            self,
            learners: Dict[str, ILearner],
            oracle: IOracle,
            discriminator: IDiscriminator,
            mitigator: IMitigator,
            heuristic_manager: IHeuristicManager = NoFilterHeuristicManager(),
            recorder: IRecorder[ISpecification] = UniqueRecorder()
    ):
        self._learners = learners
        self._oracle = oracle
        self._discriminator = discriminator
        self._mitigator = mitigator
        self._om = OrchestrationManager()
        self._hm = heuristic_manager
        self._recorder = recorder
        self._initialise_repair()

    def _initialise_repair(self):
        # Counter for recording counter-traces
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
            learned_specs = learner.learn_new(spec, data)
            if not learned_specs:
                alternate_tasks = self._mitigator.prepare_alternative_learning_tasks(spec, data)
                for alt_spec, alt_data in alternate_tasks:
                    self._om.enqueue_new_tasks(alt_spec, alt_data)
            else:
                for learned_spec in learned_specs:
                    counter_examples = self._oracle.is_valid_or_counter_arguments(learned_spec)
                    if not counter_examples:
                        self._recorder.add(learned_spec)
                    else:
                        # TODO: find a way to filter the counter examples using the heuristic manager
                        for counter_example in counter_examples:
                            new_spec, new_data = self._mitigator.prepare_learning_task(spec, data, learned_spec,
                                                                                       counter_example)
                            self._om.enqueue_new_tasks(new_spec, new_data)
