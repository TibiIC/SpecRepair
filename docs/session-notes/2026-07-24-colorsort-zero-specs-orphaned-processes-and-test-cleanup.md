# ColorSort's silent zero-specs bug, an orphaned-process root cause, and test cleanup — session notes

Session date: 2026-07-24. Started by picking up the "return here" marker
from [2026-07-23's session](2026-07-23-next-antecedent-prev-consequent-asp-gaps.md)
(the `!Prev(x)`-in-consequent fix, already implemented but uncommitted)
and ended up finding and fixing two independent, unrelated latent bugs
along the way, plus a test-suite cleanup pass.

## Part 1: finishing yesterday's Prev-in-consequent fix

The working tree already had a full implementation of yesterday's
proposed fix (truth table, `prev_timepoint_exists` helper, `not_prev`
bucket, antecedent + consequent sides). Verified it rather than trusting
the diff: 197 formatter golden-string tests passed, and
`test_bfs_repair_spec_colorsort_syn` - the test that started the whole
investigation by crashing on `!Prev(x)` - now passed without exception.
Updated the session-notes doc to mark that section resolved and committed
as `726f1b6`.

## Part 2: "I don't see colorsort returning any specification"

Passing without an exception turned out not to mean *working*. Asked to
run all 10 `_syn` case-study tests, colorsort was the outlier: 0 final
specs recorded, `log.txt` containing only the `Started at` line - no
`Learned Index` entries at all, meaning BFS repair exited on its very
first iteration having found nothing to fix.

Reproduced directly: built the `.lp` file colorsort's `strong.spectra`
actually generates (`NewSpecEncoder.encode_ASP` + the real violation
trace) and ran it through clingo by hand, bypassing the rest of the
pipeline. Result: 20+ syntax errors, `UNKNOWN`, no model.

**Root cause**: `make_names_asp_safe`
(`spec_repair/util/formula_string_util.py`, added in `f3c6a77` to fix
uppercase-leading identifiers) only renamed names starting with an
uppercase letter. It never handled names containing spaces or
punctuation. ColorSort's `strong.spectra` labels 24 of its guarantees
with free-text names via `guarantee -- <name>` (e.g. `no pause is
eternal`, or the much richer `while the bottom motor is moving, see if
the color has been found [botMot is MOVING and the color has NOT been
found; we're GOING]`), and these became literal, unescaped ASP atoms like
`guarantee(no pause is eternal).` - a hard clingo parse error. The
pipeline's clingo wrapper (`run_subprocess` /
`SpecGenerator.generate_clingo`) never checks exit status or reads
stderr, so 20+ syntax errors were silently read back as "zero violations
found," every single run, with no exception anywhere in the chain to
catch.

Confirmed no other current case study is affected: grepped all
`strong.spectra` files under `input-files/case-studies/spectra/*/` for
multi-word `--` labels - only ColorSort has any (24 of them; every other
case study's labels are single underscored identifiers already).

**Fix**: extended `make_names_asp_safe` to flag any name that isn't
already a valid ASP identifier (`^[a-z][a-zA-Z0-9_]*$`), not just
uppercase-leading ones, and sanitize by replacing runs of invalid
characters with underscores.

**A second bug found while verifying the first**: after that fix, one
label (the `[...]`-suffixed one above) was *still* unrenamed in the
output. The rename substitution used `\b<name>\b` word-boundary anchors -
but `\b` only matches at a transition between a word character and a
non-word character. A label ending in `]` has a non-word character at
its own edge, and since it's immediately followed by a newline (also
non-word), the trailing `\b` can never match: no transition, no boundary,
silent no-op instead of a rename. This wasn't a hypothetical edge case -
it was already latent even for uppercase-leading names, just never
triggered by any name ending in punctuation until ColorSort's labels
existed. Fixed by only requiring `\b` on whichever edge of the name is
actually a word character.

Re-verified with the same by-hand clingo run: clean `SATISFIABLE` model,
real `violation_holds(detect_mutual_exclusion_5,0,trace_name_0)` and
`violation_holds(once_seeing_a_cube_verMot_kicks_it_in,0,trace_name_0)`
facts. Committed as `1f29240`.

