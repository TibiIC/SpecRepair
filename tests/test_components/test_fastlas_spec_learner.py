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
    FastLASTypeError,
    translate_ilasp_task_to_fastlas,
)
from spec_repair.components.learners.optimising_final_spec_learner import OptimisingSpecLearner
from spec_repair.exceptions import NoViolationException
from spec_repair.helpers.parsers.fastlas_interpreter import FastLASInterpreter
from spec_repair.model.adaptation_learned import Adaptation

RUN_FASTLAS = "spec_repair.components.learners.fastlas_spec_learner.run_fastlas"


def _rule(atom: str) -> str:
    """
    Canned FastLAS output, in the shape the real binary emits.

    Enumeration needs a rule with a body: the exclusion constraint is built from
    the body literals, so a body-free fact cannot be excluded and ends the loop.
    """
    return (f"antecedent_exception(assumption2_1,0,V0,V1) :- "
            f"timepoint_of_op(prev,V0,V2,V1), not_holds_at({atom},V2,V1), "
            f"time(V0), trace(V1), time(V2).\n")


class TestTaskTranslation(unittest.TestCase):
    def test_modeb_loses_the_annotation_but_keeps_the_recall(self):
        """
        FastLAS accepts ILASP's recall bound and rejects only the annotation.
        Verified against the FastLAS repo, which ships the same tasks in both
        dialects under FastLAS2/data/agent/{ilasp,fastnonopl}_tasks/ - the
        recall survives translation there untouched.
        """
        las = "#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (positive)).\n"
        self.assertIn(
            "#modeb(2,holds_at(const(usable_atom), var(time), var(trace))).",
            translate_ilasp_task_to_fastlas(las))

    def test_negative_annotation_becomes_an_explicit_not(self):
        las = "#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (negative)).\n"
        self.assertIn(
            "#modeb(2,not holds_at(const(usable_atom), var(time), var(trace))).",
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

    def test_translation_leaves_modeh_alone(self):
        las = '#modeh(ev_temp_op(const(expression_v))).\n'
        self.assertEqual(las, translate_ilasp_task_to_fastlas(las))

    def test_var_types_gain_the_predicate_fastlas_grounds_them_from(self):
        """
        Without a time/1 predicate FastLAS builds an empty hypothesis space and
        reports SPACE SIZE 0 / UNSATISFIABLE with no error - indistinguishable
        from "this branch found no repair". That is why antecedent and
        consequent weakening were unsolvable while invariant-to-response
        weakening (no var() in its #modeh) worked.
        """
        las = "#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (positive)).\n"
        self.assertIn("time(T) :- timepoint(T,_).", translate_ilasp_task_to_fastlas(las))

    def test_trace_type_is_not_redefined(self):
        """Each example's context already asserts trace(name)."""
        las = "#modeh(exc(const(e), var(trace))).\n"
        self.assertNotIn("trace(T) :-", translate_ilasp_task_to_fastlas(las))

    def test_unknown_var_type_raises_rather_than_emptying_the_space(self):
        with self.assertRaises(FastLASTypeError) as ctx:
            translate_ilasp_task_to_fastlas("#modeb(p(var(mystery))).\n")
        self.assertIn("mystery", str(ctx.exception))

    def test_type_predicates_only_come_from_mode_declarations(self):
        """A var(time) inside background knowledge must not trigger emission."""
        self.assertNotIn("time(T) :-", translate_ilasp_task_to_fastlas("foo(var(time)).\n"))


class TestBiasTranslation(unittest.TestCase):
    """
    ILASP's bias meta-language is head/1 + body/1; FastLAS's is in_head/1 +
    in_body/1. Untranslated, FastLAS treats body/1 as undefined, so the whole
    block is silently inert and it returns rules the bias exists to forbid.
    """

    def _bias(self, body: str) -> str:
        return translate_ilasp_task_to_fastlas(f'#bias("\n{body}\n").\n')

    def test_body_becomes_in_body(self):
        out = self._bias(":- body(holds_at(_, _, _)).")
        self.assertIn(":- in_body(holds_at(_, _, _)).", out)

    def test_head_becomes_in_head(self):
        out = self._bias(":- head(antecedent_exception(_,_,_,_)), body(holds_at(_,_,_)).")
        self.assertIn(":- in_head(antecedent_exception(_,_,_,_)), in_body(holds_at(_,_,_)).", out)

    def test_negated_body_is_translated_too(self):
        """`:- not body(X)` is the dangerous form - it fires always, so an
        untranslated task goes instantly UNSATISFIABLE."""
        out = self._bias(":- body(holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).")
        self.assertIn("not in_body(timepoint_of_op(_,_,V1,V2))", out)
        self.assertNotIn("not body(", out)

    def test_already_translated_predicates_are_not_double_prefixed(self):
        self.assertNotIn("in_in_body", self._bias(":- in_body(holds_at(_,_,_))."))

    def test_constraint_flag_is_dropped(self):
        """ILASP's `constraint` means "the learned rule has an empty head".
        FastLAS only learns #modeh-headed rules, so the atom is undefined."""
        self.assertNotIn("constraint", self._bias(":- constraint.\n:- body(holds_at(_,_,_))."))

    def test_double_equals_becomes_single(self):
        """FastLAS's parser rejects `==` with "unexpected T_EQUAL"."""
        out = self._bias(":- body(timepoint_of_op(next,V1,V2,_)), V1 == V2.")
        self.assertIn("V1 = V2", out)
        self.assertNotIn("==", out)

    def test_a_bias_of_only_dropped_lines_leaves_no_empty_block(self):
        self.assertNotIn("#bias", self._bias(":- constraint."))


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

    def test_fastlas_type_guards_parse_to_the_same_adaptation_as_ilasp(self):
        """
        FastLAS realises `var(T)` by injecting `T(V)` into the learned rule, so
        its answers carry `time(V0), trace(V1)` guards that ILASP's do not. They
        are inert for Adaptation.from_str, which reads only timepoint_of_op and
        holds_at/not_holds_at - so the two solvers' rules compare equal and
        nothing downstream needs to strip them.
        """
        pairs = [
            ("antecedent_exception(a2_1,0,V0,V1) :- timepoint_of_op(prev,V0,V2,V1), "
             "not_holds_at(highwater,V2,V1), time(V0), trace(V1), time(V2).",
             "antecedent_exception(a2_1,0,V1,V2) :- timepoint_of_op(prev,V1,V3,V2); "
             "not_holds_at(highwater,V3,V2)."),
            ("consequent_exception(a2_1,V0,V1) :- timepoint_of_op(current,V0,V0,V1), "
             "holds_at(highwater,V0,V1), time(V0), trace(V1).",
             "consequent_exception(a2_1,V1,V2) :- timepoint_of_op(current,V1,V1,V2); "
             "holds_at(highwater,V1,V2)."),
        ]
        for fastlas_rule, ilasp_rule in pairs:
            with self.subTest(rule=fastlas_rule.split(" :-")[0]):
                self.assertEqual(Adaptation.from_str(ilasp_rule),
                                 Adaptation.from_str(fastlas_rule))

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

    def test_n_runs_is_a_ceiling_not_a_fixed_number_of_invocations(self):
        """
        Enumeration keeps asking until the task is exhausted, so a step with
        two solutions costs three invocations however high n_runs is set - the
        third being the UNSATISFIABLE that proves there is nothing left.
        """
        learner = FastLASSpecLearner(n_runs=10)
        _, run = self._find(learner, [_rule("methane"), _rule("highwater"),
                                      "UNSATISFIABLE"])
        self.assertEqual(3, run.call_count)

    def test_each_solution_found_is_excluded_from_the_next_task(self):
        """
        The mechanism the whole approach rests on: without the exclusions being
        appended, FastLAS would be asked the identical question every time and
        would answer it the same way.
        """
        learner = FastLASSpecLearner(n_runs=3)
        _, run = self._find(learner, [_rule("methane"), _rule("highwater"),
                                      "UNSATISFIABLE"])
        second_task, third_task = (run.call_args_list[i][0][0] for i in (1, 2))
        self.assertIn("not_holds_at(methane", second_task)
        self.assertIn("not_holds_at(methane", third_task)
        self.assertIn("not_holds_at(highwater", third_task)
        # ...and each exclusion pins the body size, so it cannot take a rule
        # that merely extends it down with it.
        self.assertIn("#count{X : in_body(X)} = 2", second_task)

    def test_identical_solutions_are_deduplicated(self):
        """
        Enumeration should not repeat itself, but a solver that returned the
        same answer twice anyway must not produce duplicate branches for the
        search - it would make the BFS do the same work twice.
        """
        result, _ = self._find(FastLASSpecLearner(n_runs=3), [_rule("methane")] * 3)
        self.assertEqual(1, len(result))

    def test_distinct_solutions_are_all_kept(self):
        result, _ = self._find(
            FastLASSpecLearner(n_runs=3),
            [_rule("methane"), _rule("highwater"), _rule("pump")])
        self.assertEqual(3, len(result))

    def test_a_body_free_fact_stops_enumeration(self):
        """
        A fact has no body literals, so the only constraint expressible for it
        would key on the head alone and block every rule sharing that head -
        far more than the one solution found. Asking again would just repeat
        the same answer, so the loop stops instead.
        """
        result, run = self._find(FastLASSpecLearner(n_runs=5), ["ev_temp_op(a).\n"] * 5)
        self.assertEqual(1, run.call_count)
        self.assertEqual(1, len(result))

    def test_unsatisfiable_stops_enumeration_immediately(self):
        """
        Constraints only ever accumulate, so once the task is unsatisfiable no
        later run can succeed. Burning the remaining runs would cost real time
        on the large case studies for a guaranteed non-answer.
        """
        result, run = self._find(
            FastLASSpecLearner(n_runs=3),
            ["UNSATISFIABLE", _rule("methane"), _rule("highwater")])
        self.assertEqual(1, run.call_count)
        self.assertEqual([], result)

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
        self.assertIn("#modeb(2,holds_at(const(usable_atom), var(time), var(trace))).", task)
        self.assertIn("usable_atom(highwater).", task)
        self.assertNotIn("#constant", task)
        self.assertNotIn("(positive)", task)


if __name__ == "__main__":
    unittest.main()
