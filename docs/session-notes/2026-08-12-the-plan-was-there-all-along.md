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

## 6. Running

Trace generation for all twelve viable case studies, amba and genbuf first.
arbiter is excluded permanently: its only assumption is `GF(a)`, and no finite
trace refutes liveness.

## 7. Open

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
