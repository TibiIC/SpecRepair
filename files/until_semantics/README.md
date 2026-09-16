# `until` semantics — starting workspace

The smallest formula the current translation handles, encoded by the *existing*
GR(1) pipeline, so the shape you are extending is visible on one screen.

The formula is a single guarantee:

```
guarantee -- g1
	G(a->b);
```

## Files

| file | what it is |
| --- | --- |
| `simple_implication.spectra` | the input. One env atom `a`, one sys atom `b`, one `G(a->b)` guarantee |
| `violation_trace.txt` | two timepoints; `a & !b` at t=1, so the trace violates `g1` |
| `simple_implication.asp` | the clingo program — semantics + formula + trace |
| `simple_implication.las` | the ILASP task that would weaken `g1` |
| `generate.py` | regenerates both from the spec and trace |

Nothing is hand-written. Both encodings come from `NewSpecEncoder`, the same
encoder the repair loop uses, so what you see is what the tool really emits.

## Regenerating

```bash
conda activate arm_env
python files/until_semantics/generate.py
```

It prints the violations clingo finds before writing the `.las`. Right now:

```
violations found: ['guarantee(g1) violation_holds(g1,1,trace_name_0)']
```

That line is the check worth keeping. If a change to the semantics makes it
print `NONE`, the trace no longer violates `g1` and the `.las` below it is
vacuous — which is easy to miss, because both files are still written.

Diffing the two outputs before and after a change is the fastest way to see what
the change did.

## Where the semantics lives

`simple_implication.asp` is in two halves.

**Domain-independent (lines 1–145)** — the part you are extending. Within it:

* `Temporal Operator Definitions` (~line 18) declares the operators:
  `current`, `next`, `prev`, `eventually`.
* `Timepoint of operation definitions` (~line 24) gives each one meaning, as a
  relation between the point the formula is evaluated at and the point an atom
  is read at.
* `Weak Timepoint Definitions` (~line 63) handles trace ends — the reason
  `next` at the last timepoint and `prev` at the first are not simply false.
* `GR(1) Rules` (~line 81) turn antecedent/consequent into `violation_holds`.

**Domain-dependent (lines 146 onwards)** — what `G(a->b)` itself became:

```prolog
antecedent_holds(g1,T,S) :- ..., root_antecedent_holds(current,g1,0,T,S).
root_antecedent_holds(OP,g1,0,T1,S) :- ..., timepoint_of_op(OP,T1,T2,S), holds_at(a,T2,S).

consequent_holds(g1,T,S) :- ..., root_consequent_holds(current,g1,0,0,T,S).
root_consequent_holds(OP,g1,0,0,T1,S) :- ..., timepoint_of_op(OP,T1,T2,S), holds_at(b,T2,S).
```

The `G` never appears. It is implicit: the rules are written for an arbitrary
`T`, and `GR(1) Rules` quantifies over every timepoint. Only the inner
`a -> b` is explicit, split into an antecedent and a consequent, each reading
its atom at whatever timepoint `timepoint_of_op` maps to.

## The bit that will not extend as-is

`timepoint_of_op(OP, T1, T2, S)` is **binary**: one evaluation point, one read
point. Every current operator fits, because each names a single other timepoint
— `current` maps `T1` to itself, `next` to its successor, `prev` to its
predecessor, `eventually` to some later point.

`a U b` does not. It needs a *witness* `T2 >= T1` where `b` holds, **and** a
condition on every `T` in `[T1, T2)` where `a` must hold. That second part is a
bounded universal over an interval, which a single binary `timepoint_of_op` atom
has nowhere to put.

So the question the extension turns on is whether to add an interval relation
alongside `timepoint_of_op` and leave the existing operators untouched, or to
generalise `timepoint_of_op` itself — and if the latter, what happens to the
`#modeb` declarations in the `.las`, which currently enumerate
`const(temp_op_v)` over exactly the four operators above. That is your call, and
it is the reason this folder exists rather than a patch.

One practical note either way: the `.las` mode bias lists the operators as
`#constant(temp_op_v, ...)` entries. A new operator that is not declared there
is invisible to the learner even if the `.asp` understands it perfectly.
