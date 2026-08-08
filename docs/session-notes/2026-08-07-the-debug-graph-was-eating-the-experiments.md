# The debug graph was eating the experiments, and case_study_3 learned to aim

Report date: 2026-08-07. Continues
[2026-08-06](2026-08-06-dead-ends-preconditions-and-deterministic-fastlas-enumeration.md),
which introduced `case_study_3` at midnight.

**Short version.** Six of gpu11's eight jobs had been sitting at **0% CPU for
twelve hours**, blocked on a `dot -Tpng` subprocess that never returned. The
debug graph - write-only diagnostic output - was consuming the entire
experiment. Fixing it raised throughput about **eightfold**.

The other half of the day was `case_study_3`. Its methodology was wrong in a way
worth recording: a uniformly random environment can break every assumption at
once, which no deployment does and which tells the repair nothing. It now aims
at one assumption at a time, and generation is reproducible.

Also: CUDD does fix the BDD garbage-collection thrash, measured; the Imperial
Slurm cluster is reachable and its job script is written but blocked on one
missing library; and a broken clingo is silently read as "no violations".

## 1. Twelve hours inside Graphviz

`status.txt` - added yesterday - localised this in one command:

    lift_trace2       12h51m elapsed | verifying d1 candidate | in-phase 12h49m00s
    humanoid_trace4   12h51m elapsed | verifying d1 candidate | in-phase 12h45m19s
    minepump_trace2   12h48m elapsed | verifying d1 candidate | in-phase 12h35m20s

But they were not verifying. `ps` showed six processes at **0.0% CPU**, and the
kernel wait state named the culprit:

    wchan: futex_do_wait
    child: /vol/bitbucket/tg4018/anaconda3/envs/logic/bin/dot -Tpng

Not contention - load 6 and 31G of 62G used. Not the specification either:
minepump verifies in seconds locally. They were blocked in Graphviz.

**This is the third time the debug graph has taken down a run.** A label threw
(`db6f1fe`), drawing threw (`4327443`), and now drawing hangs. The first two
were fixed by catching exceptions, which does nothing for a process that never
returns.

`pygraphviz`'s `A.draw(prog="dot")` spawns a subprocess with **no timeout**, and
the callback fires on every record - a run reaching 255 leaves laid out a
growing graph 255 times. Three fixes (`e430e23`, `a11b8da`):

* `dot` is driven directly with an explicit timeout;
* the picture is skipped past `GRAPH_RENDER_MAX_NODES` (a layout of thousands of
  nodes is unreadable regardless);
* it is drawn **once per depth** rather than once per record - 20 records across
  3 depths now cost 3 renders.

The pickle is still written unconditionally, and both pictures regenerate from
it.

### Result

| case_study_2 ILASP | Elapsed | Logs | Completed |
| --- | --- | --- | --- |
| Before | ~13 hours | 20 | 10 |
| After | **~1.6 hours** | **41** | **19** |

Roughly **8x**. Afterwards: zero processes at 0% CPU on any machine, zero hung
`dot`, every job between 18% and 138%.

## 2. A stopped branch is not always a broken invariant

Three `case_study_3` runs died with `MitigationMadeNoProgressException`. **None
of them was the failure that exception describes** (`14a780b`).

* **The ordering was wrong.** `_reject_unchanged_mitigations` raised *before*
  `_record_if_solution` ran, so a branch standing on a perfectly good repair
  killed the run instead of recording its leaf.
* **The reported cause was wrong.** Tracing gyro trace 0: assumption weakening
  timed out, returned nothing, the mitigator moved the branch to guarantee
  weakening, which has nothing to weaken without counter-traces, and the run
  died reporting a mitigation that made no progress. *Nothing in that chain
  mentions a timeout.* The learner timeout was hardcoded at 60s and is now
  `SPEC_REPAIR_LEARNER_TIMEOUT` - though that was not the fix here: gyro does
  not finish in 600s either, so it is genuinely intractable.
* **Not every stopped branch is a lost one.** `RepairData` now carries a named
  `unresolvable_reason`. Those branches are reported as `LIMIT` events and
  counted in a summary line, so they are never silent, but they do not discard
  the rest of the run. A branch that stalls with *no* known reason still raises,
  because that is the case the invariant is about.

This matters more than it looks: minepump's controller-generated trace reaches
**168 leaves** before one branch needs deadlock completion. The old behaviour
threw away all 168; with the fix it runs past 255 and keeps going.

## 3. CUDD does fix the garbage-collection thrash

Yesterday's §16 left this unmeasured. Measured now, on a full amba repair:

    RESULT amba cudd: completed in 577s | GC lines=0 | finals=21

**Zero garbage-collection lines**, against the ~186 per second that JTLV
produces indefinitely on the same repair. The thrash is a JTLV artefact and CUDD
does not have it.

Still opt-in and Linux-only (the jars ship `libcudd.so` and `cudd.dll`, no
`.dylib`), so **no sweep currently uses it**. Turning it on for a sweep is a
deliberate act, since a different BDD package can return a different
counter-strategy and the search branches on the one it is given.

