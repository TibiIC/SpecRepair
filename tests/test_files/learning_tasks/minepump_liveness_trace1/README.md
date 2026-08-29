# minepump_liveness trace 1 / assumption3_1 — the disjunction-index case

The learning task whose answer was mis-applied by `integrate_multiple`, kept
verbatim so the defect can be re-examined without re-running a search.

Captured 2026-08-29 from
`input-files/case-studies/spectra/case_study_3/minepump_liveness`
(`original.spectra` + `violation_trace_1.txt`), antecedent-weakening
configuration, `Learning.ASSUMPTION_WEAKENING`.

| file | what it is |
| --- | --- |
| `task.las` | the task as the encoder emits it, in ILASP's dialect |
| `task.fastlas.las` | the same task after `translate_ilasp_task_to_fastlas` |
| `fastlas_run_N.out` | raw stdout of FastLAS invocation N, in order |
| `solutions.txt` | the parsed `Adaptation`s, per run |

## What the task says

The violation being repaired:

    violation_holds(assumption3_1,7,trace_name_1)
    violation_holds(guarantee1_1,7,trace_name_1)

The example requires the whole trace to be entailed, i.e. *no* expression
violated at any timepoint:

    #pos({entailed(trace_name_1)},{},{ trace(trace_name_1). timepoint(0..8). ... })

`assumption3_1`'s antecedent is a two-disjunct disjunction, and the encoder
derives `antecedent_holds` with **one rule per disjunct**, each guarded by its
own exception:

    antecedent_holds(assumption3_1,T,S) :- ... root(current,...,0), root(prev,...,1),
                                           not antecedent_exception(assumption3_1,0,T,S).
    antecedent_holds(assumption3_1,T,S) :- ... root(current,...,2),
                                           not antecedent_exception(assumption3_1,1,T,S).

    index 0  ==  highwater=true & PREV(pump=false)
    index 1  ==  highwater=true & pump=false

Excepting one disjunct therefore does not stop the antecedent holding — the
other rule still derives it unaided. **A one-rule hypothesis cannot cover this
example, and FastLAS never returns one.**

## What FastLAS actually returns

Both solutions carry one rule per index, which is correct:

    run 0   antecedent_exception(assumption3_1,0,...) :- ..., not_holds_at(pump,V0,V1), ...
            antecedent_exception(assumption3_1,1,...) :- ..., holds_at(flag,V0,V1), ...

    run 1   antecedent_exception(assumption3_1,1,...) :- ..., holds_at(highwater,V0,V1), ...
            antecedent_exception(assumption3_1,0,...) :- ..., not_holds_at(methane,V0,V1), ...

Run 2 is UNSATISFIABLE under the accumulated exclusions, so the space holds
exactly two solutions.

Note run 1 lists **index 1 before index 0**. FastLAS's rule order varies between
runs, which is why the bug below was intermittent rather than deterministic: the
corruption depends on which index is applied first.

## The defect these files document

`integrate_multiple` applied a solution's rules one at a time, and
`_integrate_antecedent_exception` rewrote the antecedent on each call — removing
the indexed disjunct and appending the narrowed version at the end. The second
rule's index, numbered against the *original* antecedent, was then looked up in
the *rewritten* one:

    ORIGINAL   G(((highwater & PREV(!pump)) | (highwater & !pump)) -> next(highwater))
    0 then 1   G(( highwater & !pump                                   <-- UNTOUCHED
                 | ((highwater & PREV(!pump)) & !flag) & pump) -> next(highwater))
    1 then 0   G((((highwater & !pump) & pump)
                 | ((highwater & PREV(!pump)) & !flag)) -> next(highwater))

`highwater & !pump` is the disjunct the t=7 violation fires through. Leaving it
unguarded is what put a specification that fails its own trace into
`final_specs`.

Fixed by `GR1Formula.integrate_all`; see
`tests/test_helpers/test_integrate_multiple.py`, which replays these exact
solutions.
