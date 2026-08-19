from typing import Dict, List, Tuple

from spec_repair.enums import Learning
from spec_repair.exceptions import InvalidCaseStudyException, \
    MitigationMadeNoProgressException, SpecificationNotVerifiableException
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
from spec_repair.loggers.progress_reporter import ProgressReporter, Timed
from spec_repair.loggers.spec_logger import SpecLogger
from spec_repair.wrappers.asp_wrappers import get_violations


def _learning_label(learning_type) -> str:
    """ASM/GAR - which side of the specification this node is weakening."""
    if learning_type == Learning.ASSUMPTION_WEAKENING:
        return "ASM"
    if learning_type == Learning.GUARANTEE_WEAKENING:
        return "GAR"
    return "-"


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
            logger: SpecLogger = SpecLogger("./main/spec_repair.log"),
            reporter: ProgressReporter = None
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
        self._reporter = reporter or ProgressReporter(to_stdout=False, heartbeat_seconds=0)
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
        # The mitigator and oracle share the run's heuristic manager: their
        # choices - which counter-traces to keep, which alternative tasks to
        # pursue - are about the search, and are the same question wherever they
        # are asked.
        #
        # Learners no longer have theirs reassigned here. Each carries its own
        # immutable LearningConfig (see spec_repair/components/learning_config),
        # decided when it was built. Overwriting it at the start of every run was
        # what made per-learner configuration impossible: whatever the assumption
        # learner was configured with, the guarantee learner got the same object.
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

    @staticmethod
    def _mitigation_made_no_progress(
            spec: ISpecification,
            data: RepairData,
            alt_tasks: List[Tuple[ISpecification, RepairData]]
    ) -> bool:
        """
        Did the mitigation hand back its own input?

        That is neither progress nor a decision to stop: the orchestration
        manager recognises the task as already visited, returns its id without
        pushing it, and the branch vanishes without reaching a leaf.
        `complete_counter_traces` does exactly this when there are no
        counter-traces to complete.

        A predicate rather than a raise. It used to throw here, which put it
        *before* `_record_if_solution` and so killed the whole run over branches
        that were standing on a perfectly good repair - measured on the
        case_study_3 sweep: gyro traces 0 and 3 and minepump_liveness trace 4,
        all guarantee weakening with no counter-traces. "The mitigator has
        nothing to add" and "this branch is a dead end" are different claims,
        and only the second is a problem.
        """
        return any(alt_spec.to_str() == spec.to_str()
                   and alt_data.learning_type == data.learning_type
                   and alt_data.counter_traces == data.counter_traces
                   for alt_spec, alt_data in alt_tasks)

    def _is_solution(self, spec: ISpecification, data: RepairData) -> bool:
        """
        A solution is realisable, and its assumptions are no longer violated by
        the violation trace.

        The third property - assumptions weaker, guarantees weaker or equivalent
        than the input's - is a side effect of only ever weakening, so it is not
        re-checked here.
        """
        if not data.trace:
            return False
        if not self._oracle.is_realisable(spec):
            return False
        asp: str = NewSpecEncoder.encode_ASP(spec, data.trace, [])
        violations: List[str] = get_violations(
            asp, exp_type=Learning.ASSUMPTION_WEAKENING.exp_type())
        return not get_violated_expression_names_of_type(violations, "assumption")

    def _record_if_solution(self, spec: ISpecification, data: RepairData) -> bool:
        """
        Record a terminating branch as a leaf when it is in fact a solution.

        A branch can run out of moves while standing on a perfectly good repair -
        the learner has nothing left to weaken precisely because there is nothing
        left to fix. Without this, that repair is dropped and the run reports
        fewer solutions than it found, with nothing to indicate the loss.
        """
        if self._is_solution(spec, data):
            learned_id = self._recorder.add(spec)
            self._om.connect_leaf_node(spec, learned_id, prev=None)
            self._logger.record(learned_id, spec, data, "Learned")
            self._reporter.event("SOLVED", f"leaf #{learned_id} (branch exhausted, already a solution)")
            return True
        return False

    def repair_bfs(
            self,
            og_spec: ISpecification,
            og_data: RepairData
    ):
        self._initialise_repair()
        self._reporter.start()
        self._assert_repair_preconditions(og_spec, og_data)
        self._om.initialise_learning_tasks(og_spec, og_data)

        node_no = 0
        self._unresolved: List[str] = []
        while self._om.has_next():
            spec, data = self._om.get_next()
            node_no += 1
            self._reporter.node_started(
                depth=data.learning_steps, node=node_no,
                queue=self._om.pending_count(),
                learning_type=_learning_label(data.learning_type))
            learning_strategy: str = self._discriminator.get_learning_strategy(spec, data)
            learner = self._learners[learning_strategy]
            # The learning step is the expensive one and the one worth timing:
            # it is where ILASP/FastLAS and Spectra actually run, and where a
            # run that appears stuck is nearly always sitting.
            with Timed(self._reporter, "LEARN", f"learning d{data.learning_steps} ({learning_strategy})") as t:
                learned_tasks: List[Tuple[ISpecification, RepairData]] = learner.learn_new(spec, data)
                t.result(f"{len(learned_tasks)} candidate(s)")
            if not learned_tasks:
                alt_tasks: List[Tuple[ISpecification, RepairData]] = self._mitigator.prepare_alternative_learning_tasks(
                    spec,
                    data)
                stalled = self._mitigation_made_no_progress(spec, data, alt_tasks)
                if stalled:
                    # Handing back the input is the mitigator saying it has
                    # nothing, in the one way the search cannot act on.
                    alt_tasks = []
                self._reporter.event("MITIG", f"{len(alt_tasks)} alternative task(s)")
                if not alt_tasks:
                    # The branch ends here. Before letting it, check whether the
                    # specification we are standing on is already a solution -
                    # otherwise a valid repair is thrown away silently.
                    if not self._record_if_solution(spec, data) and stalled:
                        if data.unresolvable_reason:
                            # The branch stopped for a known reason - a learner
                            # out of time, or a repair shape the methodology does
                            # not cover. Both are real limitations, and both are
                            # reported rather than hidden, but neither justifies
                            # discarding what every other branch found.
                            self._unresolved.append(data.unresolvable_reason)
                            self._reporter.event(
                                "LIMIT", f"branch abandoned - {data.unresolvable_reason}")
                            continue
                        # Nowhere to go and nothing worth keeping: a real dead
                        # end, and the invariant that every node reaches a leaf
                        # is broken. Loud, because it means the search lost work.
                        raise MitigationMadeNoProgressException(
                            f"A {data.learning_type} mitigation returned its input "
                            f"unchanged and the specification is not a solution: same "
                            f"specification, same learning type, same "
                            f"{len(data.counter_traces)} counter-trace(s). The branch "
                            f"would be silently dropped as already visited.\n"
                            f"{spec.to_str()}")
                for alt_spec, alt_data in alt_tasks:
                    self._om.enqueue_new_tasks(alt_spec, alt_data, prev=(spec, data))
            else:
                for learned_spec, data in learned_tasks:
                    try:
                        with Timed(self._reporter, "VERIFY",
                                   f"verifying d{data.learning_steps} candidate",
                                   min_seconds=5.0):
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
                        # Say *which* of the two reasons it was. The exception
                        # covers both "Spectra's BDD engine exhausted the heap"
                        # and "the candidate breaks a structural rule", and the
                        # log recorded neither - so colorsort traces 2 and 3
                        # could run to completion abandoning every branch, and
                        # leave nothing behind to say why 0 specifications came
                        # out of 3h17m and 5h48m of search.
                        reason = str(e).split("\n", 1)[0]
                        self._logger.record(-1, learned_spec, data,
                                            f"Unverifiable: {reason}")
                        self._reporter.event("SKIP", f"cannot verify - {reason}")
                        continue
                    if not counter_examples_with_data:
                        learned_id = self._recorder.add(learned_spec)
                        self._om.connect_leaf_node(learned_spec, learned_id, prev=(spec, data))
                        self._logger.record(learned_id, learned_spec, data, "Learned")
                        self._reporter.event("SOLVED", f"leaf #{learned_id}")
                    else:
                        intermediate_id = self._intermediate_recorder.add(learned_spec)
                        self._logger.record(intermediate_id, learned_spec, data, "Intermediate")
                        self._reporter.event(
                            "CEX", f"spec #{intermediate_id} -> "
                                   f"{len(counter_examples_with_data)} counter-example(s)")
                        for counter_example, data in counter_examples_with_data:
                            new_spec, new_data = self._mitigator.prepare_learning_task(spec, data, learned_spec,
                                                                                       counter_example)
                            self._om.enqueue_new_tasks(new_spec, new_data, prev=(spec, data), failed_spec=learned_spec)

        if self._unresolved:
            # Never silent: a branch that ended without a leaf is a gap in the
            # result, whatever the reason for it.
            counts = {r: self._unresolved.count(r) for r in set(self._unresolved)}
            self._reporter.event("LIMIT", "unresolved branches: " + ", ".join(
                f"{n}x {reason}" for reason, n in sorted(counts.items())))
        self._reporter.finish(len(self._recorder.get_specs()),
                              len(self._intermediate_recorder.get_specs()))