## 4. case_study_3: aiming instead of flailing

### 4.1 The methodology was wrong

A uniformly random environment can, at worst, violate the **entire set of
assumptions** in one step. That is not a deployment anyone would recognise -
real environments fail in one way at a time - and it is useless besides: a trace
violating everything says nothing about which weakening it is asking for.

Each candidate input is now scored by *which* assumptions it would break, and
one that would break anything outside the target is **never chosen**
(`13aac69`). Preferences in order: exactly the target, a non-empty subset,
nothing at all. A step that overshoots anyway abandons the episode, since a
controller step cannot be undone.

### 4.2 Targets are spread across the five traces

The first attempt let each trace pick its own target, and the *easy* assumption
won repeatedly - gyro produced `ready_stays_ready` five times, traffic_updated
produced `carB_idle_when_red` four times. Targets are now assigned per trace,
cycling through the assumptions, with covered ones tried last on fallbacks.

| Case study | Before | After |
| --- | --- | --- |
| traffic_updated | 1 distinct | **4 distinct** |
| minepump | 1 | **2** (both it has) |
| traffic_single | 1 | **2** |
| pcar | 1 | **2** |

### 4.3 Liveness assumptions are not targets

A JUSTICE assumption is `GF(p)`: **no finite prefix can refute it**, because the
prefix can always be extended. Targeting one is not merely fruitless but
expensive - every attempt runs its full step budget with an ASP call per step
before giving up. With `--attempts 14` that made gyro slower than the rest of
the suite combined.

Now excluded (`0c64805`). It is the same reason arbiter has no trace at all, and
why `not_police_often`, `no_emergency_often` and minepump_liveness's
`assumption4_1` never appeared as violated.

### 4.4 Generation is reproducible - after pinning the controller

Writing the tests turned up a finding. Generation was **not** reproducible, and
the cause was not this code:

* the seed always governed every choice made here;
* synthesis is deterministic - two syntheses of minepump hash identically;
* yet identical seeds produced traces differing **across separate processes and
  in length**.

A controller usually has several legal responses to an input - hence
`getAllLegalSystemOutputs` - and `ControllerExecutor` picked among them itself,
differently each time. `FlexibleControllerExecutor` hands that decision back: it
waits with `waitingForChoice` set, offers the successor states through
`getChoices()`, and advances only on `chooseNextState()`. Sorting those into a
canonical order and drawing with the seeded generator makes the whole trace a
function of the seed (`7dd2473`).

Drawn with the seed rather than always-first on purpose: always taking the first
choice would collapse the five traces towards each other. Verified both ways -
the same seed gives a byte-identical trace across three separate processes, and
five seeds give five distinct traces.

**A caveat that remains.** Replaying a *single* trace from its manifest
reproduces it exactly for the smaller case studies (gyro) but not always for the
larger ones (pcar). Spectra's `Env` is global to the JVM, so state accumulates
across the generator's calls. Regenerating the whole case study in order is the
reliable replay.

### 4.5 Manifests

Each case study now carries `traces.json` with, per trace, the seed, the
assumption aimed at, what was violated, and the settings. The target is the part
that mattered: a trace whose preferred target proved unreachable fell back to
another, and nothing in the trace file said which - found the hard way, when two
of three spot-checks failed to reproduce for exactly that reason.

### 4.6 Tests, which should have existed first

19 tests (`438675b`), split so the pure parts run everywhere and the end-to-end
ones skip without the toolchain. The two regressions are the ones worth reading,
because **both bugs produced plausible output rather than an error**:

* a refused step is free to retry - the executor does not advance when the
  controller rejects an input, so giving up threw away most attempts;
* a refusal during the rogue phase **is** the violation, not a dead end. The
  controller is only obliged to respond while the environment keeps its
  assumptions. Treating it as failure produced traces for **minepump alone**,
  whose controller happens to tolerate the violating input and carry on, while
  every other case study silently produced nothing.

### 4.7 Current state

**Audit: 27 OK, 0 BAD**, no trace violating more than one assumption.

| Case study | Traces | Distinct assumptions |
| --- | --- | --- |
| minepump | 5 | 2 |
| minepump_liveness | 5 | 2 |
| gyro | 5 | 1 |
| traffic_single | 5 | 2 |
| traffic_updated | 5 | **4** |
| pcar | 2 | 2 |

Still producing nothing: **genbuf** (still searching after a long run),
**colorsort**, **lift**, **elevator**, **humanoid**. `lift` needs two-step
planning specifically - `G(b1 & f1 -> next(!b1))` cannot be violated by any
single choice, only by setting up `b1 & f1` and then pressing b1 again, which
one-step greedy targeting cannot do.

## 5. Slurm on the DoC cluster

