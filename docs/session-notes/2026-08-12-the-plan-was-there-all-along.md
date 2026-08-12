# The plan was there all along

Report date: 2026-08-12. Follows
[2026-08-11](2026-08-11-the-environment-was-never-driven-it-was-guessed.md).

**Short version.** Yesterday's rewrite made the environment's moves constructive
instead of sampled. It still produced almost nothing, and today found out why:
three separate faults, each hiding the next, none of them in the solver.

The last one is the embarrassing one. The generator asked clingo for a plan,
executed only its first move, threw the rest away, and went looking for the
discarded moves one at a time. A GR(1) invariant needs three steps at worst;
it was taking twenty and usually failing. Fixed, minepump generates five traces
in about a second.

## 1. Every program was unsatisfiable, and randomness hid it

`_pinned_response_asp` froze the system's values at the new timepoint while
`:- violation_holds(E,T,S), is_guarantee(E)` demanded the guarantees hold. The
controller's next move is precisely the move that maintains them, so freezing
it and then requiring them admits no model. Every solve, at every horizon, for
every case study, returned UNSATISFIABLE.

It was invisible because the code fell back to the old sampler whenever the
solver returned nothing. "We use clingo now" was never true in practice. The
fallback came out - if the solver cannot answer, that is a bug to see - and the
failure became total, immediate, and diagnosable.

## 2. Liveness cannot be held against a finite prefix

With that fixed, amba still failed:

    SOLVE  t=5 UNSAT to horizon 6 for ['a10_0']

The pinned prefix was the problem. amba has seven justice guarantees, and a
five-step window from a real controller routinely does not contain the state a
`GF(p)` asks for - so the encoding reported that guarantee violated by the
*history*, which no future step can undo. Restricted to invariant guarantees.

The same rule applies to the precondition audit: a trace neither satisfies nor
refutes a `GF`, so counting one as violated fails a case study for a property
no finite trace could have.

## 3. The plan was being discarded

Then amba still failed, and the step logging - added because a run that prints
nothing for two hours cannot be diagnosed - showed the walk taking single steps
and re-planning.

`_asp_next_inputs` returned only the environment values at the *first* new
timepoint. The rest of the plan - the assumption-respecting moves that reach
the state where the target becomes breakable - was thrown away, and then hunted
for with a separate "violate nothing" query, up to twenty times.

Two smaller things fell out of the same investigation:

* the trace ends in a weak timepoint where everything holds vacuously, so a
  violation involving `next` must land before the end. Horizon *k* buys *k-1*
  usable steps and horizon 1 buys none, which is why a `next`-based assumption
  was always UNSAT at 1. The search starts at 2.
* guarantees are no longer held against the final step. That state is the
  controller's own output, and once the environment has broken an assumption
  the system owes nothing.

minepump: 5/5 traces, plans of 2 and 4 steps, about a second.

## 4. `G` and `alw` are not the same operator

Raised because the Rich Controller Walker refuses assumption-violating inputs
under `alw` but accepts them under `G`. It reproduces exactly in our executor.
Same specification modulo the operator, stepped with `(!highwater,!methane)`
then the violating `(highwater,methane)`:

    G    accepted, two choices offered, stepped to pump=false
    alw  refused: "The inputs are a safety violation for the environment"

The grammar explains it: `G` is an alias for `trans` and fills the `safety`
field, `alw`/`always` fills `stateInv`. Different categories, different
transition relations. Both specifications are realizable and both synthesise.

This matters because case_study_3 *needs* `G`: a violating step the controller
will not answer cannot be completed, and the final state would have to be
fabricated. All thirteen case studies already use `G`/`GF` exclusively, so
nothing changes - but the spelling is now a switch
(`SPEC_REPAIR_TEMPORAL_DIALECT=alw`, or `to_str(dialect=...)`) rather than an
assumption, because `alw` is wanted in other contexts.

## 5. What the walker settled

A minepump trace run by hand in the walker gave the answer we could not get:
at the violating step the controller responds `pump=false`, and crashes only on
the step *after*. With `next`-based guarantees the violating input creates
contradictory obligations one timepoint later, not at the timepoint itself - so
the system can and does answer, and the trace can be completed genuinely.

Our carry-over would have written `pump=true` there, violating
`G(methane -> next(!pump))`. That is exactly why four of genbuf's five traces
failed their preconditions.

## 6. Three more, found by running it

