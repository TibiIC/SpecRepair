# A killed run that looked like a queued one

Report date: 2026-08-10. Picks up from
[2026-08-08](2026-08-08-wrong-answers-that-looked-like-results.md), which closed
by restarting case_study_2 and case_study_3.

**Short version.** An audit of the two case_study_3 arms found seven FastLAS
runs that had died without leaving a verdict, an exit status, a traceback or a
shell message. Nothing distinguished them from runs still waiting behind the
concurrency semaphore, so they had been counted as "running" for two days.

The cause is the same shape as the last two sessions - not a wrong answer this
time, but no answer at all, reported as if it were progress. Three separate
mechanisms in this repository were each discarding part of the evidence.

Fixed, the FastLAS arm relaunched under the fixes, and a new problem surfaced
while checking the relaunch: **two runs of the same tuple with the same learner
do not produce the same specifications.**

## 1. Where the two arms actually stood

Neither arm was finished, and they were not comparable with each other.

| | ILASP (gpu20) | FastLAS (gpu12) |
| --- | --- | --- |
| Sweep started | 2026-08-09 21:15 | 2026-08-08 20:11 |
| Code | post-`58c3def` | **pre-fix** |
| Learner budget | 600s | **60s (library default)** |
| Output stamp | `*_2026-08-09` | `*_2026-08-08` **and** `*_2026-08-09` |
| Concluded | 18 / 27 | 21 / 27, seven of them by dying |

The FastLAS arm predated `58c3def`, so it ran under the old budget *and* the
midnight rollover, scattering its output across two dates that no single
`*_<date>` glob collects. It needed relaunching whatever else was true of it.

The ILASP arm's finished runs:

| Case study | Traces | Result |
| --- | --- | --- |
| minepump | 0, 2, 4 | 12 specs each |
| minepump_liveness | 0, 1, 3, 4 | 7, 7, 15, 5 |
| traffic_single | 0, 2, 4 | 16 each |
| traffic_updated | 0-4 | 19 each |
| gyro | 1, 3 | **0 specs** - learner timed out at 600s |
| minepump_liveness | 2 | `MitigationMadeNoProgressException` |

Two findings there worth separating from the crash work:

* **gyro produces nothing on ILASP even at 600s.** The timeout fix did not
  rescue it; it made the same failure take ten minutes instead of one.
* **`minepump_liveness_2` errors identically on both learners** - guarantee
  weakening returns its input unchanged and the branch would be silently
  dropped as already visited. It reproduced a third time on today's relaunch,
  so it is a repair-logic gap, not a learner artefact.

## 2. The seven deaths

Five died with no message at all; two left a JVM SIGSEGV (`malloc_consolidate:
invalid chunk size`). Times and phases come from each run's `status.txt`, which
keeps ticking independently of stdout - the sweep log's last line is not the
death.

| Job | Died | Elapsed | Depth/node | Queue | In phase |
| --- | --- | --- | --- | --- | --- |
| traffic_single_1 | 08-08 20:52 | 38m50s | d2 n150 | 657 | 0.0s |
| minepump_3 | 08-08 22:36 | 2h24m | d4 n526 | 1,417 | 0.0s |
| minepump_1 | 08-08 23:00 | 2h46m | d4 n682 | 1,880 | 0.0s |
| traffic_single_3 | 08-09 08:25 | 11h20m | d2 n983 | 4,861 | 0.0s |
| gyro_4 | 08-10 10:45 | 38h31m | d1 n163 | 28,149 | **12m06s** |

**All seven died inside a Spectra verification call**, the SIGSEGVs included.
Four of the five silent ones died at the *instant* of entering one (`in phase:
0.0s`), which is when a fresh BDD manager allocates. gyro_4 died twelve minutes
into a single call, and its `status.txt` kept updating for eleven minutes after
its stdout went quiet - the process was alive and producing nothing.

