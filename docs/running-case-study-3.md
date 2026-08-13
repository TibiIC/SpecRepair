# Running case_study_3 end to end

The order matters: traces, then preconditions, then experiments, then
post-processing. Each step has a way of failing that looks like success, and
they are noted where they arise.

See [running-on-ssh.md](running-on-ssh.md) for the shell setup, picking a box,
and reading exit codes.

## 1. Generate the traces

    python scripts/generate_case_study_3.py                    # all case studies
    python scripts/generate_case_study_3.py amba genbuf        # named ones
    python scripts/generate_case_study_3.py amba --traces 5

Writes `input-files/case-studies/spectra/case_study_3/<case>/violation_trace_<n>.txt`
plus a `traces.json` manifest recording, per trace, the seed, the assumption it
aimed at, and everything it actually violated.

On a GPU box: the large specifications need CUDD. Locally only the small ones
will finish.

The controller is cached under `tests/test_files/out/controller_cache/`, keyed
by a hash of the specification, so the second run of a case study skips
synthesis - which for amba is about eight minutes.

**Two case studies produce nothing, for different reasons.** `arbiter`'s only
assumption is `GF(a)`, and no finite trace refutes liveness - it is excluded by
construction and always will be. `humanoid` is a limitation of ours: the solver
plans, the controller accepts the first move, and the second hits an
environment deadlock.

## 2. Check the preconditions

**Do this before launching anything.** A 24-hour sweep on invalid traces is the
most expensive mistake available here.

    python scripts/check_case_study_preconditions.py case_study_3
    python scripts/check_case_study_preconditions.py case_study_3 genbuf
    python scripts/check_case_study_preconditions.py case_study_3 --skip-realisability

Exit status is 0 only if everything passes, so it can gate a sweep.

It asserts:

1. `original.spectra` is **realisable**;
2. **guarantees hold at every step except possibly the last** - the last state
   is the controller's own output, and once the environment has broken an
   assumption GR(1) releases the system;
3. **assumptions hold at every step except the last, where at least one fails** -
   both halves matter: a trace that broke one early and carried on has a prefix
   that is not assumption-respecting behaviour.

Liveness is excluded from both, since a finite trace neither satisfies nor
refutes `GF(p)`.

`--skip-realisability` exists because that check hangs on macOS for a large
specification (JTLV, no CUDD). It says so in its output rather than reporting a
weaker check as a pass.

## 3. Run the experiments

    EXCLUDE="colorsort elevator gyro lift minepump minepump_liveness pcar traffic_single traffic_updated" \
      LEARNER=fastlas FASTLAS_RUNS=10 ./scripts/run_case_study_3.sh

    LEARNER=ilasp LEARNER_TIMEOUT=3600 ./scripts/run_case_study_3.sh
    TRACES="0 3 4" LEARNER=fastlas ./scripts/run_case_study_3.sh genbuf
    ./scripts/run_case_study_3.sh minepump 2

One tmux window per run, capped by `MAX_WINDOWS` (default 4 - a run holds
5-9GB and the boxes have 26-58GB free).

Knobs worth knowing:

| variable | default | why |
| --- | --- | --- |
| `LEARNER` | ilasp | `fastlas` is the other arm |
| `LEARNER_TIMEOUT` | 600 | seconds per learning task. At 60 the sweep measured the timeout, not the learner |
| `FASTLAS_RUNS` | 1 | solutions enumerated per step; 10 mirrors ILASP |
| `MAX_WINDOWS` | 4 | concurrency |
| `EXCLUDE` | - | case studies to leave out |
| `TRACES` | all on disk | which traces to run |

The runner refuses to start if another sweep is open on that box, because both
would write into the same output tree. That refusal is a feature; move to
another box rather than using `FORCE=1`.

## 4. Post-process

Steps 2-4 (merge, guarantee-maximal, semantically unique) need **nothing** from
step 5. Only the graphs use trivial solutions, and they degrade gracefully
without them. So run the merge chain first and do not wait:

    python scripts/run_experiment_pipeline.py 2026-08-12 --setup case_study_3 \
        --case-study amba_trace0_fastlas --skip-graph

    python scripts/generate_trivial_solutions.py 2026-08-12 --setup case_study_3
    python scripts/run_experiment_pipeline.py 2026-08-12 --setup case_study_3 \
        --case-study amba_trace0_fastlas

`--case-study` takes the run directory name minus the date, so
`amba_trace0_fastlas`, not `amba`.

On a GPU box, point it at the runs in place and skip the pull entirely:

    --runs-root tests/test_files/out/case_study_3

Locally, pull first:

    REMOTE_SUBDIR=case_study_3 ./scripts/pull_experiment_from_ssh.sh 2026-08-12 gpu12

**Only post-process runs whose `status.txt` says `phase: done`.** A directory
caught mid-run has a partial `final_specs/` that will merge as though it were a
result.

The merge is the step that does not always finish: it merges everything, checks
realisability, and splits in half recursively when the union is unrealisable.
Give it a timeout per run and process smallest-first.

## 5. Inspect a specification by hand

    python scripts/dump_env_step_asp.py amba --list-targets
    python scripts/dump_env_step_asp.py amba --target a30 --horizon 2 -o /tmp/a.lp
    clingo /tmp/a.lp 5

Writes the exact ASP program the generator hands to clingo when it chooses an
environment step. `--prefix-steps` pins synthetic all-false states, which for
some case studies violate the guarantees on their own and make the program
unsatisfiable for a reason the real generator never hits - inspect with
`--prefix-steps 0` unless you have a real prefix.

`SPEC_REPAIR_DUMP_UNSAT=<dir>` keeps the *real* program whenever a solve comes
back unsatisfiable, prefix and all. That is the one to bisect when something
will not plan.

## 6. Known failures, so they are not rediscovered

* **Spot segfaults** in `spot::fnode::unique` (`SIGSEGV`, `si_addr 0x30`) on
  deep searches and during merges. Deterministic, reproduces across machines,
  kills the longest runs - so specification counts have a survivorship bias
  until it is fixed. `hs_err_pid*.log` lands in the sweep's `jvm/` directory.
* **ILASP cannot repair amba or genbuf** at 600s or 3600s: 9 of 10 runs finish
  having produced nothing. FastLAS does all five amba traces cleanly.
* **genbuf runs die seconds after `LEARN`** at depth 0, mixed SIGKILL/SIGTERM,
  no crash log. Cause unknown.
