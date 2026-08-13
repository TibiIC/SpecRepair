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
| **genbuf dies seconds after LEARN** | Killed at depth 0, node 1, immediately after the learner returns 21 candidates - 46s and 2m12s, not deep runs. Mixed SIGKILL and SIGTERM, no crash log. Distinct from the two above. | genbuf_0, genbuf_3, genbuf_4 (twice each: gpu12, then again on gpu03) | **Unknown.** Reproduces on two machines, so not host-local. Verifying 21 candidate specifications at once is the biggest allocation in the run and happens exactly there, but SIGTERM does not fit an OOM kill. |
| **ILASP produces nothing on the large case studies** | 25 learner timeouts against FastLAS's zero. `amba_0` ran 17m52s and hit the 600s per-task limit at depth 0 node 2: task times out, `0 candidate(s)`, mitigator flips to guarantee weakening, run ends empty. Unchanged at 3600s. | amba 0-4, genbuf 0,1,3,4 (ILASP arm) | **Not a bug.** A result: ILASP cannot repair these two at a practical budget, where FastLAS does all five amba traces cleanly. Worth reporting as such. |
| **~~Runs finish having produced nothing~~** *(solved - not a bug)* | Not empty searches: they error in 4ms with `AttributeError: type object 'TestCaseStudy3' has no attribute 'test_case_study_3_elevator_0_syn'`. The test module generates one test per trace *found on disk at import*, and these traces were absent when the sweep launched - swept away by a `git stash -u` and restored afterwards. The runner had already enumerated its windows. | elevator 0,2,4; colorsort 2,4; pcar_2 (FastLAS) | **Done.** Nothing to fix in the system; the runs need re-running now the traces are back. |
| **humanoid produces no trace** | The solver plans, the controller accepts the plan's first move, and the second hits an environment deadlock - no input is legal from the state the first move reached. Five distinct causes were found and fixed behind this one; this is what remains. | humanoid (all) | **Medium.** Needs the planner to know something about the controller's reachable region, which it currently has none of - it plans against the specification alone. |
| **~~Trivial solutions run under JTLV~~** *(withdrawn - never true)* | Claimed on the strength of `100019 nodes` in the log, read as JTLV's signature. It is not: `jvm.py` records JTLV's table as fixed at **200033**. amba's five trivial solutions completed on gpu03 - the generation is simply working through case studies alphabetically and was on colorsort. Two further inferences from the same reading were also wrong: an "empty" CUDD native directory (an artefact of testing without `SPEC_REPAIR_TOOLS` sourced, so paths resolved to `~/Tools` instead of `/vol/bitbucket/tg4018/Tools`, where `libcudd.so` is present) and a missing CLI jar (same cause). | none | **None.** No fault existed. |

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
