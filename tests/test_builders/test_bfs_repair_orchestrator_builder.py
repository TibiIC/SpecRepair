import os
import shutil
import tempfile
import unittest

from main.bfs_repair_orchestrator_builder import ASSUMPTION_WEAKENING, GUARANTEE_WEAKENING, \
    BFSRepairOrchestratorBuilder
from spec_repair.components.discriminators.spectra_discriminator import SpectraDiscriminator
from spec_repair.components.heuristic_managers.choose_first_heuristic_manager import ChooseFirstHeuristicManager
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.components.mitigators.mitigation_strategies import complete_counter_traces, \
    finish_here_return_nothing, move_one_to_guarantee_weakening
from spec_repair.components.oracles.spectra_gr1_oracle import SpectraGR1Oracle
from spec_repair.components.orchestration_managers.orchestration_manager_semantic_equivalence import \
    OrchestrationManagerSemanticEquivalence
from spec_repair.components.orchestration_managers.orchestration_manager_semantic_equivalence_aw_merge import \
    OrchestrationManagerSemanticEquivalenceAsmOnly
from spec_repair.components.orchestration_managers.orchestration_manager_syntactic_equivalence import \
    OrchestrationManagerSyntacticEquivalence
from spec_repair.enums import Learning


class TestBFSRepairOrchestratorBuilder(unittest.TestCase):
    """
    Pins each preset to the wiring the hand-written call sites used before the
    builder existed, so a preset can't silently drift away from the
    configuration its callers expect.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _log(self):
        return os.path.join(self.tmp, "log.txt")

    # ---------------- presets ----------------

    def test_semantic_preset_wiring(self):
        r = BFSRepairOrchestratorBuilder.semantic().with_log_file(self._log()).build()
        self.assertIsInstance(r._om, OrchestrationManagerSemanticEquivalence)
        self.assertEqual({ASSUMPTION_WEAKENING, GUARANTEE_WEAKENING}, set(r._learners))
        self.assertEqual(move_one_to_guarantee_weakening,
                         r._mitigator._mitigation_strategies[Learning.ASSUMPTION_WEAKENING])
        self.assertEqual(complete_counter_traces,
                         r._mitigator._mitigation_strategies[Learning.GUARANTEE_WEAKENING])
        self.assertTrue(r.recorder._semantic_equivalence)

    def test_syntactic_preset_uses_syntactic_om_and_recorder(self):
        r = BFSRepairOrchestratorBuilder.syntactic().with_log_file(self._log()).build()
        self.assertIsInstance(r._om, OrchestrationManagerSyntacticEquivalence)
        self.assertEqual({ASSUMPTION_WEAKENING, GUARANTEE_WEAKENING}, set(r._learners))
        # The recorder must dedupe the same way the search does.
        self.assertFalse(r.recorder._semantic_equivalence)
        self.assertFalse(r.intermediate_recorder._semantic_equivalence)

    def test_assumption_only_preset_has_no_guarantee_learner(self):
        r = BFSRepairOrchestratorBuilder.assumption_only().with_log_file(self._log()).build()
        self.assertIsInstance(r._om, OrchestrationManagerSemanticEquivalenceAsmOnly)
        self.assertEqual({ASSUMPTION_WEAKENING}, set(r._learners))
        self.assertEqual(finish_here_return_nothing,
                         r._mitigator._mitigation_strategies[Learning.ASSUMPTION_WEAKENING])
        self.assertNotIn(Learning.GUARANTEE_WEAKENING, r._mitigator._mitigation_strategies)

    def test_guarantee_only_preset_has_no_assumption_learner(self):
        r = BFSRepairOrchestratorBuilder.guarantee_only().with_log_file(self._log()).build()
        self.assertEqual({GUARANTEE_WEAKENING}, set(r._learners))
        self.assertEqual(complete_counter_traces,
                         r._mitigator._mitigation_strategies[Learning.GUARANTEE_WEAKENING])
        self.assertNotIn(Learning.ASSUMPTION_WEAKENING, r._mitigator._mitigation_strategies)

    # ---------------- defaults and overrides ----------------

    def test_defaults_are_spectra_oracle_discriminator_and_no_filter_hm(self):
        r = BFSRepairOrchestratorBuilder.semantic().with_log_file(self._log()).build()
        self.assertIsInstance(r._oracle, SpectraGR1Oracle)
        self.assertIsInstance(r._discriminator, SpectraDiscriminator)
        self.assertIsInstance(r._hm, NoFilterHeuristicManager)

    def test_enabling_sets_heuristic_flags(self):
        r = (BFSRepairOrchestratorBuilder.semantic()
             .enabling("INCLUDE_NEXT", "INCLUDE_PREV")
             .with_log_file(self._log()).build())
        self.assertTrue(r._hm.is_enabled("INCLUDE_NEXT"))
        self.assertTrue(r._hm.is_enabled("INCLUDE_PREV"))

    def test_heuristic_manager_override_is_shared_with_learners(self):
        hm = ChooseFirstHeuristicManager()
        r = BFSRepairOrchestratorBuilder.semantic().with_heuristic_manager(hm).with_log_file(self._log()).build()
        self.assertIs(hm, r._hm)
        for learner in r._learners.values():
            self.assertIs(hm, learner._hm)

    def test_with_debug_dir_creates_both_spec_folders(self):
        out = os.path.join(self.tmp, "run")
        r = BFSRepairOrchestratorBuilder.semantic().with_debug_dir(out).with_log_file(self._log()).build()
        self.assertTrue(os.path.isdir(f"{out}/final_specs"))
        self.assertTrue(os.path.isdir(f"{out}/intermediate_specs"))
        self.assertEqual(f"{out}/final_specs", r.recorder.debug_folder)
        self.assertEqual(f"{out}/intermediate_specs", r.intermediate_recorder.debug_folder)

    def test_with_flat_debug_dir_records_into_one_folder(self):
        out = os.path.join(self.tmp, "flat")
        r = BFSRepairOrchestratorBuilder.semantic().with_flat_debug_dir(out).with_log_file(self._log()).build()
        self.assertTrue(os.path.isdir(out))
        self.assertEqual(out, r.recorder.debug_folder)
        self.assertIsNone(r.intermediate_recorder.debug_folder)

    def test_no_debug_dir_means_no_debug_folders(self):
        r = BFSRepairOrchestratorBuilder.semantic().with_log_file(self._log()).build()
        self.assertIsNone(r.recorder.debug_folder)
        self.assertIsNone(r.intermediate_recorder.debug_folder)

    # ---------------- the on_record wiring ----------------

    def test_on_record_receives_the_built_orchestrator(self):
        """
        The whole reason with_on_record exists: callers used to need a mutable
        `repairer_ref = []` closure because the logger is constructed before the
        orchestrator that owns it.
        """
        seen = []
        r = (BFSRepairOrchestratorBuilder.semantic()
             .with_log_file(self._log())
             .with_on_record(lambda repairer, idx, spec, data: seen.append((repairer, idx)))
             .build())
        r._logger.record(7, spec=None, data=_FakeData())
        self.assertEqual(1, len(seen))
        self.assertIs(r, seen[0][0])
        self.assertEqual(7, seen[0][1])

    def test_no_on_record_leaves_logger_callback_unset(self):
        r = BFSRepairOrchestratorBuilder.semantic().with_log_file(self._log()).build()
        self.assertIsNone(r._logger._on_record)
        r._logger.record(1, spec=None, data=_FakeData())  # must not raise


class _FakeData:
    learning_type = Learning.ASSUMPTION_WEAKENING
    learning_steps = 0
    learning_time = 0


if __name__ == "__main__":
    unittest.main()
