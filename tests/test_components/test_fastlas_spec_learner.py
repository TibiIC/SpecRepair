"""
Unit tests for the FastLAS learner component.

These cover the two things the learner is responsible for - translating the
ILASP task into FastLAS's dialect, and turning FastLAS output back into
adaptations - without invoking FastLAS itself. The end-to-end tests that do run
the binary live in tests/test_main/test_fastlas_integration.py.
"""
import unittest
from unittest.mock import patch

from spec_repair.components.heuristic_managers.no_filter_heuristic_manager import NoFilterHeuristicManager
from spec_repair.components.learners.fastlas_spec_learner import (
    FastLASSpecLearner,
    translate_ilasp_task_to_fastlas,
)
from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.exceptions import NoViolationException
from spec_repair.helpers.parsers.fastlas_interpreter import FastLASInterpreter

RUN_FASTLAS = "spec_repair.components.learners.fastlas_spec_learner.run_fastlas"


class TestTaskTranslation(unittest.TestCase):
    def test_modeb_loses_recall_and_positive_annotation(self):
        las = "#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (positive)).\n"
        self.assertEqual(
            "#modeb(holds_at(const(usable_atom), var(time), var(trace))).\n",
            translate_ilasp_task_to_fastlas(las))

    def test_constant_becomes_a_background_fact(self):
        """FastLAS has no #constant; it reads const(t) values from a t/1 predicate."""
        las = "#constant(usable_atom,highwater).\n#constant(temp_op_v,next).\n"
        self.assertEqual("usable_atom(highwater).\ntemp_op_v(next).\n",
                         translate_ilasp_task_to_fastlas(las))

    def test_constant_ranges_survive_as_valid_clingo_facts(self):
        self.assertEqual("index(0..2).\n", translate_ilasp_task_to_fastlas("#constant(index,0..2).\n"))

    def test_examples_gain_the_identifier_fastlas_requires(self):
        las = "#pos({entailed(t0)},{},{\nholds_at(a,0,t0).\n}).\n"
        translated = translate_ilasp_task_to_fastlas(las)
        self.assertIn("#pos(eg1,{entailed(t0)}", translated)

    def test_multiple_examples_get_distinct_identifiers(self):
        las = "#pos({a},{},{}).\n#pos({b},{},{}).\n#pos({c},{},{}).\n"
        translated = translate_ilasp_task_to_fastlas(las)
        for i in (1, 2, 3):
            self.assertIn(f"#pos(eg{i},", translated)

    def test_translation_leaves_modeh_and_bias_alone(self):
        las = ('#modeh(ev_temp_op(const(expression_v))).\n'
               '#bias(":- constraint.").\n')
        self.assertEqual(las, translate_ilasp_task_to_fastlas(las))


class TestOutputInterpretation(unittest.TestCase):
    def test_unsatisfiable_is_none(self):
        self.assertIsNone(FastLASInterpreter.extract_learned_possible_adaptations("UNSATISFIABLE"))

    def test_empty_output_is_none(self):
        self.assertIsNone(FastLASInterpreter.extract_learned_possible_adaptations(""))

    def test_single_fact_solution_is_parsed(self):
        result = FastLASInterpreter.extract_learned_possible_adaptations(
            "ev_temp_op(car_moves_when_green).\n")
        self.assertIsNotNone(result)
        self.assertEqual(1, len(result), "FastLAS returns exactly one solution per run")
        score, adaptations = result[0]
        self.assertEqual(1, len(adaptations))

    def test_rule_with_body_is_parsed(self):
        result = FastLASInterpreter.extract_learned_possible_adaptations(
            "consequent_exception(assumption1_1,V0,V1) :- holds_at(highwater,V0,V1).\n")
        self.assertIsNotNone(result)
        self.assertEqual(1, len(result[0][1]))

    def test_diagnostic_lines_are_not_mistaken_for_rules(self):
        """FastLAS mixes progress output into stdout; only rules may be parsed."""
        rules = FastLASInterpreter.extract_learned_rules(
            "% a comment\nSolving...\nev_temp_op(x).\nDone in 3s\n")
        self.assertEqual(["ev_temp_op(x)."], rules)

    def test_empty_hypothesis_raises_rather_than_returning_nothing(self):
        with self.assertRaises(NoViolationException):
            FastLASInterpreter.extract_learned_possible_adaptations("Solving...\nDone\n")


