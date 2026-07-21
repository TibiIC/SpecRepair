# The ColorSort Prev-boundary bug: a wrong fix, a revert, and the safe fix — session notes

Session date: 2026-07-21. Continuation of
[2026-07-20-enum-desugar-vs-native-multivalued-parser.md](2026-07-20-enum-desugar-vs-native-multivalued-parser.md).
Branches: `journal_final` (4 commits) and `spectra-rich-syntax-support`
(2 commits), both pushed to origin.

## Starting point

The previous session had left ColorSort out of scope on both branches: its
`<->`-desugared formulas crashed `to_dnf` with "Negation push-down for this
formula not implemented" whenever a conjunct containing `PREV(...)` needed
negating. You asked to see the actual failing formulas and, if `to_dnf`
looked fixable, to add exhaustive tests for it first (it had zero direct
test coverage — only exercised indirectly through `normalize_to_pattern`).

## Round 1: a plausible fix that was actually wrong

Added `!Next(x)===Next(!x)` and `!Prev(x)===Prev(!x)` as De Morgan
push-down rules in `to_dnf`, plus `Next(A|B)===Next(A)|Next(B)` /
`Prev(A|B)===Prev(A)|Prev(B)` distribution. Wrote 25 tests in a new
`TestToDnf` class covering literals, De Morgan, distribution, and the
Next/Prev cases specifically, cross-checked two ways: `spot.are_equivalent`
(via this repo's `SpotFormulaFormatter`) and a second, independently
implemented oracle (`satisfies_ltl_formula`, evaluating both forms on
concrete traces). Both agreed. Along the way also found and fixed a
genuine, unrelated bug: `satisfies_ltl_formula`'s `Prev` case computed its
result but never `return`ed it, always vacuously `False` — safe to fix
since its one production caller only ever evaluates at t=0, where the bug
never manifested.

Pushed further per your "keep pushing" instruction: fixed two more
`enum_desugar.py` gaps found along the way (enum-to-enum comparisons —
`detect=spec_currentColor`, `color=next(spec_currentColor)` — and an
exponential DNF blowup in the mutual-exclusion generator, both confirmed
independent of the Prev work). One ColorSort file
(`ColorSortLTL2_794_ColorSort_fixed.spectra`) then fully parsed and
matched the raw file's realizability — confirmed twice via the lighter
`realizable()` check.

## The correction

You asked to wire up a pure realizability check (no `--counter-strategy`
extraction, since the mutation-generator pipeline never reads the
counter-strategy) and then generate the stronger specification as a case
study. Implementing it — `SpectraGR1Oracle.is_realisable` now uses a new
`synthesise_check_realisability_only` (mirrors the existing
`synthesise_extract_counter_strategies` minus the flag; every existing
caller benefits automatically since the method's contract didn't change) —
let me check ColorSort's realizability *directly* rather than only via the
lighter cross-check that had already passed. It disagreed with the raw
file.

Tracing it down: three formulas differed between the raw desugared text
and the parsed-then-reserialized version, on 20,000+ random traces. All
three came from the `<->`-desugaring producing a negated
`PREV(...)`-containing conjunct — exactly the identity just added. Built a
minimal 2-variable reproduction (a spec with only `!(a&PREV(!a))` as its
one guarantee) and checked both forms directly against the real Spectra
CLI: the original was realizable, the "equivalent" `Prev`-pushed form was
not, on the exact same variables.

**The identity is false under real Spectra semantics.** `Prev` has a
genuine, unavoidable boundary at the very first state (t=0) — even a
forward-infinite realizability game has a first state with nothing before
it. `Next` has no equivalent boundary (there's always a next state), which
is why that half of the fix was fine. Spot said both `Prev` forms were
equivalent only because `SpotFormulaFormatter` renders `Prev` via a
shift-compensation trick that never models a t=0 boundary at all — a real
gap in what spot could tell me, not a flaw in the 25-test suite's logic
(saved as its own memory:
[[feedback_verify_ltl_identities_against_real_spectra]], since the lesson —
verify temporal-boundary identities against the actual tool, not just
internal oracles — applies well beyond this one case).

Reverted just the unsafe half on both branches (kept `!Next(x)===Next(!x)`
and the non-negation distributions, all independently re-verified against
the real CLI), updated the test suite to assert the correct behavior, and
reverted the ColorSort case-study addition.

## The safe fix

Rather than leaving `Prev` negation permanently unimplemented, reconsidered:
the unsafe move wasn't attempting a `to_dnf` rule for `!Prev(x)` — it was
*claiming an equivalent form* without checking it first. The safe
alternative: don't claim any equivalence at all. `to_dnf` now leaves
`!Prev(x)` as an opaque, terminal literal — the identity transformation,
which can never be wrong, unlike guessing a replacement. The one thing
still done proactively: `Prev(A|B)===Prev(A)|Prev(B)` doesn't cross the
t=0 boundary (independently verified safe), so if what's inside `Prev`
reduces to a disjunction, that gets pulled out first, and ordinary
(always-valid) De Morgan applies to the resulting `Or` of two now-separate
`Prev(...)` terms.

`is_conjunction_of_literals_and_temporals` was extended to recognize this
opaque `!Prev(x)` shape for its "at most one Prev per conjunct" check —
deliberately *not* added to `is_literal` itself, since that's used broadly
elsewhere and would silently bypass the same counting anywhere else it's
called. A conjunct with both a bare `Prev(a)` and a `!Prev(b)` has two
independent previous-timestep references that can't be safely merged
without the same false identity, so it's now correctly rejected rather
than undercounted — added a dedicated test for exactly this case.
`group_temporals_in_and` needed no changes: its existing fallback already
treats an unrecognized item as an opaque literal.

Verified both new code paths against the real Spectra CLI again before
trusting them: the exact ColorSort `<->`-expansion shape, and the
`Prev`-of-disjunction distribution case separately. Both matched. Re-ran
`ColorSortLTL2_794`: it fully parses and matches realizability via
`SpectraGR1Oracle.is_realisable` directly (not just the lighter check),
and the full case-study test — generating mutations and violation traces —
passes in ~16 seconds, down from 8+ minutes and a Java heap
`OutOfMemoryError` under the old always-`--counter-strategy` path.

## What's in each branch now

**`journal_final`** (4 commits): the `to_dnf` fix and 25-test suite; the
`enum_desugar.py` fixes (enum-to-enum comparisons, non-exponential mutual
exclusion, duplicate-name disambiguation); the revert of the unsafe
`Prev` identity with updated tests; the safe opaque-literal fix, its
verification, and `ColorSortLTL2_794` added as a case study
(`input-files/case-studies/spectra/colorsort/ideal.spectra`,
`test_generate_stronger_specs_colorsort`).

**`spectra-rich-syntax-support`** (2 commits): the same revert and safe
fix to `to_dnf`/`is_conjunction_of_literals_and_temporals` — this branch
never had the `TestToDnf` suite, so no test file changes were needed there,
just the underlying code. Corpus-scan success count against the 258-file
SYNTECH corpus stayed at 90/258 throughout this whole arc (unaffected by
either the bug or its fixes).

The other 2 of ColorSort's 3 desugar-successful files remain out of scope:
blocked by a hand-expanded 3-argument custom pattern with an explicit
internal state machine (`spec_state=S0/S1`), likely
`pBecomesTrue_betweenQandR` per the reference the native-parser branch's
corpus scan turned up. Reverse-engineering its semantics (like `respondsTo`
was, in the previous session) would be a separate, larger undertaking —
not attempted.

All 136 tests pass on `journal_final` (101 on `spectra-rich-syntax-support`,
which lacks the new `TestToDnf` suite). Both branches pushed to origin.
