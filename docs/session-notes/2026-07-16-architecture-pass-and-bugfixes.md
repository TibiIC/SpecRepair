# spec_repair/ architecture pass, tree-formation and JVM-setup bug fixes — session notes

Session date: 2026-07-16. Branch: `journal_final`. 10 commits on top of `bb22177`
(the previous session's tip).

## Housekeeping carried over from last session

- `pytest-timeout` pinned in `requirements.txt`/`pip_requirements.txt` at the
  version actually installed (`2.4.0`).
- `tests/lib/` (pyvis-generated JS/CSS assets, same class of artifact as the
  already-ignored `/web/lib/`) deleted and gitignored.
- `tests/test_new_research.py` had pre-existing uncommitted WIP (relative-path
  fixes, `@unittest.skip` markers on known-slow/broken tests) — committed.

## Architecture pass (7 phases, each independently verified and committed)

You asked me to actually answer the boundary questions the previous session's
refactor left open: were `enums.py`/`exceptions.py`/`ltl_types.py` well
placed, was `components/` vs `helpers/` a correct split given `helpers/`
hides its own local interfaces, was pulling `interfaces/` out of
`components/` actually right, what makes something belong in `model/`
(specifically `ilasp_interpreter.py`), and why `mitigation_strategies.py`
lived apart from the `Mitigator` components it serves. Separately: reorganize
every function in `util/` by actual scope, splitting further where sensible,
reducing duplication, and sweeping dead code into `legacy/`.

Findings and decisions:

- `enums.py`/`ltl_types.py` stay at root — genuinely broad usage (12+ and 4+
  subpackages) plus a root-to-root dependency between them. `exceptions.py`
  stays too, despite narrower usage — no single better owner, and `model/`
  already reaches into `components/` elsewhere anyway, so there's no strict
  layering being protected by moving it.
- `interfaces/` at top level (last session's call) was correct, and now
  covers everything of that kind: `IRecorder` and `IHeuristicManager` moved
  there from stranded `helpers/` subpackages.
- **Real fix for `components/` vs `helpers/`**: `helpers/recorders/` and
  `helpers/heuristic_managers/` are DI-pluggable strategy components exactly
  like the ones already in `components/` — moved there. `helpers/` now only
  holds format adapters (`formatters/`, `parsers/`) and self-contained
  algorithm libraries (`weakness_measurement/`, `heuristics.py`).
- `model/ilasp_interpreter.py` → `helpers/parsers/` — confirmed it's a
  stateless two-staticmethod regex decoder of ILASP's raw stdout, not a data
  structure, same shape as `strix_cs_parser.py`.
- `strategies/mitigation_strategies.py` → `components/mitigators/` (the
  top-level `strategies/` package retired). `new_research.py`'s three
  functions → `diagnosis/trivial_solution.py` (revised mid-session from an
  earlier `strategies/` proposal once it was clear the function signatures
  don't match `mitigation_strategies.py`'s shape at all).
- `util/` reorganized by scope: `specification_helper.py` (the worst
  grab-bag file) dissolved into `util/subprocess_util.py` (new),
  `formula_string_util.py`, and `legacy/case_study_helpers.py`; duplication
  reduced (three near-identical hitting-set search implementations
  collapsed into one, `fold_or`/`disjoin`/`disjoin_all` collapsed from three
  copies of the same one-liner into one, several smaller internal dupes in
  `asp_trace_util.py` cleaned up).
- `legacy/` sweep: ~18 whole files with zero callers anywhere (including
  tests) moved there, plus assorted dead functions inside otherwise-live
  files, verified individually (a first-pass automated grep produced a
  couple of false positives, caught by reading real call chains before
  moving anything). Also did a best-effort fix of `legacy/`'s pre-existing
  broken `spec_util` imports (broken since before this session), repointing
  them at where those functions actually live now.

Every phase: `pytest --collect-only` held at 732 tests throughout, full
suite runs showed the same 8 pre-existing failures every time, stale-import
greps came back clean. Nothing here changed behavior — pure code motion plus
safe, verified duplication removal.

## Two real bugs found and fixed

### 1. Tree-formation dedup was quadratic with an expensive constant factor

You asked me to run the first 5 `test_bfs_repair_orchestrator.py` tests and
find an error. `test_bfs_repair_spec_arbiter` timing out turned out to be
expected (you confirmed arbiter is meant to run for a long time — that's not
a bug). Chasing it down through `minepump` instead (not one of the tests you
named, but where the real error showed up) found it:

`OrchestrationManagerSemanticEquivalence.enqueue_new_tasks`/`_get_task_id`
(and the same pattern in `..._aw_merge.py`) scan every previously-visited
search-tree node on every single task enqueue, checking
`visited_node[0] == past_spec and visited_node[1] == past_data`. Python's
`and` only short-circuits after evaluating the *first* operand — and the
first operand here was the **expensive** one: `SpectraSpecification.__eq__`,
which does a `deepcopy` plus SPOT formula conversion plus automaton
equivalence checking, called against *every* prior node regardless of
whether the far cheaper counter-trace/learning-type comparison would have
ruled it out immediately. Cost grows with the size of the search tree.

Fixed by reordering the `and` operands (cheap check first) in three places
across two files. Pure reordering — same boolean result, no behavior change,
only cost. Confirmed via `test_bfs_repair_spec_minepump`, which was hanging
inside this exact code path: after the fix it progresses much further before
hitting a *separate*, later bottleneck (see below). `traffic_single`,
`traffic_updated`, and `lift` — the tests you actually asked me to check —
passed cleanly both before and after this fix; I never managed to reproduce
an error there specifically.

### 2. Duplicate, conflicting JVM bootstrap

You flagged that `spectra_toolbox.py` sets up a JPype-wrapped Java object and
asked me to check it was done to standard practice, "wherever it is used."
Following that led to a second, independent `jpype.startJVM()` call in
`scripts/controller_shield.py` — its own classpath, its own `atexit` shutdown
handler, entirely unaware of the other one. JPype only allows one JVM per
process with a classpath fixed at first start, so whichever module happened
to import first silently determined which jars were actually available for
the rest of the process. This is exactly what caused the
`Class uk.ac.imperial.logix.AdaptiveShield is not found` error from earlier
in the session (attributed at the time to JVM contention between concurrent
background test runs — it wasn't just that).

Fix: new `spec_repair/wrappers/jvm.py` is now the single source of truth,
combining every required jar (`PATH_TO_TOOLBOX`, `PATH_TO_CLI`, and
`PATH_TO_SHIELD` — newly centralized in `config.py` alongside the other jar
paths, previously hardcoded inline in `controller_shield.py`) into one
`startJVM()` call with one `atexit` shutdown handler. Both consuming modules
now just import it for the side effect before doing their own `JClass()`
lookups. Also brought the `startJVM()` call itself up to current
jpype/JDK practice while in there:

- `classpath` as a proper list instead of jars joined with a hardcoded `":"`
  in one string (only ever worked by POSIX accident)
- `jvmpath` passed explicitly as a keyword rather than relying on jpype's
  positional-argument path-detection heuristic
- `convertStrings=False` set explicitly (jpype's own recommended default,
  and consistent with this codebase's existing explicit `JString`/`JArray`
  usage)
- `--enable-native-access=ALL-UNNAMED` added, silencing the
  "restricted method in java.lang.System... use
  --enable-native-access=ALL-UNNAMED" warning that showed up on every single
  JVM start all session (the configured JVM is OpenJDK 25, where JEP 472's
  native-access restrictions apply)
- `run_spectra_cli()`'s legacy `jpype.JPackage(...)` calls switched to
  `jpype.JClass(...)`, matching the style already used elsewhere in the same
  file

Verified: both import orders now resolve all classes correctly with a
single clean JVM start/shutdown; `adaptive_controller_shield.py` still runs;
full suite re-run shows the same 8 pre-existing failures, no regressions.

## Left open / for next session

- The clingo/ILASP subprocess calls (`run_clingo_raw`, `run_ILASP_raw`) and
  the `ltlfilt` equivalence-check call (`is_left_cmp_right` in
  `wrappers/spec.py`) all run with no timeout on `Popen.communicate()`. This
  is what `test_genbuf_compare` hits (confirmed hangs past 8+ minutes) and is
  part of what `minepump`'s search eventually reaches too, post-fix. Flagged
  but not changed this session — pre-existing, and a real design decision
  (what timeout is reasonable for a solver call?) rather than a quick fix.
- `new_research.py`'s relocation to `diagnosis/trivial_solution.py` was a
  revision of what I'd proposed earlier in the session — worth knowing if
  anything downstream still assumes the old name/location.
- `legacy/` is confirmed importable again (`old_experiments.py` aside, which
  is blocked only by a missing `sympy` dependency, not code) — ready for
  whatever you want dug out and modernized next.