**Response-shaped assumptions were being offered as targets.** `G(a -> F(b))`
is classified an invariant because its outer operator is `G`, but the
consequent is an eventually and no finite prefix refutes one. amba spent three
of its five seeds on `a10_0`, `a10_1` and `a10_2`, each costing a full horizon
search that could only return UNSAT. Filtered with `PRS_REG`, the same pattern
the pRespondsToS rewrite uses. amba: five targets down to two, humanoid two
down to one.

**The audit disagreed with the generator.** The generator stopped holding
guarantees against the final step; the check still held them everywhere, so
amba failed 2/2, colorsort 5/5 and genbuf 4/5 on traces the generator
considered valid. "Violates an assumption and no guarantee" is unsatisfiable as
literally stated - it asks a trace to break the antecedent while honouring the
consequent, when GR(1) is `assumptions -> guarantees`. minepump's own
controller, run by hand in the walker, breaks a guarantee at that step.
Guarantees are now judged on the trace *without* its final state. Re-audited:
**0 BAD, all 51 traces pass**.

**lift needed a shorter run-up.** A controller step cannot be undone, so five
compliant steps that walk into a state the target is unreachable from end the
episode - and the next attempt walks into it again. Attempts now shorten the
prefix once each target has been tried at the current length. lift went from
1/5 to 5/5, violating five different assumptions in two-to-four step plans.

## 7. Coverage, and what it cost before

| | traces | note |
| --- | --- | --- |
| amba | 5 | first ever; two hours for nothing before, four seconds each now |
| colorsort | 5 | first ever |
| elevator | 5 | first ever |
| lift | 5 | first ever |
| genbuf, gyro, minepump, minepump_liveness, pcar, traffic_single, traffic_updated | 5 each | pcar was 2 |
| humanoid | 0 | unexplained |
| arbiter | - | excluded permanently |

**55 traces across 11 case studies, 0 BAD.** The controller-trace test file runs
in 8s against 100s when the day started.

## 8. Experiments running

68 runs across five machines, all stamped 2026-08-12:

| box | arm | runs |
| --- | --- | --- |
| gpu12 | FastLAS, amba + genbuf | 10 |
| gpu20 | ILASP, amba + genbuf, `LEARNER_TIMEOUT=3600` | 10 |
| gpu03 | FastLAS, genbuf reruns 0/3/4 | 3 |
| gpu06 | FastLAS, the other eight + lift_4 | 41 |
| gpu01 | FastLAS, lift 0-3 | 4 |

**amba's FastLAS arm is already complete: 5/5 clean, 21 repaired specifications
each.**

**ILASP is failing on the learner budget again.** 25 timeouts against FastLAS's
zero; `amba_0` ran 17m52s and hit the 600s per-task limit at depth 0, node 2 -
task times out, `0 candidate(s)`, branch abandoned, no repair. Nine of ten runs
ended that way. Relaunched at 3600s. If that is still not enough, it is a
result rather than a bug: ILASP cannot do these two at a practical budget.

**Three genbuf runs were killed** - exit 137 and 143, external termination
rather than a crash. Rerun on a different box, which will discriminate between
something local to gpu12 and something systemic. The `.exitcode` files are the
only reason this was visible at all; a fortnight ago they would have been
indistinguishable from queued.

## 9. Two process mistakes

`git stash -u` on the remote, to unblock a merge, swept up freshly generated
traces: colorsort, elevator and lift vanished and pcar fell back to its
committed two. Recovered with `git checkout stash@{0}^3 -- <path>`, but the
memory in this project says not to stash for exactly this reason, written after
a stray `pop` conflicted eight files in June. Move the directory aside instead.

lift's regenerated traces were left local while gpu06 was launched, so that
sweep started with the single old trace - one `lift_4` window among 41. Caught
from the window list, pushed, and the missing four launched separately on
gpu01. lift's runs are therefore split across two boxes and two log
directories, which post-processing has to collect from both.

## 10. Open

* **lift and humanoid** produce nothing: the solver names no violating input
  for their targets at all. Untouched by today's fixes and not understood.
* **Response-shaped assumptions** - `G(a -> F(b))` - are classified as
  invariants and offered as targets, though no finite trace can break them.
  amba wastes three of five seeds on them. `PRS_REG` already detects the shape.
* **`violations_in_initial_conditions`** decides a formula is initial by
  testing for a literal `G`/`F`, so it misreads every `alw` spec and would
  reject one outright. No current spec triggers it.
* The old sampler-generated traces for gyro, pcar and the traffic pair predate
  all of this and should be regenerated before they are compared with anything.
