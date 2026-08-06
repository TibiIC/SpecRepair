# Why merging repairs reconstructs the original specification

Investigation date: 2026-07-31 (overnight, following the 2026-07-30 session).

**Short version.** Merging a set of repairs can produce a specification whose
assumptions are semantically **equivalent to the unrepaired original**. It is
not that the merge reinstates the original formula — the original is not in the
merged set at all. It is that the learner emits several weakenings of the same
formula by adding alternative disjuncts, and when some of those disjuncts are
**jointly unsatisfiable**, conjoining them annihilates the weakening and
restores exactly what it weakened.

Affects **4 of 9** strengthened case studies (elevator, humanoid, lift, pcar)
and **2 of 7** trace-violation ones. Two independent sources; one is fixable at
trace generation, the other is not, and needs a fix in the merge.

## The question

The 2026-07-30 report noted that ILASP's merged output "implies FastLAS's on
assumptions", and that elevator's merge was equivalent to `strong.spectra` on
both sides. The stated acceptance criterion is:

> assumptions weaker (to satisfy the violation), and the spec realisable

Equivalent-on-guarantees is expected and fine. Equivalent **on assumptions** is
not — that is the side that has to weaken for the trace to be admitted.

## It is not formula reinstatement

The obvious hypothesis — the merge pulls the original strong formula back in
from repairs that did not touch it — is **wrong**. Elevator's merged assumption
set does not contain the original formula anywhere:

```
strong.spectra:
  stopped_implies_floor_known    G((!elevMot_fwd & !elevMot_bwd) -> floor_upper)

merged — 9 variants, none of them the above:
  _0  G(((!fwd & !bwd) & elevMot_fwd)   -> floor_upper)
  _1  G(((!fwd & !bwd) & !floor_middle) -> floor_upper)
  _2  G((!fwd & !bwd) -> (floor_upper | X(!floor_middle)))
  _3  G((!fwd & !bwd) -> (floor_upper | X(floor_middle)))
  _4  G((!fwd & !bwd) -> (floor_upper | X(floor_lower)))
  _5  G((!fwd & !bwd) -> (floor_upper | !floor_lower))
  _6  G((!fwd & !bwd) -> F(floor_upper))
  _7  G((!fwd & !bwd) -> (floor_upper | X(!floor_lower)))
  (base) G((!fwd & !bwd) -> (floor_upper | X(!floor_upper)))
```

All 16 elevator repairs are individually **strictly weaker** than
`strong.spectra` on assumptions — checked, none vacuous. The repairs are sound.
**The merge is what destroys them.**

## The mechanism

Take variants `_2` and `_3`:

```
(floor_upper | X(¬floor_middle)) ∧ (floor_upper | X(floor_middle))
  ≡ floor_upper | (X(¬fm) ∧ X(fm))
  ≡ floor_upper | false
  ≡ floor_upper                        <- the original formula, restored
```

Merging `spec_10` and `spec_11` **alone** is enough to make the assumptions
equivalent to `strong.spectra`. That is a two-file minimal reproduction.

Only 3 of elevator's 120 pairs collapse — but the pipeline merges all 16, so one
is enough.

## Two independent sources of joint unsatisfiability

This is the part that took a wrong turn first (see below), so it is worth
stating carefully. The added disjuncts need only be **jointly unsatisfiable
given the rest of the specification** — not syntactically complementary. Two
distinct sources:

### (a) Both polarities of the same literal

```
elevator  X(!floor_middle)        / X(floor_middle)
humanoid  X(!inputMoveMode_fwd)   / X(inputMoveMode_fwd)
pcar      X(sideSense_p_o)        / X(!sideSense_p_o)
```

This arises when the violation is at the trace's **final timepoint**. `X(...)`
then evaluates on the weak final timepoint, where every atom both holds and does
not, so `X(p)` and `X(¬p)` are *both* valid escapes and the learner records
both. Over infinite traces they are genuinely distinct, genuinely weaker
specifications — the learner is not wrong to emit them.

### (b) A mutually exclusive variable family

```
elevator  X(floor_middle) / X(floor_lower)     -- floor_mutual_exclusion
lift      f1              / X(b1)              -- unsatisfiable in context
```

Here the disjuncts are all *positive*, and unsatisfiable jointly only because
the specification itself says the family is mutually exclusive. The learner
enumerates one disjunct per family member, which is exactly what makes the pair
available.

This is why **arbiter and gyro do not collapse**. Their added disjuncts range
over independent variables:

```
arbiter   (!g1 & !r2),  X(a),  !g2,  !g1        -- all jointly satisfiable
gyro      !balancer_turn_right,  X(isReady)     -- jointly satisfiable
```

No mutually exclusive family to enumerate over, so no unsatisfiable pair.

## The wrong turn, and the controlled experiment that caught it

The initial hypothesis was that source (a) was the whole story, giving a clean
predictor and an easy fix: *violation at the final timepoint*. The correlation
looked convincing —

| Violation position | Runs | Collapses |
|---|---|---|
| at the final timepoint | 10 | 4 |
| strictly before the end | 7 | **0** |

— 7 out of 7 clean, and the recommendation wrote itself: pad the traces.

**The controlled experiment refutes it.** Elevator's traces 1-4 violate the same
assumption at timepoint 0 but run 2-3 timepoints, so the violation is not last.
Re-running repair against trace 1 isolates exactly that variable:

| | repairs | with `next` | full merge |
|---|---|---|---|
| trace 0 — violation AT end | 16 | 5 | **collapsed** |
| trace 1 — violation BEFORE end | 14 | 3 | **collapsed** |

