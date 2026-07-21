# Enum-to-boolean desugaring vs. native multi-valued parser — session notes

Session date: 2026-07-20/21. Two branches, one commit each.

## Why the split

The `journal_final` branch is paper-scoped: mostly done, just adding case
studies. You were explicit that letting real multi-valued/enum support grow
in place there would "bloat the work significantly more" and force reworking
the paper, since it needs "a very in-depth change" to the spec-repair
components. So the ask was two tracks, kept deliberately apart:

1. **`journal_final`** — mechanical enum-to-boolean desugaring only, no
   parser changes, no new modeling capability.
2. **`spectra-rich-syntax-support`** — a new, separate branch, free to
   extend `SpectraSpecification`'s actual semantics to understand
   multi-valued domains natively. Backwards compatibility best-effort, not
   a priority.

## `journal_final` — automated desugar-to-boolean, two new case studies

Commit `c15a354`.

`spec_repair/diagnosis/enum_desugar.py` automates what elevator and gyro
(the two prior case studies) had been hand-translated with: enum-typed
variables become N-1 boolean indicator variables plus explicit
mutual-exclusion constraints, `respondsTo(trigger, response)` inlines to
`G(trigger->F(response))`, and `next(...)` gets distributed over any
disjunction it winds up wrapping. Also added `A<->B => (A&B)|(!A&!B)`
desugaring, recursing into nested parens since `<->` almost always sits
inside the enclosing temporal operator's own parens rather than at the
formula's textual top level.

Ran it across all 258 files in `files/SYNTECH15/17/19` (~40 module
families). Only Elevator, GyroAspect (already case studies), ColorSort,
Humanoid, and PCar have any file that desugars cleanly — everywhere else
uses `import`, `predicate`, `Int(...)`, `monitor`, or `define`, real new
modeling capability out of scope for a mechanical rewriter. **Humanoid and
PCar** both fully succeed (desugar, parse, and match the raw file's
realizability via direct Spectra CLI) and are now case studies alongside
elevator and gyro.

**ColorSort was left out.** 3 of its files get past desugaring and `<->`
but crash in `to_dnf` ("Negation push-down for this formula not
implemented") — negating a conjunct containing `PREV(...)` needs DNF
negation-pushdown through temporal operators, which `to_dnf` didn't support
at the time. Fixing it means touching shared normalization logic used by
every case study's formula parsing; deliberately not attempted on this
branch for what might be 3 near-duplicate variants of one case study,
given the low regression tolerance here.

Also found and removed genuinely dead code: `distribute_next`/
`_push_next_into`, an earlier AST-level attempt at the same next-over-or
distribution that ended up superseded by the text-level version actually
used in `enum_desugar.py`. Reverted before committing.

All 9 case-study tests in `tests/test_main/test_mutated_spec_generator.py`
pass, including the two new ones.

## `spectra-rich-syntax-support` — native multi-valued parser

Commit `fc2dcd1`, branched from a point identical to `main` (pre-existing
branch name, apparently set up in advance for exactly this purpose — there
was also an older, abandoned `enum` branch with a prior attempt at
something adjacent, renaming `SpectraSpecification`→`SpectraBooleanSpecification`
and adding ASP/ILASP enum encoders, ending mid-way on a bug; not built on,
per your choice).

Turned out `AtomicProposition(name, value)` already supported arbitrary
(not just boolean) values, and `SpectraFormulaFormatter` already
round-tripped them as `name=value` — the gap was declaration parsing and
domain tracking, not the formula representation. So the actual scope came
out much narrower than expected:

- `SpectraAtom` gained a `domain: Optional[List[str]]` field.
  `SpectraSpecification` now parses `type X = {A,B,C};` aliases and inline
  `env {A,B,C} name;` declarations, resolving named-type var decls against
  the alias table.
- Fixed two structural bugs in `SpectraSpecification.__init__` that were
  **not enum-specific**: formula bodies spanning multiple lines were
  silently truncated to just the next line, and assumption/guarantee
  headers with no `-- name` were silently dropped entirely (any unnamed
  formula in *any* file was being lost, not just enum ones). Added comment
  stripping too, since a commented-out line containing `--` was previously
  misread as a real header.
- Added `!=` to the tokenizer, `<->` as a proper infix operator built
  directly as AST (composes correctly under nesting, unlike a text-level
  rewrite would), `next(var)=value`/`prev(var)=value` (equality applied to
  the operator's *result*, the other spelling used interchangeably in the
  corpus alongside `next(var=value)`), and a `respondsTo(trigger,
  response)` pattern-call translation — the only custom pattern actually
  used across the corpus.
- Fixed the same `to_dnf` negation-pushdown gap ColorSort hit on
  `journal_final`, properly this time: `!Next(x)===Next(!x)`,
  `!Prev(x)===Prev(!x)`, and `Next(A|B)===Next(A)|Next(B)` (needed because
  De Morgan through a negated conjunct produces an `Or` that has to
  distribute back out of the temporal wrapper). Safe to fix here since this
  branch can absorb the regression risk that made it out-of-scope on
  `journal_final` — validated against all 26 existing `ltl_formula_util`
  tests plus the full corpus scan.
- Removed `formula_string_util.py`'s `enumerate_spec`: a dead, and actually
  semantically incomplete (no mutual-exclusion constraints), prior
  boolean-desugaring-of-enums helper that was never reachable end-to-end
  since no enum file could previously parse at all.

**Corpus result:** native parsing goes from 0 files (nothing with enums
could parse before) to **90/258**. Elevator alone: 1/23 under
`journal_final`'s boolean-desugar approach vs. **22/23** natively — strong
evidence native parsing is a fundamentally better fit for this corpus than
desugaring, once the object model actually supports it.

**Realizability spot-checks** (round-tripped native parse vs. raw file via
direct Spectra CLI): Junction and Irrigation families matched. A full
90-file cross-check was attempted but the JVM-backed synthesis calls proved
too slow/heavy to run at that scale in this environment — repeatedly killed
regardless of foreground/background handling. Settled for a smaller sample
plus reuse of `journal_final`'s existing 4-file validation (elevator,
gyro, humanoid, pcar) as corroborating evidence.

**A real caveat found via that spot-checking, not fixed:** some files
reference types declared in a companion file via `import` (explicitly out
of scope, matching `journal_final`'s stance). These parse *syntactically*
through this branch's parser — the unresolved type name is kept as an
opaque, `domain=None` value_type — but aren't guaranteed
realizability-checkable standalone, since the type is never actually
resolved from the single file. One ATM file demonstrated this directly:
round-tripping it back through the Spectra CLI failed with "Couldn't
resolve reference to TypeDef 'Response'".

**Remaining failure buckets**, unaddressed: custom pattern calls other than
`respondsTo`, `Int(...)`-typed arithmetic/comparisons, `predicate`/
`monitor` blocks, and some structurally unrecognized GR1 formula shapes in
`normalize_to_pattern`. These are real new modeling capability or a bigger
`normalize_to_pattern` redesign, not mechanical parsing gaps — the kind of
"very in-depth change" to the spec-repair components you flagged as
longer-term, out of scope for this session.

All 101 tests across `test_main/test_mutated_spec_generator.py`,
`test_helpers/test_spectra_formula_parser.py`,
`test_helpers/test_spectra_specification.py`, and
`test_util/test_ltl_formula_util.py` pass (1 pre-existing skip, unrelated).
