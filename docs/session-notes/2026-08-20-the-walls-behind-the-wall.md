# The walls behind the wall

Report date: 2026-08-20. Follows
[2026-08-18](2026-08-18-every-failure-was-one-failure.md).

genbuf produced no results for five days, and the reason turned out to be one
algorithm called from three places. Removing it from the first place exposed the
second, and the second exposed a third. Each is a real finding; none of them is
the same bug.

## Everything genbuf touches ends in `exploreAllCores`

`Checker$Memoize.lookupPos` walks every previously-checked subset calling
`isSubset`, so a check costs O(|memo| x n) with |memo| growing per check. On
genbuf's 81 guarantees it does not finish. Three call sites reach it:

| call site | what it blocked | fixed by |
| --- | --- | --- |
| `get_all_trivial_solutions_guarantee_only` | genbuf had no trivial solutions | MARCO, `--marco` |
| `filter_counter_traces` (verification) | genbuf 1/3/4 produced nothing at all | MARCO, `SPEC_REPAIR_MARCO_CORES=1` |

The verification one was settled by a stack dump rather than by inference.
genbuf trace 3, alive on gpu20 after 142 hours:

    "main" ... cpu=489246243.18ms      <- 136 hours of CPU
      at tau.smlab.syntech.cores.util.Checker$Memoize.isSubset(Checker.java:142)
      at tau.smlab.syntech.cores.util.Checker$Memoize.lookupPos(Checker.java:88)
      ... AllCoresPunchAlgorithm.computeCoresWithBase x24
      at cores.SpectraToolbox.exploreAllCores(SpectraToolbox.java:53)

All three traces sat in `verifying d1 candidate`, depth 0, node 1 - the *first*
candidate - having learned their 21 candidates in about a minute.

Re-run with MARCO cores, trace 1 cleared that verification in **~14 seconds**
and wrote a specification. The learner is unchanged at 31.8s; only the core
enumeration differs.

Both switches are opt-in. MARCO returns every core and each one minimal, which
is a *larger* union than Syntech's incomplete answer, so more counter-traces
survive the filter and results are not identical to the runs already finished.
Where Syntech's terminates the two agree - checked on gyro, same three names.

## The second wall: the games themselves

Traces 1 and 4 then spent over four hours each inside a single
`CUDDFactory.gr1Game0`. The cost moved out of the memoisation and into genuinely
hard BDD realisability games on the subsets the enumeration probes.

This corrects a measurement made earlier the same day. Realisability of genbuf
was timed at 2.8s on the full guarantee set, 0.2s on 80 of them, 0.1s on 40, and
read as showing that per-call cost was not a factor. Those were subsets of the
*original* specification; the subsets reached while verifying a weakened
candidate are far more expensive. The claim held for what was sampled, not for
what the enumeration asks.

Left running untouched rather than bounded.

## The third wall: one equivalence check, twenty-three hours

genbuf's two merges looked idle - the Python parent at 0.0% CPU - but the parent
was only waiting. Its `ltlfilt` child had been at 99.7% for 23 hours, on the
*first* comparison of the stage.

Not a deadlock: RUNNABLE, CPU tracking wall clock 1:1, RSS climbing 200-275MB/h
against 62.7GB of machine. Simply not converging.

What it was deciding: two specifications of shape `(assumptions) -> (guarantees)`,
28 atoms, 81 guarantee conjuncts each, differing in **three** conjuncts, each by
one variable substitution - `stateG12` for `stateG7_1`, `sLC1` for `btoS_ACK2`,
`stateG12` for `btoR_REQ1`.

Two changes, doing different jobs:

* `_equivalent_by_structure` proves equivalence cheaply where it can, via two
  standard reductions - `A1->B1 == A2->B2` if the sides match, `C&L == C&R` if
  `L == R`. Sound and one-directional, so failure proves nothing and the exact
  check still runs. On this pair: reordered guarantees proved equivalent in 5ms;
  the genuinely-different pair falls through in 74ms. It does not rescue this
  pair - a shortcut is not a decision procedure.
* `SPEC_REPAIR_EQUIV_TIMEOUT` bounds the exact check, raising
  `EquivalenceUndecided`. Unset, behaviour is unchanged. `filter_then_merge`
  counts undecided as *not* equivalent - the conservative direction, since it can
  only leave the pool larger than the truth, so no repair is dropped on an
  unanswered question. The stage line then reports an upper bound.

genbuf trace 0 merged **21 minutes** after restart, against 23 hours of nothing:

    stage 2  semantically unique  2  [upper bound: 1 equivalence check(s) hit ...]
    stage 3  merged               1

trace 2 finished at 17:32: 21 -> 21 -> 21 -> **1**, with all 210 equivalence
checks timing out. Its unique count is therefore an upper bound that establishes
nothing; its merge is real.

## `pkill` orphans the child

Killing the Python parent leaves its `ltlfilt` child running. One orphan from
the process killed on 2026-08-19 had been burning a core for **1 day 17 hours**,
owned by nothing. Kill the children by PID too, or they survive.

The same shape as the JVM surviving `tmux kill-session`, already in
`running-on-ssh.md`.

## Minepump is complete, and its merge is not minimal

All five traces merged:

| run | final | strongest_gar | unique | merged |
| --- | --- | --- | --- | --- |
| minepump_trace0 | 17 | 11 | 11 | **1** |
| minepump_trace1 | 26,877 | 296 | 54 | **50** |
| minepump_trace2 | 23,598 | 94 | 36 | **35** |
| minepump_trace3 | 23,201 | 120 | 45 | **40** |
| minepump_trace4 | 27,589 | 178 | 50 | **48** |

Every stage-0 count equals what is on disk now, so these are merges over the
complete pools, not stale snapshots.

The merged counts are not 1, and that needed checking. `merge_solutions` merges
pairwise left to right and splits in half whenever a conjunction comes out
unrealisable, so 54 -> 50 says the repairs largely over-constrain each other.
Sampling ten random pairs *of the fifty outputs* and merging each pair:

    8 of 10 stay split       - genuinely incompatible
    2 of 10 merge into one   - never tested together by the split strategy

So **50 is an upper bound, not the minimum**. The number is an artifact of the
order the strategy happens to try, and the same applies to 35, 40 and 48. Worth
saying explicitly before any of them goes in a table.

## Counts

| | |
| --- | --- |
| runs with results (colorsort excluded) | **48 of 50** |
| merged | **47 of 55** - all but colorsort 0-4 and genbuf 1/3/4 |
| trivial solutions | 51 of 55 |
| unique-from-final | 19 measured, rest running |

`semantically_unique` now reports progress every 60s. It printed nothing at all
before, so a stage that ran for 27 hours was indistinguishable from a hung one -
which is exactly what the four minepump unique-only runs were doing.
