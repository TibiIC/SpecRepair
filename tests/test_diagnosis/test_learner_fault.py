"""
A learned solution that still violates its own trace must be loud.

The quiet version of this check already existed and was not enough: the search
dropped the candidate and moved on, so a run could produce trace-violating
specifications with nothing in its output saying so. These tests pin the
behaviour that replaced it - an ERROR log, a reproduction bundle on disk, and an
opt-in strict mode that stops the run at the first one.
"""
import json
import os
import tempfile
from unittest import TestCase, mock

from spec_repair.diagnosis.learner_fault import (
    LearnerContractViolation, LearningArtifact, report_learner_fault,
    strict_mode)


class FakeSpec:
    def __init__(self, text):
        self._text = text

    def to_str(self):
        return self._text


class TestReportLearnerFault(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # report_learner_fault writes beside the recorder's folder, i.e. into
        # <parent>/learner_faults, mirroring where final_specs lives.
        self.debug_folder = os.path.join(self.tmp.name, "run", "final_specs")
        os.makedirs(self.debug_folder, exist_ok=True)
        self.artifacts = [
            LearningArtifact(solver="fastlas", task="#pos({entailed(t)},{},{}).",
                             raw_outputs=["antecedent_exception(a3,0,V0,V1) :- x."],
                             learning_type="ASSUMPTION_WEAKENING"),
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def report(self, **overrides):
        kwargs = dict(
            spec_before=FakeSpec("BEFORE"),
            spec_after=FakeSpec("AFTER"),
            adaptations=["antecedent_exception(a3,0,[('current','pump=false')])"],
            violated_assumptions=["assumption3_1"],
            artifacts=self.artifacts,
            trace=["trace_name_1\n", "highwater=true\n"],
            debug_folder=self.debug_folder,
            note="depth=2",
        )
        kwargs.update(overrides)
        return report_learner_fault(**kwargs)

    def test_bundle_lands_beside_the_run_output(self):
        out = self.report()
        self.assertTrue(os.path.isdir(out))
        self.assertEqual(os.path.join(self.tmp.name, "run", "learner_faults"),
                         os.path.dirname(out))

    def test_bundle_contains_everything_needed_to_reproduce(self):
        out = self.report()
        for name in ("summary.json", "spec_before.spectra", "spec_after.spectra",
                     "violation_trace.txt", "adaptations.txt",
                     "task_0.fastlas.las", "task_0_output_0.txt"):
            self.assertTrue(os.path.exists(os.path.join(out, name)), name)

    def test_summary_names_the_violated_assumption(self):
        out = self.report()
        with open(os.path.join(out, "summary.json")) as fh:
            summary = json.load(fh)
        self.assertEqual(["assumption3_1"], summary["violated_assumptions"])
        self.assertEqual(["fastlas"], summary["solvers"])
        self.assertEqual(1, summary["n_adaptations"])

    def test_the_solver_task_and_answer_are_kept_verbatim(self):
        """Without these the fault cannot be re-run offline, which is the point."""
        out = self.report()
        with open(os.path.join(out, "task_0.fastlas.las")) as fh:
            self.assertEqual("#pos({entailed(t)},{},{}).", fh.read())
        with open(os.path.join(out, "task_0_output_0.txt")) as fh:
            self.assertIn("antecedent_exception(a3,0,V0,V1)", fh.read())

    def test_it_logs_at_error(self):
        with self.assertLogs("spec_repair.diagnosis.learner_fault", level="ERROR") as caught:
            self.report()
        joined = "\n".join(caught.output)
        self.assertIn("LEARNER CONTRACT VIOLATED", joined)
        self.assertIn("assumption3_1", joined)

    def test_two_faults_do_not_overwrite_each_other(self):
        first, second = self.report(), self.report()
        self.assertNotEqual(first, second)

    def test_an_unwritable_location_still_logs_rather_than_raising(self):
        """A diagnostic must never be the thing that kills a run."""
        with mock.patch("os.makedirs", side_effect=OSError("read-only")):
            with self.assertLogs("spec_repair.diagnosis.learner_fault",
                                 level="ERROR") as caught:
                out = self.report()
        self.assertEqual("", out)
        self.assertIn("LEARNER CONTRACT VIOLATED", "\n".join(caught.output))


class TestStrictMode(TestCase):
    def test_off_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(strict_mode())

    def test_enabled_by_the_environment_variable(self):
        with mock.patch.dict(os.environ, {"SPEC_REPAIR_STRICT_LEARNER": "1"}):
            self.assertTrue(strict_mode())

    def test_strict_mode_raises_after_writing_the_bundle(self):
        """The bundle is still written - stopping must not cost the evidence."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = os.path.join(tmp, "run", "final_specs")
            os.makedirs(folder)
            with mock.patch.dict(os.environ, {"SPEC_REPAIR_STRICT_LEARNER": "1"}):
                with self.assertRaises(LearnerContractViolation):
                    report_learner_fault(
                        spec_before=FakeSpec("B"), spec_after=FakeSpec("A"),
                        adaptations=[], violated_assumptions=["assumption3_1"],
                        artifacts=[], trace=[], debug_folder=folder)
            bundles = os.listdir(os.path.join(tmp, "run", "learner_faults"))
            self.assertEqual(1, len(bundles))
