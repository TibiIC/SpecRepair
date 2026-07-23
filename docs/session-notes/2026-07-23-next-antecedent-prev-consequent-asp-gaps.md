# ASP encoding gaps for Next-in-antecedent and Prev-in-consequent — session notes

Session date: 2026-07-23. Surfaced while running the new BFS-repair case
studies added this week (colorsort/gyro/elevator/humanoid/pcar) in the
background on the GPU box.

## Starting point

`colorsort_syn` crashed: `asp_exception_formatter.py` doesn't know how to
serialize `!Prev(x)` as a literal - the deliberately opaque, unrewritten
form `to_dnf` leaves in place after the Prev-boundary work archived in
[2026-07-21-colorsort-prev-boundary-bug.md](2026-07-21-colorsort-prev-boundary-bug.md).
Asked whether `Next` in an antecedent had the same kind of gap, since the
antecedent/consequent halves of this formatter grew somewhat asymmetrically.

## What's fixed this session: Next in antecedent

Built 4 minimal specs and ran them straight through
`NewSpecEncoder.encode_ASP` + clingo (bypassing the rest of the pipeline,
same approach as the humanoid ASP-naming investigation) to observe actual
behavior rather than guess:

| Case | Formula | Trace | Before fix | After fix |
|---|---|---|---|---|
| `PREV` in consequent | `G(a -> PREV(b))` | T0: a=true, b=false | violation at T0 (correct) | unchanged |
| `next` in antecedent, mid-trace | `G(next(a) -> b)` | T0: a=false,b=false; T1: a=true,b=false | violation at **both** T0 and T1 | violation at **T0 only** |
| `next` in antecedent, last timepoint | `G(next(a) -> b)` | T0 only: a=true, b=false | violation at T0 | **no violation** |

The T1/T0-as-last-timepoint violations were spurious. The background ASP
program (`files/background_knowledge.txt`) appends one synthetic
"weak" timepoint after a trace's last real timepoint so that an unresolved
*consequent*-side `Next`/`Eventually` gets the benefit of the doubt
(`holds_at` and `not_holds_at` are both true there, deliberately, so an
eventuality that hasn't happened within the truncated trace isn't falsely
flagged as violated). `reformat_conjunction_to_op_atom_conjunction`'s
`Next` case is shared between antecedent and consequent, so the same
mechanism applied to an *antecedent* has the opposite, unsound effect:
`holds_at` being unconditionally true at the boundary makes the antecedent
unconditionally true there too, manufacturing a violation regardless of
what the trace actually says. The last-timepoint case above proves it
directly - the reported violation didn't depend on the trace's actual `a`
value at all, only on the boundary mechanism.

Confirmed no currently-committed case study is affected: grepped all 10
`strong.spectra` files for `next(...)` occurring before a `->`, and every
match found is consequent-side. This was a real but previously
unexercised gap, not something silently corrupting an already-passing
test result.

**Fix applied**: `format_boilerplate_root_antecedent_holds` in
`spec_repair/helpers/formatters/asp_exception_formatter.py` now adds
`not weak_timepoint(T2,S)` to the generated rule body. Scoped to the
antecedent-side generator only - the consequent-side one
(`format_boilerplate_root_consequent_holds`) is untouched, so the
existing (correct) benefit-of-the-doubt behavior for consequent-side
`Next`/`Eventually` is unaffected. Verified the guard is a no-op for
`current` (T2=T1, already guaranteed non-weak by antecedent_holds' own
`not weak_timepoint(T1,S)`) and `prev` (the synthetic timepoint is only
ever placed *after* the last real timepoint via the `next(X,T,S):-
weak_timepoint(X,S), ...` extension rule, so it can never be resolved as
anyone's *predecessor* - only `next` can ever bind T2 to it). Updated the
~100 golden-string formatter tests across
`tests/test_helpers/test_asp_{formula,consequent_formula,
antecedent_exception,eventually_formula}_formatter.py` and
`test_spectra_specification.py` to include the new line; all pass.

## What's still open: Prev in consequent

`!Prev(x)` as a consequent-side literal still crashes
(`reformat_conjunction_to_op_atom_conjunction`'s `Not` case only accepts
`Not(AtomicProposition)`). Derived a truth table before touching anything
(cross-checked against the ASP background knowledge's own boundary
mechanics and last session's real-Spectra reproduction):

| Timepoint T | `Prev(x)` | `!Prev(x)` |
|---|---|---|
| T=0 (no predecessor) | false, vacuously, for any x | true, vacuously, for any x |
| T>0 | value of x at T-1 | value of `!x` at T-1 |

Proposed fix (not yet implemented - this is the "return here" marker):

1. `files/background_knowledge.txt` - add a helper mirroring the existing
   end-of-trace one (`next_timepoint_exists`), for the *start* of trace:
   ```
   prev_timepoint_exists(T1,S):- prev(T2,T1,S), timepoint(T2,S).
   ```
2. `asp_exception_formatter.py` - recognize `Not(Prev(inner))` in
   `reformat_conjunction_to_op_atom_conjunction` (currently falls into the
   `else: raise ValueError` branch), route it to a new `"not_prev"`
   bucket, and emit two rules sharing one head (same disjunctive-definition
   style already used for `weak_timepoint`):
   ```
   root_consequent_holds(OP,{name},{depth},{i},T1,S):-
       trace(S), timepoint(T1,S), temporal_operator(OP),
       not prev_timepoint_exists(T1,S).        # vacuous branch: true when T1 has no predecessor

   root_consequent_holds(OP,{name},{depth},{i},T1,S):-
       trace(S), timepoint(T1,S), timepoint(T2,S), temporal_operator(OP),
       timepoint_of_op(prev,T1,T2,S),
       not_holds_at(x,T2,S).                    # normal branch: negated x at the real predecessor
   ```
   (plus the antecedent-side twin.)

Known limitation of this narrow fix: it only covers `!Prev(x)` as a
top-level DNF conjunct - colorsort's actual guarantees only ever use it
that way (confirmed by inspection), but a `!Prev(x)` nested *inside*
another temporal operator (e.g. `Next(!Prev(x))`) would need a second,
harder fix (2-hop timepoint composition) not designed here.

## The broader picture

Both gaps come from the same root cause: `asp_exception_formatter.py`'s
antecedent- and consequent-side code paths were written somewhat
independently and have drifted out of symmetry - some temporal-operator
handling that's correct on one side is wrong (Next, now fixed) or missing
(Prev, still open) on the other. A proper refactor would treat Next and
Prev symmetrically across both antecedent and consequent from the start,
rather than patching each asymmetry as it's discovered. Didn't judge that
worth a separate branch - the fixes so far are small and independently
testable - but noting it here as the place to come back to if more of
these asymmetries turn up, or if the broader refactor becomes worth doing
in one pass instead of piecemeal.
