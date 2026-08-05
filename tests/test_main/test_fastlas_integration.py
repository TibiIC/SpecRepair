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
import re
import shutil
import unittest
from unittest.mock import patch

from main.bfs_repair_orchestrator_builder import (
    BFSRepairOrchestratorBuilder,
    FASTLAS_RUNS_ENV_VAR,
    LEARNER_ENV_VAR,
    fastlas_runs_from_env,
    learner_from_env,
)
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
from spec_repair.model.adaptation_learned import Adaptation
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.util.file_util import read_file_lines
from spec_repair.wrappers.asp_wrappers import get_violations, run_ILASP
from tests.base_test_case import BaseTestCase

CASE_STUDIES = '../input-files/case-studies/spectra/strengthened'
FASTLAS_AVAILABLE = shutil.which(SETUP_DICT.get('FastLAS', 'FastLAS')) is not None \
                    or os.path.isfile(SETUP_DICT.get('FastLAS', ''))


WEAKENINGS = ("ANTECEDENT_WEAKENING", "CONSEQUENT_WEAKENING",
              "INVARIANT_TO_RESPONSE_WEAKENING")


def heuristic_manager(only: str = None) -> NoFilterHeuristicManager:
    """A manager with all three #modeh enabled, or just `only`."""
    hm = NoFilterHeuristicManager()
    hm.set_enabled("INCLUDE_NEXT")
    hm.set_enabled("INCLUDE_PREV")
    if only is not None:
        for flag in WEAKENINGS:
            (hm.set_enabled if flag == only else hm.set_disabled)(flag)
    return hm


