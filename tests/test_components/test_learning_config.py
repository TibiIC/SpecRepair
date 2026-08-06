import unittest

from main.bfs_repair_orchestrator_builder import (
    ASSUMPTION_WEAKENING, GUARANTEE_WEAKENING, BFSRepairOrchestratorBuilder)
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.components.learning_config import (
    ANTECEDENT_WEAKENING, CONSEQUENT_WEAKENING, INCLUDE_NEXT, INCLUDE_PREV,
    INVARIANT_TO_RESPONSE_WEAKENING, LearningConfig)
from spec_repair.ltl_types import GR1TemporalType


class TestLearningConfig(unittest.TestCase):
    def test_narrowing_returns_a_new_config_and_leaves_the_original_alone(self):
        """
        The property the old heuristic manager could not offer. A learning step
        runs one operator at a time; doing that by mutating the learner's own
        settings is what made "what is this learner configured to do" a question
        with a time-dependent answer.
        """
        full = LearningConfig()
        narrowed = full.with_only(ANTECEDENT_WEAKENING)

        self.assertTrue(narrowed.is_enabled(ANTECEDENT_WEAKENING))
        self.assertFalse(narrowed.is_enabled(CONSEQUENT_WEAKENING))
        self.assertTrue(full.is_enabled(CONSEQUENT_WEAKENING), "the original was mutated")
        self.assertIsNot(full, narrowed)

    def test_config_is_frozen(self):
        with self.assertRaises(Exception):
            LearningConfig().operators = frozenset()

    def test_narrowing_cannot_widen(self):
        """`with_only` intersects: a learner cannot gain an operator it was denied."""
        antecedent_only = LearningConfig().with_only(ANTECEDENT_WEAKENING)
        self.assertFalse(
            antecedent_only.with_only(CONSEQUENT_WEAKENING).is_enabled(CONSEQUENT_WEAKENING))

    def test_initial_formulas_are_not_learnable_by_default(self):
        """
        Weakening an initial assumption pulls system variables into it, which
        Spectra rejects outright - and it changes which states the system may
        start in, which is the realisability question rather than an answer.
        """
        config = LearningConfig()
        self.assertFalse(config.may_learn(GR1TemporalType.INITIAL))
        self.assertTrue(config.may_learn(GR1TemporalType.INVARIANT))
        self.assertTrue(config.may_learn(GR1TemporalType.JUSTICE))

    def test_enabling_sorts_flags_onto_the_right_axis(self):
        config = LearningConfig(operators=frozenset(), temporal_atoms=frozenset())
        config = config.enabling(ANTECEDENT_WEAKENING, INCLUDE_NEXT)
        self.assertEqual(frozenset({ANTECEDENT_WEAKENING}), config.operators)
        self.assertEqual(frozenset({INCLUDE_NEXT}), config.temporal_atoms)

    def test_an_unknown_flag_is_rejected(self):
        with self.assertRaises(ValueError):
            LearningConfig().enabling("NOT_A_REAL_FLAG")


class TestPerLearnerConfiguration(unittest.TestCase):
    def test_a_learner_defaults_to_the_flags_it_was_built_with(self):
        """Configuring through the heuristic manager still works, read once."""
        hm = NoFilterHeuristicManager()
        hm.set_enabled(INCLUDE_PREV)
        hm.set_disabled(CONSEQUENT_WEAKENING)
        learner = OptimisingSpecLearner(heuristic_manager=hm)

        self.assertTrue(learner.config.is_enabled(INCLUDE_PREV))
        self.assertFalse(learner.config.is_enabled(CONSEQUENT_WEAKENING))
        self.assertTrue(learner.config.is_enabled(ANTECEDENT_WEAKENING))

    def test_the_config_survives_a_later_change_to_the_shared_manager(self):
        """
        The bug this refactor exists to remove. One manager was shared by every
        learner and reassigned at the start of each run, so no learner could
        hold a policy of its own.
        """
        hm = NoFilterHeuristicManager()
        learner = OptimisingSpecLearner(heuristic_manager=hm)
        hm.set_disabled(ANTECEDENT_WEAKENING)
        self.assertTrue(learner.config.is_enabled(ANTECEDENT_WEAKENING))

    def test_two_learners_can_hold_different_policies(self):
        """
        The capability that did not exist before: assumption weakening and
        guarantee weakening are different jobs, and a third learner can be added
        with a policy of its own.
        """
        repairer = (BFSRepairOrchestratorBuilder.syntactic()
                    .with_learner_config(ASSUMPTION_WEAKENING,
                                         LearningConfig().with_only(ANTECEDENT_WEAKENING))
                    .with_learner_config(GUARANTEE_WEAKENING,
                                         LearningConfig().with_only(INVARIANT_TO_RESPONSE_WEAKENING))
                    .build())
        asm = repairer._learners[ASSUMPTION_WEAKENING].config
        gar = repairer._learners[GUARANTEE_WEAKENING].config

        self.assertTrue(asm.is_enabled(ANTECEDENT_WEAKENING))
        self.assertFalse(asm.is_enabled(INVARIANT_TO_RESPONSE_WEAKENING))
        self.assertTrue(gar.is_enabled(INVARIANT_TO_RESPONSE_WEAKENING))
        self.assertFalse(gar.is_enabled(ANTECEDENT_WEAKENING))

    def test_configuring_one_learner_leaves_the_others_alone(self):
        repairer = (BFSRepairOrchestratorBuilder.syntactic()
                    .enabling(INCLUDE_NEXT)
                    .with_learner_config(ASSUMPTION_WEAKENING,
                                         LearningConfig().with_only(ANTECEDENT_WEAKENING))
                    .build())
        gar = repairer._learners[GUARANTEE_WEAKENING].config
        self.assertTrue(gar.is_enabled(CONSEQUENT_WEAKENING))
        self.assertTrue(gar.is_enabled(INCLUDE_NEXT))

    def test_configuring_an_unknown_learner_fails_loudly(self):
        with self.assertRaises(ValueError):
            (BFSRepairOrchestratorBuilder.syntactic()
             .with_learner_config("no_such_learner", LearningConfig()))

    def test_a_run_does_not_overwrite_learner_configs(self):
        """
        `_initialise_repair` used to assign the orchestrator's own manager to
        every learner at the start of each run, silently discarding per-learner
        settings before the first node was even explored.
        """
        repairer = (BFSRepairOrchestratorBuilder.syntactic()
                    .with_learner_config(ASSUMPTION_WEAKENING,
                                         LearningConfig().with_only(ANTECEDENT_WEAKENING))
                    .build())
        repairer._initialise_repair()
        asm = repairer._learners[ASSUMPTION_WEAKENING].config
        self.assertTrue(asm.is_enabled(ANTECEDENT_WEAKENING))
        self.assertFalse(asm.is_enabled(CONSEQUENT_WEAKENING))


if __name__ == "__main__":
    unittest.main()
