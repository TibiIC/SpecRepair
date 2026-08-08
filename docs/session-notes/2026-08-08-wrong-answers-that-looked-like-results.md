# Wrong answers that looked like results

Report date: 2026-08-08. Picks up where
[2026-08-07](2026-08-07-the-debug-graph-was-eating-the-experiments.md) left off -
three of the commits below landed after that note was written.

**Short version.** Yesterday closed with one open item flagged as the most
valuable on the list: *a failed clingo is read as "no violations"*. Fixing it
led straight into a second, worse instance of the same shape - an ASP encoding
that was silently wrong because negating an atom **mutated the specification**.
Both produced confident wrong answers rather than errors, which is why the
elevator result had looked like a mystery for two days.

A third bug, an `IndexError` killing 11 of 57 ILASP runs, turned out to be the
debug graph again - the fourth time.

All three are fixed, the preconditions are re-audited under the corrected
encoder (**107 scenarios, 0 BAD**), and case_study_2 and case_study_3 have been
restarted.

## 1. A solver that cannot run is not a solver that found nothing

`get_violations` returned an empty list for both. So on the Slurm compute
nodes, where clingo cannot load `liblua5.1.so.0` and exits 127 with empty
output, a trace that passes the precondition check locally was reported as
violating **nothing at all**, and the run stopped blaming the case study.

The cause was upstream: `run_subprocess` returned stdout alone, discarding both
stderr and the exit code, so no caller could tell the difference.

Clingo signals its verdict through the exit code - **10** SATISFIABLE, **20**
UNSATISFIABLE, **30** satisfiable and exhausted - and anything else means it
never reached one. The exit code is the only reliable test here: a malformed
program exits **65** but still prints `UNKNOWN`, so reading the output cannot
distinguish an error from an answer. `UNSATISFIABLE` stays a verdict, not a
failure; the repair depends on it.

`run_subprocess` now takes an optional `ok_returncodes` and raises
`SolverInvocationError` with the code and stderr. Off by default: the other
callers each read failure out of their own output, and adding a check for them
would change what they see.

Verified against a stub clingo exiting 127 with the real message:

    before:  []                          -> "violates no assumption at all"
    after:   SolverInvocationError: clingo exited 127 (expected one of [10, 20, 30])
             stderr: error while loading shared libraries: liblua5.1.so.0

## 2. Negating an atom mutated the specification

The elevator question from two days ago: a state with `floor_middle` **and**
`floor_upper` true reported no violation of `floor_mutual_exclusion`, which is
precisely what that assumption forbids.

`format_exp` handled `Not(atom)` by flipping the atom's stored value in place:

```python
formula.value = not formula.value
return self.format_exp(formula)
```

Formatting the same object twice therefore flipped it back, so every other
occurrence of a negated atom came out with the wrong polarity. `negate_literal`,
in the same file, already did it correctly by returning a new
`AtomicProposition`.

`G(!(fl&fm) & !(fl&fu) & !(fm&fu))` normalises to eight disjuncts of negated
atoms. The encoding alternated with a period of four:

| Disjunct | Formula | Encoded as | |
| --- | --- | --- | --- |
| 0 | `!fl & !fl & !fm` | not, not, not | ✓ |
| 1 | `!fl & !fl & !fu` | **holds, holds**, not | ✗ |
| 2 | `!fl & !fu & !fm` | not, not, **holds** | ✗ |
| 3 | `!fl & !fu & !fu` | **holds, holds, holds** | ✗ |
| 4-7 | (same shape) | repeats | |

Fixed, all eight are correctly negated and the state reports
`floor_mutual_exclusion`.

### 2.1 A control test that nearly hid it

Asked whether I was sure this was a fix, I ran an exhaustive check - all eight
assignments of the three floors, comparing the encoding's verdict against the
formula's plain meaning. **Both versions scored 0 disagreements of 8.**

That test was worthless, and worth recording as a lesson. It called
`encode_ASP` eight times in a loop *on one specification object*. The bug is
persistent mutation, so after the first call the atoms were left in a state
that made every subsequent call correct. **A loop is the worst possible harness
for a bug about state that survives between calls.**

The decisive test is one call in a fresh process, which is also what a repair
step actually does:

    FIXED : ['floor_mutual_exclusion']
    OLD   : []

### 2.2 Blast radius

Measured by hashing every case study's ASP with and without the fix. **34 of 41
contain the vulnerable shape** - a formula with more than one disjunct - but
only **4 actually encoded differently**:

* `case_study_2/colorsort`
* `case_study_2/elevator`
* `case_study_2/gyro`
* `case_study_3/gyro`

Everything else is byte-identical, **case_study_1 entirely unaffected**.
case_study_3's committed traces still audit clean under the corrected encoder,
so they did not need regenerating.

## 3. The debug graph, for the fourth time

11 of 57 runs on the 2026-08-07 ILASP sweep died with the same `IndexError` -
**every amba trace, every colorsort trace, and gyro_0**:

    last_adaptation=[str(a) for a in prev_data.adaptation_history[-1]]
    IndexError: list index out of range

