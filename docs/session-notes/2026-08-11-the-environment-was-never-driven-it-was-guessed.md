# The environment was never driven, it was guessed

Report date: 2026-08-11. Follows
[2026-08-10](2026-08-10-a-killed-run-that-looked-like-a-queued-one.md).

**Short version.** Post-processing the two previous case_study_3 sweeps needed
trivial solutions, which turned out not to exist for this setup at all. Adding
them was routine. Adding amba and genbuf was not: amba had never been
generatable, because a paren-dropping rewrite of our own made Spectra reject its
specification, and genbuf cannot be generated because the environment side of
case_study_3 is a sampler, not a driver.

That last finding is the important one, and it is a design fault rather than a
bug: **case_study_3's coverage is decided by the size of the environment's input
space.** Every case study it covers has at most 16 environment assignments;
every one it misses for this reason has 512 or more.

## 1. Trivial solutions did not exist for this setup

Every graph drawn yesterday reported `no trivial ... - omitted from graph`. The
reason was not that step 5 had been skipped: `tests/test_diagnosis/
test_trivial_solution.py` reads `strong.spectra` and a single
`violation_trace.txt`, which is case_study_1's layout. case_study_3 has neither.

It also has one violating trace *per run*, so a trivial solution exists per
(case study, trace): `minepump_trace3`'s floor is not `minepump_trace0`'s.
Running the existing test would have computed case_study_1's trivial solutions
and let the graphs pick them up by case-study name - a specification derived
from a different specification, drawn as this one's baseline. It would have
looked right.

`scripts/generate_trivial_solutions.py` now generates them per run for any
setup, stamped with the experiment's date. All 27 case_study_3 tuples produce
one, and each prints the single assumption its trace violates - which is also
the cross-check that the trace is aimed where the generator intended.
`--graph-only` was added alongside, because redrawing a graph should not
re-run a merge that took 900s and failed.

Regenerated: 185 graphs across 2026-08-08 and 2026-08-09, all three groups
present.

## 2. amba could never have worked

`pRespondsToS_substitution` rewrites `G(s -> F(p))` into a call on the pattern
in `files/pRespondsToS.txt`. It extracted the two operands by regex: everything
between `G(` and the first `-`, and everything after `F(` less its last two
characters. Both are correct only when the implication is wrapped in exactly one
level of parentheses:

    G((a->F(b)))   ->   pRespondsToS((a,b))

`s` keeps an unmatched `(`, `p` gains a spare `)`, and Spectra reports

    ErrorsInSpectraException: missing ')' at ','

which names a comma that amba's own specification does not contain. The comma is
ours.

**26 of the 92 response formulas across the case studies were malformed** - not
only amba's six, but every `strong.spectra` with a response pattern: colorsort,
gyro, humanoid, pcar, lift_updated, traffic_updated_updated and the `*_updated`
variants. Their `ideal.spectra` counterparts are fine, which is the shape of a
fault that hides: the same case study works in one setup and not in another.
Worth re-reading past amba and colorsort failures in that light.

Fixed by counting parentheses rather than assuming a depth (`3983cb2`). All 92
now yield balanced operands; amba's realisability check reaches the BDD engine
instead of dying in the parser, and its generation run went from 25 parse errors
to none.

### 2.1 Two wrong diagnoses on the way there

Recorded because the error was methodological, not incidental. amba failed so
fast that its output directory was never created, while genbuf's was - so the
errors interleaved in a shared log were attributed to genbuf, and genbuf's
symptom (a JTLV garbage-collection equilibrium, macOS-only, because the jars
ship no CUDD `.dylib`) was attributed to amba. Both attributions were backwards,
and both were stated before being checked. Running the two separately settled it
in minutes.

## 3. The environment side is a sampler

`_candidate_inputs` enumerates the full cross-product of environment assignments
when it is at most `EXHAUSTIVE_LIMIT` (64), and otherwise draws
`MAX_CANDIDATES_PER_STEP` (64) at random. `_targeted_input` then runs the ASP
violation check on each candidate and keeps the first whose predicted violations
are exactly the targets, else a subset, else nothing.

So it is generate-and-test, not blind randomness - each candidate is checked
before being taken. But above 64 assignments it samples, and the consequences
are exactly what the coverage shows:

