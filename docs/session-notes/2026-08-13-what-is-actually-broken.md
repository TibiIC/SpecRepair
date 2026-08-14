# What is actually broken

Report date: 2026-08-13. Follows
[2026-08-12](2026-08-12-the-plan-was-there-all-along.md).

Post-processing day. The traces are sound - 55 of 55 pass the preconditions,
11 of 11 specifications realisable, checked with realisability on a box where
CUDD loads - so every run that failed, failed for a reason of its own. This is
the list.

## Preconditions, tightened

The check asserted only that *some* assumption is violated somewhere in a
trace. A trace that broke one at step 2 and carried on would have passed, and
its prefix would not have been assumption-respecting behaviour. It now asserts
the condition as stated:

* the specification is realisable;
* guarantees hold at every step **except possibly the last** - that state is
  the controller's own output, and GR(1) releases the system once the
  environment breaks its side;
* assumptions hold at every step **except the last, where at least one fails** -
  the prefix must be clean *and* the whole trace must not be.

Liveness is excluded from both: a finite trace neither satisfies nor refutes
`GF(p)`. Verified the check can fail - appending a state after the violating
one makes the prefix report `assumption1_1` where it previously reported
nothing. All 55 traces still pass.

## The bugs

| bug | details | experiments affected | difficulty |
| --- | --- | --- | --- |
| **~~Spot segfaults in-process~~** *(fixed, `c83c3d1`)* | `SIGSEGV` in `spot::fnode::unique`, `si_addr 0x30` - a null dereference while interning formula nodes. `import spot` loads libspot into *this* process alongside the JVM, so the crash takes the whole run down. Deterministic: identical frame and address across machines. Reachable from the repair search *and* from the merge. | minepump_3, minepump_liveness_0, amba_trace3 (during merge, `rc=139`), colorsort (suspected) | **Fixed.** `equivalent_to` and `is_equivalent_to_spot` now go through `ltlfilt` in a subprocess, as `does_left_imply_right` always did. Timed first, since `equivalent_to` backs `__eq__`: on amba's 777-char formula the subprocess is *faster* than in-process (0.014s vs 0.029s). |
| **Long runs killed by SIGTERM** | Exit 143 after 4-6 hours, no crash log, no `hs_err`. Ended 01:38, 02:38, 04:21 - spread out, so not one event. Not `kill-stale-maint`, which only reaps the lab's own `maint` processes. No systemd limits: `MemoryMax=infinity`, `TasksMax=infinity`, no `RuntimeMaxSec`, no Slurm. Long runs are intended, so being stopped at all is the bug. | minepump_2, minepump_4, colorsort_3, genbuf_3, genbuf_4 | **Unknown.** Source not identified. Our own tooling is not ruled out - `pkill -f` has twice matched its own command line this week. |
| **~~genbuf dies seconds after LEARN~~** *(found and fixed, `a759c60`)* | It was an **out-of-memory kill**, and the reason it looked like anything else is that the lab boxes never say so. `extract_trace` expands a counter-strategy into *every path* through it, keeping the ASP encoding of each - exponential in the graph. Measured on genbuf trace 0: **52.89GB resident**, caught by tripping `PYTHONFAULTHANDLER` at 25GB and reading the stack (`counter_trace.py:184`, twelve frames deep, under `is_valid_or_counter_arguments`). That single fact explains the whole symptom set: dies under 4-way concurrency and survives solo (4 x 53GB does not fit in 62GB), dies seconds after LEARN (where the expansion runs), and leaves no `hs_err` log (the kernel kills the process, so the JVM never writes one). **Slurm is what cracked it**: `Detected 1 oom_kill event`, in one line, where the lab boxes had only ever shown SIGKILL. | genbuf 0-4, and every large case study that reaches this path | **Fixed.** Capped at 1000 counter-traces (`SPEC_REPAIR_MAX_COUNTER_TRACES`, 0 unbounded): **52.89GB -> 1.60GB**. The cap is far above normal - minepump trace 2 peaks at 3 per expansion across 18 - and a test asserts small expansions are unchanged. Truncation prints: kept counter-traces are genuine, so repairs stay real, but the set is no longer exhaustive. |
| **genbuf still does not finish** | With the memory fixed, two ceilings behind it. **JTLV**: an hour at 100% CPU in `net.sf.javabdd.JTLVJavaFactory.makenode`, the equilibrium `_bdd_args` documents as never erroring and never finishing. `SPEC_REPAIR_BDD` is set nowhere, so *every* run defaults to JTLV while CUDD sits available on Linux. **Cores**: under `SPEC_REPAIR_BDD=cudd` the run clears JTLV immediately and then spends over an hour in `Checker$Memoize.seek` - Spectra's exhaustive `exploreAllCores`, paid per node. The existing guard only skips it for *realizable* specs, and here the spec is unrealisable by construction. | genbuf 0-4; colorsort and amba likely share the cores ceiling | **Open, and a methodology call.** CUDD is opt-in on purpose: a different BDD package can return a different counter-strategy among many valid ones, and the search branches on what it is given, so runs either side are not result-comparable. `83e5761` defers the cores search until a counter-trace actually needs it, which is free and semantics-preserving but does not help a node whose counter-traces do have violations. |
| **ILASP produces nothing on the large case studies** | 25 learner timeouts against FastLAS's zero. `amba_0` ran 17m52s and hit the 600s per-task limit at depth 0 node 2: task times out, `0 candidate(s)`, mitigator flips to guarantee weakening, run ends empty. Unchanged at 3600s. | amba 0-4, genbuf 0,1,3,4 (ILASP arm) | **Not a bug.** A result: ILASP cannot repair these two at a practical budget, where FastLAS does all five amba traces cleanly. Worth reporting as such. |
| **~~Runs finish having produced nothing~~** *(solved - not a bug)* | Not empty searches: they error in 4ms with `AttributeError: type object 'TestCaseStudy3' has no attribute 'test_case_study_3_elevator_0_syn'`. The test module generates one test per trace *found on disk at import*, and these traces were absent when the sweep launched - swept away by a `git stash -u` and restored afterwards. The runner had already enumerated its windows. | elevator 0,2,4; colorsort 2,4; pcar_2 (FastLAS) | **Done.** Nothing to fix in the system; the runs need re-running now the traces are back. |
| **~~clingo exits 127 on Slurm~~** *(fixed)* | The first real Slurm submission - array 273723, genbuf traces 0-4 - died five for five, seconds in, with `SolverInvocationError: clingo exited 127`. The sbatch prepended `/vol/bitbucket/tg4018/clingo-build/bin` and guarded it with `[[ -x ]]`, which a binary passes on every node right up to the point where it cannot load `liblua5.1.so.0` and refuses to start. The guard now runs `clingo --version` instead of testing the file bit, and prefers the conda env's clingo, which carries its own libraries. **The error handling worked**: a solver that cannot start is now an error naming its exit code, not a run reporting "this trace violates nothing" - exactly what the 2026-08-08 fix was written for, firing for the first time in anger. | the whole Slurm arm; no lab-box run affected | **Fixed.** The comparison it was meant to run has not happened yet. |
| **~~FastLAS returns UNSATISFIABLE for every task~~** *(self-inflicted, reverted)* | Fixing clingo for the Slurm nodes, I ran `conda install -c conda-forge clingo` into the `logic` env. That env is on shared NFS, so it put a clingo at `$CONDA_PREFIX/bin` on **every lab box**, ahead of `/usr/bin/clingo`. FastLAS shells out to whatever `clingo` is on PATH, and against the conda build every learning task came back `UNSATISFIABLE` in 0.4s where the same task file against `/usr/bin/clingo` returns solutions. genbuf trace 0 went from 21 candidates in 1m16s to 0 candidates in 0.4s with no code change at all. Both builds report **version 5.7.1** - the version string is not the thing that matters. Reverted: conda clingo removed, `/usr/bin/clingo` restored, same task file verified solving again. | everything run between 15:45 and 16:30 on 2026-08-13, on every box: the Slurm array 273740, the gpu12 HEAD and pre-Spot-fix bisect runs, and whatever gpu03 was doing | **Reverted.** The lesson is about shared infrastructure: `logic` is on NFS, so installing into it is a change to every machine at once, and a matching version string is not evidence that two builds behave alike. Do not install into that env to fix one node - point `CLINGO_BIN` at the node instead. |
| **humanoid produces no trace** | The solver plans, the controller accepts the plan's first move, and the second hits an environment deadlock - no input is legal from the state the first move reached. Five distinct causes were found and fixed behind this one; this is what remains. | humanoid (all) | **Medium.** Needs the planner to know something about the controller's reachable region, which it currently has none of - it plans against the specification alone. |
| **Everything runs under JTLV** *(withdrawn, then reinstated - it was true)* | Originally claimed from `100019 nodes` in a log, read as JTLV's signature. That reasoning was bad - `jvm.py` records JTLV's table as 200033 - so the row was withdrawn as "never true". **The withdrawal was the error.** `_bdd_args()` returns `--jtlv` unless `SPEC_REPAIR_BDD=cudd`, and that variable is set nowhere: not in `scripts/`, not in `~/phd_work.sh`. Every run uses JTLV. Settled not by log-reading but by a thread dump: `net.sf.javabdd.JTLVJavaFactory.makenode`, on the stack, at 100% CPU. The lesson is to check which class is loaded rather than infer a package from numbers in output - twice now, in both directions. (The two related inferences from that same reading *were* wrong: the "empty" CUDD native directory and the missing CLI jar were both artefacts of testing without `SPEC_REPAIR_TOOLS` sourced.) | every run on every case study | **Open** - see the genbuf row; switching to CUDD is a methodology call, not a bug fix. |

