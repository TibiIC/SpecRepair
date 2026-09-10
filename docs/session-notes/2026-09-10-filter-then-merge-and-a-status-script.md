# Switching to filter_then_merge, and a status script worth trusting — session notes

Session date: 2026-09-10, starting late on 09-09. Asking a simple question —
"what is the status of the step 2 jobs?" — turned up a collision I had caused,
a much better tool for the same work sitting unused in `scripts/`, and the fact
that my own jobs had no way of reporting progress at all.

Continues [2026-09-09](2026-09-09-the-pre-merge-views.md).

## The question that could not be answered

Nine post-processing jobs had been in step 2 for between one and five days.
`run_experiment_pipeline.py` prints nothing between `step 2: filtering N final
specs...` and completion, so there was no way to tell a job three days from
finishing from one three months away. Silence and progress look identical.

Meanwhile the pre-existing `filter_then_merge.py` runs — the ones I had wrongly
called stale on 09-09 — were printing a counter every few seconds:

```
...26225/27589 compared, 3879 kept (1732574s)
```

Same algorithm, same stage, and it says exactly where it is.

## A collision I caused

Reading those logs properly turned up three processes writing into the same run
directory:

| host | job | age |
| --- | --- | ---: |
| gpu14 | `filter_then_merge minepump_trace4_…_08-13 --unique-only` | 20 days, 95% done |
| gpu25 | `filter_then_merge minepump_trace4_…_08-13 --five-step` | 13 days |
| **gpu06** | **`run_experiment_pipeline … minepump_trace4_fastlas`** | **1 day** |

All three compute semantic uniqueness over the same 27,589 specifications and
write into `minepump_trace4_fastlas_2026-08-13/`. `save_specs` deletes existing
`.spectra` files before writing, so whichever finished last would have silently
clobbered the others.

I launched the third on 09-08 after looking only in `postproc_logs/` and not
finding the other two, which write to `uniq_logs/` and `five_logs/`. Nothing was
corrupted — the clobber only happens at completion and mine was days away — but
it would have destroyed twenty days of work. Killed mine; it was both the
newest and the redundant one.

No other overlap exists: gpu09's `minepump_liveness_trace0` is on the 08-13 run
while mine is on 08-29.

## Switching the rest

`filter_then_merge.py <run_dir> --workers N` runs the same three stages the
pipeline's steps 2–4 do — and its docstring argues it does them in the right
order, which `run_experiment_pipeline.py` had backwards until 2026-08-18. It
takes `--workers` where the pipeline is single-threaded at ~41% CPU, and it
reports progress.

All nine remaining jobs were moved onto it (`--workers 8`, or 4 for GenBuf where
parallelism cannot help). That discards up to five days of in-memory work per
job, since step 2 has no checkpoint — accepted, because the jobs were opaque and
unparallelised, and there was no way to know whether the sunk time was near
completion or nowhere near it.

`pcar` needed no switch: it finished during the investigation. Trace 3 went
**2,555 → 764 unique → 71 min → 1 merged**, which is the largest
`unique`→`min` reduction seen anywhere. So the minimal-guarantee filter is not
always a no-op; it just was on every run measured before.

### Rates, honestly

After 11 hours the new jobs are at:

| job | compared | kept |
| --- | --- | ---: |
| ts_t3 | 4,249 / 15,504 | 1,201 |
| mp_t2b | 3,979 / 23,598 | 580 |
| mp_t1 | 3,308 / 26,877 | 610 |
| mp_t0 | 3,175 / 34,651 | 628 |
| ts_t1 | 3,164 / 55,145 | 500 |
| mp_t4 | 3,059 / 35,603 | 584 |
| mp_t3 | 2,808 / 23,201 | 637 |
| mp_t2 | 2,530 / 21,456 | 854 |

That is 0.06–0.10 items/second against gpu14's 0.015/s. Tempting to call it a
6× speedup, and wrong to: gpu14 is at `kept=3,937` and every new comparison runs
against that whole set, while these are at 500–1,200. Most of the gap is the
cheap early phase, not parallelism. The quadratic is still ahead of them, and
ts_t1 at 55,145 specifications is the one to watch.

What is unambiguously better is that the decay is now *visible*.

## Both pre-merge views are complete

GenBuf trace 0's assumption graph finished, and trace 1 followed —
**36 of 36 for both `asm_with_unique_min` and `gar_with_unique_min`**.

Trace 0 took **25,871 seconds — 7.2 hours — for a graph with three nodes**
(original, one `unique_min`, one merged). About six pairwise comparisons. That
is the translation cliff from
[2026-09-08](2026-09-08-the-translation-cliff-and-all-eleven-case-studies.md)
priced exactly: roughly an hour per comparison on a 28-conjunct assumption set,
against milliseconds for Gyro's four conjuncts.

## `scripts/experiment_status.sh`

The ad-hoc status script had been living at
`/vol/bitbucket/tg4018/postproc_logs/status.sh` with every path hardcoded. It is
now in the repository with all of them parameterised:

| override | default |
| --- | --- |
| `SPEC_REPAIR_WORK` | `/vol/bitbucket/$USER` |
| `SPEC_REPAIR_LOGS` | `$SPEC_REPAIR_WORK/postproc_logs` |
| `SPEC_REPAIR_UNIQ_LOGS` | `$SPEC_REPAIR_WORK/uniq_logs` |
| `SPEC_REPAIR_FIVE_LOGS` | `$SPEC_REPAIR_WORK/five_logs` |
| `EXPERIMENT_DATES` | `2026-08-29 2026-08-13` |
| `SETUP` | `case_study_3` |
| `FRESH_SECONDS` | `1800` |
| `SEARCH_WINDOW_DAYS` | `7` |

The repository root comes from the script's own location, so it runs in place
with no configuration:

```bash
ssh gpu20 bash /vol/bitbucket/tg4018/PhD/SpecRepair/scripts/experiment_status.sh
```

Filesystem-only by design. The lab boxes cannot ssh each other — an earlier
version tried to fan out and returned `?` for every field — and the work tree is
shared NFS, so reading it directly gives the same answer from any box. `stat`
and `date` go through GNU-or-BSD wrappers so it also runs on the Mac.

It reports post-processing jobs with their progress counters, other
`filter_then_merge` runs still moving, searches without an exitcode, graphs
drawn by type, and the per-run stage counts, with footnotes on the `min`/`max`
naming and the cliff.

### The searches section is deliberately hedged

It took two wrong attempts. Filtering on log freshness reported "none active"
while GenBuf 3 and 4 were demonstrably running at 128% CPU — they sit inside one
Spectra call for days without writing a line. Reporting every log without an
exitcode instead dumped 34KB covering every sweep back to 2026-08-07, because a
*killed* run leaves no exitcode either.

The filesystem cannot separate "silent but working" from "killed before it could
write one". So the section is bounded to recently-touched directories and
labelled as candidates rather than proof of life, with the `pgrep` command to
confirm. Better a hedged answer than a confident wrong one — the first version
would have had someone conclude GenBuf had stopped when it had not.