class TestFastLASSpecLearner(unittest.TestCase):
    def setUp(self):
        self.learner = FastLASSpecLearner(heuristic_manager=NoFilterHeuristicManager())

    def test_is_an_optimising_learner_so_the_rest_of_the_search_is_unchanged(self):
        self.assertIsInstance(self.learner, OptimisingSpecLearner)

    def test_n_runs_must_be_positive(self):
        for n in (0, -1):
            with self.subTest(n_runs=n):
                with self.assertRaises(ValueError):
                    FastLASSpecLearner(n_runs=n)

    def _find(self, learner, outputs):
        """Drive find_adaptations_with_heuristic with canned FastLAS output."""
        with patch.object(learner, "spec_encoder") as encoder:
            encoder.encode_ILASP.return_value = "#modeh(ev_temp_op(const(expression_v)))."
            with patch(RUN_FASTLAS, side_effect=outputs) as run:
                result = learner.find_adaptations_with_heuristic(
                    None, [], [], None, [], NoFilterHeuristicManager())
        return result, run

    def test_single_run_returns_one_solution(self):
        result, run = self._find(FastLASSpecLearner(n_runs=1), ["ev_temp_op(a).\n"])
        self.assertEqual(1, run.call_count)
        self.assertEqual(1, len(result))

    def test_n_runs_invokes_fastlas_that_many_times(self):
        learner = FastLASSpecLearner(n_runs=4)
        _, run = self._find(learner, ["ev_temp_op(a).\n"] * 4)
        self.assertEqual(4, run.call_count)

    def test_identical_solutions_are_deduplicated(self):
        """
        The measured behaviour of FastLAS 2.1.0: repeated runs return the same
        answer, so extra runs must not produce duplicate branches for the search.
        """
        result, _ = self._find(FastLASSpecLearner(n_runs=3), ["ev_temp_op(a).\n"] * 3)
        self.assertEqual(1, len(result))

    def test_distinct_solutions_are_all_kept(self):
        result, _ = self._find(
            FastLASSpecLearner(n_runs=3),
            ["ev_temp_op(a).\n", "ev_temp_op(b).\n", "ev_temp_op(a).\n"])
        self.assertEqual(2, len(result))

    def test_unsatisfiable_runs_contribute_nothing(self):
        result, _ = self._find(
            FastLASSpecLearner(n_runs=3),
            ["UNSATISFIABLE", "ev_temp_op(a).\n", "UNSATISFIABLE"])
        self.assertEqual(1, len(result))

    def test_all_runs_unsatisfiable_gives_no_adaptations(self):
        result, _ = self._find(FastLASSpecLearner(n_runs=2), ["UNSATISFIABLE"] * 2)
        self.assertEqual([], result)

    def test_the_task_handed_to_fastlas_is_translated(self):
        learner = FastLASSpecLearner(n_runs=1)
        with patch.object(learner, "spec_encoder") as encoder:
            encoder.encode_ILASP.return_value = (
                "#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (positive)).\n"
                "#constant(usable_atom,highwater).\n")
            with patch(RUN_FASTLAS, return_value="ev_temp_op(a).\n") as run:
                learner.find_adaptations_with_heuristic(
                    None, [], [], None, [], NoFilterHeuristicManager())
        task = run.call_args[0][0]
        self.assertIn("#modeb(holds_at(const(usable_atom), var(time), var(trace))).", task)
        self.assertIn("usable_atom(highwater).", task)
        self.assertNotIn("#constant", task)
        self.assertNotIn("(positive)", task)


if __name__ == "__main__":
    unittest.main()
