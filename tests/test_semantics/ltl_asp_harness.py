"""
Compare the ASP encoding of a formula against its LTL meaning on a finite trace.

The ASP semantics and the LTL semantics are supposed to agree: a formula is
violated by a trace under the encoding exactly when the trace does not satisfy
the formula. This module runs both sides and hands the test a comparable answer.

Two oracles, deliberately:
  * `asp_violated_names`  - encodes the spec with the real `NewSpecEncoder` and
    asks clingo which expressions the trace violates.
  * `ltl_violated_names`  - evaluates each formula directly with
    `satisfies_ltl_formula`, the repo's finite-trace evaluator.

Neither is trusted over the other. A test asserts they agree, and a divergence
is reported with the formula, the trace, and both verdicts, because a divergence
is the interesting output of this suite rather than an inconvenience.

Boundary conventions of the LTL side, which are what the ASP is being checked
against (`ltl_formula_util.satisfies_ltl_formula`):

    Next(f)  at the last timepoint  -> False
    Prev(f)  at timepoint 0         -> False

so `!next(a)` is True at the end while `next(!a)` is False, and likewise for
prev at the start. Those are exactly the cases the `weak_timepoint` guards in
the ASP exist to handle, and exactly where the two sides may part company.
"""
from __future__ import annotations

import re
from typing import Dict, List, Sequence, Set

from spec_repair.components.new_spec_encoder import NewSpecEncoder
from spec_repair.model.spectra_specification import SpectraSpecification
from spec_repair.wrappers.asp_wrappers import get_violations

TRACE_NAME = "trace_name_0"

# A trace is a list of states; a state is the set of atoms true at that instant.
Trace = Sequence[Set[str]]


def trace_to_asp(trace: Trace, atoms: Sequence[str], name: str = TRACE_NAME) -> List[str]:
    """
    A trace as the `holds_at`/`not_holds_at` facts the encoder expects.

    Every atom is stated at every timepoint - the encoding has no notion of an
    atom being unconstrained, so leaving one out would silently change the
    formula's meaning rather than leave it open.
    """
    lines: List[str] = []
    for t, state in enumerate(trace):
        for atom in atoms:
            fact = "holds_at" if atom in state else "not_holds_at"
            lines.append(f"{fact}({atom},{t},{name}).")
        lines.append("")
    return lines


def spec_text(formulas: Dict[str, str], env: Sequence[str], sys: Sequence[str],
              module: str = "SemanticsProbe") -> str:
    """
    A Spectra module holding `formulas`, given as {name: spectra_formula}.

    A name beginning `asm` becomes an assumption, anything else a guarantee, so
    a case can put a formula on either side without a second argument.
    """
    lines = [f"module {module}", ""]
    lines += [f"env boolean {a};" for a in env]
    lines += [f"sys boolean {a};" for a in sys]
    lines.append("")
    for name, body in formulas.items():
        kind = "assumption" if name.startswith("asm") else "guarantee"
        lines += [f"{kind} -- {name}", f"\t{body};", ""]
    return "\n".join(lines)


def asp_violated_names(spec: SpectraSpecification, trace: Trace,
                       atoms: Sequence[str]) -> Set[str]:
    """Which expression names clingo reports as violated by `trace`."""
    asp = NewSpecEncoder.encode_ASP(spec, list(trace_to_asp(trace, atoms)), [])
    raw = get_violations(asp)
    names: Set[str] = set()
    for line in raw:
        names.update(re.findall(r"violation_holds\(([^,]+),", line))
    return names


