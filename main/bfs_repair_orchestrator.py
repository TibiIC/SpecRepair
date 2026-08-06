from typing import Dict, List, Tuple

from spec_repair.enums import Learning
from spec_repair.exceptions import InvalidCaseStudyException, SpecificationNotVerifiableException
from spec_repair.interfaces.idiscriminator import IDiscriminator
from spec_repair.interfaces.ilearner import ILearner
from spec_repair.interfaces.imitigator import IMitigator
from spec_repair.interfaces.ioracle import IOracle
from spec_repair.interfaces.iorchestration_manager import IOrchestrationManager
from spec_repair.interfaces.ispecification import ISpecification
from spec_repair.components.orchestration_managers.orchestration_manager_semantic_equivalence import \
    OrchestrationManagerSemanticEquivalence
from spec_repair.components.new_spec_encoder import NewSpecEncoder, \
    get_violated_expression_names_of_type
from spec_repair.components.repair_data import RepairData
from spec_repair.ltl_types import GR1TemporalType
from spec_repair.model.counter_trace import CounterTrace
from spec_repair.interfaces.iheuristic_manager import IHeuristicManager
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.interfaces.irecorder import IRecorder
from spec_repair.components.recorders.unique_recorder import UniqueRecorder
from spec_repair.loggers.spec_logger import SpecLogger
from spec_repair.wrappers.asp_wrappers import get_violations


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

    def _assert_repair_preconditions(self, spec: ISpecification, data: RepairData) -> None:
        """
        Refuse to start on a case study that breaks the repair's assumptions.

        A repair run assumes the input specification is realisable, and that the
        violation trace violates at least one **non-initial** assumption. Both
        are properties of the case study, not of the search, so a violation here
        is a malformed input rather than a hard problem.

        Checked up front because the downstream symptom is unrecognisable as its
        cause. A trace that violates no assumption makes assumption weakening
        raise NoViolationException; the mitigator then moves the (already
        realisable) specification to guarantee weakening, where the unrealisable
        core is empty, so no guarantee is marked learnable and the learning task
        is UNSAT - reported as "No guarantee weakening produces realizable
        spec", which reads as though the specification were unrealisable when it
        is the opposite. The branch then dies without reaching a leaf, breaking
        the invariant that every node leads to one.

        Initial assumptions are excluded deliberately. Weakening them changes
        which states the system may start in, which changes the realisability
        question itself rather than answering it, so a trace whose only
        violation is initial does not describe a repairable problem.
        """
        if data.learning_type != Learning.ASSUMPTION_WEAKENING:
            return
        if not self._oracle.is_realisable(spec):
            raise InvalidCaseStudyException(
                "Precondition 1 violated: the input specification is not realisable. "
                "A repair run starts from a realisable specification and weakens it "
                "until the trace is admitted; starting unrealisable is a different "
                f"problem.\n{spec.to_str()}")

        asp: str = NewSpecEncoder.encode_ASP(spec, data.trace, data.counter_traces)
        violations: List[str] = get_violations(
            asp, exp_type=Learning.ASSUMPTION_WEAKENING.exp_type())
        violated: List[str] = get_violated_expression_names_of_type(violations, "assumption")

        initial_names = set(spec.filter(
            lambda x: x["when"] == GR1TemporalType.INITIAL)["name"])
        non_initial_violated = [name for name in violated if name not in initial_names]

        if not non_initial_violated:
            detail = (f"only the initial assumption(s) {sorted(set(violated) & initial_names)}"
                      if violated else "no assumption at all")
            raise InvalidCaseStudyException(
                f"Precondition 2 violated: the violation trace violates {detail}. "
                "A repair run needs a trace that violates at least one non-initial "
                "assumption - there is nothing for it to weaken otherwise, and the "
                "search cannot reach a leaf.\nTrace:\n" + "".join(data.trace))

    def repair_bfs(
            self,
            og_spec: ISpecification,
            og_data: RepairData
    ):
        self._initialise_repair()
        self._assert_repair_preconditions(og_spec, og_data)
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