The 7/7 correlation was confounding across case studies, not causation within
one.

But the experiment is not a dead loss — it separates the two sources cleanly.
The `next` disjuncts the learner produced:

| | next-disjuncts | variables in both polarities |
|---|---|---|
| trace 0 | `next(floor_lower=false/true)`, `next(floor_middle=false/true)`, `next(floor_upper=false)` | `floor_lower`, `floor_middle` |
| trace 1 | `next(floor_lower=true)`, `next(floor_middle=true)`, `next(floor_upper=true)` | **none** |

**Padding the trace eliminated source (a) exactly as predicted** — with a real
timepoint following the violation, only the polarity matching the trace is a
valid weakening, so no complementary pair is ever learned. It collapsed anyway,
via source (b): `next(floor_upper)` and `next(floor_lower)` cannot both hold
because floors are mutually exclusive.

So trace padding is a real improvement that fixes half the problem, and is not
sufficient on its own.

## Consequences

1. **For elevator, humanoid, lift and pcar the pipeline's final answer is a
   specification whose assumptions are equivalent to the unrepaired original.**
   `unique_max_merged_specs` holds one spec, and on the assumption side it is
   `strong.spectra`. Read off the implication graph, that is "no repair
   happened".
2. **Two oracles disagree, and both are right.** `spot`/`implies` says the merge
   is equivalent to strong, because over infinite traces the added disjuncts
   cancel. The ASP `get_violations` check says the merge admits the trace,
   because on the finite prefix the disjuncts are individually satisfiable. The
   merged spec is realisable too. **It passes every check the pipeline applies
   while being, semantically, the specification we started from.**
3. **Nothing currently tests the property that matters.** Realisable: yes.
   Admits the trace: yes. Assumptions strictly weaker: *no* — and unchecked.

## Recommendations

1. **Assert the invariant.** *(implemented)* After merging, check the result is
   strictly weaker than the original on assumptions. One spot call, catches both
   sources and anything else of this shape — it converts a silent wrong answer
   into a visible one.

   `warn_if_merge_undid_the_weakening` in `spec_repair/diagnosis/solution_merging.py`,
   called from `merge_solutions` whenever an `og_spec` is supplied. Verified: it
   fires on elevator and stays silent on gyro. A **warning**, not an exception,
   matching the existing `check_weakens_original` — the merge is not wrong, it is
   just not a repair, and callers studying the solution space may still want it.

   Note the pipeline only passes `og_spec` under `--og-spec-from-case-study`, so
   the check is off by default. Making that flag the default is a one-line change
   and probably right, but it changes pipeline behaviour so I left it alone.
2. **The weakest-merge variant.** When two formulas are comparable, keep the
   weaker instead of conjoining. This makes the collapse *structurally
   impossible* rather than merely detected, and is the only proposal here that
   addresses source (b). Caveat from the 2026-07-30 discussion: weaker
   assumptions make guarantees harder to realise, so it may fragment more.
3. **Prefer traces with a timepoint after the violation.** Confirmed to remove
   source (a), and cheap — the generator already produces such traces, it just
   does not require them. Worth doing on its own merits (it also stops the
   learner enumerating weakenings that only weaken at the weak timepoint), but
   it is not a fix on its own.
4. **Redundancy elimination does not fix this**, though it is worth having.
   Skipping formulas already entailed by the target is semantics-preserving —
   elevator's merged spec goes from 15 formulas to about 5, so output gets
   smaller, cheaper and readable — but the survivor of a comparable pair is the
   stronger formula, which is the problem.

## Where to look

| | |
|---|---|
| Minimal reproduction | `tests/test_files/out/repair_syn/elevator_2026-07-30/final_specs/spec_10.spectra` + `spec_11.spectra` |
| Compare against | `input-files/case-studies/spectra/strengthened/elevator/strong.spectra` |
| Formula | `stopped_implies_floor_known` |
| Source (b) reproduction | `tests/test_files/out/repair_trace_syn/elevator_trace1_2026-07-31/final_specs/spec_5.spectra` + `spec_7.spectra` |
| Merge implementation | `spec_repair/model/spectra_specification.py::merge` (syntactic union) |

```python
from spec_repair.model.spectra_specification import SpectraSpecification as S
from spec_repair.ltl_types import GR1FormulaType as T
D = 'tests/test_files/out/repair_syn/elevator_2026-07-30/final_specs'
m = S.from_file(f'{D}/spec_10.spectra').merge(S.from_file(f'{D}/spec_11.spectra'))
strong = S.from_file('input-files/case-studies/spectra/strengthened/elevator/strong.spectra')
print(m.implies(strong, T.ASM) and strong.implies(m, T.ASM))   # True
```

## Two unrelated findings

**Step 6 can hang indefinitely.** A `run_experiment_pipeline.py --setup
trace_violation` invocation was found still running after **2h12m**. Not the
merge — every merge in it had completed. It was stuck in
`visualise_resulting_specs.py` drawing colorsort's `gr1` graph, in spot
equivalence checks over colorsort's boolean-expanded state space. The 2026-07-30
work made the merge terminate; the graph step is a separate unbounded cost centre
on the same case study. `--skip-graph` avoids it; a per-graph timeout would be
better.

**Run directories split across midnight.** The elevator trace-1 run above landed
in `elevator_trace1_2026-07-31` because `cls.date_str` is read per test process.
A sweep spanning midnight will scatter across two date directories, and
`run_learner_comparison.py` — which computes its date once at the start — will
report `final_specs=0` for anything that crossed over. It reported correctly for
all 40 runs of the 2026-07-30 sweep, checked explicitly.