`status.txt` is also the only reason the timings above exist. It is worth more
than it looks.

## 3. Why they were silent

Three mechanisms, all local, each sufficient on its own.

**The exit status went into the pipe.** Every runner ran
`python -m unittest ... 2>&1 | tee LOG`, whose status is *tee's*, and nothing
recorded python's. Verified with a process that SIGKILLs itself: bash prints no
message whatsoever, because the pipeline's last element exited cleanly. A killed
run and a queued run leave the same evidence - none.

**Python's stdout was block-buffered.** `PYTHONUNBUFFERED` is not set in the
sweep environment (checked in `/proc/<pid>/environ` on a live run) and stdout is
a pipe, so a hard death discards up to a buffer of output: exactly the part that
would name the cause.

**Spectra's output died in memory.** `run_spectra_cli` redirected Java's
`System.out` into a `ByteArrayOutputStream` and read it back only after `main`
returned. Spectra runs in *this process's* JVM, so anything it printed on the
way down was lost with the buffer. The two SIGSEGVs escaped only because the
JVM's fatal handler writes to fd 2, bypassing the Java-level capture.

### 3.1 What actually killed them - not established

Memory is the obvious pressure: a run holds **5-9GB resident** once its BFS
queue is thousands of nodes deep, `MAX_WINDOWS` was 10, and the box has 62GB
with 3GB of swap (2GB already used, 13.9M pages swapped out). `jvm.py` sets no
`-Xmx`, and CUDD's BDD tables are native and uncapped by design, so a
verification call has no ceiling.

Against the kernel OOM killer specifically: `memory.events` for the user slice
reports `oom_kill 0`, and the slice has existed continuously since the tmux
server started. `dmesg` is `Operation not permitted` on gpu12, so the kernel log
could not be consulted either way. Concurrency was 6-7 at every death, the same
as at every completion, so it was not a concurrency spike.

Recorded as unresolved. The point of this session's fixes is that the *next*
one will say so itself.

## 4. Fixed

`0161e28`:

* `${PIPESTATUS[0]}` written to `<job>.exitcode`, so 0, 1 and 128+signal are
  afterwards distinguishable. The simulated SIGKILL now records **137**.
* `python -u`.
* Spectra's output captured to a per-pid file with `autoFlush` instead of to
  memory, so the last call survives the process that made it; `-XX:ErrorFile`
  points the JVM's fatal log beside it, after seven crashes left no `hs_err`
  file in the default location.
* case_study_3's concurrency cap **10 -> 4**, from the 5-9GB measurement.

The command builder moved to `scripts/lib/job_cmd.sh`, shared by all three
runners for the reason `slots.sh` gives: a fix applied to one copy of a
duplicated string is not applied to the others.

4 new tests; 177 pass in `test_util` and `test_wrappers`, with the three
pre-existing cwd-relative failures in `test_spec.py` unchanged.

## 5. The cap of 4 needed EXCLUDE to be usable

Jobs queue in case-study order, so at cap 4 **gyro claims every slot at launch**
and has never finished a run on either learner in 44 hours. Nothing behind it
would ever start. The old cap of 10 hid this because six other slots remained.

One session per case study is not the alternative: each session gets its own
slots directory and therefore its own semaphore, so four sessions "capped at 4"
run sixteen JVMs on a box that cannot hold ten.

`a719cfa` adds `EXCLUDE="gyro pcar"`. Testing the degenerate case caught a bug:
`"${_kept[@]}"` on an empty array aborts under `set -u` before the intended
error message is reached.

## 6. Relaunched

gpu12's pre-fix session was killed (0 orphaned processes left; memory dropped
from 41GB to 9GB used), the checkout pulled to `a719cfa`, and:

    EXCLUDE="gyro pcar" LEARNER=fastlas FASTLAS_RUNS=10 ./scripts/run_case_study_3.sh

**20 runs**, not 21: 27 - 5 gyro - 2 pcar.

