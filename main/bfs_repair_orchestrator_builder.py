"""
Fluent builder for BFSRepairOrchestrator.

Constructing an orchestrator by hand takes ~13 lines of which almost all are
the same every time: the oracle, the discriminator, one OptimisingSpecLearner
per weakening direction, and a recorder pair. What actually varies between call
sites is a small, discrete set of choices - which weakening directions are
allowed, how the search dedupes specs (semantic vs syntactic), and what happens
when a learner runs out of options. Those three travel together, so they are
exposed as presets rather than as independent knobs.

Everything else is an override on top of a preset:

    repairer = (BFSRepairOrchestratorBuilder.syntactic()
                .enabling("INCLUDE_NEXT", "INCLUDE_PREV")
                .with_debug_dir(out_dir)
                .with_log_file(log_file)
                .with_on_record(lambda r, idx, spec, data: save_graph(r, out_dir))
                .build())

`with_on_record` exists to remove a real wart, not just to save lines: the usual
callback wants to snapshot the orchestrator's search graph, but the orchestrator
takes the logger as a constructor argument, so callers had to construct the
logger with a closure over a mutable `repairer_ref = []` list and append to it
afterwards. The builder owns both objects, so it can wire them together directly
once both exist.
"""
import os
from typing import Callable, Dict, Iterable, Optional

from main.bfs_repair_orchestrator import BFSRepairOrchestrator
from spec_repair.components.discriminators.spectra_discriminator import SpectraDiscriminator
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.components.mitigators.learning_type_spec_mitigator import LearningTypeSpecMitigator
from spec_repair.components.mitigators.mitigation_strategies import complete_counter_traces, \
    finish_here_return_nothing, move_one_to_guarantee_weakening
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.components.orchestration_managers.orchestration_manager_semantic_equivalence import \
    OrchestrationManagerSemanticEquivalence
from spec_repair.components.orchestration_managers.orchestration_manager_semantic_equivalence_aw_merge import \
    OrchestrationManagerSemanticEquivalenceAsmOnly
from spec_repair.components.orchestration_managers.orchestration_manager_syntactic_equivalence import \
    OrchestrationManagerSyntacticEquivalence
from spec_repair.components.recorders.unique_spec_recorder import UniqueSpecRecorder
from spec_repair.enums import Learning
from spec_repair.interfaces.idiscriminator import IDiscriminator
from spec_repair.interfaces.iheuristic_manager import IHeuristicManager
from spec_repair.interfaces.ilearner import ILearner
from spec_repair.interfaces.ioracle import IOracle
from spec_repair.interfaces.iorchestration_manager import IOrchestrationManager
from spec_repair.interfaces.irecorder import IRecorder
from spec_repair.components.learning_config import LearningConfig
from spec_repair.loggers.progress_reporter import ProgressReporter
from spec_repair.loggers.spec_logger import SpecLogger

ASSUMPTION_WEAKENING = "assumption_weakening"
GUARANTEE_WEAKENING = "guarantee_weakening"

# Solver names accepted by `using_learner`, and by the SPEC_REPAIR_LEARNER
# environment variable the experiment runners pass through. ILASP is the default
# because every published result so far used it; FastLAS is opt-in.
ILASP_LEARNER = "ilasp"
FASTLAS_LEARNER = "fastlas"
LEARNER_NAMES = (ILASP_LEARNER, FASTLAS_LEARNER)
DEFAULT_LEARNER = ILASP_LEARNER

# The runners set this to choose a solver without editing any test.
LEARNER_ENV_VAR = "SPEC_REPAIR_LEARNER"

# How many times FastLAS is invoked per learning step. FastLAS returns one
# solution per run and picks non-deterministically among equally-optimal
# candidates, so this is how an experiment samples the ties that ILASP would
# have enumerated. Exposed as an environment variable so a sweep can vary it
# without editing a test.
FASTLAS_RUNS_ENV_VAR = "SPEC_REPAIR_FASTLAS_RUNS"
DEFAULT_FASTLAS_RUNS = 1


def learner_from_env() -> str:
    """
    The solver named by $SPEC_REPAIR_LEARNER, defaulting to ILASP.

    Validated here rather than where it is used, so a typo fails immediately
    with the valid names instead of silently running the default solver and
    producing results labelled as the other one.
    """
    name = os.environ.get(LEARNER_ENV_VAR, "").strip().lower() or DEFAULT_LEARNER
    if name not in LEARNER_NAMES:
        raise ValueError(
            f"{LEARNER_ENV_VAR}='{name}' is not a known learner. "
            f"Use one of: {', '.join(LEARNER_NAMES)}.")
    return name