def build_learning_task(case_study: str, hm: NoFilterHeuristicManager = None) -> str:
    """
    The ILASP task the encoder would hand to a learner for this case study.

    `hm` selects which #modeh declarations are enabled; the default enables all
    three, which is what the orchestrator does.
    """
    directory = f'{CASE_STUDIES}/{case_study}'
    spec = SpectraSpecification.from_file(f'{directory}/strong.spectra')
    trace = read_file_lines(f'{directory}/violation_trace.txt')
    hm = hm or heuristic_manager()
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

    def test_every_weakening_direction_is_solvable(self):
        """
        Regression for the missing `time/1` type predicate. Before that fix
        FastLAS built an empty hypothesis space for every antecedent-only and
        consequent-only task and reported UNSATISFIABLE with no error - which
        looked exactly like "this branch found no repair", so the search
        silently explored nothing.
        """
        for case_study in ('minepump', 'traffic_single', 'lift'):
            for weakening in WEAKENINGS:
                with self.subTest(case_study=case_study, weakening=weakening):
                    task = translate_ilasp_task_to_fastlas(
                        build_learning_task(case_study, heuristic_manager(only=weakening)))
                    output = run_fastlas(task)
                    self.assertNotIn("UNSATISFIABLE", output)
                    adaptations = FastLASInterpreter.extract_learned_possible_adaptations(output)
                    self.assertIsNotNone(adaptations)
                    self.assertGreater(len(adaptations[0][1]), 0)

    def test_learned_rules_respect_the_bias(self):
        """
        The bias forces a `timepoint_of_op` into any rule with an exception
        head. ILASP honours it natively; FastLAS only does once the block is
        rewritten from head/body into in_head/in_body - untranslated it is
        silently inert and FastLAS returns bare `holds_at` rules.
        """
        for weakening in ("ANTECEDENT_WEAKENING", "CONSEQUENT_WEAKENING"):
            with self.subTest(weakening=weakening):
                task = translate_ilasp_task_to_fastlas(
                    build_learning_task('minepump', heuristic_manager(only=weakening)))
                rules = FastLASInterpreter.extract_learned_rules(run_fastlas(task))
                for rule in rules:
                    self.assertIn("timepoint_of_op", rule)

    def test_fastlas_answers_are_among_ilasps(self):
        """
        The point of the whole translation: both solvers should be searching the
        same space. FastLAS returns one solution per run where ILASP returns
        several, so containment is what we can assert - not equality.
        """
        for weakening in WEAKENINGS:
            with self.subTest(weakening=weakening):
                ilasp_task = build_learning_task('minepump', heuristic_manager(only=weakening))
                ilasp_rules = re.findall(r"%% Solution \d+ \(score \d+\)\s*\n(.+)",
                                         run_ILASP(ilasp_task))
                # Adaptation is unhashable, so this stays a list.
                expected = [Adaptation.from_str(r.strip()) for r in ilasp_rules]
                self.assertTrue(expected, "ILASP found nothing to compare against")

                task = translate_ilasp_task_to_fastlas(ilasp_task)
                for _ in range(4):
                    for rule in FastLASInterpreter.extract_learned_rules(run_fastlas(task)):
                        self.assertIn(Adaptation.from_str(rule), expected,
                                      f"FastLAS returned a rule ILASP never found: {rule}")

    def test_a_single_candidate_task_gives_the_same_answer_every_run(self):
        """
        With every #modeh enabled, `ev_temp_op` - a body-free fact costing 0 -
        dominates and the space collapses to one candidate, so repeated runs
        agree. A property of this task, not of FastLAS: given ties it varies,
        which is what n_runs samples.
        """
        task = translate_ilasp_task_to_fastlas(build_learning_task('traffic_single'))
        outputs = {run_fastlas(task).strip() for _ in range(3)}
        self.assertEqual(1, len(outputs))

    def test_n_runs_deduplicates_repeated_solutions(self):
        """Identical answers across runs must not become duplicate branches."""
        learner = FastLASSpecLearner(n_runs=3)
        directory = f'{CASE_STUDIES}/traffic_single'
        spec = SpectraSpecification.from_file(f'{directory}/strong.spectra')
        trace = read_file_lines(f'{directory}/violation_trace.txt')
        hm = heuristic_manager()
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

    def test_fastlas_runs_come_from_the_environment(self):
        """
        The SSH sweeps set SPEC_REPAIR_FASTLAS_RUNS rather than editing a test.
        It matters because FastLAS samples one solution per run, so this is the
        knob that decides how much of ILASP's solution set a run sees.
        """
        with patch.dict(os.environ, {LEARNER_ENV_VAR: "fastlas",
                                     FASTLAS_RUNS_ENV_VAR: "5"}):
            repairer = (BFSRepairOrchestratorBuilder.syntactic()
                        .using_learner(learner_from_env())
                        .with_log_file(os.devnull).build())
        for learner in repairer._learners.values():
            self.assertEqual(5, learner.n_runs)

    def test_explicit_n_runs_beats_the_environment(self):
        with patch.dict(os.environ, {FASTLAS_RUNS_ENV_VAR: "5"}):
            repairer = (BFSRepairOrchestratorBuilder.syntactic()
                        .using_learner("fastlas", n_runs=2)
                        .with_log_file(os.devnull).build())
        for learner in repairer._learners.values():
            self.assertEqual(2, learner.n_runs)

    def test_fastlas_runs_defaults_to_one(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(FASTLAS_RUNS_ENV_VAR, None)
            self.assertEqual(1, fastlas_runs_from_env())

    def test_a_bad_fastlas_runs_value_fails_loudly(self):
        for bad in ("nonsense", "0", "-3"):
            with self.subTest(value=bad):
                with patch.dict(os.environ, {FASTLAS_RUNS_ENV_VAR: bad}):
                    with self.assertRaises(ValueError):
                        fastlas_runs_from_env()

    def test_default_builder_still_uses_ilasp_learner(self):
        from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
        repairer = BFSRepairOrchestratorBuilder.semantic().with_log_file(os.devnull).build()
        for learner in repairer._learners.values():
            self.assertIsInstance(learner, OptimisingSpecLearner)
            self.assertNotIsInstance(learner, FastLASSpecLearner)


if __name__ == "__main__":
    unittest.main()
