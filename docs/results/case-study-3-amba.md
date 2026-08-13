# amba — case_study_3 results

Run date **2026-08-12**. FastLAS arm on gpu12
(`logs/case_study_3/all_fastlas_2026-08-12_161741`), ILASP arm on gpu20
(`all_ilasp_2026-08-12_221239`).

amba had never produced a case_study_3 trace before 2026-08-12. Three faults
stood in the way, each hiding the next: a paren-dropping rewrite that made
Spectra reject the specification outright, a frozen system response that made
every ASP program unsatisfiable, and a planner that discarded its own plan
after the first move. See
[2026-08-12](../session-notes/2026-08-12-the-plan-was-there-all-along.md).

## The traces

Two of amba's five candidate assumptions are violable by a finite trace. The
other three - `a10_0`, `a10_1`, `a10_2` - are response properties of the form
`G(a -> F(b))`: an eventually is never refuted by a prefix, so they are
excluded as targets.

| assumption | formula |
| --- | --- |
| `a30` | a large disjunction over `hlock_{0,1,2}` and `hbusreq_{0,1,2}`, all environment variables, all at the same timepoint |
| `hburst_mutual_exclusion` | `G(!hburst_single \| !hburst_burst4)` |

| trace | seed | target | violated | steps |
| --- | --- | --- | --- | --- |
| 0 | 0 | `a30` | `a30`, `hburst_mutual_exclusion` | 6 |
| 1 | 1 | `hburst_mutual_exclusion` | `a30`, `hburst_mutual_exclusion` | 7 |
| 2 | 2 | `a30` | `a30`, `hburst_mutual_exclusion` | 6 |
| 3 | 3 | `hburst_mutual_exclusion` | `a30`, `hburst_mutual_exclusion` | 6 |
| 4 | 4 | `a30` | `a30` | 6 |

Four of the five break **both** assumptions at their violating step. That is
allowed by design - the target must break, but nothing requires it to break
alone, and insisting otherwise made targets unreachable where assumptions
overlap. Only trace 4 isolates a single assumption.

Both are safety invariants over environment variables only, which is why
`a30` is breakable in one step: make every disjunct false simultaneously.

All five pass the preconditions (checked on gpu03 with realisability, since
CUDD is unavailable on macOS): the specification is realisable, guarantees hold
at every step but the last, and assumptions hold at every step but the last,
where at least one fails.

## Repair results

**FastLAS: 5/5 clean, 21 repaired specifications each.**

| trace | final specs | merged | maximal (GAR) | unique | note |
| --- | --- | --- | --- | --- | --- |
| 0 | 21 | 1 | 1 | 1 | |
| 1 | 21 | 1 | 1 | 1 | |
| 2 | 21 | 1 | 1 | 1 | |
| 3 | 21 | - | - | - | merge died, `SIGSEGV` |
| 4 | 21 | 1 | 1 | 1 | |

**ILASP: 0/5.** Every run finished having produced no repaired specification,
at a 600s learning budget and again at 3600s. 25 learner timeouts across the
arm against FastLAS's zero. This is the clearest learner comparison in the set:
same traces, same specification, same budget, one arm produces 21 repairs per
trace and the other none.

Twenty-one repaired specifications merge to exactly **one** realisable
specification, which is then trivially maximal and semantically unique. The
same collapse-to-one holds across every case study measured so far, so amba is
not unusual in that respect - the repair produces one coherent answer per
trace rather than a spread.

Results are under
`tests/test_files/out_ssh/2026-08-12/amba_trace<N>_fastlas_2026-08-12/`, with
`final_specs/`, `merged_specs/`, `max_merged_specs/` and
`unique_max_merged_specs/`.

## Outstanding

* **trace 3's merge segfaults.** `spot::fnode::unique`, `SIGSEGV`,
  `si_addr 0x30` - a null dereference in Spot's formula interning, identical to
  the crash killing runs during the sweeps. Spot is called in-process
  (`spectra_specification.py`, `gr1_formula.py`, `spot_ltl_conjoining_util.py`
  all `import spot`), so its crash takes the whole run down. Isolating those
  calls the way `does_left_imply_right` already isolates `ltlfilt` would cost
  one comparison instead of a run.
* **No implication graphs yet.** They need the trivial solutions from step 5,
  which are still generating - and under JTLV rather than CUDD, which will not
  finish for a specification amba's size.
