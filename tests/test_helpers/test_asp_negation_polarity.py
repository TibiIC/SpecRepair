"""
Negating an atom must not mutate the specification it came from.

`format_exp` used to handle `Not(atom)` by flipping the atom's stored value in
place. Formatting the same object twice therefore flipped it back, and every
other occurrence came out with the wrong polarity - a silently wrong encoding,
never an error.

Found on elevator's `floor_mutual_exclusion`,
`G(!(fl&fm) & !(fl&fu) & !(fm&fu))`, which normalises to eight disjuncts of
negated atoms. The encoding alternated with a period of four: disjuncts 0 and 4
correct, the other six wrong. A state with two floors true was reported as
violating nothing at all.
"""
import os
import re
import unittest

from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.model.spectra_specification import SpectraSpecification

CASE_STUDIES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "input-files", "case-studies", "spectra", "case_study_2")
ELEVATOR = os.path.join(CASE_STUDIES, "elevator", "original.spectra")


def _disjunct_bodies(asp: str, formula: str):
    return {int(i): [l.strip().rstrip(",.") for l in body.splitlines() if "holds_at" in l]
            for i, body in re.findall(
                rf"root_consequent_holds\(OP,{formula},\d+,(\d+),T1,S\):-\n(.*?)\n\n",
                asp, re.S)}


class TestNegationPolarity(unittest.TestCase):
    def setUp(self):
        self.spec = SpectraSpecification.from_file(ELEVATOR)
        self.asp = self.spec.to_asp(for_clingo=True)

    def test_every_disjunct_of_a_mutual_exclusion_is_all_negative(self):
        """
        `!(a&b) & !(a&c) & !(b&c)` normalises to disjuncts of negated atoms
        only, so a single positive `holds_at` in any of them is the bug.
        """
        bodies = _disjunct_bodies(self.asp, "floor_mutual_exclusion")
        self.assertGreater(len(bodies), 1, "expected a multi-disjunct formula")
        for index, literals in sorted(bodies.items()):
            positive = [l for l in literals if not l.startswith("not_holds_at")]
            self.assertEqual([], positive,
                             f"disjunct {index} has positive literals: {positive}")

    def test_formatting_twice_gives_the_same_encoding(self):
        """
        The mutation showed up as an encoding that depended on how many times
        it had been produced.
        """
        self.assertEqual(self.asp, self.spec.to_asp(for_clingo=True))

    def test_two_floors_at_once_violates_mutual_exclusion(self):
        """The property the formula exists to state, end to end through clingo."""
        from spec_repair.components.new_spec_encoder import get_violated_expression_names_of_type
        from spec_repair.wrappers.asp_wrappers import get_violations

        variables = sorted(a.name for a in self.spec.get_atoms())
        legal = {"elevMot_bwd": "false", "elevMot_fwd": "true",
                 "floor_lower": "true", "floor_middle": "false", "floor_upper": "false"}
        two_floors = {**legal, "floor_lower": "false",
                      "floor_middle": "true", "floor_upper": "true"}

        trace = []
        for t, state in enumerate([legal, two_floors]):
            for var in variables:
                prefix = "" if state.get(var, "false") == "true" else "not_"
                trace.append(f"{prefix}holds_at({var},{t},trace_name_0).\n")
            trace.append("\n")

        violations = get_violations(NewSpecEncoder.encode_ASP(self.spec, trace, []),
                                    exp_type="assumption")
        names = get_violated_expression_names_of_type(violations, "assumption")
        self.assertIn("floor_mutual_exclusion", names)


if __name__ == "__main__":
    unittest.main()
