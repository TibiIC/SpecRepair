# The translation cliff, and all eleven case studies — session notes

Session date: 2026-09-08. Three days after the searches were stopped, nothing is
wedged — every remaining job is alive and burning CPU. But GenBuf is behaving
unlike every other case study, and chasing that produced the cliff that explains
it, ColorSort's long-standing zero specifications, and the fact that the
experiment is eleven case studies rather than the four the re-run covered.

Continues [2026-09-04](2026-09-04-stopping-the-non-terminating-searches.md).

## The symptom that does not fit

GenBuf trace 2's post-processing has spent **three days on 21 specifications**.
AMBA's 21 specifications took about 35 minutes. Same stage, same count, same
pipeline. And AMBA is the *bigger* case study:

| | original size | variables | formulas |
| --- | ---: | ---: | ---: |
| AMBA | 37,030 B | 34 | 63 |
| GenBuf | 14,342 B | 24 | 109 |
| Gyro | 1,571 B | 6 | 12 |
| Minepump Liveness | 606 B | 4 | 9 |

So it is not size. Sampling the live `ltlfilt` on gpu22 showed a single
comparison running 24 minutes on a formula of **1,327 bytes with 2 justice
goals**. That is a tiny formula. Something about it is pathological.

## It is not the repair

First guess was that the learned exceptions were the problem. They do look
overfitted — GenBuf's weakenings attach arbitrary conjunctions of unrelated
signals, e.g. `stoB_REQ2`'s exception mentions `stateG12`, and `stoB_REQ3`'s
mentions `btoR_REQ0`:

```
G(((stoB_REQ2 & !btoS_ACK2) -> (X(stoB_REQ2) | (((stateG12 & stoB_REQ1) & stoB_REQ3) & stoB_REQ4))))
```

I stripped all five learned disjuncts back to the unrepaired form and timed both
through `ltl2tgba`. **Both time out at 120s.** The exceptions are not the cause —
GenBuf's *original* assumptions are already beyond translation.

(The exceptions still look like overfitting and are worth their own look. They
are just not what is costing the days.)

## What it actually is

Translating the conjunction to an automaton is exponential in the number of
top-level conjuncts. Bisecting GenBuf's assumption conjunction, taking the first
*k* of its 28 conjuncts:

| conjuncts | automaton states | translation |
| ---: | ---: | ---: |
| 15 | 28 | 0.07s |
| 18 | 163 | 0.18s |
| 20 | 487 | 0.87s |
| 21 | 730 | 2.03s |
| 22 | 1,459 | 10.51s |
| 23 | 2,188 | 23.97s |
| 28 | — | **>300s** |

States double per conjunct; time grows about 2.4× per conjunct. The cliff sits
between 20 and 23 conjuncts, and it is sharp.

Every case study measured against that cliff — `ltl2tgba` on the original
specification's assumption and guarantee conjunctions:

| Case study | ASM conjuncts | ASM translate | GAR conjuncts | GAR translate |
| --- | ---: | ---: | ---: | ---: |
| Minepump Liveness | 4 | 0.33s (11 states) | 5 | 0.02s (3 states) |
| Gyro | 4 | 0.02s (5 states) | 8 | 0.03s (4 states) |
| AMBA | 8 | 0.10s (9 states) | 55 | **timeout** |
| GenBuf | **28** | **timeout** | **81** | **timeout** |

This is the whole story, and it lines up exactly with which runs finish.

## Why AMBA survives its own untranslatable guarantees

AMBA's GAR conjunction has 55 conjuncts and does not translate either — yet
AMBA's `gar` graphs drew fine in 35 minutes. That looked like a contradiction,
so I checked it.

The 21 AMBA final specifications are 21 distinct files, but their **guarantee
formulas are byte-identical** — 27,421 bytes, the same in every one. AMBA's
repairs weaken assumptions only and never touch the guarantees. So every GAR
comparison hits Spot's syntactic fast path and returns in **0.04s** without ever
building an automaton. The formula being untranslatable never comes up.

That also explains the six-hour `gr1` hang from 09-04. `gr1` is
`(assumptions) -> (guarantees)`, so the two sides are coupled and the specs
*differ* on the assumption side. The syntactic shortcut no longer applies, Spot
has to build the automaton for the 55-conjunct guarantee formula, and it does not
come back.

## Why GenBuf does not survive

GenBuf is the one case study where the formula that **changes** is also the one
that is **too big to translate**. Its repairs weaken assumptions, its assumption
conjunction is 28 conjuncts, and so no comparison can take the fast path. Every
semantic operation — the visited-set check in the search, `are_equivalent` in
post-processing step 2, every edge of every graph — needs a translation that does
not terminate in any useful time.

