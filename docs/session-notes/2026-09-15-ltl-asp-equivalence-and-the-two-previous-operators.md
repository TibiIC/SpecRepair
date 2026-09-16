# LTL/ASP equivalence, and why there are two previous operators — session notes

Session date: 2026-09-15. Building a test suite to ask whether the ASP encoding
means the same thing as the LTL formula it came from. The answer is yes, but
only once "the same thing" is stated precisely — and getting there required
three corrections to the oracle, turned up two gaps in the translation, and
ended in the past-LTL literature.

Continues [2026-09-10](2026-09-10-filter-then-merge-and-a-status-script.md).

## What the encoding actually computes

The naive framing — "does the ASP agree with LTL on this trace?" — is wrong, and
it is wrong in a way that produced 15 spurious failures before I noticed.

A violation trace is a **finite prefix of an infinite behaviour**, not a finite
model. The encoding reports a violation only when the prefix *definitely
refutes* the formula, i.e. when every infinite extension of it violates. That is
a strictly weaker claim than "the finite trace fails to satisfy", and the two
differ in exactly two places:

* `next` at the last instant — the next state is unseen
* every liveness obligation — `F b` unmet within the prefix could still be met
  after it

`G` needs no special treatment: a counterexample *inside* the prefix is final,
because no extension can repair a violation that already happened. That is why
`run_experiment_pipeline`'s ASP has `weak_timepoint` guards on `next`/`prev` and
nothing analogous on `always`, and it is correct not to.

### Two-valued logic cannot express it

The first repair I attempted was to make the oracle treat an unknown `next` at
the last instant as *true* ("unrefuted"). That fixed eight of nine failures and
broke on the ninth, `G(next(a) -> b)`:

| position | what "unknown `next(a)`" must mean | why |
| --- | --- | --- |
| consequent | **true** | the prefix has not refuted the obligation |
| antecedent | **false** | the rule might not fire, so the prefix has not *forced* a violation |

The same unknown has to denote opposite things depending on polarity. That is
the signature of a missing third value, and Kleene's strong three-valued logic
K3 gives it for free: `∧` is false if any conjunct is false (regardless of
unknowns), `∨` is true if any disjunct is true, and `¬` maps unknown to unknown.
Violation is then "evaluates to **false**", with unknown explicitly not a
violation.

With K3 the oracle and the ASP agree on every one of the 90 cases. So the
theorem the encoding actually satisfies is:

> For a finite prefix π and a supported formula φ, the ASP derives
> `violation_holds(φ)` iff φ evaluates to **false** under K3 three-valued LTL on
> π, where `Next` past the end and unfulfilled `Eventually` evaluate to unknown.

`Prev` at t=0 is **not** unknown in that statement, and that asymmetry is the
subject of the rest of this note.

## The two previous operators

The past is not the mirror of the future, and conflating them is the single
most expensive mistake available here.

A prefix is open on the right and **closed on the left**: t=0 is the actual
first instant of the behaviour, not a window onto unseen earlier states. So
`next` past the end is genuinely unknown, while `prev` at t=0 is genuinely
determined — there is nothing before the beginning, and that is a fact about the
behaviour rather than a limitation of the prefix.

Past-LTL therefore has **two** primitive previous operators, not one:

| operator | at t = 0 | at t > 0 | names |
| --- | :---: | --- | --- |
| **Y** φ | **false** | φ held at t−1 | "yesterday", strong previous, ⊖ |
| **Z** φ | **true** | φ held at t−1 | "weak yesterday", "before", ⊖̃ |

They agree everywhere except the first instant, and they are **duals**:

```
¬Y φ  ≡  Z ¬φ
¬Z φ  ≡  Y ¬φ
```

Neither is definable from the other without the boundary case, which is why
both are primitive. The standard references are Lichtenstein, Pnueli & Zuck,
*"The Glory of the Past"* (Logics of Programs, 1985), which introduces the past
fragment, and Manna & Pnueli, *The Temporal Logic of Reactive and Concurrent
Systems: Specification* (1992), which defines ⊖ and ⊖̃ explicitly. I am recalling
those definitions rather than reading them; the wording should be checked before
either is cited in the thesis.

### Spectra's PREV is Y — measured, not assumed

The valuation Spectra gives its own `PREV` is the load-bearing fact, and it is
not documented anywhere I could find. It is, however, directly measurable
through realizability. Two minimal specifications, `a` a **system** variable so
the system has full control of it:

```
module PrevControl        module PrevAtZero
sys boolean a;            sys boolean a;
guarantee G(a);           guarantee G(PREV(a));
```

Run through the Spectra CLI:

| specification | realizable |
| --- | --- |
| `G(a)` | **true** |
| `G(PREV(a))` | **false** |

The control shows the system can hold `a` true forever, so `G(a)` is trivially
realizable. `G(PREV(a))` then requires `PREV(a)` at **every** instant including
t=0. The system already demonstrably controls `a` at every instant from 0
onward, so the only proposition it cannot make true is `PREV(a)` at t=0. Hence:

> **Spectra evaluates `PREV(φ)` to false at t = 0.** Its `PREV` is Y, the strong
> previous operator. There is no `Z` in the surface language.

Note what this does *not* say. It does not say Spectra's traces are finite —
Spectra's game is forward-infinite, and `next` never meets a boundary there at
all. The t=0 boundary is real in an infinite game too, which is precisely why
`next` and `prev` are not symmetric:

```
¬X φ  ≡  X ¬φ     valid in Spectra: the future never runs out
¬Y φ  ≢  Y ¬φ     invalid: the past does, exactly once, at t=0
```

`to_dnf` in `ltl_formula_util.py` already encodes both of these correctly — it
pushes negation through `Next` and refuses to push it through `Prev` — and the
comment there records the same realizability experiment being used to establish
it. This note supplies the name for what was measured: the missing rewrite is
not missing, it is *inexpressible*, because the correct dual `Z ¬φ` needs an
operator the language does not have.

### The valuation table, from the encoding

Probed against the GR(1) ASP with a marker atom isolating one instant, and
cross-checked against the K3 oracle. They agree on every cell:

| previous state | `PREV(x)` | `!PREV(x)` | `PREV(!x)` |
| --- | :---: | :---: | :---: |
| does not exist (t=0) | F | **T** | **F** |
| exists, x = T | T | F | F |
| exists, x = F | F | T | T |

One cell of difference, and it is the whole story.

## Gap A: the refusal is sound but too strong

`!PREV(x) & PREV(y)` cannot be normalised, because `to_ednf` cannot merge two
independent prev-references into one conjunct and the result is not EDNF. The
author confirms this is a gap rather than intended behaviour.

The interesting part is that the rewrite is **valid**, and the duality says why.
`Y(y)` is false at t=0 for every `y`. So in the conjunction:

```
¬Y(x) ∧ Y(y)   at t=0   =  T ∧ F  =  F
Y(¬x ∧ y)      at t=0   =           F
```

The positive `Y(y)` conjunct forces falsity at t=0 on **both** sides, masking
the single cell where Y and Z part company. At t > 0 the two forms are
identical by distribution. Hence:

> `¬Y(A) ∧ Y(B) ≡ Y(¬A ∧ B)` whenever the conjunct contains at least one
> positive `Y` term.

Verified exhaustively: **0 differences over 228 (trace, timepoint) pairs**.

So closing Gap A does not require representing two prev-references. It requires
a narrower rule: *when grouping prevs, if any positive `Prev` is present, absorb
the negated ones into it*. The existing opaque treatment remains correct and
necessary for the case where `!Prev(x)` stands alone or with only non-prev
literals — there, the dual really is `Z`, and it really is inexpressible.

Caveat before acting: this is verified against our ASP and our oracle, which
agree with each other. The standing instruction is to cross-check
temporal-boundary rewrites against the real Spectra CLI, because spot and a
trace-oracle have previously agreed on a *false* `!Prev` identity. That check has
not been done for this rewrite.

## Gap B: fixed

`!(a->b)` raised `NotImplementedError: Negation push-down for this formula not
implemented`. It should flatten to `a & !b`, which is valid EDNF, so the form is
inside the intended grammar and merely unimplemented.

Added to `to_dnf`'s negation push-down:

```python
if isinstance(formula, Implies):
    return to_dnf(And(formula.left, Not(formula.right)))
```

Purely propositional — the implication carries no temporal operator of its own,
so nothing crosses the t=0 boundary and this needs none of the care the `Prev`
case does. Any `Prev` inside either operand is reached by the recursive calls
and handled by the rules that already exist. The positive direction
(`to_dnf(Implies) -> to_dnf(Or(Not(left), right))`) was already present; only
the negated one was missing.