def fastlas_runs_from_env() -> int:
    """
    `$SPEC_REPAIR_FASTLAS_RUNS`, defaulting to 1.

    Validated here for the same reason as the learner name: a typo should fail
    immediately rather than silently run a 1-sample sweep and produce results
    labelled as an n-sample one.
    """
    raw = os.environ.get(FASTLAS_RUNS_ENV_VAR, "").strip()
    if not raw:
        return DEFAULT_FASTLAS_RUNS
    try:
        runs = int(raw)
    except ValueError:
        raise ValueError(
            f"{FASTLAS_RUNS_ENV_VAR}='{raw}' is not an integer.") from None
    if runs < 1:
        raise ValueError(f"{FASTLAS_RUNS_ENV_VAR}='{raw}' must be at least 1.")
    return runs

# Callback signature: (repairer, idx, spec, data) -> None
OnRecord = Callable[[BFSRepairOrchestrator, int, object, object], None]


class BFSRepairOrchestratorBuilder:
    def __init__(self):
        self._learner_names = (ASSUMPTION_WEAKENING, GUARANTEE_WEAKENING)
        # Which solver backs the learners. Takes the heuristic manager and
        # returns an ILearner, so swapping solver is one override rather than a
        # new preset per (search strategy x solver) combination.
        self._learner_factory: Callable[[IHeuristicManager], ILearner] = \
            lambda hm: OptimisingSpecLearner(heuristic_manager=hm)
        self._om: Optional[IOrchestrationManager] = None
        self._mitigation = {
            Learning.ASSUMPTION_WEAKENING: move_one_to_guarantee_weakening,
            Learning.GUARANTEE_WEAKENING: complete_counter_traces,
        }
        # Semantic dedup is UniqueSpecRecorder's own default; the syntactic
        # preset flips it so the recorder dedupes the same way the search does.
        self._sem_equivalence = True
        self._hm: Optional[IHeuristicManager] = None
        self._enabled: list = []
        self._oracle: Optional[IOracle] = None
        self._discriminator: Optional[IDiscriminator] = None
        self._recorder: Optional[IRecorder] = None
        self._intermediate_recorder: Optional[IRecorder] = None
        self._debug_dir: Optional[str] = None
        self._flat_debug_dir: Optional[str] = None
        self._log_file: Optional[str] = None
        self._run_label: Optional[str] = None
        # Which solver, for the progress status file - _learner_names holds the
        # weakening strategies, which is a different question.
        self._learner_kind: str = ILASP_LEARNER
        # Per-learner policy, keyed by learner name. Absent means "the default
        # built from the shared flags", which is what every caller got before
        # per-learner configuration existed.
        self._learner_configs: Dict[str, LearningConfig] = {}
        self._on_record: Optional[OnRecord] = None

    # ---------------- presets ----------------

    @classmethod
    def semantic(cls) -> "BFSRepairOrchestratorBuilder":
        """Both weakening directions, specs deduped by semantic equivalence."""
        builder = cls()
        builder._om = OrchestrationManagerSemanticEquivalence()
        return builder

    @classmethod
    def syntactic(cls) -> "BFSRepairOrchestratorBuilder":
        """Both weakening directions, specs deduped by syntactic equivalence."""
        builder = cls()
        builder._om = OrchestrationManagerSyntacticEquivalence()
        builder._sem_equivalence = False
        return builder

    @classmethod
    def assumption_only(cls) -> "BFSRepairOrchestratorBuilder":
        """
        Assumption weakening only. Guarantee weakening is not merely unused -
        there is no guarantee learner, so a spec that cannot be repaired by
        weakening assumptions terminates that branch (finish_here_return_nothing)
        instead of being handed over to the guarantee side.
        """
        builder = cls()
        builder._om = OrchestrationManagerSemanticEquivalenceAsmOnly()
        builder._learner_names = (ASSUMPTION_WEAKENING,)
        builder._mitigation = {Learning.ASSUMPTION_WEAKENING: finish_here_return_nothing}
        return builder

    @classmethod
    def guarantee_only(cls) -> "BFSRepairOrchestratorBuilder":
        """Guarantee weakening only - the degradation search."""
        builder = cls()
        builder._om = OrchestrationManagerSemanticEquivalence()
        builder._learner_names = (GUARANTEE_WEAKENING,)
        builder._mitigation = {Learning.GUARANTEE_WEAKENING: complete_counter_traces}
        return builder

    # ---------------- overrides ----------------

    def with_heuristic_manager(self, hm: IHeuristicManager) -> "BFSRepairOrchestratorBuilder":
        self._hm = hm
        return self

    def with_learner_factory(
            self, factory: Callable[[IHeuristicManager], ILearner]
    ) -> "BFSRepairOrchestratorBuilder":
        """Build learners with `factory(heuristic_manager)` instead of the default."""
        self._learner_factory = factory
        return self

    def using_fastlas(self, n_runs: int = 1, **learner_kwargs) -> "BFSRepairOrchestratorBuilder":
        """
        Learn with FastLAS rather than ILASP, keeping the rest of the preset.

        Composes with any preset, e.g.
        `BFSRepairOrchestratorBuilder.syntactic().using_fastlas(n_runs=3)`.
        Imported lazily so that nothing outside this method depends on FastLAS
        being installed.

        `n_runs` caps how many distinct solutions a learning step enumerates.
        FastLAS returns one solution per invocation where ILASP returns all
        optimal ones, so the step runs it repeatedly, forbidding each solution
        found before asking again, and stops as soon as the space is exhausted.
        Raising it trades invocations for search breadth without risking
        duplicate branches.
        """
        from spec_repair.components.learners.fastlas_spec_learner import FastLASSpecLearner
        self._learner_kind = f"{FASTLAS_LEARNER} (n_runs={n_runs})"
        return self.with_learner_factory(
            lambda hm: FastLASSpecLearner(heuristic_manager=hm, n_runs=n_runs, **learner_kwargs))

    def using_learner(self, name: Optional[str], **learner_kwargs) -> "BFSRepairOrchestratorBuilder":
        """
        Select the solver by name: `"ilasp"` (the default) or `"fastlas"`.

        The name-keyed form of `using_fastlas`, so a run can be pointed at a
        solver from a command line or an environment variable without the caller
        having to branch. `None` or an empty string leaves the preset's default
        in place, which is what an unset environment variable should mean.

        For FastLAS, `n_runs` defaults to `$SPEC_REPAIR_FASTLAS_RUNS` so a sweep
        can set the sampling depth from the environment; an explicit keyword
        still wins.
        """
        if not name:
            return self
        key = name.strip().lower()
        if key == ILASP_LEARNER:
            return self
        if key == FASTLAS_LEARNER:
            learner_kwargs.setdefault("n_runs", fastlas_runs_from_env())
            return self.using_fastlas(**learner_kwargs)
        raise ValueError(
            f"Unknown learner '{name}'. Use one of: {', '.join(sorted(LEARNER_NAMES))}.")

    def enabling(self, *flags: str) -> "BFSRepairOrchestratorBuilder":
        """Enable heuristic flags (e.g. "INCLUDE_NEXT", "INCLUDE_PREV")."""
        self._enabled.extend(flags)
        return self

    def with_orchestration_manager(self, om: IOrchestrationManager) -> "BFSRepairOrchestratorBuilder":
        self._om = om
        return self

    def with_mitigation(self, mitigation: Dict) -> "BFSRepairOrchestratorBuilder":
        self._mitigation = mitigation
        return self

    def with_oracle(self, oracle: IOracle) -> "BFSRepairOrchestratorBuilder":
        self._oracle = oracle
        return self

    def with_discriminator(self, discriminator: IDiscriminator) -> "BFSRepairOrchestratorBuilder":
        self._discriminator = discriminator
        return self

    def with_debug_dir(self, out_dir: str) -> "BFSRepairOrchestratorBuilder":
        """
        Record specs to `{out_dir}/intermediate_specs` and `{out_dir}/final_specs`,
        creating both. Use `with_flat_debug_dir` for the older single-folder layout.
        """
        self._debug_dir = out_dir
        return self

    def with_flat_debug_dir(self, out_dir: str) -> "BFSRepairOrchestratorBuilder":
        """Record final specs straight into `out_dir`, with no subfolders."""
        self._flat_debug_dir = out_dir
        return self

    def with_recorder(self, recorder: IRecorder) -> "BFSRepairOrchestratorBuilder":
        self._recorder = recorder
        return self

    def with_intermediate_recorder(self, recorder: IRecorder) -> "BFSRepairOrchestratorBuilder":
        self._intermediate_recorder = recorder
        return self

    def with_log_file(self, log_file: str) -> "BFSRepairOrchestratorBuilder":
        self._log_file = log_file
        return self

    def with_learner_config(self, learner_name: str,
                            config: LearningConfig) -> "BFSRepairOrchestratorBuilder":
        """
        Give one learner its own policy.

        The point of `LearningConfig` being per learner: assumption weakening and
        guarantee weakening are different jobs and need not be allowed the same
        moves, and a third learner can be added with a policy of its own without
        touching either. Learners left unconfigured keep the shared default, so
        setting one does not silently change the others.
        """
        if learner_name not in self._learner_names:
            raise ValueError(
                f"No learner named '{learner_name}' in this preset. "
                f"Known: {', '.join(self._learner_names)}.")
        self._learner_configs[learner_name] = config
        return self

    def with_run_label(self, label: str) -> "BFSRepairOrchestratorBuilder":
        """
        Name this run in its progress output and status file.

        Worth setting on a sweep: the status files of 60 concurrent runs are
        only tellable apart by what is written inside them.
        """
        self._run_label = label
        return self

    def with_on_record(self, on_record: OnRecord) -> "BFSRepairOrchestratorBuilder":
        """
        Called as `on_record(repairer, idx, spec, data)` every time a spec is
        recorded. The built orchestrator is passed in, so callbacks that need to
        inspect the search graph don't have to close over a placeholder.
        """
        self._on_record = on_record
        return self

    # ---------------- build ----------------

    def _build_recorders(self):
        recorder, intermediate = self._recorder, self._intermediate_recorder
        if recorder is None:
            if self._flat_debug_dir:
                os.makedirs(self._flat_debug_dir, exist_ok=True)
                recorder = UniqueSpecRecorder(sem_equivalence=self._sem_equivalence,
                                              debug_folder=self._flat_debug_dir)
            elif self._debug_dir:
                final_dir = f"{self._debug_dir}/final_specs"
                os.makedirs(final_dir, exist_ok=True)
                recorder = UniqueSpecRecorder(sem_equivalence=self._sem_equivalence, debug_folder=final_dir)
            else:
                recorder = UniqueSpecRecorder(sem_equivalence=self._sem_equivalence)
        if intermediate is None:
            if self._debug_dir and not self._flat_debug_dir:
                intermediate_dir = f"{self._debug_dir}/intermediate_specs"
                os.makedirs(intermediate_dir, exist_ok=True)
                intermediate = UniqueSpecRecorder(sem_equivalence=self._sem_equivalence,
                                                  debug_folder=intermediate_dir)
            else:
                intermediate = UniqueSpecRecorder(sem_equivalence=self._sem_equivalence)
        return recorder, intermediate

    def build(self) -> BFSRepairOrchestrator:
        hm = self._hm if self._hm is not None else NoFilterHeuristicManager()
        for flag in self._enabled:
            hm.set_enabled(flag)

        # BFSRepairOrchestrator._initialise_repair reassigns every learner's
        # heuristic manager to its own, so passing `hm` here just keeps the
        # learners consistent before the first repair rather than mattering later.
        learners: Dict[str, ILearner] = {}
        for name in self._learner_names:
            learner = self._learner_factory(hm)
            config = self._learner_configs.get(name)
            if config is not None:
                learner._config = config
            learners[name] = learner
        recorder, intermediate_recorder = self._build_recorders()

        logger_kwargs = {"filename": self._log_file} if self._log_file else {}
        logger = SpecLogger(**logger_kwargs)

        # Progress goes next to the run's own output, so a status file belongs
        # to exactly one run even when 60 share a filesystem.
        progress_dir = self._debug_dir or self._flat_debug_dir
        reporter = ProgressReporter(
            label=self._run_label or (os.path.basename(progress_dir.rstrip("/"))
                                      if progress_dir else "run"),
            out_dir=progress_dir,
            learner=self._learner_kind,
        )

        repairer = BFSRepairOrchestrator(
            learners,
            self._oracle if self._oracle is not None else SpectraGR1Oracle(),
            self._discriminator if self._discriminator is not None else SpectraDiscriminator(),
            LearningTypeSpecMitigator(self._mitigation),
            om=self._om if self._om is not None else OrchestrationManagerSemanticEquivalence(),
            hm=hm,
            recorder=recorder,
            intermediate_recorder=intermediate_recorder,
            logger=logger,
            reporter=reporter,
        )

        if self._on_record is not None:
            on_record = self._on_record
            logger.set_on_record(lambda idx, spec, data: on_record(repairer, idx, spec, data))

        return repairer
