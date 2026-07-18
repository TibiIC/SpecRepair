# Mutation-generator investigation, deprecated-Spec cleanup, and the genbuf hang — session notes

Session date: 2026-07-17. Branch: `journal_final`. 2 commits on top of `26df4e5`
(the previous session's tip).

## Starting point

`spec_repair/diagnosis/spec_mutation.py`, `main/mutated_spec_generator.py`, and
their test were already sitting in the working tree, uncommitted, at the start
of this session (a prior session's WIP). The ask was: verify the suite is
clean, then commit and push — but first, you wanted to understand why the
mutation generator's output looked so sparse for some case studies.

## Why minepump/arbiter/traffic_single generate so few mutations

Walked the actual generation logic (`_try_strengthen` in `spec_mutation.py`)
against each case study's `ideal.spectra` to find out whether this was a bug
or expected:

- **arbiter has a hard ceiling of 1.** Its only assumption, `a_often: GF(a)`,
  has no antecedent and a single-literal consequent, so only one of the three
  strengthening patterns applies at all (justice → invariant, `GF(a)` →
  `G(a)`). There is no second variant to find — 1 is correct, not a bug.
- **minepump has a ceiling of 2, but only 1 survives.** Only one of its two
  assumptions is structurally mutable (the other isn't `G`-wrapped, so none
  of the three patterns apply). That one assumption has a 2-conjunct
  antecedent, giving exactly 2 candidate mutations. Generated both directly
  and fed them through `generate_violating_traces`: one produces a violating
  trace, the other doesn't — clingo finds nothing within the search's
  3-timepoint window, so `generate_stronger_specs_with_violations` silently
  drops it. The real bottleneck here is the trace-search depth, not the
  mutation generator.
- **traffic_single "always hitting the same assumption" was a coincidence.**
  All three of its assumptions are structurally eligible and their mutations
  are all realizable (verified directly). Re-ran `generate_realizable_mutations`
  with fresh unseeded RNG several times and got well-mixed formula selection
  across trials — the one run you saw in `test_files/out/` had just drawn the
  same formula three times in a row by chance, with only 3 draws and no seed
  fixing anywhere.
- **Only one violation trace per mutation** was also not a limitation — it's
  the test's `n_traces_per_mutation=1` default. `generate_violating_traces`
  already loops and feeds each found trace back into `compose_old_traces`,
  which adds ASP constraints excluding it, so repeat calls are pushed toward
  new distinct traces. Raising the parameter should yield more, bounded only
  by what clingo can find in the 3-timepoint window.

No code changes came out of this — it was diagnosis, at your request ("don't
necessarily implement anything, but do explain").

## Verification pass: the genbuf hang

Running the full suite (`tests/`, excluding `test_main/` and
`test_new_research.py` per standing policy) stalled at 708/747 with the
process itself sitting at 0% CPU for 30+ minutes — looked like a deadlock.
`ps`/`lsof` on the process tree showed otherwise: a live child process,
`ltlfilt -c -f <genbuf ideal spec> --equivalent-to <genbuf strong spec>`,
burning 100% CPU. `tests/test_wrappers/test_spec.py::TestSpec::test_genbuf_compare`
shells out to spot's `ltlfilt` to check LTL equivalence between genbuf's
`ideal.spectra` and `strong.spectra` — a 5-slot buffer arbiter spec with
30+ conjuncts over many boolean variables. This is genuine, expensive
automaton-based equivalence checking, not a bug — this is exactly the
no-timeout risk flagged as left-open in the 2026-07-16 session notes
(`is_left_cmp_right` in `wrappers/spec.py` has no timeout on
`Popen.communicate()`), now actually observed hanging a run.

You clarified `Spec` (`spec_repair/wrappers/spec.py`) is deprecated —
superseded by `SpectraSpecification` in `spec_repair/model/`. Killed the run,
excluded `tests/test_wrappers/test_spec.py` specifically (not the whole
`test_wrappers/` directory — `test_strix.py` and `test_asp_wrappers.py` are
still in scope), and saved this to memory alongside the existing
`test_main`/`test_new_research` skip policy so future verification passes
exclude it automatically without re-investigating.

## TestSpecRecorder migrated off Spec

Mid-session you flagged `tests/test_builders/test_spec_recorder.py` was still
constructing `Spec(...)` objects, despite `Spec` being deprecated. Checked
what it was actually testing: `UniqueSpecRecorder` is typed for
`SpectraSpecification` and only worked with `Spec` because `Spec.__eq__` and
`SpectraSpecification.__eq__` happen to implement the same ASM+GAR
equivalence check (one via `ltlfilt` subprocess, the other via spot's Python
API directly) — so the test was duck-typing past its own type hints without
actually exercising what production code passes in. Swapped
`Spec(copy.deepcopy(x))` for `SpectraSpecification.from_str(x)` against the
same string fixtures; all 3 cases pass unchanged.

## Full suite result

694 passed, 5 skipped, 28 xfailed, 5 failed — the same 5 failures both before
and after this session's changes, confirmed by reproducing them against a
`git stash`'d clean baseline:

- `test_cs_to_trace_performance[cs_line0/1]` — `AttributeError: 'list' object
  has no attribute 'dead_state'` in `spec_repair/model/counter_trace.py:171`.
- `test_all_unrealisable_cores_raw_{ideal,multiple,one}` — CWD-relative path
  (`SpecRepair/../input-files/...`) not resolving under this invocation,
  hitting the Java toolbox as a `FileNotFoundException`.

Neither touches any file in this session's diff. Pre-existing, unrelated,
not investigated further this session.

## Commits

- `1f9fe73` — the mutation generator itself (`spec_mutation.py`,
  `mutated_spec_generator.py`, its test, and the `get_conjuncts_from_conjunction`
  move out of `legacy/dead_ltl_formula_util.py` into `util/ltl_formula_util.py`
  now that it has a live caller again).
- `b84ca99` — `TestSpecRecorder` migrated off `Spec`.

## Left open / for next session

- The no-timeout risk on `Popen.communicate()` calls (`ltlfilt` in
  `wrappers/spec.py`, and `run_clingo_raw`/`run_ILASP_raw`) is now confirmed
  to bite in practice (genbuf), not just theoretical. Still unfixed — worked
  around this session only because the specific test that hit it uses the
  deprecated `Spec` class and could be excluded outright. `run_clingo_raw`/
  `run_ILASP_raw` don't have that escape hatch if something in the mutation
  generator's clingo-based trace search ever hangs the same way.
- The mutation generator's trace search is capped at 3 timepoints
  (`generate_trace_asp`) — this is what silently dropped one of minepump's
  two valid mutations. Worth deciding whether that bound should be
  configurable if richer case studies need deeper traces to find a
  violation.
- The two other files in `tests/test_wrappers/` (`test_strix.py`,
  `test_asp_wrappers.py`) are still in scope and untouched — only
  `test_spec.py` was excluded, since only the `Spec` class itself is
  deprecated.
- `spec_repair/wrappers/spec.py` (`Spec`) itself is confirmed dead-end
  (deprecated, only remaining test now excluded) — a candidate for a future
  `legacy/` sweep alongside its remaining non-test callers, if any.