A leaf can be reached with an empty adaptation history. Guarantee weakening with
no counter-traces hands its task straight back for the oracle to extract
counter-strategies from - unchanged, nothing appended - and if that
specification then verifies clean, it is a leaf whose incoming edge has no
adaptation to name. That path is the one `abff783` opened, so this is a
consequence of that fix rather than an old bug.

`_add_edge_data_to_graph` has guarded exactly this since it was written;
`connect_leaf_node` never did.

**The running tally**: a label threw (`db6f1fe`), drawing threw (`4327443`),
drawing hung (`e430e23`), and now labelling a leaf (`61bf482`). Write-only
diagnostic output should not be able to decide whether an experiment produces
results.

Those 11 failures were also *entirely* amba, colorsort and gyro - and colorsort
and gyro are two of the four case studies the polarity fix changed. They were
failing for two independent reasons at once, so the current run is the first in
which amba and colorsort can produce ILASP results in case_study_2 at all.

## 4. The three setups, as they actually stand

| | case_study_1 | case_study_2 | case_study_3 |
| --- | --- | --- | --- |
| Spec repaired | `strong.spectra` | `original.spectra` | `original.spectra` |
| Reference | `ideal.spectra` | none | none |
| Trace source | ASP, against a manufactured strengthening | ASP, violating assumptions | **a real controller run** |
| Traces each | 1 | 5 | 5 (mostly) |
| Extra files | `ideal*.spectra`, `DwyerPatterns.spectra` | - | `traces.json` manifest |
| **Runs** | **19** | **60** = 12x5 | **27** |

Under `input-files/case-studies/spectra/case_study_{1,2,3}/<case>/`.

The expected shape - N, then Nx5 - holds for the first two. **case_study_3 does
not reach it**, in two ways:

* only **6 of 12** case studies produce traces (missing: amba, colorsort,
  genbuf, lift, elevator, humanoid);
* **pcar has 2 traces, not 5**. So 5x5 + 2 = 27.

Deliberate exclusions elsewhere: case_study_1's runner omits `submarine`,
`weird_uc` and `minepump_liveness` (22 directories, 19 runs); case_study_2's
`arbiter` has no traces, its only assumption being `GF(a)`, which no finite
prefix can violate.

## 5. Preconditions, re-audited

This needed redoing rather than citing: the polarity fix **changes violation
detection**, so every earlier audit was taken under the broken encoder.

    case_study_1: 20 OK, 0 BAD, 1 ERROR
    case_study_2: 60 OK, 0 BAD, 0 ERROR
    case_study_3: 27 OK, 0 BAD, 0 ERROR

**107 scenarios, 0 BAD.** Every trace violates at least one non-initial
assumption from a realisable specification. The single ERROR is `submarine`,
whose realisability check throws - the standing exclusion, and not in any
runner's list.

## 6. A process note: git stash

Three times today I used `git stash` locally to A/B test the encoder fix. It was
unnecessary - copying the file to the scratchpad and restoring it does the same
job - and it caused damage: a `git stash pop` applied the repository's
long-lived `WIP on not_weak_t_removal` stash (June, a different branch) into the
working tree, leaving `UU`/`DU` conflicts in eight unrelated files, several of
which do not exist on this branch.

Recovered with `git reset --hard HEAD`, which was only safe because everything
else was committed. The stash is intact.

Worth separating from the remote setup, which was raised in the same breath and
is unaffected: making `config.py` machine-independent removed the need to stash
on the GPU boxes, and the remote checkout still reports **0 local
modifications**. The 18 stashes sitting there are residue from the old
workflow.

## 7. Restarted

case_study_2 and case_study_3 restarted on `61bf482` - twice, since the first
relaunch preceded the leaf-edge fix. case_study_1 left running: the polarity fix
does not touch it.

| Machine | Setup | Learner | Runs |
| --- | --- | --- | --- |
| gpu11 | case_study_2 | FastLAS `n_runs=10` | 60 |
| gpu13 | case_study_2 | ILASP | 60 |
| gpu12 | case_study_3 | FastLAS `n_runs=10` | 27 |
| gpu20 | case_study_3 | ILASP | 27 |
| gpu14 | case_study_1 | FastLAS `n_runs=10` | 19 |
| gpu15 | case_study_1 | ILASP | 19 |

Logs under `logs/case_study_{2,3}/*_2026-08-08_1246*`.

## 8. Open

* **Two jobs were genuinely stuck inside Spectra** before the restart -
  `genbuf_trace2` (12h38m at depth 1) and `gyro_trace3` (5h46m at depth 3).
  Not Graphviz this time; whether the restart clears them is unknown.
* **Slurm** is one `conda install -c conda-forge clingo` from working. Every
  other environment gap is fixed.
* **case_study_3 coverage**: pcar's 3 missing traces, and six case studies with
  none. `lift` specifically needs two-step planning -
  `G(b1 & f1 -> next(!b1))` cannot be violated by any single choice.
* **`ok_returncodes` is only wired to clingo.** ILASP, FastLAS and Spectra still
  read failure out of their own output; the same class of silent wrong answer
  is possible there.
* **`test_trivial_solution.py`** still needs `--ignore`; colorsort alone exceeds
  150s in `exploreAllCores`.
