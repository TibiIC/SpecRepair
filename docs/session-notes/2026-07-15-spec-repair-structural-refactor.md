# spec_repair/ + main/ structural refactor — session notes

Session date: 2026-07-15. Branch: `journal_final`. Landed as 5 local commits
on top of `f32b514`.

## Why

You flagged two problems: utility functions scattered everywhere, and
recurring circular-import issues when adding new code. Investigation found
concrete causes rather than just "things feel messy":

- `util/mittigation_strategies.py` imported from `components/`, `helpers/`,
  and `wrappers/` despite having zero in-package consumers — it alone
  created 3 of the 4 detected package-level import cycles.
- `ISpecification` lived under `components/interfaces/` but was implemented
  by `helpers/spectra_specification.py` and consumed by
  `helpers/counter_trace.py` — a real `helpers → components` back-edge,
  already worked around once via a `TYPE_CHECKING` guard.
- `helpers/` mixed domain-model classes (`CounterTrace`,
  `SpectraSpecification`, `GR1Formula`, ...) with genuinely behavioral
  subpackages (`formatters/`, `parsers/`, `heuristic_managers/`) — the name
  collided conceptually with `util/`.
- `util/spec_util.py` was 1558 lines with the highest import fan-in in the
  package (18+ importers), mixing ASP/trace conversion, DataFrame parsing,
  string-based formula manipulation, and JVM/Spectra-CLI integration.
- `special_types.py` mixed unrelated regex-pattern classes with a type
  alias, and carried a dead commented-out import — a fossil of a past
  circular-import workaround.

## What changed (5 commits, each independently verified + committed)

1. **`bf3b66b`** — `components/interfaces/` → top-level `spec_repair/interfaces/`;
   `util/mittigation_strategies.py` → `spec_repair/strategies/mitigation_strategies.py`
   (typo fixed). Kills the two real cross-package cycles.
2. **`896d8e5`** — `helpers/`'s 8 domain-model files (`adaptation_learned`,
   `counter_strategy`, `counter_trace`, `gr1_formula`, `ilasp_interpreter`,
   `spectra_atom`, `spectra_specification`, `trace`) → new `spec_repair/model/`.
   `helpers/` now only holds `formatters/`, `parsers/`, `recorders/`,
   `heuristic_managers/`, `repair_nodes/`, `weakness_measurement/`.
3. **`8ccccd1`** — `special_types.py` dissolved: regex-pattern classes →
   `util/patterns.py`, `StopHeuristicType` → `ltl_types.py` (now properly
   typed via a `TYPE_CHECKING` import instead of `Any`). `heuristics.py`
   moved from package root into `helpers/`.
4. **`af5d19f`** — `util/formula_util.py` merged into `util/ltl_formula_util.py`
   (both were small AST-based `py_ltl.formula` utilities with no reason to
   be separate files).
5. **`bb22177`** — the big one. `util/spec_util.py` split by concern into:
   - `util/asp_trace_util.py` — ASP/trace conversion, trace-list
     manipulation, clingo model generation
   - `util/spec_dataframe_util.py` — Spectra-to-DataFrame parsing
   - `util/formula_string_util.py` — generic string-based formula
     parsing/normalization (self-contained, no deps on the other two)
   - `util/file_util.py` — gained `write_trace`
   - **new** `wrappers/spectra_toolbox.py` — the JVM-backed
     `SpectraToolbox`/`SpectraCLI` integration (`realizable`,
     `synthesise_*`, `run_all_unrealisable_cores*`) plus the `ltlfilt`-based
     Spot semantic-equivalence cluster (it calls `realizable()`, so keeping
     it separate would have forced a `util → wrappers` back-edge)
   - `tests/test_spec_util.py` renamed to `tests/test_asp_trace_util.py`
     to match

Placement throughout followed the codebase's **existing** import direction
(`wrappers → util`, `components`/`model` → `wrappers`) rather than
introducing new backwards edges — e.g. `run_clingo_raw` stayed in `util/`
because `wrappers/asp_wrappers.py` already imported it from there.

## What was explicitly out of scope

- No logic was rewritten — this was a pure code-motion refactor. Function
  bodies moved verbatim.
- No deduplication of near-duplicate functions (e.g. the 4 different
  paren-stripping functions and 3 different splitting functions that
  coexisted inside the old `spec_util.py`, or the similarly-named but
  differently-typed `get_disjuncts`/`get_conjuncts` in
  `ltl_formula_util.py` vs `spot_ltl_conjoining_util.py` — one operates on
  a custom `LTLFormula` AST, the other on `spot.formula` objects, genuinely
  different types). That's a separate, riskier task requiring semantic
  verification, not a placement fix.
- `new_research.py` was **not** renamed (was planned, low-priority) —
  its only test importer, `tests/test_new_research.py`, has your own
  uncommitted WIP edits (path fixes, `@unittest.skip` additions) that were
  deliberately left untouched, and renaming would have forced touching
  that file's import line too.

## Left alone on purpose

- **`spec_repair/legacy/`** — confirmed zero live importers (nothing
  outside itself references it), so it was left completely untouched per
  explicit instruction. Its imports of the now-deleted
  `spec_repair.util.spec_util` module path are consequently broken. This
  was already true in spirit (the module was dead/WIP-marked) and nothing
  live depends on it, but worth knowing if that code is ever revived.
- **`tests/test_new_research.py`** — had uncommitted WIP changes, never
  touched by this session.
- **`tests/lib/`** — untracked pyvis-generated JS assets (`vis-network`,
  `tom-select`), unrelated to this refactor, left untracked.

## Verification performed

- `pytest --collect-only` after every phase: **808 tests collected**,
  matching the pre-refactor baseline exactly, every time.
- Full non-benchmark suite run in chunks after every phase (chunked because
  a single background shell call caps at ~10 minutes and the JVM/Strix
  integration tests are slow). `tests/test_main/` and
  `tests/test_new_research.py` were excluded from automated runs per
  instruction (already verified separately / known slow).
- Every failure seen was checked against the **pre-refactor codebase via
  `git stash`** to confirm it was pre-existing, not a regression:
  - `tests/test_util/test_spec.py::test_all_unrealisable_cores_raw_*` (3
    tests) — relative-path/cwd bug, pre-existing.
  - `tests/test_wrappers/test_spec.py::test_genbuf_*` (3 tests) — one is a
    literal `self.assertTrue(False)` placeholder, pre-existing.
  - No other failures appeared at any point.
- Final pass: re-ran the import-graph cycle detector — the only "cycle"
  left is a `TYPE_CHECKING`-only edge (`ltl_types` ↔ `model.counter_trace`,
  same safe pattern as the pre-existing `new_spec_encoder`↔`counter_trace`
  guard). Confirmed with a direct `python3 -c "import ..."` smoke test
  across every touched/new module plus `main/` — no `ImportError`.
- Repo-wide grep swept for stale references to every old import path
  (`spec_util`, `formula_util`, `components.interfaces`,
  `util.mittigation_strategies`, `special_types`, `helpers.<domain-class>`,
  root `heuristics.py`) across `spec_repair/`, `main/`, `scripts/`,
  `pipeline/`, `tests/` — zero hits outside `legacy/`.

## Follow-ups picked up next session (2026-07-16)

- `pytest-timeout` pinned into `requirements.txt`/`pip_requirements.txt`.
- 5 commits pushed to `origin/journal_final`.
- `new_research.py` rename still deferred; investigating better homes for
  its functions within `spec_repair/` (not a rename, a relocation).
- `legacy/` being kept as-is on purpose — there's dead code in there
  slated to be dug out and modernised in an upcoming session.
