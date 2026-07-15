import re
from unittest import TestCase

from spec_repair.util.patterns import EventuallyConsequentRule, ConsequentExceptionRule, AntecedentExceptionRule


class TestRegex(TestCase):
    def test_EventuallyConsequentRule(self):
        pattern = EventuallyConsequentRule.pattern
        test_string = "consequent_exception(arg1,arg2,arg3) :- root_consequent_holds(arg4,arg5,arg6,arg7,arg8)."
        self.assertIsNotNone(pattern.match(test_string))

    def test_EventuallyConsequentRule_fails_on_bad_argument_amount(self):
        pattern = EventuallyConsequentRule.pattern
        test_string = "consequent_holds(arg1,arg2) :- root_consequent_holds(arg5,arg6,arg7,arg8,arg9)."
        self.assertIsNone(pattern.match(test_string))

    def test_AntecedentExceptionRule(self):
        pattern = AntecedentExceptionRule.pattern
        test_string = "antecedent_exception(arg1,arg2,arg3,arg4) :- not_holds_at(arg5,arg6,arg7)."
        self.assertIsNotNone(pattern.match(test_string))

    def test_AntecedentExceptionRule_fails_on_bad_argument_amount(self):
        pattern = AntecedentExceptionRule.pattern
        test_string = "antecedent_exception(arg1,arg2,arg3,arg4) :- not_holds_at(arg4)."
        self.assertIsNone(pattern.match(test_string))

    def test_ConsequentExceptionRule(self):
        pattern = ConsequentExceptionRule.pattern
        test_string = "consequent_exception(guarantee1_1,V1,V2) :- holds_at(methane,V1,V2)."
        self.assertIsNotNone(pattern.match(test_string))

    def test_ConsequentExceptionRule_fails_on_bad_argument_amount(self):
        pattern = ConsequentExceptionRule.pattern
        test_string = "consequent_exception(arg1,arg2,arg3,arg4,arg5) :- holds_at(arg1)."
        self.assertIsNone(pattern.match(test_string))