## Not bugs, though they looked like them

**Long searches.** minepump explores thousands of leaves to depth 5 over
hours; `minepump_2` was at leaf #2149 after 5h51m. The specification is tiny -
three variables - but the repair search is combinatorial, and the two traces
that violate *both* assumptions are the two that run longest. That is intended
behaviour and not something to constrain generation over. It was listed as a
finding before this was clarified.

## amba

Five traces, five clean FastLAS runs, 21 repaired specifications each, all
merging to exactly one. Written up in
[results/case-study-3-amba.md](../results/case-study-3-amba.md), with which
assumption each trace targets and which it actually violates.

Worth noting as a limitation: four of the five traces violate *both* violable
assumptions, and only trace 4 isolates one. No trace isolates
`hburst_mutual_exclusion`. So as coverage of distinct weakenings amba gives two
cases, not five.

**Those numbers are now superseded.** They were measured under JTLV, and the
rerun below is under CUDD. The two are not comparable, and the results file
still carries the JTLV figures until the rerun finishes.

## CUDD, and the rerun

JTLV does not merely slow the large case studies down, it never finishes them,
so `SPEC_REPAIR_BDD` now defaults to **cudd** (`7fdb277`); `=jtlv` opts out, and
macOS still falls back since the jars ship no `.dylib`. The comparability
caveat that kept it opt-in is real and unchanged - a different BDD package can
return a different counter-strategy, and the search branches on what it is
given - which is why it changed between full reruns rather than underneath one.