[CSG's guide](https://www.imperial.ac.uk/computing/people/csg/guides/hpcomputing/gpucluster/).
Login `gpucluster2` / `gpucluster3`; 32 CPU cores, 200GB RAM, 3-day limit
(`long` partition: 30 days); **`/vol/bitbucket` is mounted on the nodes**, so
there is no data to move.

Two reasons it fits better than tmux, both demonstrated today: **per-job time
limits are enforced** - a twelve-hour hang would have been killed at `--time`
rather than going unnoticed - and **the scheduler owns concurrency**, where
`scripts/lib/slots.sh` exists only because nothing else capped it and its first
version ran 39 jobs against a cap of 8.

`scripts/slurm/run_case_study.sbatch` submits one array task per (case study,
trace), enumerated from disk. Getting a trial to run took five environment
fixes, each found by running it:

1. `conda` is undefined in a batch shell (`type -t conda` is empty,
   `which python` is `/usr/bin/python`);
2. `~/phd_work.sh` is written for a login shell and **ends the job when sourced**
   in batch - the first trial exited 1 with a completely empty output file;
3. `SPEC_REPAIR_TOOLS` defaults to `~/Tools`, which does not exist on the compute
   nodes - the JVM started and failed with `Class cores.SpectraToolbox is not found`;
4. sdkman's init reads `SDKMAN_CANDIDATES_API` before setting it, so `set -u`
   kills the job on its line 20;
5. `clingo` is not installed on the compute nodes at all.

**Blocked on (5).** The `/vol/bitbucket` clingo build needs `liblua5.1.so.0`,
which the nodes do not have:

    clingo: error while loading shared libraries: liblua5.1.so.0

`conda install -c conda-forge clingo` into the `logic` env would fix it
properly, but that changes the environment and has not been done.

### 5.1 A broken clingo is read as "no violations"

The more important finding. When clingo failed to start, the run did not error -
it reported *"the violation trace violates no assumption at all"* for a trace
that passes the identical check locally.

**A tool failing silently becomes a wrong answer rather than an error.** Worth
fixing in `get_violations`, and suggestive for the unexplained elevator result
in yesterday's notes, which has the same shape: something goes wrong in the ASP
path and the answer comes back as "nothing violated".

### 5.2 The SSH puzzle

`ssh gpucluster2` failed with `Permission denied (publickey,...)` when attempted
**from gpu11/gpu12**, but works directly from the Mac. The key `ic_tg4018_rsa`
lives only on the Mac; gpu11's shared home has `id_ed25519`,
`id_firecrest_ed25519` and `id_rsa_tibigg_github`, no agent in a non-interactive
session, and no `gpucluster2` in its `known_hosts`. With
`PreferredAuthentications publickey` in the `Host *` block there is no fallback,
so it fails immediately rather than prompting. `ssh -A gpu11` forwards the agent
if the hop is ever needed.

## 6. Housekeeping

* **`run_case_study_1.sh` had no concurrency cap** - 19 simultaneous JVMs, the
  condition behind its OutOfMemoryError failures. Now `MAX_WINDOWS=8`, with the
  semaphore shared from `scripts/lib/slots.sh` so the runners cannot drift.
* **The runner discovers case studies and traces from disk.** It iterated a
  fixed 0..4 and launched a phantom `pcar_3`; then its hardcoded case-study list
  skipped genbuf when genbuf started producing traces, running 27 jobs where 28
  existed. A controller-generated setup gains and loses case studies as the
  generator improves, so nothing about it should be written down twice.
* **The sweep guard earned itself.** gpu12 refused to start because a 3h46m-old
  orphaned minepump process had survived a kill and would have written into the
  same output tree - the contamination that cost 241 stale specs on 2026-07-24.

## 7. Running now

| Machine | Setup | Learner |
| --- | --- | --- |
| gpu11 | case_study_2 | FastLAS `n_runs=10` |
| gpu13 | case_study_2 | ILASP |
| gpu14 | case_study_1 | FastLAS `n_runs=10` |
| gpu15 | case_study_1 | ILASP |
| gpu12 | case_study_3 | FastLAS `n_runs=10` |
| gpu20 | case_study_3 | ILASP |

## 8. Open

* ~~`get_violations` treats a failed clingo as "no violations"~~ **Fixed
  2026-08-08.** It was the most valuable thing on the list, and chasing it
  turned up a second instance of the same shape - see that day's notes, §1-2.
* ~~elevator's `floor_mutual_exclusion` reports no violation~~ **Explained and
  fixed 2026-08-08**: negating an atom mutated the specification, so every other
  occurrence of a negated atom was encoded with the wrong polarity. See that
  day's notes, §2.
* **Slurm** is one `conda install clingo` from working.
* **genbuf, colorsort, lift, elevator, humanoid** produce no case_study_3
  traces; `lift` needs two-step planning.
* **Single-trace manifest replay** is not exact on the larger case studies
  (§4.4).
* **`test_trivial_solution.py`** still needs `--ignore`; colorsort alone exceeds
  150s in `exploreAllCores`.
