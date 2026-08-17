# The filters came after the merge

Report date: 2026-08-17. Follows
[2026-08-15](2026-08-15-the-sigterm-was-earlyoom.md).

Two things came out of today, and the first invalidates a number in the report.

## The pipeline had the methodology inverted

The steps are: **semantically unique -> strongest guarantees -> merge only
those**. `scripts/run_experiment_pipeline.py` does **merge -> maximal -> unique**
- it merges the entire pool and filters the merged output afterwards. That has
been true since the pipeline was written on 2026-07-27 (`6912fc8`), and the doc
written with it records the same wrong order.

The two scripts it calls, `find_semantically_unique_specifications.py` and
`find_maximal_specifications.py`, are from 2025-06 and are correct in isolation.
The error was in how they were wired: applied to the merged output rather than
used to choose what gets merged.

What it cost:

* every run merged its whole pool - 24,619 specifications for traffic_single
  trace 1 rather than a filtered handful;
* fifteen variants of `floor_mutual_exclusion` were conjoined into one merged
  elevator specification, five of them carrying `PREV`;
* `shift_prev_to_next` wraps every variable occurrence in `X(...)`, so those
  five expanded 315x - a 563-character formula into 177,492 characters - and the
  merged assumptions became **892,937 characters with 295,020 X operators**,
  from a 10KB specification containing no `next(` at all;
* every semantic comparison then cost ~45s and 3.5GB in `ltl2tgba`, which is
  what produced the crashes below.

The `21 -> 1 -> 1 -> 1` figures in
[results/case-study-3-fastlas-report.md](../results/case-study-3-fastlas-report.md)
describe that wrong computation and are being replaced.

`scripts/filter_then_merge.py` does it in the specified order and reports the
count at each stage. Measured so far, 25 runs:

| run | final | semantically unique | strongest guarantees | merged |
| --- | --- | --- | --- | --- |
| gyro 0 | 97 | 35 | **24** | 1 |
| gyro 1 | 109 | 50 | **35** | 1 |
| lift 0-4 | 21 | 9-17 | same | 1 |
| traffic_single 0/2/4 | 19 | 7 | same | 1 |
| traffic_updated 0-4 | 21 | 10-12 | same | 1 |
| minepump 0 | 17 | 11 | same | 1 |
| pcar 1 | 21 | 17 | same | 1 |

**Half to two-thirds of every pool is semantically redundant**, and all of it was
being merged. Stage 2 only bites on the larger pools - for the 21-spec runs
every semantically distinct repair is guarantee-incomparable. Everything still
merges to exactly one, so that result survives, now computed correctly.

Syntactic distinctness told us nothing here: all 21 of elevator's and amba's
final specifications are syntactically distinct, and they collapse to 9-17
semantically.

## Four crashes in the merge, each hiding the next

All fixed, all real, and all provoked by merging unfiltered pools:

| failure | cause | fix |
| --- | --- | --- |
| SIGSEGV, exit 139 | `GR1Formula.__eq__` called `spot.formula`/`are_equivalent` **in this process**, and libspot shares the JVM's address space | `746a9a4` - route through ltlfilt |
| `Argument list too long` | merged formula past Linux's 128KB argv cap, implication side | `256c714` - check via stdin over `ltl2tgba`/`autfilt` |
| the same, equivalence side | `are_equivalent` had the identical defect and was patched a cycle later | `474e341` |
| SIGSEGV, no stderr | Spot recurses over the formula tree; 59,004 nested `X` overflow the 8MB stack | raise `RLIMIT_STACK` in every Spot subprocess |

`does_left_imply_right` reported all of them as "the output of ltlfilt is
unexpected", discarding the exit code and stderr, so each cost its own
investigation. It now includes both, and dumps the offending formula somewhere
that survives the scratch sweep - which is how the fourth was diagnosed in one
run rather than five.

## Our own unrealisable-core enumeration

`spec_repair/diagnosis/all_unrealisable_cores.py` - MARCO, with the references
in the module docstring.

Spectra's `exploreAllCores` is not merely slow. Disassembled from the jar:
`Checker$Memoize.lookupPos` iterates the **entire** set of previously-checked
subsets calling `isSubset` on each, so a check costs O(|memo| x n) with |memo|
growing per check. On genbuf that is fifteen hours at 100% CPU with memory flat
at 1.5GB - rescanning its own cache rather than computing cores. That matches
the defect reported to the SYNTECH team.

MARCO keeps the unexplored region as a formula rather than a list of subsets: a
maximal seed either grows to a maximal realisable subset and blocks everything
below it, or shrinks to a minimal core and blocks everything above it. The map
solver is clingo. The component takes its realisability oracle as a parameter,
so it knows nothing about Spectra or the JVM - eleven tests, 1.3s, no JVM - and
is deterministic throughout: sorted names, optimal seed, no randomness anywhere.

## lift's traces were not what git recorded

`violation_trace_4.txt` on the shared checkout was 56 lines; the committed one
was 16. The regenerated file had been staged on 2026-08-13 at 11:56 and never
committed - a minute before `76ad318`, which therefore missed it. Every lift run
in this rerun read the on-disk file, so the results were not reproducible from
the repository.

The same regeneration had overwritten `traces.json` with trace 4 alone, dropping
the seeds and targets of traces 0-3. Committed in `0d4b561`: trace 4 as it ran,
manifest entries for 0-3 restored from the previous commit.

## Where post-processing stands

25 runs through the corrected pipeline, all merging to one. 16 running. Four
have pools of 2,496 to 19,000 specifications, where stage 1 is O(n^2) semantic
comparisons and is not expected to finish.

No graphs have been drawn from the corrected merges yet. The 98 PNGs on disk
came from the old order and are not results.