Everything measured before 2026-08-13 therefore needs regenerating.

Both arms relaunched at 21:57 and 21:58 on gpu20 and gpu12: 55 runs each, all
eleven case studies, four concurrent. Confirmed on a live process rather than
assumed - `net.sf.javabdd.CUDDFactory` loaded, zero JTLV frames.

## The sweep that started nothing

The first launch printed `Started 10 run(s)` and produced no windows and an
empty log directory. tmux had loaded conda's `libtinfo` and died with
`undefined symbol: tiparm_s`, so every `new-window` failed while the script
counted them as started. The trigger is the `LD_LIBRARY_PATH` export that
`running-on-ssh.md` tells you to set, so the trap sits in the documented path.

Fixed in all three runners and the doc (`04da663`). The first attempt at the fix
used `env -u LD_LIBRARY_PATH command tmux`, which asks `env` to exec a shell
builtin and failed identically - a session with no windows (`7bc984d`). The
count also went from a wrong "10" to the correct 55 once tmux worked, so the job
enumeration had been fine all along.

## Trivial solutions

50 of 55 generated ahead of the runs, stamped `2026-08-13` to match them: 146
specification files, every directory populated (checked for empty directories
explicitly - one produces a graph silently missing its floor).

genbuf is the exception, at 0 of 5. It has sat over 13 hours in
`Checker$Memoize.seek` - Spectra's `exploreAllCores` - and because the script
works alphabetically it was blocking the 40 case studies behind it, which is why
the rest ran separately on gpu01.

## What the rerun is showing so far

**genbuf finishes.** It had never once completed, on any machine, under either
learner. It now does, in about ten minutes: ILASP has four of five in
(`genbuf_2` repaired, `genbuf_0/1/4` completing with no repair), and FastLAS has
`genbuf_2` clean. Both fixes were needed - the counter-trace cap for the 53GB,
CUDD for the JTLV thrash.

**ILASP repairs amba after all.** The results file records 0/5 at 600s and
3600s; under CUDD `amba_4` comes back exit 0. Those earlier runs were dying
rather than failing to learn, so "ILASP cannot repair amba or genbuf" needs
rewriting from this data rather than carried forward.

Two things still open, both on the same two ceilings:

* `colorsort_0` reached **28.5GB** and ended on **exit 143**, a SIGTERM rather
  than the kernel's SIGKILL. Not the expansion bug - that is capped, and this
  grew steadily with elapsed time, which is what CUDD's native, uncapped BDD
  tables do. The unexplained SIGTERM is therefore still unexplained.
* `genbuf_3` on the FastLAS arm has been in `exploreAllCores` for 13 hours,
  where its sibling traces cleared the same code in minutes. Same wall as the
  trivial solutions. **Not to be bounded** - a truncated core set is silently
  indistinguishable from a complete one and breaks the proven hitting-set
  argument beneath the trivial solutions, so the options are to wait or to
  report without graphs. Reducing how *often* it is called is fine and is what
  the core cache does.