That is why GenBuf sits at node 1 for days: it is not stuck in a loop, it is
waiting on an automaton that will not finish. The 133% CPU is Spot and the JVM
doing real work on an intractable input.

So the two bottlenecks in this experiment are now fully separated:

* **Gyro, Minepump Liveness** — formulas translate in milliseconds. What kills
  them is the O(V²) visited-set scan from Part 2. Python-side, fixable.
* **GenBuf** — the O(V²) scan is irrelevant; it never gets far enough to matter.
  What kills it is exponential LTL-to-automaton translation on a 28-conjunct
  assumption set. Not fixable by touching the dedup.
* **AMBA** — sits on the boundary and only passes because its repairs happen to
  leave the large formula untouched. That is luck, not headroom: any repair that
  touched AMBA's guarantees would put it in GenBuf's position.

## What follows from this

Semantic comparison by automaton translation does not scale to GenBuf, and AMBA
only clears it on a technicality. Bigger machines and longer waits will not
change that — the curve above is exponential, and GenBuf is five conjuncts past
where it goes vertical.

If GenBuf has to be in the results, the comparison has to stop going through
whole-specification translation — comparing formula-by-formula rather than
conjunction-to-conjunction would keep every individual translation small, at the
cost of a weaker (sound but incomplete) notion of equivalence. That is a
methodology decision, not a bug fix, so it is not one I have made.

The alternative is honest and cheap: report GenBuf as out of scope for semantic
post-processing, with the conjunct-count table above as the reason.

## All eleven case studies, not four

The atlas showed four case studies, which was wrong as a picture of the
experiment. There are **eleven**, and 55 runs. Only AMBA, GenBuf, Gyro and
Minepump Liveness appear in the 2026-08-29 re-run because the disjunction bug
only invalidated those 18 runs; the other seven were never re-run and their
latest results are from **2026-08-13**.

Those seven have valid searches. What they do not have is comparable
post-processing: the 08-13 runs went through the pre-2026-08-18 pipeline, which
merged before filtering and wrote `merged_specs/` rather than `unique_specs/`.
Their stage counts are marked *old* in the atlas rather than silently mixed in
with the 08-29 numbers.

### The root-node finding holds across all 55 runs

| | runs | complete | of those, past depth 0 |
| --- | ---: | ---: | ---: |
| all case studies | 55 | 28 | **0** |

Every one of the 28 complete runs terminated at `Explored 1, Depth 0`. Adding
seven more case studies did not produce a single counter-example. Elevator, Lift
and Traffic Updated finish all five traces in under a minute each — and all of
them at the root node.

The stopped runs are worse than the 08-29 four suggested. PCar 4 ran **238
hours** and was stopped with **263,266** nodes queued, at depth 2. Traffic Single
3 ran 303 hours. PCar's four unfinished traces each sit above 200,000 queued.

### ColorSort is past the translation cliff, and that explains the zero specs

ColorSort has produced **zero** specifications on every trace of every date, and
that has been open since July. Measuring it against the cliff:

| Case study | ASM conjuncts | ASM translate | GAR conjuncts | GAR translate |
| --- | ---: | ---: | ---: | ---: |
| Traffic Single | 3 | 0.02s | 2 | 0.02s |
| Elevator | 2 | 0.02s | 5 | 0.02s |
| Minepump | 3 | 0.02s | 3 | 0.02s |
| Gyro | 4 | 0.02s | 8 | 0.03s |
| PCar | 4 | 0.02s | 5 | 0.02s |
| Minepump Liveness | 4 | 0.33s | 5 | 0.02s |
| Traffic Updated | 5 | 0.02s | 4 | 0.02s |
| AMBA | 8 | 0.10s | 55 | **timeout** |
| Lift | 11 | 0.03s | 7 | 0.02s |
| **ColorSort** | **25** | **timeout** | **52** | **timeout** |
| **GenBuf** | **28** | **timeout** | **81** | **timeout** |

ColorSort and GenBuf are the only two case studies whose *assumptions* are past
the cliff, and they are precisely the two that return nothing and sit at node 1
in `verifying d1 candidate` — ColorSort for 20 minutes to 2 hours before being
stopped, GenBuf for days. Same signature, same cause: waiting on an automaton
that does not arrive.

That is a much better answer than "ColorSort produces no specs". It produces no
specs because it cannot complete a single semantic comparison, and no amount of
waiting or memory changes that. It also predicts the fix is the same one GenBuf
needs — comparison that does not go through whole-specification translation.

