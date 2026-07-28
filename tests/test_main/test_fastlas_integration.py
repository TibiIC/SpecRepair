"""
Integration tests that actually invoke the FastLAS binary.

Kept apart from tests/test_components/test_fastlas_spec_learner.py, which mocks
the binary out: these need FastLAS installed and are skipped when it is not, so
the suite still runs on a machine without it.

Two things are being checked. That a real ILASP task, once translated, is
accepted by FastLAS and yields parseable adaptations - the translation is
guesswork until a real solver agrees with it. And that the orchestrator built
with `using_fastlas()` is wired to the FastLAS learner, since the point of the
component is that nothing else in the search changes.
"""
import os
import shutil
import unittest

from main.bfs_repair_orchestrator_builder import BFSRepairOrchestratorBuilder
from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.components.learners.fastlas_spec_learner import (
    FastLASSpecLearner,
    FastLASTaskError,
    run_fastlas,
    translate_ilasp_task_to_fastlas,
)
from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.config import SETUP_DICT
from spec_repair.enums import Learning
from spec_repair.helpers.parsers.fastlas_interpreter import FastLASInterpreter
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from spec_repair.wrappers.asp_wrappers import get_violations
from tests.base_test_case import BaseTestCase

CASE_STUDIES = '../input-files/case-studies/spectra/strengthened'
FASTLAS_AVAILABLE = shutil.which(SETUP_DICT.get('FastLAS', 'FastLAS')) is not None \
                    or os.path.isfile(SETUP_DICT.get('FastLAS', ''))


def build_learning_task(case_study: str) -> str:
    """The ILASP task the encoder would hand to a learner for this case study."""
    directory = f'{CASE_STUDIES}/{case_study}'
    spec = SpectraSpecification.from_file(f'{directory}/strong.spectra')
    trace = read_file_lines(f'{directory}/violation_trace.txt')
    hm = NoFilterHeuristicManager()
    hm.set_enabled("INCLUDE_NEXT")
    hm.set_enabled("INCLUDE_PREV")
    encoder = NewSpecEncoder(hm)
    encoder.set_heuristic_manager(hm)
    violations = get_violations(NewSpecEncoder.encode_ASP(spec, trace, []),
                                exp_type=Learning.ASSUMPTION_WEAKENING.exp_type())
    return encoder.encode_ILASP(spec, trace, [], violations, Learning.ASSUMPTION_WEAKENING)


@unittest.skipUnless(FASTLAS_AVAILABLE, "FastLAS is not installed")
class TestFastLASOnRealTasks(BaseTestCase):
    def test_untranslated_ilasp_task_is_rejected_loudly(self):
        """
        Pins why the translation exists, and that a rejected task raises rather
        than looking like "no adaptations found". FastLAS reports the syntax
        error on stderr and writes nothing to stdout.
        """
        with self.assertRaises(FastLASTaskError) as ctx:
            run_fastlas(build_learning_task('minepump'))
        self.assertIn("syntax error", str(ctx.exception).lower())

    def test_translated_task_is_accepted_and_yields_adaptations(self):
        for case_study in ('minepump', 'traffic_single', 'lift'):
            with self.subTest(case_study=case_study):
                task = translate_ilasp_task_to_fastlas(build_learning_task(case_study))
                output = run_fastlas(task)
                self.assertNotIn("syntax error", output.lower())
                self.assertNotIn("Unknown token", output)
                adaptations = FastLASInterpreter.extract_learned_possible_adaptations(output)
                self.assertIsNotNone(adaptations, f"FastLAS found nothing for {case_study}")
                self.assertEqual(1, len(adaptations), "FastLAS returns one solution per run")
                self.assertGreater(len(adaptations[0][1]), 0)

    def test_fastlas_is_deterministic_across_runs(self):
        """
        Documents the measured behaviour that shapes the n_runs design: FastLAS
        2.1.0 returns the same solution every time, so extra runs cost
        invocations without finding extra solutions. If this ever starts
        failing, FastLAS has gained randomisation and n_runs > 1 becomes
        genuinely useful - which is a good reason to keep the test.
        """
        task = translate_ilasp_task_to_fastlas(build_learning_task('traffic_single'))
        outputs = {run_fastlas(task).strip() for _ in range(3)}
        self.assertEqual(1, len(outputs))

    def test_learner_deduplicates_the_repeated_solutions(self):
        """n_runs > 1 against a deterministic FastLAS yields one branch, not n."""
        learner = FastLASSpecLearner(n_runs=3)
        directory = f'{CASE_STUDIES}/traffic_single'
        spec = SpectraSpecification.from_file(f'{directory}/strong.spectra')
        trace = read_file_lines(f'{directory}/violation_trace.txt')
        hm = NoFilterHeuristicManager()
        hm.set_enabled("INCLUDE_NEXT")
        hm.set_enabled("INCLUDE_PREV")
        violations = get_violations(NewSpecEncoder.encode_ASP(spec, trace, []),
                                    exp_type=Learning.ASSUMPTION_WEAKENING.exp_type())
        adaptations = learner.find_adaptations_with_heuristic(
            spec, trace, [], Learning.ASSUMPTION_WEAKENING, violations, hm)
        self.assertEqual(1, len(adaptations))


class TestFastLASBuilderConfiguration(unittest.TestCase):
    """Wiring only - no FastLAS invocation, so these run everywhere."""

    def test_using_fastlas_swaps_every_learner(self):
        repairer = (BFSRepairOrchestratorBuilder.syntactic()
                    .using_fastlas(n_runs=2).with_log_file(os.devnull).build())
        self.assertTrue(repairer._learners)
        for learner in repairer._learners.values():
            self.assertIsInstance(learner, FastLASSpecLearner)
            self.assertEqual(2, learner.n_runs)

    def test_using_fastlas_composes_with_any_preset(self):
        for preset in (BFSRepairOrchestratorBuilder.semantic,
                       BFSRepairOrchestratorBuilder.syntactic,
                       BFSRepairOrchestratorBuilder.assumption_only,
                       BFSRepairOrchestratorBuilder.guarantee_only):
            with self.subTest(preset=preset.__name__):
                repairer = preset().using_fastlas().with_log_file(os.devnull).build()
                for learner in repairer._learners.values():
                    self.assertIsInstance(learner, FastLASSpecLearner)

    def test_preset_keeps_its_own_learner_names_and_mitigation(self):
        """Swapping solver must not change which weakening directions exist."""
        default = BFSRepairOrchestratorBuilder.assumption_only().with_log_file(os.devnull).build()
        fastlas = (BFSRepairOrchestratorBuilder.assumption_only()
                   .using_fastlas().with_log_file(os.devnull).build())
        self.assertEqual(set(default._learners), set(fastlas._learners))
        self.assertEqual(default._mitigator._mitigation_strategies.keys(),
                         fastlas._mitigator._mitigation_strategies.keys())

    def test_default_builder_still_uses_ilasp_learner(self):
        from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
        repairer = BFSRepairOrchestratorBuilder.semantic().with_log_file(os.devnull).build()
        for learner in repairer._learners.values():
            self.assertIsInstance(learner, OptimisingSpecLearner)
            self.assertNotIsInstance(learner, FastLASSpecLearner)


if __name__ == "__main__":
    unittest.main()