| Case study | Env assignments | Method | cs3 traces |
| --- | --- | --- | --- |
| gyro, minepump, minepump_liveness | 4 | exhaustive | 5 each |
| traffic_single, traffic_updated | 8 | exhaustive | 5 each |
| pcar | 16 | exhaustive | 2 |
| **amba, genbuf** | **512** | **64 sampled** | **0** |
| **colorsort** | **65,536** | **64 sampled** | **0** |
| arbiter, elevator, humanoid, lift | 8-16 | exhaustive | 0 - other causes |

Every covered case study has at most 16 assignments. Cost, at 64 candidates per
step and one clingo call each: roughly 2,900 solver calls per episode, 72,000
per target over 25 attempts. genbuf ran that to completion today and produced
nothing - `EXIT=0`, zero traces, no error.

The remaining four are a second, separate cause: arbiter's only assumption is
liveness, lift needs a two-step plan, elevator and humanoid are unexplained.

## 4. How SYNTECH actually does it

Checked in their repositories, not only in the shipped jars.

**spectra-sim's examples hand-roll the environment.** `CinderellaStepmother`
holds a `java.util.Random` and calls `generateRandomWaterFills(inputs)` before
`executor.updateState(inputs)`; `DiningPhilosophers` builds its inputs from its
own `hungry[]` array. There is no shared environment driver among them.

**The real mechanism is in `spectra-ext`'s controller walker.**
`richcontrollerwalker/Engine.java`:

```java
this.successors = ctrl.succ(this.state);
...
return Algs.randomSat(fullState.successors, BddUtil.getVarsByModule(getTurn()));
```

The controller's successor BDD, restricted to the variables of whichever
module's turn it is, and a satisfying assignment taken from it. **Legal by
construction** - no candidate is generated and tested, because the BDD already
is the set of legal moves. Turns alternate between `Mod.ENV` and `Mod.SYS`.

That is the right answer, and it is not available to us:

* our `StaticController` has `kSucc(BDD, int)` and `next(BDD, BDD)` but no
  `succ(BDD)`, the method the walker calls;
* `Algs` and `BddUtil` live in `spectra-ext`, which we do not ship;
* `FlexibleControllerExecutor.getNextStates` already fails with
  `NoSuchMethodError: SymbolicController.deep...`, so our `spectra-executor.jar`
  and toolbox jar are not the same vintage;
* what remains is native BDD manipulation over jpype, across three mismatched
  jar versions, with primed/unprimed variable handling to get right.

Identified precisely; judged too difficult to implement faithfully. The fallback
is ASP.

## 5. Seeds, audited

Asked whether random seeds had ever been tuned for better outcomes. They have
not, on the evidence:

* the seed **is** the trace index (`for seed in range(traces)`, passed as
  `seed=seed`), at the only call site in the repository;
* there is no seed search anywhere - the only other `for seed in range(...)` is
  a test asserting reproducibility;
* all 27 committed manifests record `seed == trace`, zero mismatches.

Seeds exist because `ControllerExecutor` picked its own successor states and
identical seeds produced different traces across processes (`7dd2473`).

**But there is a selection effect, and it is not the seed.** The generator
retries over *target assumptions*, keeping the first that yields a violation, so
traces are biased toward assumptions that are easy to violate. gyro's manifest
shows it plainly: all five traces target and violate `ready_stays_ready`. That
belongs in any description of the setup.

## 6. Where this leaves case_study_3

The environment generator is being rewritten to construct inputs with ASP -
satisfying the assumptions for the compliant prefix, violating exactly one
assumption at the chosen step - while the system half stays genuine controller
output, which was the point of the setup and is worth keeping. Constructive
rather than generate-and-test: no sampling, unsatisfiable is a definite answer
rather than an exhausted budget, and multi-step violations become a planning
problem rather than a lucky walk.

This changes the traces for the six existing case studies too, so the sweeps
running on gpu12 and gpu20 are superseded by it.

## 7. Open

* **The rewrite itself**, and regeneration of all case_study_3 traces.
* **amba's generation** is still running on gpu03 under the old sampler; it will
  be superseded.
* **elevator and humanoid** produce no trace despite a small environment space -
  unexplained, and not the sampling problem.
* **Everything from 2026-08-10 §8** stands, including the uncleared run
  directories and the untested reproducibility question.