def evaluate(f, trace: Trace, t: int = 0):
    """
    Three-valued LTL on a finite PREFIX of an infinite behaviour.

    Returns True, False, or None for "unknown" - the prefix does not determine
    it, and some completions satisfy while others refute. A formula counts as
    violated only when this returns False, i.e. *every* completion refutes it.
    That is the claim the ASP encoding makes, and `weak_timepoint` is how it
    makes it.

    Two-valued logic cannot express this. Treating an unknown `next(a)` as True
    is right in a consequent (it leaves the formula unrefuted) and wrong in an
    antecedent (it fires a rule that might not fire, inventing a violation).
    The same unknown has to mean different things by position, which is exactly
    what Kleene's three-valued connectives do for free.

    Where unknown arises:
        Next(f) at the last timepoint  -> None, the next state is unseen
        Eventually(f) unmet by the end -> None, a later state could satisfy it

    `Prev(f)` at timepoint 0 is False, not None, and that asymmetry is real: a
    prefix starts at the beginning of the behaviour, so there is no unseen
    earlier state. The past is closed; only the future is open.

    This deliberately does not reuse `ltl_formula_util.satisfies_ltl_formula`,
    which drops the `value` field of an `AtomicProposition` and so evaluates
    every negated atom backwards - the Spectra parser encodes `!a` as
    `AtomicProposition(a, value=False)`, not `Not(...)`. Nothing in the package
    calls that function, so the bug is latent, but it cannot be ground truth
    for a suite about negation.
    """
    from py_ltl.formula import (AtomicProposition, Not, And, Or, Implies, Next,
                                Prev, Eventually, Globally, Top, Bottom)

    def k_not(x):
        return None if x is None else not x

    def k_and(xs):
        xs = list(xs)
        if any(x is False for x in xs):
            return False                      # one false settles it
        return None if any(x is None for x in xs) else True

    def k_or(xs):
        xs = list(xs)
        if any(x is True for x in xs):
            return True                       # one true settles it
        return None if any(x is None for x in xs) else False

    match f:
        case AtomicProposition(name=name, value=value):
            return (name in trace[t]) == value
        case Not(formula=inner):
            return k_not(evaluate(inner, trace, t))
        case And(left=l, right=r):
            return k_and([evaluate(l, trace, t), evaluate(r, trace, t)])
        case Or(left=l, right=r):
            return k_or([evaluate(l, trace, t), evaluate(r, trace, t)])
        case Implies(left=l, right=r):
            return k_or([k_not(evaluate(l, trace, t)), evaluate(r, trace, t)])
        case Next(formula=inner):
            if t + 1 >= len(trace):
                return None
            return evaluate(inner, trace, t + 1)
        case Prev(formula=inner):
            return False if t == 0 else evaluate(inner, trace, t - 1)
        case Eventually(formula=inner):
            vals = [evaluate(inner, trace, j) for j in range(t, len(trace))]
            if any(v is True for v in vals):
                return True
            return None                       # could still happen later
        case Globally(formula=inner):
            return k_and([evaluate(inner, trace, j) for j in range(t, len(trace))])
        case Top():
            return True
        case Bottom():
            return False
        case _:
            raise NotImplementedError(f"oracle does not handle {type(f).__name__}")


def ltl_violated_names(spec: SpectraSpecification, trace: Trace) -> Set[str]:
    """
    Which formulas the prefix DEFINITELY refutes.

    Only a hard False counts. An unknown is not a violation - some completion
    of the prefix still satisfies the formula.
    """
    states = [set(s) for s in trace]
    violated: Set[str] = set()
    for name, formula in formulas_of(spec):
        if evaluate(formula.to_ltl_formula(), states, 0) is False:
            violated.add(name)
    return violated


def formulas_of(spec: SpectraSpecification):
    """(name, GR1Formula) pairs. The spec keeps them in a DataFrame."""
    df = spec._formulas_df
    return [(row["name"], row["formula"]) for _, row in df.iterrows()]


def describe(trace: Trace, atoms: Sequence[str]) -> str:
    """A trace as `t0: a,!b` lines, for a failure message worth reading."""
    out = []
    for t, state in enumerate(trace):
        cells = [(a if a in state else "!" + a) for a in atoms]
        out.append(f"    t{t}: " + " ".join(cells))
    return "\n".join(out)
