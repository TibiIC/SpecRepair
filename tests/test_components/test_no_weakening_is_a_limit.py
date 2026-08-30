"""
An empty hypothesis space ends a branch; it does not end the run.

`learn_new` has three ways to come back with nothing that are all the same kind
of event - a real limitation of the methodology, not a broken invariant:

  * the learning task is UNSAT      (NoWeakeningException)
  * deadlock completion is required (DeadlockRequiredException)
  * the solver ran out of time      (subprocess.TimeoutExpired)

Two of them set `unresolvable_reason` and the orchestrator reports the branch as
a LIMIT and carries on. The first did not, so the orchestrator read it as
"nowhere to go and nothing worth keeping", raised
MitigationMadeNoProgressException, and killed the run - discarding every other
branch's work. minepump_liveness trace 2 died that way at 8 minutes in both the
2026-08-13 and 2026-08-29 sweeps, with 163 solutions already recorded.
"""
import subprocess
from unittest import TestCase, mock

from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.components.repair_data import RepairData
from spec_repair.enums import Learning
from spec_repair.exceptions import (
    DeadlockRequiredException, NoAssumptionWeakeningException,
    NoWeakeningException)


class TestEmptyHypothesisSpaceIsALimit(TestCase):
    def setUp(self):
        self.learner = OptimisingSpecLearner()
        self.spec = mock.Mock()

    def learn_raising(self, exc, learning_type=Learning.GUARANTEE_WEAKENING):
        data = RepairData(trace=["t"], counter_traces=[mock.Mock()],
                          learning_type=learning_type)
        with mock.patch.object(self.learner, "find_possible_adaptations",
                               side_effect=exc):
            tasks = self.learner.learn_new(self.spec, data)
        return tasks, data

    def test_no_weakening_ends_the_branch_with_a_reason(self):
        tasks, data = self.learn_raising(NoWeakeningException("las file UNSAT"))
        self.assertEqual([], tasks)
        self.assertIsNotNone(
            data.unresolvable_reason,
            "without a reason the orchestrator treats this as a broken "
            "invariant and aborts the whole run")
        self.assertIn("guarantee", data.unresolvable_reason)
        self.assertIn("weakening", data.unresolvable_reason)

    def test_the_reason_names_the_side_that_could_not_be_weakened(self):
        _, gar = self.learn_raising(NoWeakeningException("x"),
                                    Learning.GUARANTEE_WEAKENING)
        _, asm = self.learn_raising(NoWeakeningException("x"),
                                    Learning.ASSUMPTION_WEAKENING)
        self.assertIn("guarantee", gar.unresolvable_reason)
        self.assertIn("assumption", asm.unresolvable_reason)

    def test_the_assumption_subclass_is_handled_too(self):
        """NoAssumptionWeakeningException extends NoWeakeningException."""
        tasks, data = self.learn_raising(
            NoAssumptionWeakeningException("las file UNSAT"),
            Learning.ASSUMPTION_WEAKENING)
        self.assertEqual([], tasks)
        self.assertIsNotNone(data.unresolvable_reason)

    def test_it_matches_how_the_sibling_outcomes_are_reported(self):
        """
        All three empty-handed outcomes must look the same to the orchestrator,
        which is the property that was broken.
        """
        outcomes = [
            NoWeakeningException("las file UNSAT"),
            DeadlockRequiredException("deadlock completion required"),
            subprocess.TimeoutExpired(cmd="FastLAS", timeout=600),
        ]
        for exc in outcomes:
            tasks, data = self.learn_raising(exc)
            self.assertEqual([], tasks, type(exc).__name__)
            self.assertIsNotNone(data.unresolvable_reason, type(exc).__name__)