Regression check: **686 existing tests pass**. Three failures in
`tests/test_util/test_spec.py` are pre-existing `FileNotFoundError`s on
`./test_files/...` — those tests assume `tests/` as the working directory and
have nothing to do with `to_dnf`.

## A latent bug in the obvious oracle

`ltl_formula_util.satisfies_ltl_formula` cannot be used as ground truth:

```python
case AtomicProposition(name=name, value=value):
    return name in trace[t]          # value is bound and never read
```

The Spectra parser encodes `!a` as `AtomicProposition(a, value=False)` rather
than `Not(...)`, so **every negated atom evaluates backwards**. Nothing in the
package calls the function, so no result is affected, but it is the natural
thing to reach for and it is wrong. The suite carries its own K3 evaluator
instead, and the docstring explains why rather than leaving the next person to
rediscover it.

## The grammar, corrected

What the translation supports is what `normalize_to_pattern` can **convert**,
not what is already canonical. Probing `is_ednf` alone gave a far narrower
answer than the truth. Six top-level shapes:

```
EDNF | EDNF -> EDNF | G(EDNF) | G(EDNF -> EDNF)
     | G(EDNF -> F(EDNF)) | G(F(EDNF))
```

`F` appears only under `G`; bare `F(φ)` and `φ -> F(ψ)` are both rejected. EDNF
is a disjunction of conjunctions of literals, each conjunct carrying at most one
`next(...)` and one `prev(...)`, each wrapping a *conjunction* of literals
rather than a single atom.

The input language is much wider than that canonical form, because `to_ednf`
applies De Morgan, distribution and temporal grouping first: `next(a)&next(b)`
becomes `next(a&b)`, `!(a&b)` becomes `!a|!b`, `(a|b)&c` distributes, and
`!next(a)` becomes `next(!a)`. That last rewrite is sound for the reason above —
the future never runs out — and the suite confirms it on every trace.

A regex cannot express this grammar: balanced parentheses are not regular, and
"at most one next and one prev **per disjunct**" is a counting constraint.
`is_pattern(formula)` is the check; string matching is not.

## What was built

| file | contents |
| --- | --- |
| `tests/test_semantics/ltl_asp_harness.py` | K3 evaluator, spec/trace builders, clingo bridge |
| `tests/test_semantics/test_ltl_asp_equivalence.py` | 90 cases over the GR(1) encoding |
| `tests/test_semantics/ltlf_ext_harness.py` | formulas, traces and reference evaluator for `ltl2asp_ext.asp` |
| `tests/test_semantics/test_ltlf_asp_ext.py` | 116 cases over the structural encoder |
| `files/until_semantics/prev_rules.asp` | `prev`/`weakprev` rules, with the Y/Z reasoning |
| `files/until_semantics/ltlf_testkit.py` | interactive table over the same harness |

**206 passed, 2 xfailed** — the xfails being Gap A, kept as documentation of a
known gap so that a *new* divergence breaks the build rather than hiding among
known ones.

The GR(1) suite runs each case against **exhaustive** traces where the space is
small (64 traces of length 3 over two atoms). The `ltl2asp_ext` suite issues one
clingo solve per (formula, semantics) with every trace in the same program and
compares the whole `sat` set, which is both faster — 116 tests in 3.3s — and a
better failure message, since it names the traces wrongly accepted *and* wrongly
rejected instead of stopping at the first.

Two of the prev tests assert structure rather than values, because the values
alone would not catch the mistakes that matter: that `Y` stays `Y` under both
future semantics (it must not be wired to the `semantics(strong|weak)` toggle,
which would silently turn it into `Z`), and that `¬Y(a) ≡ Z(¬a)` while
`¬Y(a) ≢ Y(¬a)`. If those two ever agree, the t=0 boundary has stopped being
modelled and every argument in this note collapses.

## Open

* Gap A's narrow rewrite is identified but not implemented, and wants the
  Spectra CLI cross-check before it is.
* The `ltl2asp_ext.asp` `prev` tests pass against `prev_rules.asp`, which
  supplies rules the encoder does not have yet. When it grows them, drop
  `with_prev=True` so the tests exercise the real implementation.
* Whether Spectra offers any surface syntax for `Z` is unknown. If it does not,
  a specification language built on it simply cannot state `¬Y φ` in normalised
  form, and that is a limitation worth stating explicitly rather than working
  around.
