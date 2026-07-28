"""
Parse FastLAS output into learned adaptations.

FastLAS and ILASP disagree about output shape, which is the only reason this
exists alongside ILASPInterpreter:

* ILASP prints `%% Solution N (score M)` blocks, several per run.
* FastLAS prints the learned rules bare, one per line, and only ever one
  solution per run.

The individual rules are in the same syntax, so `Adaptation.from_str` handles
both unchanged - a FastLAS answer like

    ev_temp_op(car_moves_when_green).
    consequent_exception(assumption1_1,V0,V1) :- holds_at(highwater,V0,V1).

parses exactly as the equivalent lines inside an ILASP solution block.
"""
import re
from typing import List, Optional, Tuple

from spec_repair.exceptions import NoViolationException
from spec_repair.model.adaptation_learned import Adaptation

# FastLAS has no notion of a solution score in its default output, so every
# solution is reported at this score. Downstream, filter_useful_adaptations
# keeps the minimum-scoring adaptations; with one uniform score that reduces to
# "keep them all", which is what we want when the scores are not comparable.
FASTLAS_SCORE = 0

_UNSATISFIABLE = re.compile(r"\bUNSATISFIABLE\b")
_RULE_LINE = re.compile(r"^[a-z_][\w]*\(.*\)\s*(:-.*)?\.$")


class FastLASInterpreter:
    @staticmethod
    def extract_learned_rules(output: str) -> Optional[List[str]]:
        """
        The learned rules from one FastLAS run.

        Three outcomes, deliberately distinguished, because collapsing the last
        two would hide a real difference:

        * `None`  - no solution exists (UNSATISFIABLE, or nothing on stdout);
          the caller should treat the branch as not having panned out, which is
          what ILASPInterpreter also signals with None.
        * `[]`    - FastLAS ran and answered, but the hypothesis is empty, i.e.
          the task is trivially solvable.
        * a list  - the learned rules.
        """
        if not output.strip() or _UNSATISFIABLE.search(output):
            return None
        rules = []
        for line in output.splitlines():
            line = line.strip()
            # FastLAS mixes diagnostics and timing into stdout; keep only what
            # looks like an ASP rule so a stray progress line cannot be parsed
            # as a hypothesis.
            if line and not line.startswith("%") and _RULE_LINE.match(line):
                rules.append(line)
        return rules

    @staticmethod
    def extract_learned_possible_adaptations(
            output: str,
    ) -> Optional[List[Tuple[int, List[Adaptation]]]]:
        """
        One FastLAS run's solution, in the shape the learners expect:
        a list of (score, adaptations) - here always a single entry, since
        FastLAS returns one solution per run.
        """
        rules = FastLASInterpreter.extract_learned_rules(output)
        if rules is None:
            return None
        if not rules:
            raise NoViolationException(
                "FastLAS returned an empty hypothesis: the learning problem is "
                "trivially solvable. If the spec is not realisable, this is a "
                "learning error.")
        return [(FASTLAS_SCORE, [Adaptation.from_str(rule) for rule in rules])]