Note the ordering: it is the **assumption** conjunct count that decides. AMBA has
a worse guarantee formula than ColorSort (55 vs 52) and still runs, because AMBA's
repairs never touch its guarantees. Lift has 11 assumption conjuncts, more than
AMBA's 8, and is entirely fine — the cliff is between 20 and 23, and nothing sits
in that gap.

### Post-processing launched for the six runs that had no graphs

Minepump 1–4 (23,201–27,589 specs) and Traffic Single 1 and 3 (55,145 and
15,504) had no graphs at all. Post-processing is now running for all six, one per
box on gpu01/04/05/06/20/21, against their 2026-08-13 output. ColorSort is
skipped: there is nothing to post-process.

These are step-2 bound in exactly the way Part 2 describes, and Traffic Single 1
at 55,145 specifications is larger than anything that has finished. They are not
quick.

## The pre-merge guarantee view, and what it shows

A fourth graph now sits beside the existing three:
`implication_graph_gar_with_unique_min.png`. It is the guarantees-only view with
a fourth group added — the strongest-guarantee survivors of step 3, *before* the
merge collapses them. **36 drawn, no failures.**

### Naming

The strongest guarantee formula admits the *fewest* infinite traces, so it is
semantically **minimal**, not maximal — consistent with Cavezza's weakness
measure, where a larger value means a weaker formula and the strongest sits at
the minimum. The directories still read `max_unique_specs/`; only the graph
labels use the correct name.

| graph group | on disk | stage |
| --- | --- | --- |
| `original` | `original.spectra` | the specification being repaired |
| `trivial` | `trivial_solutions/` | the floor |
| `unique_min` | `max_unique_specs/` | step 3, pre-merge |
| `unique_min_merged` | `filtered_merged_specs/` | step 4, post-merge |

Renaming the directories through the pipeline and the five-step code is a
separate change, not made here — it would invalidate paths mid-experiment.

### min_unique generated where it was missing

The 2026-08-13 runs never had `max_unique_specs/`, because the pre-2026-08-18
pipeline wrote different directories. Generated for 21 runs: Elevator 0–4,
Lift 0–4, Traffic Updated 0–4, Traffic Single 0/2/4, PCar 1. The searches were
not re-run; only steps 2–4.

**`unique` and `min` came out identical in all 21.** The minimal-guarantee filter
removed nothing. It only bites on PCar (161→67, 96→65) and Gyro (33→24, 37→29,
37→26).

### What the view says: on guarantees, the merge absorbs nothing

In every run drawn, the `unique_min` solutions sit in the *same equivalence
bubble* as the original and the merged result. Gyro 0 puts 24 of them there;
PCar 0 puts 67 — the largest pre-merge set in the experiment, and the one with
the biggest `unique`→`min` drop.

So collapsing 24 or 67 solutions to one loses no guarantee distinction, because
there was none. All the variation between distinct repairs lives on the
**assumption** side.

That also explains why `unique == min` almost everywhere: with equivalent
guarantees, no solution is strictly stronger than another, so the minimal filter
has nothing to drop. It is not that step 3 is broken — it is that the guarantee
dimension is degenerate for these repairs, and step 3 is correctly reporting so.

It also means the "everything merges to exactly 1" result from Part 9 is less
alarming than it looked: on guarantees the solutions really are one
specification. Whether that holds on the assumption side is the open question,
and it needs the same view drawn for `asm`.

### A bug of mine, caught before publishing

Trivial solutions are stored two ways: **per run** (`all/pcar_trace0`) for the
2026-08-12 and 08-13 sets, and **per case study** (`all/pcar`) for 08-22 and
08-29. My first script only looked for the second form, so all 22 graphs from
the 08-13 runs silently dropped the trivial group — no error, just a missing
group and a three-entry legend. Fixed to try the run directory first and fall
back to the case study, the order `run_experiment_pipeline.py` itself uses; the
22 were deleted and redrawn.

Worth noting for the tables: **AMBA and GenBuf have no trivial solutions at
2026-08-29** — that date's set covers arbiter, colorsort, elevator, gyro,
humanoid, lift, minepump, minepump_liveness, pcar and traffic only. Their new
graphs legitimately carry three groups, matching their existing `gar` graphs.

Atlas: <https://claude.ai/code/artifact/2fb2b369-3b4e-48e1-bfec-7f0f1ecae76b>

Continued in [2026-09-09](2026-09-09-the-pre-merge-views.md).
