"""
What a learner is allowed to do, decided once and never mutated.

This is the half of the old heuristic manager that was never a heuristic. A
heuristic narrows a search that would still be correct without it; these flags
decide what counts as an admissible repair, which is a property of the
methodology.

Keeping them in `IHeuristicManager` had three concrete problems:

* **One object, every learner.** `BFSRepairOrchestrator._initialise_repair`
  assigned its own manager to every learner at the start of each run, so a flag
  set for the assumption learner could not mean anything different for the
  guarantee learner. The knobs read as per-learner configuration while being
  global.
* **Mutated mid-run, then reset.** Selecting one weakening operator at a time
  meant deep-copying the manager, flipping flags on the copy, and handing it to
  the encoder - three times per learning step. What a learner was configured to
  do depended on when you asked.
* **Fixed at two learners.** Nothing was wrong with two, but nothing supported
  a third either.

A `LearningConfig` is frozen. Narrowing it returns a new one, so the
configuration a learner was built with is still exactly what it was at the end
of the run, and two learners can differ without either knowing about the other.

`is_enabled` is kept so `NewSpecEncoder` and the heuristic managers can ask the
same question they always asked - the answer is now immutable rather than
whatever the last mutation left behind.
"""
from dataclasses import dataclass, replace
from typing import FrozenSet, Iterable

from spec_repair.ltl_types import GR1TemporalType

# The weakening operators a learner may apply.
ANTECEDENT_WEAKENING = "ANTECEDENT_WEAKENING"
CONSEQUENT_WEAKENING = "CONSEQUENT_WEAKENING"
INVARIANT_TO_RESPONSE_WEAKENING = "INVARIANT_TO_RESPONSE_WEAKENING"
WEAKENING_OPERATORS = (ANTECEDENT_WEAKENING, CONSEQUENT_WEAKENING,
                       INVARIANT_TO_RESPONSE_WEAKENING)

# Temporal-operator atoms the learner may introduce into a weakened formula.
INCLUDE_NEXT = "INCLUDE_NEXT"
INCLUDE_PREV = "INCLUDE_PREV"
TEMPORAL_ATOMS = (INCLUDE_NEXT, INCLUDE_PREV)


@dataclass(frozen=True)
class LearningConfig:
    """
    One learner's policy: which weakenings it may apply, over which formulas.

    :param operators: weakening operators this learner may use.
    :param temporal_atoms: temporal atoms it may introduce (next/prev).
    :param learnable_when: temporal types of formula it may weaken. INITIAL is
        absent by default and should stay absent: weakening an initial
        assumption drags system variables into it, which Spectra's CLI rejects
        outright, and it changes which states the system may start in - the
        realisability question itself rather than an answer to it.
    """

    operators: FrozenSet[str] = frozenset(WEAKENING_OPERATORS)
    temporal_atoms: FrozenSet[str] = frozenset()
    learnable_when: FrozenSet[GR1TemporalType] = frozenset(
        {GR1TemporalType.INVARIANT, GR1TemporalType.JUSTICE})

    def is_enabled(self, flag: str) -> bool:
        """Answer the question the old heuristic manager answered."""
        return flag in self.operators or flag in self.temporal_atoms

    def may_learn(self, when: GR1TemporalType) -> bool:
        return when in self.learnable_when

    def with_only(self, *operators: str) -> "LearningConfig":
        """
        The same policy, narrowed to these operators.

        Returns a new config rather than mutating: a learning step runs one
        operator at a time, and the learner's own configuration must not be a
        casualty of that.
        """
        return replace(self, operators=frozenset(operators) & self.operators)

    def enabling(self, *flags: str) -> "LearningConfig":
        """The same policy, plus these flags, on whichever axis they belong to."""
        ops = set(self.operators) | {f for f in flags if f in WEAKENING_OPERATORS}
        atoms = set(self.temporal_atoms) | {f for f in flags if f in TEMPORAL_ATOMS}
        unknown = set(flags) - set(WEAKENING_OPERATORS) - set(TEMPORAL_ATOMS)
        if unknown:
            raise ValueError(f"Unknown learning flags: {sorted(unknown)}")
        return replace(self, operators=frozenset(ops), temporal_atoms=frozenset(atoms))

    @staticmethod
    def from_flags(flags: Iterable[str] = ()) -> "LearningConfig":
        return LearningConfig().enabling(*flags)
