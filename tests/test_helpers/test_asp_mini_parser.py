from unittest import TestCase

from py_ltl.formula import AtomicProposition

from spec_repair.helpers.asp_mini_parser import ASPMiniParser


class TestASPMiniParser(TestCase):
    def test_parse(self):
        test_cases = [
            ("not_holds_at(highwater,0,trace_name_0).",AtomicProposition(name="highwater", value=False)),
            ("not_holds_at(methane,0,trace_name_0).",AtomicProposition(name="methane", value=False)),
            ("not_holds_at(pump,0,trace_name_0).", AtomicProposition(name="pump", value=False)),
            ("holds_at(highwater,1,trace_name_0).", AtomicProposition(name="highwater", value=True)),
            ("holds_at(methane,1,trace_name_0).", AtomicProposition(name="methane", value=True)),
            ("not_holds_at(pump,1,trace_name_0).", AtomicProposition(name="pump", value=False))
        ]
        for line, expected in test_cases:
            with self.subTest(line=line):
                result = ASPMiniParser.parse(line)
                self.assertEqual(result, expected)

    def test_parse_adv(self):
        test_cases = [
            ("not_holds_at(highwater,0,trace_name_0).", (AtomicProposition(name="highwater", value=False), 0, "trace_name_0")),
            ("not_holds_at(methane,0,trace_name_0).", (AtomicProposition(name="methane", value=False), 0, "trace_name_0")),
            ("not_holds_at(pump,0,trace_name_0).", (AtomicProposition(name="pump", value=False), 0, "trace_name_0")),
            ("holds_at(highwater,1,trace_name_0).", (AtomicProposition(name="highwater", value=True), 1, "trace_name_0")),
            ("holds_at(methane,1,trace_name_0).", (AtomicProposition(name="methane", value=True), 1, "trace_name_0")),
            ("not_holds_at(pump,1,trace_name_0).", (AtomicProposition(name="pump", value=False), 1, "trace_name_0"))
        ]
        for line, expected in test_cases:
            with self.subTest(line=line):
                result = ASPMiniParser.parse_adv(line)
                self.assertEqual(result, expected)
