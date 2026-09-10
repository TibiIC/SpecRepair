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

## A randomness audit of the reporting

Asked to confirm nothing in the reported numbers is random. Audited every RNG
call site in `spec_repair/`, `scripts/` and `main/`.

### The reporting path is deterministic

`filter_then_merge.py` contains no RNG at all. The pool is
`sorted(glob.glob(...))`, every set is consumed through `sorted(...)`, and
`_equivalent_to_any` submits futures in `kept` order and consumes them in order,
so even at `--workers 8` the result does not depend on scheduling. The same
holds for `run_experiment_pipeline.py`, `visualise_resulting_specs.py`,
`generate_trivial_solutions.py` and `spectra_specification.py`. Every stage count
reported came from exhaustive directory listings.

### Where RNG exists, and whether it can reach a number

| site | seeded? | reaches the reporting? |
| --- | --- | --- |
| `controller_trace_generation.py` | `random.Random(seed)`, seed = trace index | yes, by design - the traces are the input |
| `spec_mutation.py`, `violation_trace_generation.py`, `generate_*_traces.py` | rng passed in, seeded by caller | no - case study 1 and 2 paths |
| `file_util.generate_random_string` | unseeded | no - temp **filenames** only |
| `heuristics.manual_choice` | unseeded fallback | no - only fires when `config.MANUAL` is False; it is True, and the callers are all in `legacy/` |
| `heuristics.random_choice` | unseeded | **no - dead code** |
| `weakness_measurement/syntax_utils.py` | - | no - unused import |
| `legacy/old_experiments.py` | unseeded | no - legacy |

The one that needed chasing was `counter_trace.py:265`:

```python
def complete_ct_from_ct(ct, spec, entailed_list,
                        heuristic: HeuristicType = random_choice) -> CounterTrace:
```

An unseeded random default, in a module the BFS uses. It has **no callers** -
the live path calls the plural `complete_cts_from_ct`, which returns the whole
list and makes no choice. `random_choice` is referenced nowhere else. The live
heuristic manager is `NoFilterHeuristicManager`, and none of the heuristic
managers under `components/` mention `random`.

### FastLAS, and a memory of mine that was wrong

I nearly reported FastLAS as deterministic on the strength of a stale note. The
module docstring is explicit, and was corrected on 2026-08-04:

> FastLAS 2.1.0 *is* non-deterministic: given a hypothesis space with several
> equally-optimal candidates it returns different ones on different runs. (An
> earlier note here claimed the opposite. That was an artefact of a broken
> translation.)

What saves the reporting is that `enumerate_adaptations` **enumerates rather than
samples**: each solution found is added to `#bias` as a constraint forbidding it
and the next run asks for something else, stopping when the task goes
UNSATISFIABLE. So the solution *set* is deterministic and complete.

The residual exposure is real but bounded: `n_runs = 10` is a ceiling, so **if a
task has more than ten equally-optimal solutions, which ten come back is not
guaranteed reproducible**. Nothing in the outputs says whether that ever bit.

### A false alarm I raised, and the real gap underneath

I reported that seven traces had "no recorded seed" and offered to recover the
seeds by search. Both were wrong, and the second contradicts a standing
instruction not to manipulate seeds. `generate_case_study_3.py` line 60 is
`for seed in range(traces)` with `"trace": seed, "seed": seed` - **the seed is
the trace index by construction**. Nothing was ever lost.

What *is* missing from `lift/traces.json` (1 entry for 5 traces) and
`pcar/traces.json` (2 for 5) is the **target assumption**, and the script says
why that matters:

> Generation is reproducible from the seed, but only if you know which
> assumption it aimed at: a trace whose preferred target proved unreachable fell
> back to another, and nothing in the trace file says which.

A later partial re-run overwrote those manifests wholesale. So lift 0-3 and
pcar 0-2 have lost the record of what they aimed at. The trace files themselves
are intact and are fixed inputs, so no reported number moves.

The same comment carries a caveat that applies everywhere: replaying a single
trace reproduces it for the small case studies but **not for the larger ones**,
because Spectra's `Env` is global to the JVM and state accumulates across calls.
Reproducibility is at the granularity of regenerating a whole case study in
order, not one trace.

### Measurements, de-randomised

My own comparison benchmark had used `random.sample`. Re-run deterministically
(first 300 specs by sorted filename, `itertools.combinations` in order) on
`minepump_trace1`:

| | sampled | deterministic |
| --- | ---: | ---: |
| distinct assumption strings | 2 / 300 | **2 / 300** |
| distinct guarantee strings | 300 / 300 | **300 / 300** |
| one comparison | 52.0 ms | **53.0 ms** |

Same conclusions, now reproducible. Note the shape: minepump's repairs vary the
**guarantees** and leave the assumptions alone - the mirror image of Gyro and
AMBA. Identical strings already short-circuit at 0.0 ms, so the assumption half
of every minepump comparison is free and the guarantee half always pays.

Where the 53 ms goes: 13 ms is re-serialising both specs (`to_formatted_string`
is recomputed on every comparison and is trivially cacheable), 40 ms is process
spawn for a 116-byte formula. Memoising the *pairwise result* would not help -
each (candidate, representative) pair is compared exactly once, and all 300
guarantee strings are distinct, so a string-keyed cache would never hit either.

## GenBuf trace 2 stopped: no equivalence timeout

The one post-processing job not progressing. It printed `stage 0 final specs on
disk 21` at 09-09 22:42 and nothing since - and the progress line prints every
60 seconds, so silence meant it was stuck inside a single comparison.

It was: one `ltlfilt` at **99.9% CPU for 24 hours 15 minutes**, 3.9 GB resident,
on the first pair.

`SPEC_REPAIR_EQUIV_TIMEOUT` was unset, and `_equiv_timeout`'s docstring names
this exact failure:

> Unset or 0 means no limit... A limit turns a check that would not converge into
> an `EquivalenceUndecided` the caller must handle, rather than a process that
> holds a machine for a day.

Twenty-one specifications need up to 210 comparisons. At 24 hours each that is
not a slow job, it is an impossible one - GenBuf is past the cliff, as
established on 2026-09-08. Stopped, and recorded as not computable alongside
GenBuf 3 and 4. GenBuf 0 and 1 completed only because they hold **one**
specification each, so stage 1 makes zero comparisons.

Setting a timeout would not rescue it. Undecided checks are conservatively
treated as *not* equivalent, so a timed-out GenBuf would report 21 unique
specifications - an upper bound that reads as a result, which is the failure mode
`semantically_unique`'s docstring warns about.

**Latent risk for the other eight:** they run without a timeout too. They are
progressing, so nothing is wrong now, but a single pathological pair would hang
any of them the same way, silently. Worth setting
`SPEC_REPAIR_EQUIV_TIMEOUT` on the next launch and treating a non-empty
`UNDECIDED` list as a reason to exclude a run rather than report it.

## Post-processing, end of day

Eight jobs live and progressing, all with visible counters:

| job | compared | kept |
| --- | ---: | ---: |
| ts_t3 | 6,174 / 15,504 | 1,733 |
| mp_t0 | 5,924 / 34,651 | 905 |
| mp_t2b | 5,917 / 23,598 | 936 |
| ts_t1 | 5,474 / 55,145 | 584 |
| mp_t4 | 5,332 / 35,603 | 823 |
| mp_t1 | 5,110 / 26,877 | 852 |
| mp_t3 | 4,431 / 23,201 | 875 |
| mp_t2 | 3,965 / 21,456 | 1,206 |

Your `minepump_trace4.uniq` is at 26,900 / 27,589 - 97%.