## Part 3: the Bus error

With real violations now detected, BFS repair started doing real work -
and colorsort's guarantees are enormous (one alone has 100+ disjuncts),
which makes Spectra's GR(1) synthesis (BDD-based, via JTLV) very heavy
for some candidate specs. First full run: found and saved 2 valid
repaired specs, then hit a clean `OutOfMemoryError: Java heap space` on
the JVM's 4GB default heap during a later candidate's synthesis check.

Tried bumping the heap to 12GB (`jvm.py`) to see if that was a simple
capacity fix. It wasn't - it crashed *harder*, with `Fatal Python error:
Bus error` (a native-level JVM crash) instead of a clean Java exception.
Investigated instead of guessing: `vm_stat` showed the machine down to
~190MB free RAM. `ps aux` turned up `/Users/tg4018/Tools/bin/ILASP
/tmp/dUquBZurqc.las`, PPID 1 (reparented to `launchd`, i.e. orphaned),
running at ~99% CPU with `lstart` showing it had been going *continuously
since 11:00:01 that morning* - 10+ hours by the time it was found that
evening.

**Root cause**: `run_subprocess`
(`spec_repair/util/subprocess_util.py`) has accepted a `timeout`
parameter since it was written, but never passed it to
`subprocess.Popen`/`communicate()` anywhere - dead code. `run_ILASP_raw`
is the one caller that relies on it (`timeout=60`), intended to bound
ILASP's hypothesis search. With no real timeout, a slow-or-stuck ILASP
call could block forever; worse, once its parent Python process died
(here, from an earlier `kill -9` during this same debugging session -
see Part 4), the child had nothing left to ever stop it, and just kept
running.

**Fix**: `run_subprocess` now passes `timeout` through to
`communicate()`, and on `subprocess.TimeoutExpired` kills the child
before re-raising, so it can never outlive its caller. Verified directly:
`sleep 30` with `timeout=1` now raises after ~1s with no lingering
process; the default untimed path (`timeout=-1` → `None`) is unchanged.

This is a real behavior change for `run_ILASP`'s one caller
(`OptimisingSpecLearner.find_adaptations_with_heuristic`), which had no
`try/except` around it - a large-enough spec's ILASP call could now
legitimately (not just when genuinely stuck) hit the 60s bound and raise,
crashing the whole BFS run instead of hanging forever. Added
`subprocess.TimeoutExpired` to `learn_new`'s existing except chain,
treating a timed-out hypothesis search the same as the other expected
"this branch didn't pan out" cases already handled there
(`NoWeakeningException`, `NoViolationException`,
`DeadlockRequiredException`). Reverted the 12GB heap experiment - it
didn't help and made the failure mode worse. Committed as `afd1f22`.

**Still open**: re-ran `colorsort_syn` after the timeout fix, with the
orphaned process cleaned up and memory freed. It did *not* crash - but
it also didn't finish. 108 minutes in, zero specs recorded, versus the
*previous* (buggy-timeout) run finding 2 valid specs within its first 3
minutes. Working theory: BFS may now be burning through many candidate
branches that each legitimately wait out the full 60s ILASP timeout
before giving up, rather than the (much rarer) genuinely-stuck call that
used to hang forever - i.e. the timeout fix traded "eventually crashes
with a clear error" for "takes a very long time with no error and no
result," on a spec this large. Killed the run rather than let it continue
indefinitely. **Not resolved this session** - the underlying memory/
performance ceiling for a spec this size is a separate, harder problem
(likely needs either a shorter/tuned ILASP timeout specifically for large
specs, profiling of where the 100+ minutes actually goes, or accepting
that ColorSort's full BFS search is currently impractical to run to
completion and treating the 2-specs-found result as sufficient evidence
the naming fix works).

## Part 4: is arbiter/minepump/gyro really "running forever"?

Asked to run all `_syn` tests in parallel, several ended up running far
longer than expected. Two `_syn` bundled-run attempts got "killed" by the
harness and were relaunched individually; by the time colorsort's
`Bus error` investigation was underway, `ps aux` showed `arbiter_syn`,
`minepump_syn`, and `gyro_syn` pytest processes still running as real OS
processes 40+ minutes after each had been reported "killed." **The
harness's "killed" status for a background task does not reliably mean
the underlying process actually died** - this happened repeatedly this
session (three pytest processes, plus separately the 10+-hour ILASP
zombie in Part 3). Not a repo bug, but a real operational gotcha worth
remembering for any future long-running background test session.

Killed the three stale processes. Immediately after, a notification
arrived reporting `arbiter_syn` "completed (exit code 0)," and its output
directory (`tests/test_files/out/repair_syn/arbiter_2026-07-24/`)
contained 23 final specs, matching the historical baseline from
2026-07-23. Reported this as "arbiter completed successfully" - too
quickly.

Challenged on it (correctly): asked whether arbiter is really expected to
finish in under 24 hours, since that contradicted prior experience of
these tests "running forever." Re-checked the evidence rather than
defending the claim: `arbiter_2026-07-24/log.txt`'s own `Started at`
timestamp read `09:29:40` - a full 70 minutes *before* the `10:40AM`
start time `ps aux` had shown for the specific PID launched today. The
log also had roughly double the line count of the single-run 2026-07-23
log for the same case study.

**This means the "23 final specs, exit 0" result is not trustworthy
evidence of a single clean run finishing quickly** - it's consistent with
*at least two* overlapping `arbiter_syn` invocations (very likely
including a first bundled `-k "_syn"` attempt from earlier in the session
that, per the pattern above, probably never actually died when reported
"killed") writing into the *same* output directory concurrently.
`run_bfs_repair_syn_unique`'s output path
(`out_test_dir_name = f"./test_files/out/repair_syn/{case_study_name}_{self.date_str}"`,
in `tests/test_main/test_bfs_repair_orchestrator.py`) is scoped only by
case-study name and *date*, not by run or process ID - any two
invocations of the same test on the same day collide, interleaving
`log.txt` and overwriting each other's numbered `final_specs/spec_N.spectra`
files.

**Not resolved this session.** Two follow-ups worth doing before trusting
any timing claim about these three tests again:
1. A single, isolated, freshly-cleared invocation of `arbiter_syn` (or
   `minepump_syn`/`gyro_syn`), watched end-to-end with nothing else
   running concurrently, to get a real, trustworthy runtime.
2. Consider making `out_test_dir_name` unique per run (e.g. include a
   PID, timestamp, or `uuid4`) rather than per case-study-per-day, so two
   concurrent or retried invocations can never silently corrupt each
   other's results again - this is a genuine latent bug independent of
   anything else found this session.

No currently-running arbiter/minepump/gyro process was found when this
was investigated. Whether the user's "runs forever" experience reflects
these tests being *individually* slow, or is itself an artifact of the
same kind of directory-collision/zombie-process contamination described
above, remains an open question.

## Part 5: `test_spectra_specification.py` - my "9 pre-existing failures" were wrong

Confidently reported 9 tests in `test_helpers/test_spectra_specification.py`
as pre-existing failures unrelated to this session's changes, "confirmed"
via `git stash` (same 9 failed identically with and without the diff).
Told the failures didn't reproduce for the user at all - all passing.

Investigated rather than assumed either side was right. The actual
failure: `Popen(['ltlfilt', ...])` raising because `ltlfilt` (a spot CLI
tool) wasn't found on `PATH`. It **is** installed -
`/Users/tg4018/miniforge3/envs/arm_env/bin/ltlfilt` exists - but every
test command this session had invoked the interpreter by its absolute
path (`/Users/tg4018/miniforge3/envs/arm_env/bin/python -m pytest ...`)
without ever running `conda activate arm_env`, so `arm_env/bin` was never
prepended to `PATH`. `git stash`-comparing whether a failure exists
with/without a diff only proves it isn't caused by *that diff* - it says
nothing about whether the test environment itself is correctly set up,
and I conflated the two. With `conda activate arm_env` actually run
first: all 40 tests in that file pass.

**Lesson for next session**: always `source
/Users/tg4018/miniforge3/etc/profile.d/conda.sh && conda activate
arm_env` before running any test that shells out to an external CLI tool
(`ltlfilt`/spot, Spectra, clingo, ILASP) - invoking the interpreter by
absolute path is not equivalent to activating the environment, even
though imports work fine either way.

The other "pre-existing" failures reported this session
(`test_util/test_spec.py`'s 3, `test_components/test_new_spec_encoder.py`'s
2, `test_perf/test_cs_to_trace_performance.py`'s 2) were re-verified with
`conda activate arm_env` properly run first and do still fail - these are
real, not a PATH artifact.

## Part 6: test cleanup

Two follow-up requests, both completed:

**Removed `tests/test_wrappers/test_spec.py`** (not to be confused with
`tests/test_util/test_spec.py`, a different file, still present, testing
`SpectraSpecification`/`run_all_unrealisable_cores_raw` instead). This
one tested `spec_repair/wrappers/spec.py`'s `Spec` class - confirmed via
grep that `Spec` has zero usage outside `legacy/` code, this test file,
and `scripts/old_scripts/process_statistics.py` (itself only reachable
through `CSVBuilder`, which nothing in `main/` or `spec_repair/components/`
references) - fully disconnected from the active BFS-repair pipeline
(`SpectraSpecification` is what that actually uses throughout). The file
also had two tests hardcoded to always fail
(`self.assertTrue(False)`), and was already on this project's standing
skip-list ([[feedback_test_scope]]) for exactly this reason. Deleted
outright rather than keep skipping indefinitely. Committed as `c3b372f`.
(The memory entry for the skip-list should be updated to drop this file
now that it no longer exists.)

**Refreshed stale `test_new_spec_encoder.py` golden fixtures**
(`tests/test_files/test_components/minepump_strong_WA_no_cs.{lp,las}`).
These had gone stale across *two* earlier, already-committed fixes -
`301d5f1`'s `not weak_timepoint(T2,S)` antecedent-side addition and
`726f1b6`'s `prev_timepoint_exists` background-knowledge predicate -
neither of which happened to touch these two fixture files in their own
test-update pass. Regenerated both by actually running the encoder
against `minepump_strong.spectra` and overwriting the fixtures; diffed
before committing to confirm the only changes were exactly those two
additions, nothing else had drifted. Committed as `475bad8`.

## Final state

Full suite (`tests/`, excluding `test_main/` and `test_new_research.py`
per the standing skip-list, `conda activate arm_env` run first): 725
passed, 6 failed, 5 skipped, 28 xfailed. All 6 failures pre-existing and
unrelated to this session's changes (confirmed via `git stash`):
`test_debug/test_asp.py::test_hongbo` (already on the skip-list),
`test_perf/test_cs_to_trace_performance.py` (2), and
`test_util/test_spec.py::test_all_unrealisable_cores_raw_*` (3, a
different file from the one removed in Part 6).

Four commits landed on `prev-consequent-support`:
`1f29240` (ASP-safe naming), `afd1f22` (subprocess timeout enforcement),
`475bad8` (fixture refresh), `c3b372f` (test_spec.py cleanup).

## Open items for next session

1. **ColorSort's BFS repair still doesn't complete in reasonable time**
   (Part 3) - not crashing anymore, but also not finishing. Needs either
   profiling, a size-aware ILASP timeout, or a decision that partial
   results are good enough for this case study.
2. **arbiter/minepump/gyro true runtime is still unknown** (Part 4) -
   needs a clean isolated run, and `out_test_dir_name` should probably be
   made run-unique regardless, since concurrent-run collision is a real
   latent bug independent of the timing question.
3. **Harness "killed" ≠ actually dead** for background bash tasks -
   operational caveat, watch for zombie processes after any session with
   multiple long-running background invocations.
4. **Always `conda activate arm_env`** before trusting a test failure as
   real (Part 5).
