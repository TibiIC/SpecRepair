import unittest
from unittest import TestCase

from spec_repair.ltl import convert_assignments
from spec_repair.old.Specification import contains_contradictions
from spec_repair.util.spec_util import integrate_rule
from spec_repair.util.exp_util import split_expression_to_raw_components, eventualise_consequent
from spec_repair.old.util_titus import semantically_identical_spot
from spec_repair.enums import When, Learning, SimEnv


class Test(TestCase):
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

        arrow = ""
        conjunct = ' holds_at(eventually,green,V1,V2).'
        learning_type = Learning.GUARANTEE_WEAKENING
        line = ['GF(', 'car=false);']
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tGF(green=true|car=false);\n")

        arrow = "->"
        conjunct = ' holds_at(current,highwater,V1,V2); holds_at(current,methane,V1,V2).'
        line = ['G(highwater=true', 'next(pump=true));']
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, '\tG(highwater=true->highwater=true&methane=true|next(pump=true));\n')

        arrow = "->"
        conjunct = "holds_at(next,highwater,V1,V2)."
        line = ["G(", "highwater=false|methane=false);"]
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(next(highwater=false)->highwater=false|methane=false);\n")

        arrow = "->"
        conjunct = "not_holds_at(next,emergency,V1,V2)."
        line = ["G(car=true&green=true", "next(car=false));"]
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(car=true&green=true&next(emergency=true)->next(car=false));\n")

        arrow = "->"
        conjunct = "not_holds_at_weak(next,emergency,V1,V2)."
        line = ["G(car=true&green=true", "next(car=false));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(car=true&green=true->next(emergency=false)|next(car=false));\n")

        arrow = "->"
        conjunct = "not_holds_at(next,emergency,V0,V1)."
        line = ["G(car=true & green=true", "next(car=false));"]
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual(output, "\tG(car=true & green=true&next(emergency=true)->next(car=false));\n")

    def test_integrate_or_inside_eventually_rule(self):
        arrow = "->"
        conjunct = "holds_at(eventually,c,V0,V1)."
        line = ["G(a=true", "F(b=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->F(c=true|b=true));\n", output)

    def test_integrate_eventually_or_rule(self):
        arrow = "->"
        conjunct = "holds_at(current,c,V0,V1)."
        line = ["G(a=true", "F(b=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->c=true|F(b=true));\n", output)

    def test_integrate_eventually_or_next_rule(self):
        arrow = "->"
        conjunct = "holds_at(next,c,V0,V1)."
        line = ["G(a=true", "F(b=true));"]
        learning_type = Learning.GUARANTEE_WEAKENING
        output = integrate_rule(arrow, conjunct, learning_type, line)
        self.assertEqual("\tG(a=true->next(c=true)|F(b=true));\n", output)

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

    @unittest.skip("Made sense when the operator wasn't replaced")
    def test_integrate_eventually_rule_3_old(self):
        exp = "G(car=true & green=true->next(car=false));"
        learning_type = Learning.ASSUMPTION_WEAKENING
        output = eventualise_consequent(exp, learning_type)
        self.assertEqual("\tG(car=true & green=true->F(next(car=false)));\n", output)

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

    def test_exp_split(self):
        exp = "G(a=true);"
        output = split_expression_to_raw_components(exp)
        self.assertEqual(["G(true", "a=true);"], output)

    def test_convert_assignments(self):
        formula = 'PREV(p=true)&p=true'
        when = When.ALWAYS
        output = convert_assignments(formula, when, consequent=False)
        self.assertEqual(output, 'holds_at(prev,p,T,S),\n\tholds_at(current,p,T,S)')

        formula = "(next(f1=true)&b2=false&b3=false)"
        when = When.ALWAYS
        output = convert_assignments(formula, when, consequent=False)
        self.assertEqual(output, 'holds_at(next,f1,T,S),\n\tnot_holds_at(current,b2,T,S),\n\tnot_holds_at(current,b3,T,S)')

        output = convert_assignments(formula, when, consequent=True)
        self.assertEqual(output, 'holds_at(next,f1,T,S),\n\tnot_holds_at(current,b2,T,S),\n\tnot_holds_at(current,b3,T,S)')

    def test_semantical_identical_spot(self):
        fixed = "../example-files/semantically_identical/minepump_fixed0_fixed.spectra"
        final = "../example-files/semantically_identical/minepump_fixed1.spectra"
        start = "../example-files/semantically_identical/minepump_fixed0.spectra"
        inc_gar = "../example-files/semantically_identical/minepump_inc_gar.spectra"

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
