# Preparing the BFS-repair experiments, the humanoid ASP-naming bug, and the Next/Prev boundary fixes — session notes

Session date: 2026-07-23. Branch: work started and mostly landed on `main`
(3 commits, pushed); the last piece (Prev-in-consequent) is in progress on
a new branch, `prev-consequent-support`, not yet committed. No session on
2026-07-22 - the only activity that day was re-running
`test_generate_stronger_specs_*` locally (visible in
`tests/test_files/out/generate_stronger/*_2026-07-22/`), no code changes,
no commits.

## Starting point

You wanted the GPU-box tmux experiment script (from an earlier session,
never checked into the repo) reviewed and extended: pick one of the
case studies that had an `original.spectra` but no strengthened variant yet,
add it as a new BFS-repair test, and rewrite the script to run it
alongside the existing arbiter/traffic_single/traffic_updated/lift/minepump
ones.

## Preparing 5 new case studies

Rather than just one, you asked for all five missing case studies
(`colorsort`, `gyro`, `elevator`, `humanoid`, `pcar`). Found
pre-generated `mutation_N.spectra`/`violation_trace_N.txt` pairs already
sitting in `tests/test_files/out/generate_stronger/` from your own recent
`test_generate_stronger_specs_*` runs (the 2026-07-22 activity mentioned
above) and used the most recent (`mutation_0`, 2026-07-22) for each.
Flagged one quality issue before committing: `gyro` and `elevator`'s
mutual-exclusion clauses had been blown up by `to_dnf`'s naive (non-
minimizing) CNF-to-DNF conversion - logically correct, just needlessly
verbose (a 4-variable pairwise exclusion turning into a ~10KB single
line for gyro). You chose to proceed as-is rather than hand-recompact
them.

