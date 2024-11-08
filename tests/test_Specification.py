import os
import unittest
from unittest import TestCase

from spec_repair.old_experiments import contains_contradictions
from spec_repair.util.spec_util import integrate_rule, parse_formula_str, semantically_identical_spot, \
    split_expression_to_raw_components, eventualise_consequent
from spec_repair.enums import When, Learning, SimEnv


class Test(TestCase):
    @classmethod
    def setUpClass(cls):
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(tests_dir)

    @classmethod
    def tearDownClass(cls):
        # Restore the original working directory
        os.chdir(cls.original_working_directory)

    def test_integrate_rule(self):
        arrow = "->"
        conjunct = "not_holds_at(eventually,r2,V1,V2)."
        learning_type = Learning.GUARANTEE_WEAKENING
        line = ['G(r1=true', 'F(g1=true));']
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(r1=true->F(r2=false|g1=true));\n")

        arrow = "->"
        conjunct = conjunct[0:-1] + ";holds_at(eventually,a,V1,V2)."
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(r1=true->F(r2=false&a=true|g1=true));\n")

        arrow = "->"
        conjunct = "holds_at(next,highwater,V1,V2)."
        line = ["G(", "highwater=false|methane=false);"]
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(next(highwater=false)->highwater=false|methane=false);\n")

        arrow = "->"
        conjunct = "not_holds_at(next,emergency,V0,V1)."
        line = ["G(car=true & green=true", "next(car=false));"]
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(car=true & green=true&next(emergency=true)->next(car=false));\n")

    def test_integrate_current_conjunct_no_antecedent_disjunction(self):
        temp_op = "current"
        conjunct = "holds_at(highwater,V1,V2)."
        line = "G(highwater=false|methane=false);"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(highwater=false->highwater=false|methane=false);\n")

    def test_integrate_current_conjunct_antecedent_disjunction(self):
        temp_op = "current"
        conjunct = "not_holds_at(emergency,V0,V1)."
        line = "G(car=true & green=true->next(car=false));"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(car=true & green=true&emergency=true->next(car=false));\n")

    def test_integrate_current_multiple_conjuncts(self):
        temp_op = "current"
        conjunct = 'holds_at(highwater,V1,V2); holds_at(methane,V1,V2).'
        line = 'G(highwater=true->next(pump=true));'
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual(output, '\tG(highwater=true->highwater=true&methane=true|next(pump=true));\n')

    def test_integrate_current_multiple_current_consequent_disjunction(self):
        temp_op = "current"
        conjunct = 'holds_at(c,V1,V2).'
        learning_type = Learning.GUARANTEE_WEAKENING
        line = 'G(a=false|b=false);'
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(c=true|a=false|b=false);\n")

    def test_integrate_current_or_next(self):
        temp_op = "current"
        conjunct = 'holds_at(c,V1,V2).'
        learning_type = Learning.GUARANTEE_WEAKENING
        line = 'G(a=true->next(b=true));'
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(a=true->c=true|next(b=true));\n")

    def test_integrate_current_conjunction(self):
        temp_op = "current"
        conjunct = 'holds_at(d,V1,V2).'
        learning_type = Learning.GUARANTEE_WEAKENING
        line = 'G(a=false->b=false&c=false);'
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(a=false->d=true|b=false&c=false);\n")

    def test_always_eventually(self):
        arrow = ""
        conjunct = ' holds_at(eventually,green,V1,V2).'
        learning_type = Learning.GUARANTEE_WEAKENING
        line = ['GF(', 'car=false);']
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tGF(green=true|car=false);\n")

    def test_integrate_or_inside_or_rule(self):
        temp_op = "current"
        conjunct = "holds_at(c,V0,V1)."
        line = "G(a=true->b=true);"
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->c=true|b=true);\n", output)

    def test_integrate_or_inside_next_or_rule(self):
        temp_op = "current"
        conjunct = "holds_at(c,V0,V1)."
        line = "G(a=true->next(b=true));"
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->c=true|next(b=true));\n", output)

    def test_integrate_not_or_inside_or_rule(self):
        temp_op = "current"
        conjunct = "not_holds_at(c,V0,V1)."
        line = "G(a=true->b=true);"
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->c=false|b=true);\n", output)

    def test_integrate_not_or_inside_next_or_rule(self):
        temp_op = "current"
        conjunct = "not_holds_at(c,V0,V1)."
        line = "G(a=true->next(b=true));"
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->c=false|next(b=true));\n", output)

    def test_integrate_next_or_inside_next_or_rule(self):
        temp_op = "next"
        conjunct = "holds_at(c,V0,V1)."
        line = "G(a=true->next(b=true));"
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->next(c=true|b=true));\n", output)

    def test_integrate_next_or_inside_or_rule(self):
        arrow = "->"
        conjunct = "holds_at(next,c,V0,V1)."
        line = ["G(a=true", "b=true);"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->b=true|next(c=true));\n", output)

    def test_integrate_next_or_inside_or_next_or_rule(self):
        arrow = "->"
        conjunct = "holds_at(next,d,V0,V1)."
        line = ["G(a=true", "next(c=true)|b=true);"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->b=true|next(d=true|c=true));\n", output)

    def test_integrate_next_or_inside_or_next_or_rule_2(self):
        arrow = "->"
        conjunct = "holds_at(next,d,V0,V1)."
        line = ["G(a=true", "b=true|next(c=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->b=true|next(d=true|c=true));\n", output)

    def test_integrate_or_inside_or_next_or_rule(self):
        temp_op = "current"
        conjunct = "holds_at(d,V0,V1)."
        line = "G(a=true->next(c=true)|b=true);"
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)

        self.assertEqual("\tG(a=true->d=true|b=true|next(c=true));\n", output)
        # NOTE: this is also correct, just non-ideal for future processing
        "\tG(a=true->d=true|next(c=true)|b=true);\n"

    def test_integrate_or_inside_eventually_rule(self):
        arrow = "->"
        conjunct = "holds_at(eventually,c,V0,V1)."
        line = ["G(a=true", "F(b=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->F(c=true|b=true));\n", output)

    def test_integrate_eventually_or_rule(self):
        temp_op = "current"
        conjunct = "holds_at(c,V0,V1)."
        line = "G(a=true->F(b=true));"
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(temp_op, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true&c=false->F(b=true));\n", output)

    def test_integrate_eventually_or_next_rule(self):
        arrow = "->"
        conjunct = "holds_at(next,c,V0,V1)."
        line = ["G(a=true", "F(b=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true&next(c=false)->F(b=true));\n", output)

    def test_integrate_eventually_or_next_rule_2(self):
        arrow = "->"
        conjunct = "holds_at(next,d,V0,V1)."
        line = ["G(a=true", "next(c=true)|F(b=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->next(d=true|c=true)|F(b=true));\n", output)

    def test_integrate_eventually_or_next_rule_3(self):
        arrow = "->"
        conjunct = "holds_at(eventually,d,V0,V1)."
        line = ["G(a=true", "next(c=true)|F(b=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->next(c=true)|F(d=true|b=true));\n", output)

    def test_integrate_eventually_rule(self):
        exp = "G(a=true);"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = eventualise_consequent(exp, learning_type)
        self.assertEqual("\tG(true->F(a=true));\n", output)

    def test_integrate_eventually_rule_2(self):
        exp = "G(h=true->a=true);"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = eventualise_consequent(exp, learning_type)
        self.assertEqual("\tG(h=true->F(a=true));\n", output)

    def test_integrate_eventually_rule_3(self):
        exp = "G(car=true & green=true->next(car=false));"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = eventualise_consequent(exp, learning_type)
        self.assertEqual("\tG(car=true & green=true->F(car=false));\n", output)

    def test_integrate_eventually_rule_4(self):
        exp = "G(a=true->b=false & c=true);"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = eventualise_consequent(exp, learning_type)
        self.assertEqual("\tG(a=true->F(b=false & c=true));\n", output)

    def test_integrate_eventually_rule_5(self):
        exp = "G(a=true&b=true->next(c=false|d=false));"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = eventualise_consequent(exp, learning_type)
        self.assertEqual("\tG(a=true&b=true->F(c=false|d=false));\n", output)

    def test_exp_split(self):
        exp = "G(a=true);"
        output = split_expression_to_raw_components(exp)
        self.assertEqual(["G(true", "a=true);"], output)

    def test_semantical_identical_spot(self):
        fixed = "test_files/semantically_identical/minepump_fixed0_fixed.spectra"
        final = "test_files/semantically_identical/minepump_fixed1.spectra"
        start = "test_files/semantically_identical/minepump_fixed0.spectra"
        inc_gar = "test_files/semantically_identical/minepump_inc_gar.spectra"

        result = semantically_identical_spot(fixed, final)
        self.assertEqual(SimEnv.Success, result)

        result = semantically_identical_spot(start, final)
        self.assertEqual(SimEnv.Realizable, result)

        result = semantically_identical_spot(inc_gar, final)
        self.assertEqual(SimEnv.IncorrectGuarantees, result)

        fixed_file = "../output-files/rq_files/traffic_single_FINAL_dropped7_fixed_patterned37.spectra"
        end_file = "../input-files/examples/Traffic/traffic_single_FINAL.spectra"
        result = semantically_identical_spot(fixed_file, end_file)
        self.assertEqual(result, SimEnv.Realizable)

        unusual = "../output-files/rq_files/minepump_fixed1_dropped2_fixed140.spectra"
        result = semantically_identical_spot(unusual, final)
        self.assertEqual(result, SimEnv.Realizable)

    def test_contains_contradictions(self):
        file = "../input-files/examples/contradiction.spectra"
        result = contains_contradictions(file, "assumption|asm")
        self.assertTrue(result)

        result = contains_contradictions(file, "guarantee|gar")
        self.assertFalse(result)
