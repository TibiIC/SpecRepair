# The merge cannot repeat itself

Report date: 2026-08-26. Follows
[2026-08-24](2026-08-24-the-pool-was-never-the-search-space.md).

The pipeline's last step merges the surviving specifications and extracts every
realisable one by unrealisable-core enumeration and minimal hitting sets. The
question was whether its output needs a semantic-uniqueness filter afterwards.
It does not: the output is semantically unique already, and it is worth proving
because the proof turns into a test that catches three separate bugs.

## The pipeline this is about

1. merge the assumptions of every solution into one set
2. filter to the *soft semantically unique* specifications by guarantees - for
   each formula in one there is an equivalent formula in the other; where two
   are soft-equivalent the one with more formulas is dropped, since it carries a
   formula equivalent to another of its own
3. broadcast the step-1 assumptions to the survivors; the count is unchanged
4. filter to the strongest specifications by guarantees; several are typically
   incomparable
5. merge those, and extract the realisable specifications by cores and minimal
   hitting sets

## Step 1 is exact, not approximate

Discarding an assumption that is equivalent to, or weaker than, another kept
assumption is lossless for the conjunction: if `A => B` then `A & B == A`. So
the merged assumption set is semantically identical to the full conjunction,
and the "lossy" discard costs nothing.

Two things make step 1 unconditionally safe:

* **It cannot break realisability.** Stronger assumptions ask the system to
  handle fewer environments. Measured: all 173 merged specifications across
  minepump traces 1-4 stay realisable when re-assumed with their pooled set.
* **It cannot exclude the violating trace.** Every input assumption admits the
  trace, so the trace satisfies their conjunction. One line, no measurement.

The discard should compare formulas of the same type only - an invariant may
retire a weaker invariant, but not a justice goal. Mathematically the type does
not matter; `A & B == A` regardless. It matters because Spectra's realisability
is **not** a purely semantic function (see below), so removing a justice goal
that an invariant happens to imply can change the verdict even though it cannot
change the meaning. Same-type comparison keeps the GR(1) structure the tool is
actually sensitive to.

## Step 5 output is semantically unique

Fix the merged assumptions `A*`. Let `E` be the pooled guarantee formulas, and
for `S` a subset of `E` write `<S>` for the specification `(A*, /\S)` and `R(S)`
for "`<S>` is realisable". Two premises:

* **(P1) semantic** - `R` depends only on the meaning of `/\S`: if
  `/\S == /\S'` then `R(S) = R(S')`.
* **(P2) monotone** - adding guarantees can only remove realisability.

Step 5 returns the maximal realisable subsets: the complements of the minimal
hitting sets of the unrealisable cores.

> **Theorem.** Distinct maximal realisable subsets denote semantically distinct
> specifications. If `S1 != S2` are both maximal realisable, then
> `/\S1 !== /\S2`.

**Proof.** Suppose `/\S1 == /\S2`. Both are maximal by inclusion, so neither is
a proper subset of the other; with `S1 != S2` there is some `x` in `S2 \ S1`.
From `x` in `S2` we get `/\S2 => x`, and by assumption `/\S1 => x`, so

    /\(S1 + {x}) ==  /\S1 & x  ==  /\S1

`S1` is realisable, so by **(P1)** `S1 + {x}` is realisable. But `x` is not in
`S1`, so `S1 + {x}` strictly contains `S1`, contradicting the maximality of
`S1`. []

Two consequences worth reporting alongside it:

* **Step 5 never loses ground on step 4.** Every input's guarantee set is a
  realisable subset of `E`, and every realisable subset extends to a maximal
  one, so each step-4 specification is contained in - hence no stronger than -
  some step-5 output. Merging can only strengthen.
* **Duplicates are a bug detector.** If step 5 emits two equivalent
  specifications then one premise failed: the subsets were not maximal (an
  incomplete core enumeration - the hitting-set argument needs *every* core,
  each minimal), or **(P1)** failed.

## (P1) is false for Spectra, and we have the witness

Same assumptions in both, `!h & !m`, `G((PREV(p) & p) -> X!h)`,
`G(p -> (!h | !m))`, guarantee `!p` in both:

| | guarantees | Spectra |
| --- | --- | --- |
| A | `G(h->Xp) & G(m->X!p)` | **unrealisable** |
| B | `G(h->Xp) & G(m->(X!p\|Xm)) & G(m->(X!p\|Xh)) & G(m->F X!p)` | **realisable** |

spot says `A == B`, and so does the hand proof: if `m(t)` and `p(t+1)`, the two
disjunctive guarantees force `m(t+1) & h(t+1)`, `G(h->Xp)` forces `p(t+2)`, and
by induction `p` holds forever, contradicting `G(m -> F X!p)`. Verified on
Linux with CUDD, not only under the macOS JTLV fallback.

So the theorem holds of the mathematics and can fail in the implementation,
precisely when a response-shaped `G(a -> F b)` is present. A duplicate in step 5
should raise suspicion of that before it raises suspicion of the merge.

## A claim withdrawn

Earlier notes argued that step 4's strongest-guarantees filter must not gate the
merge, because it deletes the only carrier of a formula the merge needs. That
argument is **wrong as stated and is withdrawn.** Domination compares the
*conjunction* of guarantees, so a dominator implies every formula the dominated
specification held. No semantic content is lost.

The weaker claim that survives is that a dominated specification is *more
combinable*, since its dominator is stronger and realisability is antitone. That
is possible in principle, and it reproduces at formula level with real formulas
from the pool - `g2_orig` strictly dominates `g2_0`, yet `{g1_0, g2_0}` is
realisable and `{g1_0, g2_orig}` is not.

It has **not** been reproduced for whole-specification domination, which is what
step 4 actually does. `spec_17284` has five strict dominators in the pool, all
realisable, and merging either it or `spec_23808` against an intact
`guarantee1_1` specification leaves both unrealisable. Two attempts, no
difference. Treat the objection as unproven, and the pipeline as written as
sound until someone produces the instance.

## Where the runs stand

All four directed minepump runs were stopped. In 26 hours they produced no
maximal subsets: traces 2 and 3 spent 98% of their time waiting on clingo, whose
`#maximize` over ~1,100 atoms slowed from 2.5 cores a minute to one every 85
minutes as constraints accumulated; traces 1 and 4 spent theirs inside Spectra,
at roughly a quarter of an hour per call on specifications of thousands of
guarantees. trace4 managed four cores in 25 hours.

The block-deletion shrink is the one change that held: 27 checks per core
instead of 1,126, a 190-fold improvement in discovery rate that simply exposed
the next two walls.