Within 40 minutes, 13 of 20 concluded, **every one with an exit code recorded**
- twelve 0s and one 1 (`minepump_liveness_2`, the mitigation error again). 16
Spectra call logs sit under `<logdir>/jvm/`.

## 7. The relaunch found something worse than the crashes

The same tuples ran on 08-08 with the same learner and the same
`FASTLAS_RUNS=10`. Comparing final specifications by content hash:

| Tuple | 08-08 | 08-10 | Shared | Only old | Only new |
| --- | --- | --- | --- | --- | --- |
| minepump_trace0 | 14 | 17 | 13 | 1 | 4 |
| traffic_single_trace4 | 19 | 19 | **14** | 5 | 5 |

Equal counts, different sets. That is divergence, not further exploration.

It is **not** the learner budget: both sweeps logged **zero** learner timeouts,
so 60s versus 600s cannot account for it. FastLAS is deterministic and BDD
reordering was off in both.

### 7.1 Retracted: the comparison was against contaminated directories

Post-processing the pulled runs later the same day showed the table above cannot
be read as run-to-run divergence, because **both** tuples in it were
contaminated.

A relaunch writes into `<case>_trace<N>[_fastlas]_<date>`, which already exists,
and nothing clears it - so `final_specs/` accumulates across every sweep that
shares a name. 2026-08-08 had three launches (00:00, 12:47, 20:11), and ten of
its FastLAS runs hold specifications written *before their own run started*:

    minepump_trace0_fastlas         14/14 stale   started 12:47, oldest spec 02:01
    traffic_single_trace4_fastlas    2/19 stale   started 20:12, oldest spec 01:01

`minepump_trace0_fastlas`'s `status.txt` reports the run 0.0s in with 0
solutions, beside 14 specification files from the midnight sweep. So the 08-08
column was a different sweep's output - entirely for one tuple, partly for the
other.

Whether two identical runs diverge is therefore **still unknown**: it was never
tested. Establishing it needs two runs into directories known to be empty. What
*is* established is that any analysis of a date with a relaunch mixes sweeps
unless the directories were cleared by hand - which affects every earlier
comparison drawn from 2026-08-08.

A smaller inconsistency found alongside it: `minepump_0`'s 08-08 log reports 15
repaired specs while its directory holds 14 files, and `status.txt` reports
`0 final, 0 intermediate` for a run that had written 937 finals and 437
intermediates. The counters and the files do not agree.

## 8. Open

* **Run directories are never cleared on relaunch** (section 7.1), so
  `final_specs/` accumulates across sweeps sharing a name. This is the more
  serious of the two: it silently corrupts the inputs to post-processing, and
  the corruption is invisible in the directory - only the file mtimes give it
  away. A run should start by clearing, or refusing to start into, a
  non-empty output directory.
* **Reproducibility** - whether two identical runs diverge is untested, the
  earlier evidence for it having been withdrawn.
* **gyro and pcar have no box.** They are excluded from the current sweep and
  every other machine is running one; the sweep guard will refuse a second
  session on gpu12. gyro has never completed on either learner.
* **No per-run wall-clock cap exists.** `LEARNER_TIMEOUT` bounds one learning
  task, not a run, so a run that never converges holds its slot indefinitely.
* **The ILASP arm is untouched**, 19h in. It has the timeout and date fixes but
  not this session's diagnostics; restarting it would cost a day and buy only
  instrumentation.
* **Still open from 08-08**: Slurm needs `conda install -c conda-forge clingo`;
  `ok_returncodes` is wired only to clingo, not ILASP/FastLAS/Spectra;
  `test_trivial_solution.py` needs `--ignore` for colorsort; case_study_3
  covers 6 of 12 case studies with pcar at 2 traces rather than 5.
* **Deeper fix not attempted**: running Spectra verification out-of-process
  would mean a native crash kills a subprocess rather than the whole run.