Added `test_bfs_repair_spec_{colorsort,gyro,elevator,humanoid,pcar}_syn`
to `tests/test_main/test_bfs_repair_orchestrator.py`, and wrote
`scripts/run_parallel_bfs_repair_syn.sh` (the tmux runner - new file, the
original wasn't in the repo). Fixed three issues in it along the way:
numeric window indices replaced with named ones (fragile if tmux's
`base-index` isn't 0 or a window is already open), a `tmux has-session`
guard so it refuses to collide with an already-running session instead
of silently reusing it, and each test's output now tees to a timestamped
log directory instead of only living in the tmux pane's scrollback.

## Running them locally surfaced real bugs, not just new tests

Asked to run the new tests and monitor for an hour. Local run needed
`brew install graphviz` first (missing `dot`, needed by the test
harness's debug graph rendering - unrelated to the new case studies,
would have blocked the pre-existing tests too).

`colorsort_syn` crashed immediately: `!Prev(x)` as a literal isn't
handled by the ASP encoder (`asp_exception_formatter.py`) - the exact
opaque, deliberately-unrewritten form left by `to_dnf` since the
2026-07-21 session. Left this one for later rather than guessing a fix,
given the history there.

`humanoid_syn` "passed" but produced zero specs - caught only because
you asked for exact intermediate/final spec counts per test, not just
pass/fail, and pushed back when the count was suspiciously empty
("that's odd if you're saying it does 'pass'"). Chased it down to three
compounding bugs, each one exposing the next as it got fixed:

1. `mitigation_strategies.move_one_to_guarantee_weakening` indexed
   `data.spec_history[0]` unconditionally - crashed when assumption
   weakening found no violation at all (spec_history still empty this
   early in the search). Now falls back to the spec the task started
   from.
2. Both `OrchestrationManager{Syntactic,Semantic}Equivalence.
   enqueue_new_tasks` used `elif prev:` to decide whether to index
   `counter_traces[-1]`, but `prev` being set doesn't guarantee
   `counter_traces` is non-empty. The correct condition
   (`elif data.counter_traces:`) was already sitting right below in each
   class's own `_get_task_id` - just never applied to the sibling method.
3. `mitigation_strategies.complete_counter_traces` let
   `NoViolationException` propagate uncaught when a trace violates
   neither assumptions nor guarantees, crashing the whole run instead of
   giving up on that BFS branch.

With all three patched, humanoid still silently found nothing - the
*real* bug: ASP/Clingo requires atom (constant) names to start
lowercase; humanoid's SYNTECH15-derived names (`HeadMotor_bwd`,
`InputMoveMode_turn`, ...) don't, so clingo failed to ground the whole
generated program (confirmed directly: `atom(HeadMotor_bwd)` - "unsafe
variable" - exit code 65). `get_violations` never checked clingo's exit
status, so a hard grounding failure silently read back as "no violations
found" everywhere, which is what the first three bugs were actually
reacting to.

Per your instruction, fixed this at the parsing layer rather than at the
ASP-emission layer: `format_spec` (`spec_repair/util/formula_string_util.py`)
now runs a new `make_names_asp_safe` as its first step, renaming every
uppercase-leading variable and rule name consistently across the whole
spec text before anything else runs. This replaced an old, already-broken
half-attempt at the same fix (`re.sub('--[A-Z]', ...)`) whose regex
required no space after `--`, so it silently never matched real spec
text. `violation_trace.txt` is a separate file read raw (not routed
through spec parsing), so its atom references needed the same renaming
by hand - checked all 10 case studies, humanoid was the only one
affected.

Verified end to end this time (not just exit code): humanoid now finds
21 real specs, confirmed in `final_specs/` and in `log.txt`'s `Learned`
entries.

## Complete test table (this session's local runs)

| Test | Result | Notes |
|---|---|---|
| `elevator_syn`, `pcar_syn`, `lift_syn`, `traffic_single_syn`, `traffic_updated_syn` | Pass | No fixes needed |
| `humanoid_syn` | Pass | Fixed 4 bugs above |
| `colorsort_syn` | Crashed at the time | `!Prev(x)` gap - see below, now fixed but a *different* issue surfaced (see "Left open") |
| `arbiter_syn`, `minepump_syn` (baseline) | Still running as of writing | No prior local baseline for expected duration |
| `gyro_syn` | Very slow | Genuinely progressing, not deadlocked - traced a multi-hour stall to a single `ILASP` subprocess call, almost certainly the `to_dnf` DNF-blowup mutual-exclusion formula making the hypothesis search space intractable. Killed and restarted once already; restarted run is on another long `ILASP` call as of writing |

Killed once mid-session to distinguish "stuck" from "slow" (checked the
actual child process, not just the parent's CPU time in `ps` - the
parent looked frozen because it was synchronously blocked on the
`ILASP` child, which was very much alive and burning CPU).

## Next-in-antecedent: found and fixed

You asked whether `Next` in an antecedent had the same kind of gap as
`Prev` in a consequent. Built 4 minimal specs, ran them straight through
`NewSpecEncoder.encode_ASP` + clingo directly (bypassing the rest of the
pipeline) to observe real behavior instead of guessing. Confirmed a real
soundness bug: the synthetic "weak" timepoint the background ASP program
appends after a trace's last real timepoint (deliberately making both
`holds_at` and `not_holds_at` true there, so an unresolved
consequent-side eventuality gets the benefit of the doubt) has the
opposite, unsound effect when the same machinery is reused for an
antecedent - it unconditionally satisfies `next(x)` at the trace's end
regardless of what the trace actually says, manufacturing violations
that aren't real.

Fixed with one guard (`not weak_timepoint(T2,S)`) added to the
antecedent-side rule generator only
(`format_boilerplate_root_antecedent_holds` in
`asp_exception_formatter.py`), confirmed a no-op for `current`/`prev` and
only actually changing `next`'s behavior. Verified against the same 4
test cases, updated ~100 golden-string formatter tests it broke, full
suite green, plus a live-pipeline regression re-run
(elevator_syn/pcar_syn). Grepped all 10 case studies first: none use
`Next` in an antecedent today, so this was a real but previously
unexercised gap, not something silently corrupting an already-passing
result.

Full technical writeup, including the truth table for `Prev` derived
before touching anything and the proposed (at the time) fix for
`!Prev(x)` in a consequent, is in
[2026-07-23-next-antecedent-prev-consequent-asp-gaps.md](2026-07-23-next-antecedent-prev-consequent-asp-gaps.md).

## New branch: `prev-consequent-support`

You wanted `main` kept clean going forward, with feature work on
branches instead - reasonable, given `main` had just accumulated 3
commits' worth of bug-hunting in a single day. Created
`prev-consequent-support` off `main` (so it carries today's fixes) to
hold the Prev-in-consequent work specifically.

Implemented the fix proposed in the linked doc: `prev_timepoint_exists`
added to `files/background_knowledge.txt` (mirrors the existing
`next_timepoint_exists`, but for the start of a trace instead of the
end), and `asp_exception_formatter.py`'s `reformat_conjunction_to_op_
atom_conjunction` now recognizes `Not(Prev(literal))`, routing it to a
new `not_prev` bucket with two rules sharing one head (vacuous branch:
true when there's no predecessor; real branch: negated literal at the
real predecessor) - both antecedent and consequent sides. Verified
against 3 direct-clingo test cases covering the vacuous boundary on both
sides and the real (non-boundary) branch; all matched the truth table
exactly. Fixed the golden-string tests this broke, including one that
was asserting the *old* "should raise ValueError" behavior for
`Not(Prev(x))` - now updated to assert the correct output instead of a
crash. Full suite green (197 formatter tests, only the 9 known
pre-existing `ltlfilt`-missing failures elsewhere, unrelated).

**Not yet committed** - this was mid-verification when you called it for
the day. The code is written, tested, and working; `git status` on
`prev-consequent-support` will show it modified but unstaged next
session.

## Left open / for next session

- **A second, different colorsort bug just surfaced.** Running
  `colorsort_syn` end to end after the Prev fix still found zero specs.
  Traced it: some of colorsort's rule names contain literal spaces
  (e.g. `guarantee -- no pause is eternal`), which is invalid ASP syntax
  the same way humanoid's uppercase names were, but a different
  character class - `make_names_asp_safe` doesn't handle it yet. Same
  fix location, needs extending. Not started.
- `prev-consequent-support`'s changes need committing once you're back
  and want to review them.
- `gyro_syn`'s ILASP hang is a real cost of the unfixed `to_dnf`
  CNF-to-DNF blowup (2026-07-21's session, `enum_desugar.py`'s
  mutual-exclusion generator) - not urgent, but worth deciding whether
  to hand-recompact gyro/elevator's mutual-exclusion clauses (you
  declined earlier this session) or fix the blowup itself at some point.
- `arbiter_syn`/`minepump_syn` baseline runs and the restarted `gyro_syn`
  were all still running in the background on this machine as of
  writing - left running rather than killed, since you didn't ask either
  way.
- Known, documented (not yet designed) limitation of the Prev-in-
  consequent fix: `!Prev(x)` nested *inside* another temporal operator
  (e.g. `Next(!Prev(x))`) would need 2-hop timepoint composition, not
  built here. Verified by inspection this doesn't block colorsort - none
  of its actual formulas nest it that way - and existing asserts in
  `reformat_conjunction_to_op_atom_conjunction` would fail loudly rather
  than silently mishandle it if that combination ever comes up.
