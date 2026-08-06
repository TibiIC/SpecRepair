from typing import Dict, List, Tuple

from spec_repair.exceptions import SpecificationNotVerifiableException
from spec_repair.interfaces.idiscriminator import IDiscriminator
from spec_repair.interfaces.ilearner import ILearner
from spec_repair.interfaces.imitigator import IMitigator
from spec_repair.interfaces.ioracle import IOracle
from spec_repair.interfaces.iorchestration_manager import IOrchestrationManager
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.orchestration_managers.orchestration_manager_semantic_equivalence import \
    OrchestrationManagerSemanticEquivalence
from spec_repair.components.repair_data import RepairData
from spec_repair.model.counter_trace import CounterTrace
from spec_repair.interfaces.iheuristic_manager import IHeuristicManager
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.interfaces.irecorder import IRecorder
from spec_repair.components.recorders.unique_recorder import UniqueRecorder
from spec_repair.loggers.spec_logger import SpecLogger


class BFSRepairOrchestrator:
    def __init__(
            self,
            learners: Dict[str, ILearner],
            oracle: IOracle,
            discriminator: IDiscriminator,
            mitigator: IMitigator,
            om: IOrchestrationManager = OrchestrationManagerSemanticEquivalence(),
            hm: IHeuristicManager = NoFilterHeuristicManager(),
            recorder: IRecorder[ISpecification] = UniqueRecorder(),
            intermediate_recorder: IRecorder[ISpecification] = UniqueRecorder(),
            logger: SpecLogger = SpecLogger("./main/spec_repair.log")
    ):
        self._learners = learners
        self._oracle = oracle
        self._discriminator = discriminator
        self._mitigator = mitigator
        self._om = om
        self._hm = hm
        self._recorder = recorder
        self._intermediate_recorder = intermediate_recorder
        self._logger = logger
        self._initialise_repair()

    @property
    def recorder(self) -> IRecorder[ISpecification]:
        """The recorder holding the final (fully repaired) specs."""
        return self._recorder

    @property
    def intermediate_recorder(self) -> IRecorder[ISpecification]:
        """The recorder holding specs seen part-way through the search."""
        return self._intermediate_recorder

    def _initialise_repair(self):
        # Counter for recording counter-traces
        self._ct_cnt = 0
        self._hm.reset()
        for learner in self._learners.values():
            learner._hm = self._hm
        self._mitigator._hm = self._hm
        self._oracle._hm = self._hm

    def repair_bfs(
            self,
            og_spec: ISpecification,
            og_data: RepairData
    ):
        self._initialise_repair()
        self._om.initialise_learning_tasks(og_spec, og_data)

        while self._om.has_next():
            spec, data = self._om.get_next()
            learning_strategy: str = self._discriminator.get_learning_strategy(spec, data)
            learner = self._learners[learning_strategy]
            learned_tasks: List[Tuple[ISpecification, RepairData]] = learner.learn_new(spec, data)
            if not learned_tasks:
                alt_tasks: List[Tuple[ISpecification, RepairData]] = self._mitigator.prepare_alternative_learning_tasks(
                    spec,
                    data)
                for alt_spec, alt_data in alt_tasks:
                    self._om.enqueue_new_tasks(alt_spec, alt_data, prev=(spec, data))
            else:
                for learned_spec, data in learned_tasks:
                    try:
                        counter_examples_with_data: List[Tuple[CounterTrace, RepairData]] = self._oracle.is_valid_or_counter_arguments(
                            learned_spec, data)
                    except SpecificationNotVerifiableException as e:
                        # Spectra cannot check this candidate at all - it breaks
                        # a structural rule of the CLI (see the exception). It is
                        # malformed rather than merely wrong, so the branch ends
                        # here: recording it would put a specification Spectra
                        # never verified into the results. Other branches are
                        # unaffected, which is the point - one bad candidate used
                        # to end the whole run with a TypeError.
                        self._logger.record(-1, learned_spec, data, "Unverifiable")
                        print(f"Skipping unverifiable candidate specification: {e}")
                        continue
                    if not counter_examples_with_data:
                        learned_id = self._recorder.add(learned_spec)
                        self._om.connect_leaf_node(learned_spec, learned_id, prev=(spec, data))
                        self._logger.record(learned_id, learned_spec, data, "Learned")
                    else:
                        intermediate_id = self._intermediate_recorder.add(learned_spec)
                        self._logger.record(intermediate_id, learned_spec, data, "Intermediate")
                        for counter_example, data in counter_examples_with_data:
                            new_spec, new_data = self._mitigator.prepare_learning_task(spec, data, learned_spec,
                                                                                       counter_example)
                            self._om.enqueue_new_tasks(new_spec, new_data, prev=(spec, data), failed_spec=learned_spec)
