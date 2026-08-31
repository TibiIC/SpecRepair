# A repair that fails its own trace

Report date: 2026-08-28. Follows
[2026-08-26](2026-08-26-the-merge-cannot-repeat-itself.md).

The five-step pipeline ran on all 48 runs with results. An ordering comparison
then looked odd on two of them, and pulling that thread found a specification
that violates the trace it was repaired for - written out, merged, and
tabulated, with nothing anywhere saying so.

## What ran

The five-step pipeline - merge the assumptions, filter to the soft semantically
unique, broadcast, filter to the strongest, merge losslessly - completed on 45
runs. minepump 1, 2 and 4 are still going. Every completed run merges to **1**
except minepump trace 3, which gives **12** from 7,056 cores over a 79-formula
pool.

Three things had to be fixed before it would finish at all:

* **Step 4 was quadratic.** `five_step` grew its own all-pairs implementation of
  the strongest-guarantee filter while `filter_then_merge.py` already had an
  incremental one, O(n x |maxima|), threaded. The script's copy was defined
  inside the script, so the library could not reach it. Moved to
  `spec_repair/diagnosis/guarantee_filters.py`. Step 4's input on minepump trace
  1 is 12,881 specifications; all-pairs did not finish.
* **The hitting sets were brute force.** `set_util.all_minimal_hitting_sets`
  walks every subset of the universe in increasing size order. minepump trace 3
  finished its core enumeration with 7,056 cores over 79 formulas and then hung
  on `combinations(79, k)`. Replaced with a clingo encoding, checked against the
  brute force on six families rather than assumed equivalent.
* **Nothing but the final stage was kept.** Steps 1, 2 and 4 were computed,
  reported as counts and discarded, so any question about the middle of a run
  meant recomputing all of it. And `five_step_runner.sh` opened its log with
  `>`, so re-running minepump trace 3 destroyed the only record of its stage
  counts. Both fixed; every stage is now written out and the previous log is
  kept under its finish time.

## The repair that is not a repair

`minepump_liveness_trace1`'s merged specification still violated
`assumption3_1` - the assumption its own trace breaks:

    original               violates: assumption3_1 @ t=7, guarantee1_1 @ t=7
    five_step merge        violates: assumption3_1_0, _1, _9

The merge was not the culprit, only the messenger. Three of that run's
seventeen `final_specs` fail the trace themselves, and pooling their assumptions
put the violated formula back.

### Why a recorded repair can fail its trace

`bfs_repair_orchestrator` has two paths to `final_specs` and they disagree about
what a solution is.

| path | realisable | trace admitted |
| --- | --- | --- |
| `_record_if_solution`, for an exhausted branch | yes | **yes** |
| the main path, "no counter-examples" | yes | **never asked** |

`_is_solution` states the right condition in its docstring - "realisable, and its
assumptions are no longer violated by the violation trace" - and only the
fallback path calls it. Verification asks Spectra whether the *system* can be
forced to fail; it does not re-evaluate the violation trace against the new
assumptions. A weakening that misses the violation passes straight through.

### Why the learner proposed such a weakening

It should not be able to. `spec_0` is a genuine weakening - strictly weaker on
assumptions, `orig => spec_0` and not the converse - it just weakens the wrong
half of the formula.

`assumption3_1`'s antecedent is a disjunction, and the adaptation carries a
`disjunction_index` saying which disjunct to narrow:

    original   [0] highwater & PREV(!pump)     [1] highwater & !pump
    spec_0     [0] highwater & !pump           [1] (highwater & PREV(!pump)) & methane & !flag

The index was 0, so `_integrate_antecedent_exception` narrowed
`highwater & PREV(!pump)` and left `highwater & !pump` untouched. The t=7
violation comes through the untouched one. (The reordering is that function
removing the indexed disjunct and appending the narrowed version at the end.)

The index crosses a representation boundary - parsed out of the ASP rule the
learner returns (`adaptation_learned.py:50`), applied to the disjunct list of the
parsed LTL formula (`gr1_formula.py:156`) - so the first suspicion was that the
two orderings disagree. **They do not.** Dumping the encoder's own output for
this formula, checked 2026-08-29:

    antecedent_holds(assumption3_1,T,S) :- root(current,...,0), root(prev,...,1),
                                           not antecedent_exception(assumption3_1,0,T,S).
    antecedent_holds(assumption3_1,T,S) :- root(current,...,2),
                                           not antecedent_exception(assumption3_1,1,T,S).

Index 0 guards `highwater & PREV(!pump)` and index 1 guards `highwater & !pump`,
matching the LTL-side order exactly. The index was applied faithfully.

The actual problem is the shape of the encoding - and then, one level below
that, the way a solution is applied. `antecedent_holds` is derived by **one rule
per disjunct**, each guarded by its own `antecedent_exception`:

    antecedent_holds(assumption3_1,T,S) :- root(current,...,0), root(prev,...,1),
                                           not antecedent_exception(assumption3_1,0,T,S).
    antecedent_holds(assumption3_1,T,S) :- root(current,...,2),
                                           not antecedent_exception(assumption3_1,1,T,S).

