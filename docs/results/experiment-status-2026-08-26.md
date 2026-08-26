# Case study 3: what ran, on which pipeline, and what is missing

Snapshot 2026-08-26 15:30. Experiment date `2026-08-13`, learner `fastlas`,
55 runs (11 case studies x 5 traces). Supersedes
[2026-08-19](experiment-status-2026-08-19.md), which predates the merge work and
records only one pipeline.

**48 of 55 runs have results. 9 of 11 case studies are complete.** The two that
are not are colorsort (0 of 5) and genbuf (3 of 5), and they fail for unrelated
reasons.

## Which pipeline produced a result

This is the column the earlier report did not have, and it matters: three
different merges have been used, and they do not answer the same question.

| pipeline | what it does | runs |
| --- | --- | --- |
| **greedy** | `merge_solutions`: filter to unique and strongest, then conjoin pairwise left to right, splitting when unrealisable | **47** |
| **maximal** | merge first, by enumerating maximal realisable subsets of the pooled guarantees | **2** |
| **directed** | descend from the original's unrealisable cores, weakening only what a core implicates | **0** (4 in flight) |

Every number in the `merged` column below except two came from the greedy
merge, and the greedy merge is order-dependent. Its outputs are an upper bound
and carry artifacts - see [Caveats](#caveats).

## Status

`final` is the specifications the search wrote; `merged` is the merge output and
which pipeline produced it; `uff` is unique-from-final, the count the paper
reports as "unique". A dash is a stage never run for that run.

| run | final | interm | merged | pipeline | uff | search |
| --- | --- | --- | --- | --- | --- | --- |
| `amba_trace0` | 21 | — | 1 | greedy | — | done |
| `amba_trace1` | 21 | — | 1 | greedy | — | done |
| `amba_trace2` | 21 | — | 1 | greedy | — | done |
| `amba_trace3` | 21 | — | 1 | greedy | — | done |
| `amba_trace4` | 21 | — | 1 | greedy | — | done |
| `colorsort_trace0` | **0** | — | — | — | — | ❌ dead |
| `colorsort_trace1` | **0** | — | — | — | — | ❌ dead |
| `colorsort_trace2` | **0** | — | — | — | — | done, no repair |
| `colorsort_trace3` | **0** | — | — | — | — | done, no repair |
| `colorsort_trace4` | **0** | — | — | — | — | ❌ dead |
| `elevator_trace0` | 21 | — | 1 | greedy | 16 | done |
| `elevator_trace1` | 21 | — | 1 | greedy | — | done |
| `elevator_trace2` | 21 | — | 1 | greedy | 15 | done |
| `elevator_trace3` | 21 | — | 1 | greedy | 7 | done |
| `elevator_trace4` | 21 | — | 1 | greedy | 16 | done |
| `genbuf_trace0` | 2 | 1 | 1 ↑ | greedy | — | ❌ dead |
| `genbuf_trace1` | 2 | 4 | **1** | **maximal** | — | ⏳ gpu03 |
| `genbuf_trace2` | 21 | — | 1 ↑ | greedy | — | done |
| `genbuf_trace3` | **0** | — | — | — | — | ⏳ gpu11 |
| `genbuf_trace4` | **0** | 1 | — | — | — | ⏳ gpu13 |
| `gyro_trace0` | 100 | 9 | 1 | greedy | 36 | ❌ dead |
| `gyro_trace1` | 120 | 9 | 1 | greedy | 53 | ❌ dead |
| `gyro_trace2` | 111 | 9 | 1 | greedy | 40 | ❌ dead |
| `gyro_trace3` | 98 | 12 | 1 | greedy | 41 | ⏳ gpu16 |
| `gyro_trace4` | 143 | 16 | 1 | greedy | 42 | ❌ dead |
| `lift_trace0` | 21 | — | 1 | greedy | 11 | done |
| `lift_trace1` | 21 | — | 1 | greedy | — | done |
| `lift_trace2` | 21 | — | 1 | greedy | 16 | done |
| `lift_trace3` | 21 | — | 1 | greedy | 17 | done |
| `lift_trace4` | 21 | — | 1 | greedy | 9 | done |
| `minepump_trace0` | 17 | — | **1** | **maximal** | 6 | done |
| `minepump_trace1` | 26,877 | 12,247 | 50 | greedy | ⏳ gpu15 | ❌ dead |
| `minepump_trace2` | 23,598 | 11,608 | 35 | greedy | — | ❌ dead |
| `minepump_trace3` | 23,201 | 9,864 | 40 | greedy | — | ❌ dead |
| `minepump_trace4` | 27,589 | 11,136 | 48 | greedy | ⏳ gpu14 | ❌ dead |
| `minepump_liveness_trace0` | 37,737 | 1,130 | 1 | greedy | — | ❌ dead |
| `minepump_liveness_trace1` | 17 | — | 1 | greedy | 13 | done |
| `minepump_liveness_trace2` | 151 | 31 | 1 | greedy | — | ❌ dead |
| `minepump_liveness_trace3` | 19 | — | 1 | greedy | — | done |
| `minepump_liveness_trace4` | 33,493 | 1,193 | 1 | greedy | 1,888 | ❌ dead |
| `pcar_trace0` | 764 | 73 | 1 | greedy | 161 | ❌ dead |
| `pcar_trace1` | 21 | — | 1 | greedy | — | done |
| `pcar_trace2` | 599 | 84 | 1 | greedy | 114 | ❌ dead |
| `pcar_trace3` | 2,555 | 1,266 | 1 | greedy | 609 | ❌ dead |
| `pcar_trace4` | 1,140 | 104 | 1 | greedy | 98 | ❌ dead |
| `traffic_single_trace0` | 19 | — | 1 | greedy | 7 | done |
| `traffic_single_trace1` | 55,145 | 7,311 | 1 | greedy | ⏳ gpu09 | ⏳ gpu02 |
| `traffic_single_trace2` | 19 | — | 1 | greedy | — | done |
| `traffic_single_trace3` | 15,504 | 3,632 | 1 | greedy | 802 | ⏳ gpu12 |
| `traffic_single_trace4` | 19 | — | 1 | greedy | 7 | done |
| `traffic_updated_trace0` | 21 | — | 1 | greedy | 10 | done |
| `traffic_updated_trace1` | 21 | — | 1 | greedy | — | done |
| `traffic_updated_trace2` | 21 | — | 1 | greedy | 10 | done |
| `traffic_updated_trace3` | 21 | — | 1 | greedy | 11 | done |
| `traffic_updated_trace4` | 21 | — | 1 | greedy | 10 | done |

`↑` marks a merged count that is an upper bound because equivalence checks hit
`SPEC_REPAIR_EQUIV_TIMEOUT`. genbuf trace 2 had **all 210** of them time out, so
its unique count of 21 restates its input and establishes nothing; its merge of
1 is real.

`❌ dead` means the process is gone but `status.txt` still reads mid-verification
- that file is only ever advanced by the process itself. Only six searches are
actually alive, confirmed by a `ps` sweep, not by the run directory.

## Why not 5 of 5: colorsort

**colorsort produced nothing on any trace, and the cause is memory, not logic.**

Its candidates are learned in seconds and then discarded, because synthesis
exhausts the JVM heap. `_synthesise_or_reject` turns the `OutOfMemoryError` into
`SpecificationNotVerifiableException`, which the search records as "cannot
verify" and skips - so a run completes, reports no repair, and looks like a
search that found nothing rather than one that ran out of memory. Measured on
trace 2: it finished with no repair after three candidates failed verification
in 46m, 1h59m and 30m.

Unset, the JVM takes a quarter of RAM - about 15.5GB of a 62GB box - and leaves
the rest idle. `SPEC_REPAIR_JVM_HEAP=48g` exists precisely for this and is
**not** set in the search launcher; it was added to the merge runners on
2026-08-24 after minepump trace 4 died with `rc=139`.

colorsort is also the largest case study by some way, at 20 violated
assumptions against one or two for most others.

**This is the most tractable of the two gaps.** Re-running colorsort with the
heap set is a configuration change, not a research problem, and it is the single
thing most likely to turn 9 of 11 into 10 of 11.

## Why not 5 of 5: genbuf

genbuf has 3 of 5, and needed three separate fixes to get that far. Each was
real; none was the same bug.

**Wall 1 - `exploreAllCores`.** `Checker$Memoize.lookupPos` walks every
previously-checked subset calling `isSubset`, so a check costs O(|memo| x n)
with |memo| growing per check. On genbuf's 81 guarantees it does not finish. A
stack dump of trace 3 after 142 hours showed 136 hours of CPU inside it. It is
reached from two places - trivial solutions, and `filter_counter_traces` during
verification - which is why genbuf had neither results nor trivial solutions.
Replaced by our MARCO enumeration, opt-in via `SPEC_REPAIR_MARCO_CORES=1`.

**Wall 2 - the BDD games themselves.** With MARCO the first verification came
back in ~14 seconds and trace 1 wrote a specification. Traces 1 and 4 then spent
hours inside single `CUDDFactory.gr1Game0` calls. The cost did not disappear, it
moved: out of Syntech's memoisation and into genuinely hard realisability games
on the guarantee subsets the enumeration probes.

**Wall 3 - per-verification cost.** Re-running from 2026-08-19, trace 1's
completed verifications took 2h51m and 3h01m each, returning ~980
counter-examples apiece; trace 4 got one back in 9h22m and its second ran 32h
without returning; trace 3 never returned from its first in 37h. At three hours
a candidate, the 21 candidates at one node are a sixty-hour job.

The "~14 seconds" figure recorded on 2026-08-20 was one fast candidate, not the
per-verify cost. Corrected here.

**Where that leaves it.** Trace 1 has 2 final specifications and a merge; traces
3 and 4 have none after a week. All three re-runs are still alive on gpu03,
gpu11 and gpu13. Note that traces 1 and 4 also have their *original* pre-MARCO
searches still running elsewhere, writing into the same directories - see
Caveats.

## Why 9 of 11 case studies

Nine case studies have all five traces: amba, elevator, gyro, lift, minepump,
minepump_liveness, pcar, traffic_single, traffic_updated. genbuf has three,
colorsort none. There is no eleventh missing case study - the count is 9
complete, 1 partial, 1 empty.

The merge atlas shows nine families for a different reason: it lists runs with
graphs, and neither colorsort nor genbuf has any.

<a id="caveats"></a>
## Caveats

**Almost every merged number came from the greedy merge, which is
order-dependent.** It conjoins left to right and splits when unrealisable, never
revisiting a pair that landed either side of a split. Two consequences are
measured rather than suspected:

* On the guarantee side it can miss a stronger merge. minepump trace 1's pool
  holds `G(methane -> (next(!pump) | next(methane)))` 15 times and the untouched
  `guarantee1_1` 2,127 times, never in the same specification.
* On the assumption side any variation is pure artifact, since conjoining
  assumptions only makes realisability easier and no split is ever forced by
  them. minepump traces 1-4 carry 2, 2, 4 and 2 semantically distinct assumption
  sets across their merged outputs; a single pooled set works for **all 173** of
  them and stays strictly weaker than the original.

**Pools have grown since their merges were taken.** These searches write
continuously, so a merge is a reading of a pool that has since moved:

| run | at 2026-08-19 | now |
| --- | --- | --- |
| `traffic_single_trace1` | 35,640 | **55,145** |
| `traffic_single_trace3` | 3,395 | **15,504** |
| `minepump_liveness_trace0` | 18,542 | **37,737** |
| `minepump_liveness_trace4` | 21,135 | **33,493** |
| `pcar_trace3` | 1,315 | 2,555 |

`traffic_single_trace3` has had **two** search processes writing one directory
throughout, which is part of why it quadrupled.

**Nothing locks a run directory.** genbuf traces 1 and 4 each have a MARCO
re-run and the original pre-MARCO search alive at once, writing the same
`final_specs/`.

## Running now

| work | runs | where |
| --- | --- | --- |
| search | traffic_single 1, traffic_single 3, gyro 3 | gpu02, gpu12, gpu16 |
| search (genbuf MARCO re-runs) | genbuf 1, 3, 4 | gpu03, gpu11, gpu13 |
| unique-from-final | minepump 1, minepump 4, traffic_single 1 | gpu15, gpu14, gpu09 |
| **directed merge** | minepump 1-4 | gpu07, gpu23, gpu24, gpu25 |
| trivial solutions (MARCO) | genbuf 0/1/3/4 | gpu04, gpu05, gpu10, gpu13 |

gpu21, gpu22, gpu28 and gpu30 refuse ssh. gpu21 stopped accepting connections
today, which is why minepump trace 1's directed run is on gpu07.