So excepting one disjunct does not stop the antecedent holding; the other rule
still derives it unaided. A hypothesis that excepts only index 0 cannot cover
the example.

**And the learner never proposed one.** Dumping the antecedent-only task for
this formula and running it, checked 2026-08-29, every one of its ten optimal
solutions contains *two* rules, one per index:

    %% Solution 2 (score 6)
    antecedent_exception(assumption3_1,0,V1,V2) :- timepoint_of_op(current,V1,V1,V2); holds_at(flag,V1,V2).
    antecedent_exception(assumption3_1,1,V1,V2) :- timepoint_of_op(current,V1,V1,V2); not_holds_at(pump,V1,V2).

The task is right, the bias is right, and the hypothesis covers its example. The
solution is destroyed on the way in.

> **Correction, 2026-08-31.** That run used *ILASP*, not FastLAS - the output
> above is ILASP's `%% Solution N (score N)` format, and case study 3 runs
> FastLAS. `OptimisingSpecLearner` calls `run_ILASP` unconditionally, and
> instantiating it rather than `FastLASSpecLearner` ran the wrong solver. The
> conclusion holds - the defect is downstream of either solver, and the real
> FastLAS run agrees - but see
> [2026-08-31](2026-08-31-too-quiet-and-too-loud.md) and the captured
> artifacts under `tests/test_files/learning_tasks/minepump_liveness_trace1/`.

### The indices are numbered against a formula that no longer exists

Each rule's `disjunction_index` numbers the disjuncts of the antecedent *as the
encoder saw it*. `integrate_multiple` applied the adaptations one at a time, and
`_integrate_antecedent_exception` rewrote the antecedent each time - it removed
the indexed disjunct and appended the narrowed version at the end, then
`_normalize()` ran. By the time the second rule was applied, index 1 named a
different disjunct than the learner meant.

Applying Solution 2's two rules to the real formula, in each order:

    ORIGINAL   G(((highwater & PREV(!pump)) | (highwater & !pump)) -> next(highwater))
    0 then 1   G(( highwater & !pump                                    <-- untouched
                 | ((highwater & PREV(!pump)) & !flag) & pump) -> next(highwater))
    1 then 0   G((((highwater & !pump) & pump)
                 | ((highwater & PREV(!pump)) & !flag)) -> next(highwater))

Both adaptations were applied in both cases. In the order the search uses, the
second landed on the disjunct the first had already narrowed, and
`highwater & !pump` came through untouched - which is exactly `spec_0`, and
exactly the disjunct the t=7 violation fires through. The weakening was real,
strictly weaker, faithful to *an* adaptation, and silently not the one learned.

## What was done about it

* **The solution is applied in one pass.** `GR1Formula.integrate_all` takes a
  whole solution and resolves every antecedent exception against the *untouched*
  antecedent, then rebuilds it once, position by position - a disjunct nobody
  excepted is carried over unchanged, and a disjunct that was excepted is
  replaced in place by its narrowings. `integrate_multiple` groups by formula
  name and routes each group through it. The result no longer depends on the
  order the learner happened to list its rules in, and both orders of Solution 2
  now give the same, fully-narrowed formula. The single-adaptation
  `integrate` path is unchanged in behaviour; it is now a one-element batch.

* **The merge refuses to lose the trace.** `run_five_step` takes an `admits`
  predicate and uses it twice: as a filter on the input, dropping
  specifications the trace does not satisfy before anything is pooled, and as a
  gate on the output, raising `TraceNotAdmitted` rather than writing a
  specification that fails its own trace. The first is the substantive half - it
  makes step 1's safety argument true rather than assumed. That argument, as
  written on 2026-08-26, was that every input assumption admits the trace so
  their conjunction does; that premise is simply false for this pool.
* **The search stops recording them.** The main path now checks `_is_solution`
  too, so both paths agree, and a verified-but-unrepaired candidate is logged as
  `REJECT` instead of becoming a result. It is an ASP violation check, not a
  synthesis call, so it costs nothing per leaf.
* **Scope.** A sweep of all 45 merged runs found `minepump_liveness_trace1` to
  be the only one whose *merged* output was affected. It has been re-run under
  the gate and now admits its trace, dropping 3 of its 17 inputs on the way. How
  many `final_specs` across all runs fail their traces is a separate sweep, and
  is what decides which searches need re-running.

## Still open

* `pcar_trace4`'s merged specification admits its trace, yet the ordering
  comparison says its assumptions are equivalent to the original's. Those cannot
  both be right and the trace check is the more direct of the two.
* colorsort produced nothing again. Both 48g and 24g of heap came back rc=143 -
  SIGTERM from earlyoom - while the ~15.5GB default exhausts the JVM during
  synthesis. `-Xmx` bounds the Java heap while CUDD's tables are native and
  uncapped, so the knob does not control the total. There may be no setting that
  works on a 62GB shared box.
* genbuf is still absent from the atlas: `asm` and `gar` both hit the one-hour
  cap, since 81 guarantees make every implication check expensive even though
  its merged set is a single specification. Re-running with a twelve-hour cap,
  one trace per machine. Its trivial solutions never completed either, which is
  why the tables showed `NumT = 0` - now reported as `n/a`, because "not
  computed" and "none exist" are different claims.
