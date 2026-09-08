# Stopping the non-terminating searches, and why they never terminated — session notes

Session date: 2026-09-04, running into the early hours of 09-05. The question
that started it was "it's been a week, what happened?" — the 18 re-runs launched
on 2026-08-29 after the disjunction-index bug had produced almost no complete
results. The answer is that they were never going to, and the reason is a
quadratic in the search itself, not bad luck with the cluster.

Continues [2026-07-28](2026-07-28-experiment-pivot-to-trace-violation-and-pipeline-fixes.md).

## The headline

**The BFS does not terminate on any non-trivial case study, and the cost per
node grows linearly with the number of nodes already visited.** Everything else
in this note is downstream of that.

## Part 1: the measurement

Queue depth against nodes expanded, taken from the live logs before anything was
stopped:

| run | nodes done | still queued | elapsed |
| --- | --- | --- | --- |
| minepump_liveness 2 | 4,248 | 212,466 | 127h |
| minepump_liveness 4 | 5,809 | 80,250 | 113h |
| minepump_liveness 0 | 5,873 | 68,853 | 113h |
| gyro 0 | 564 | 29,761 | 31h |
| gyro 4 | 362 | 35,713 | 35h |
| gyro 1/2/3 | 287–410 | 22k–28k | 35h |
| genbuf 0/1 | **1** | 0 | 87h |

Every node expanded enqueues roughly fifty more. Worse, the rate *decays*.
minepump_liveness_2, same run, over time:

```
10h  → queue 56,457     (800 nodes took 22h)
32h  → queue 154,459    (800 nodes took 23h)
55h  → queue 181,628    (800 nodes took 37h)
92h  → queue 205,854
127h → queue 212,466    ← ~16 nodes/hour and falling
```

A search whose per-node cost rises as it runs does not finish. The current queue
alone, at the current rate, is over a year of compute, and the queue is still
growing.

## Part 2: why the cost per node rises

`orchestration_manager_semantic_equivalence_aw_merge.py` keeps visited nodes in
a **`list`**:

```python
self._visited_nodes_list: list[Tuple[ISpecification, Learning, Any]] = []
...
for task_id, visited_node in enumerate(self._visited_nodes_list):
    visited_spec, visited_learning_type, visited_data = visited_node
    if new_learning_type == visited_learning_type and new_data == visited_data \
            and new_spec == visited_spec:
```

The membership test is a linear scan, and the comparison that decides it is
`SpectraSpecification.__eq__`:

```python
def __eq__(self, other) -> bool:
    return (self.equivalent_to(other, GR1FormulaType.ASM)
            and
            self.equivalent_to(other, GR1FormulaType.GAR))
```

`equivalent_to` shells out to `ltlfilt`. So **every enqueue costs up to two
`ltlfilt` subprocesses per node already visited**. Visiting V nodes costs
O(V²) subprocess round-trips, which is exactly the decay curve above: the 800
nodes that took 22h early took 37h once a few thousand nodes were in the list.

This is the single thing to fix. The dedup is semantically correct and
algorithmically hopeless. `__hash__` already exists and is syntactic:

```python
return hash((self._module_name, tuple(self._formulas_df.itertuples(index=False, name=None))))
```

so a syntactic pre-filter (dict/set on the hash, semantic `__eq__` only within a
bucket) would cut the overwhelming majority of those subprocess calls without
changing which nodes are considered distinct. That is the obvious next
experiment, and it is a change to the visited-set only.

I have not made that change — it alters what the searches explore and how fast,
and that is a decision about the experiment, not a bug fix to slip in overnight.

## Part 3: what actually killed each run

Separate from the above, and much less interesting, but it is what the exit
codes say:

* **amba 0–4** — nothing killed them. Completed normally 08-29, exit 0, 21 specs
  each. These are the only searches in the whole experiment that ran to
  completion because they wanted to.
* **gyro 0** — `VERIFY failed: RuntimeError` at 30h49m on gpu21, then SIGTERM
  (exit 143) on 09-01 09:14. The only VERIFY failure anywhere in the run set.
* **gyro 1–4** — gpu20's entire tmux server died at ~09-01 13:30, taking all
  four windows at once, with no exit codes. No reboot (gpu20 up since 06-08) and
  no OOM record in any log I can read. The socket `/tmp/tmux-13246` is simply
  gone. Cause not established.
* **genbuf 0, 1** — stopped by me on 09-04. Both were still on **node 1** after
  4d17h; genbuf_1 had been on node 1 for 87 hours.
* **minepump_liveness 1, 3** — completed normally, exit 0.
* **minepump_liveness 2** — first attempt aborted 08-29 with
  `MitigationMadeNoProgressException` ("a guarantee weakening mitigation
  returned its input unchanged"); relaunched 08-30, stopped by me 09-04.
* **minepump_liveness 0, 4** — 08-29 attempts killed at the 08-31 relaunch;
  relaunched 08-31, stopped by me 09-04.

Also stopped: pre-fix leftovers still burning cores — traffic_single 1 and 3, an
Aug-14 gyro_3, a 27-day case_study_2 genbuf_2 — and the three genbuf MARCO
core-enumeration runs. Those MARCO runs were the only source of complete
unrealisable-core sets, so stopping them means shipping without the hitting-set
graphs. That was a deliberate call, not an accident.

## Part 4: genbuf's single solution

genbuf traces 0 and 1 each produced exactly **one** final specification. That is
not "only one repair exists". It is "the search never got past its first node".

Both logs read the same way: `NODE d0 n1 ASM queue 0`, then `LEARN d0 n1 3
candidate(s)` at seven seconds, then `Counter-strategy expansion truncated at
1000 counter-traces`, then nothing for days. Sampling the relaunched genbuf 3
after six hours shows **no child processes and 133% CPU** — multi-threaded work
inside the process, i.e. the embedded JVM. genbuf is sitting inside a Spectra
BDD call at node 1 and has been since it started.

So the degradation step is not recursing semantically; it never gets the chance
to recurse at all. The wall is the Spectra side on a large specification, and it
is the same wall the MARCO runs hit from the other direction — genbuf trace 3's
core enumeration reached 12,551 cores and 19,680 maximal realisable subsets
after 16 days and was still finding a core every ~230 seconds, with no sign of
saturation.

Two different bottlenecks, then, and it matters which is which:

* **minepump / gyro** — double-digit-to-thousands of solutions, killed by the
  O(V²) visited-set scan in Part 2. Python-side, fixable.
* **genbuf** — one solution, killed by Spectra/BDD cost on a large
  specification at a single node. JVM-side, not fixable by touching the dedup.

amba is the interesting control: same learner, same pipeline, finished in 24
minutes. Whatever makes genbuf expensive is specific to genbuf's specification,
not to the method.

## Part 5: the Spot acceptance-set ceiling, and a rebuild

gyro's `gr1` implication graphs would not draw:

```
ltlfilt: Too many acceptance sets used.  The limit is 32.
```

That is a **compile-time** constant in Spot, and the conda-forge build of Spot
2.14.3 uses the default 32. gyro's whole-specification formula, with its justice
goals on both sides, needs more.

Rebuilt Spot 2.14.3 from source with `--enable-max-accsets=128 --disable-python`
into `/vol/bitbucket/tg4018/Tools/spot-acc128`. The code already had the hook —
`SPEC_REPAIR_LTLFILT` overrides which `ltlfilt` to run, and `ltl2tgba`/`autfilt`
are derived from the same path by string replacement — so pointing at the new
build needs no code change:

```bash
export SPEC_REPAIR_LTLFILT=/vol/bitbucket/tg4018/Tools/spot-acc128/bin/ltlfilt
export LD_LIBRARY_PATH=/vol/bitbucket/tg4018/Tools/spot-acc128/lib:$LD_LIBRARY_PATH
```

**All five gyro traces now draw all three graphs, exit 0.** Note that the
obvious sanity check — 40 conjoined `GF(p_i)` — does *not* reproduce the failure,
because Spot simplifies it; the real formula is the only test that discriminates.

## Part 6: amba and genbuf gr1 is a different problem, and is not computable

amba's `gr1` graph did not hit the acceptance-set ceiling. It hung. The
diagnosis matters because 0% CPU on the parent looks exactly like a deadlock:

```
viz pid=430460 state=Sl+   wchan=poll_schedule_timeout
  child: ltlfilt -c -f (G((((hmastlock & ...   6:10:59 elapsed  99.9% CPU
```

The parent is correctly blocked; the **child `ltlfilt` had been running one
single pairwise implication check at full CPU for over six hours**. genbuf was
the same at 3h52m. With up to n² such comparisons per graph, `gr1` for these two
case studies is not reachable by this method.

`asm` and `gar` were already written before `gr1` was attempted, so nothing was
lost. Both were relaunched with `--graph-type asm gar`. The pipeline's own
docstring argues `gr1` is the misleading view anyway — strengthening assumptions
weakens the implication, so `gr1` orders by the assumption side and inverts —
which makes it the right one to drop under duress.

## Part 7: genbuf 3 and 4 were never run

They had no `_2026-08-29` output directory at all. Both traces exist and are
valid — `violation_trace_3/4.txt`, seeds 3 and 4 in `traces.json` — so this was
an operational miss in the 08-31 relaunch, not a structural exclusion like
arbiter's `GF(a)`. Relaunched on gpu18/gpu19 with `RUN_DATE=2026-08-29` so they
land in the same experiment. Both are, predictably, sitting at node 1.

## Part 8: a real bug in the pipeline's `--case-study` filter

`find_run_dirs` filters with `case_study_name_from_run_dir`, which strips **only
the date**:

```python
return re.sub(rf"_{re.escape(date)}$", "", run_dir_name)   # amba_trace0_fastlas
```

but the function that strips `_fastlas` and `_trace<N>` is a *different* one,
`case_study_dir_name`, which the filter never calls. So
`--case-study amba` can never match a trace-style run directory and dies with
`No run directory for case study 'amba'`. Worked around by passing full run
names (`--case-study amba_trace0_fastlas`); the fix is to use
`case_study_dir_name` in the comparison.

## Where things stand

Complete:

| case study | specs (final → unique → max → merged) | graphs |
| --- | --- | --- |
| gyro 0–4 | 68–115 → 26–37 → 24–31 → 1 | asm, gar, gr1 |
| minepump_liveness 1 | 18 → 12 → 12 → 1 | asm, gar, gr1 |
| minepump_liveness 3 | 19 → 12 → 12 → 1 | asm, gar, gr1 |

Running: amba 0–4 and genbuf 0–2 post-processing (asm+gar); minepump_liveness
0/2/4 still on step 2, semantic uniqueness over 34,651 / 21,456 / 35,603 specs —
the same O(n²) `ltlfilt` cost as Part 2, so these are days out; genbuf 3/4
searches at node 1.

Everything merges to exactly **1** specification at step 4, in every completed
case. That is worth a look on its own — it may be correct, or it may mean the
merge is conjoining more aggressively than intended.

Status of everything, from any GPU box:

```bash
ssh gpu20 bash /vol/bitbucket/tg4018/postproc_logs/status.sh
```

It reads the shared NFS logs directly rather than fanning out over ssh, because
lab boxes cannot ssh to each other.

## Part 9: the experiment table, as of 2026-09-05 03:00

Columns follow `docs/results/tables/tab_total.tex` — Explored / Unique /
Preferred / Final / Trivial — split into two tables so the search side and the
post-processing side can be read separately. All figures are from each run's own
`status.txt` and its output directories, not reconstructed.

### Search

`Complete` is the honest column: it is `phase: done` in `status.txt`, meaning the
queue drained and the search proved it had found *every* repair. Anything else
was stopped mid-flight and its solution set is a **lower bound**.

| Case Study | Runtime | Explored | Queue left | Depth | Complete | Intermediate | Realisable (final) |
| --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: |
| AMBA 0 | 23m18s | 1 | 0 | 0 | **yes** | 0 | 21 |
| AMBA 1 | 23m14s | 1 | 0 | 0 | **yes** | 0 | 21 |
| AMBA 2 | 23m42s | 1 | 0 | 0 | **yes** | 0 | 21 |
| AMBA 3 | 25m39s | 1 | 0 | 0 | **yes** | 0 | 21 |
| AMBA 4 | 15m04s | 1 | 0 | 0 | **yes** | 0 | 21 |
| GenBuf 0 | 113h29m | 1 | 0 | 0 | no | 2 | 1 |
| GenBuf 1 | 113h29m | 1 | 0 | 0 | no | 3 | 1 |
| GenBuf 2 | **1m18s** | 1 | 0 | 0 | **yes** | 0 | 21 |
| GenBuf 3 | 6h22m | 1 | 0 | 0 | no | 0 | 0 |
| GenBuf 4 | 6h21m | 1 | 0 | 0 | no | 0 | 0 |
| Gyro 0 | 30h49m | 564 | 29,761 | 2 | no | 9 | 85 |
| Gyro 1 | 35h06m | 287 | 22,215 | 1 | no | 8 | 74 |
| Gyro 2 | 35h06m | 410 | 28,192 | 2 | no | 9 | 96 |
| Gyro 3 | 35h05m | 289 | 22,064 | 1 | no | 8 | 68 |
| Gyro 4 | 35h06m | 362 | 35,713 | 2 | no | 14 | 115 |
| Minepump Liveness 0 | 113h29m | 5,886 | 69,213 | 3 | no | 3,587 | 34,651 |
| Minepump Liveness 1 | **21.7s** | 1 | 0 | 0 | **yes** | 0 | 18 |
| Minepump Liveness 2 | 127h21m | 4,255 | 212,459 | 4 | no | 1,028 | 21,456 |
| Minepump Liveness 3 | **44.2s** | 1 | 0 | 0 | **yes** | 0 | 19 |
| Minepump Liveness 4 | 113h29m | 5,819 | 80,344 | 4 | no | 3,920 | 35,603 |

**Eight of twenty runs are complete.** Every one of those eight terminated at
the *root node* — `Explored 1, Depth 0`. Not one search that expanded past its
first node has ever finished.

That reframes Part 1. The split is not "big case studies are slow". It is
binary: either the root node's candidates are all solutions and the run is over
in seconds-to-minutes, or the search branches and never comes back. AMBA 4 took
15 minutes; Gyro 4 has spent 35 hours to explore 362 nodes with 35,713 still
queued. GenBuf 2 finished in **78 seconds** while GenBuf 0 and 1 have spent 113
hours on their first node.

Depth is the tell: the deepest any run has reached is 4, on Minepump Liveness 2,
after 127 hours.

### Post-processing

| Case Study | Realisable | Unique | Preferred | Merged (final) | Trivial | Graphs |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| AMBA 0 | 21 | 21 | 21 | 1 | *n/a* | asm, gar |
| AMBA 1–4 | 21 | *running* | *running* | *running* | *n/a* | *running* |
| GenBuf 0 | 1 | 1 | 1 | 1 | *n/a* | asm, gar |
| GenBuf 1–2 | 1 / 21 | *running* | *running* | *running* | *n/a* | *running* |
| GenBuf 3–4 | 0 | — | — | — | *n/a* | — |
| Gyro 0 | 85 | 33 | 24 | 1 | 2 | asm, gar, gr1 |
| Gyro 1 | 74 | 31 | 31 | 1 | 2 | asm, gar, gr1 |
| Gyro 2 | 96 | 37 | 29 | 1 | 2 | asm, gar, gr1 |
| Gyro 3 | 68 | 26 | 26 | 1 | 2 | asm, gar, gr1 |
| Gyro 4 | 115 | 37 | 26 | 1 | 2 | asm, gar, gr1 |
| Minepump Liveness 0 | 34,651 | *step 2* | — | — | 2 | — |
| Minepump Liveness 1 | 18 | 12 | 12 | 1 | 2 | asm, gar, gr1 |
| Minepump Liveness 2 | 21,456 | *step 2* | — | — | 2 | — |
| Minepump Liveness 3 | 19 | 12 | 12 | 1 | 2 | asm, gar, gr1 |
| Minepump Liveness 4 | 35,603 | *step 2* | — | — | 2 | — |

Three things this table says that the search table does not:

**Every completed post-processing run merges to exactly 1.** Gyro 4 goes
115 → 37 → 26 → 1; Minepump Liveness 1 goes 18 → 12 → 12 → 1; AMBA 0 goes
21 → 21 → 21 → 1. Whether that is a genuine lattice collapse or the merge
conjoining more than it should is the open question, and it is uniform enough to
be worth checking before any of these numbers go in a paper.

**Trivial solutions do not exist for AMBA or GenBuf.** `trivial_solutions/2026-08-29/all/`
has entries for arbiter, colorsort, elevator, gyro, humanoid, lift, minepump,
minepump_liveness, pcar and traffic — but neither AMBA nor GenBuf. That is why
the pipeline logs `no trivial ... - omitted from graph` for those two, and why
their `Trivial` column is *n/a* rather than 0.

**The three large Minepump runs are still in step 2** after seven hours, on
34,651 / 21,456 / 35,603 specifications. Step 2 is semantic uniqueness, the same
pairwise `ltlfilt` cost as Part 2, so it is quadratic in exactly the same way.
These are days out, not hours.

## Part 10: the atlas, and where to read it from a phone

**No, the graphs were not on the atlas.** `docs/results/merge-atlas.html` is dated
2026-08-28, predates every graph in this note, and is untracked in git — it has
never been part of the repository.

Rather than regenerate that file, the 25 graphs that currently exist are
published as a page, with the two tables above alongside them:

**<https://claude.ai/code/artifact/2fb2b369-3b4e-48e1-bfec-7f0f1ecae76b>**

It is a single self-contained page — every PNG is embedded, so there is nothing
to fetch and it works on a phone. Tap any graph to open it full size. The page is
private until shared from its own share menu.

What is on it: Gyro 0–4 in all three views, Minepump Liveness 1 and 3 in all
three, AMBA 0 and GenBuf 0 in `asm` and `gar` only. That is every graph that
exists — the missing ones are missing for the reasons in Parts 5 and 6, not
because they were skipped.

It is a snapshot, not a live view. AMBA 1–4 and GenBuf 1–2 are re-running now and
the three large Minepump runs are days from having graphs at all; the page needs
republishing once they land.

---

# 2026-09-08: why GenBuf is the outlier

Three days on, nothing is wedged — every remaining job is alive and burning CPU.
But GenBuf is behaving unlike every other case study, and this is the reason.

## The symptom that does not fit

GenBuf trace 2's post-processing has spent **three days on 21 specifications**.
AMBA's 21 specifications took about 35 minutes. Same stage, same count, same
pipeline. And AMBA is the *bigger* case study:

| | original size | variables | formulas |
| --- | ---: | ---: | ---: |
| AMBA | 37,030 B | 34 | 63 |
| GenBuf | 14,342 B | 24 | 109 |
| Gyro | 1,571 B | 6 | 12 |
| Minepump Liveness | 606 B | 4 | 9 |

So it is not size. Sampling the live `ltlfilt` on gpu22 showed a single
comparison running 24 minutes on a formula of **1,327 bytes with 2 justice
goals**. That is a tiny formula. Something about it is pathological.

## It is not the repair

First guess was that the learned exceptions were the problem. They do look
overfitted — GenBuf's weakenings attach arbitrary conjunctions of unrelated
signals, e.g. `stoB_REQ2`'s exception mentions `stateG12`, and `stoB_REQ3`'s
mentions `btoR_REQ0`:

```
G(((stoB_REQ2 & !btoS_ACK2) -> (X(stoB_REQ2) | (((stateG12 & stoB_REQ1) & stoB_REQ3) & stoB_REQ4))))
```

I stripped all five learned disjuncts back to the unrepaired form and timed both
through `ltl2tgba`. **Both time out at 120s.** The exceptions are not the cause —
GenBuf's *original* assumptions are already beyond translation.

(The exceptions still look like overfitting and are worth their own look. They
are just not what is costing the days.)

## What it actually is

Translating the conjunction to an automaton is exponential in the number of
top-level conjuncts. Bisecting GenBuf's assumption conjunction, taking the first
*k* of its 28 conjuncts:

| conjuncts | automaton states | translation |
| ---: | ---: | ---: |
| 15 | 28 | 0.07s |
| 18 | 163 | 0.18s |
| 20 | 487 | 0.87s |
| 21 | 730 | 2.03s |
| 22 | 1,459 | 10.51s |
| 23 | 2,188 | 23.97s |
| 28 | — | **>300s** |

States double per conjunct; time grows about 2.4× per conjunct. The cliff sits
between 20 and 23 conjuncts, and it is sharp.

Every case study measured against that cliff — `ltl2tgba` on the original
specification's assumption and guarantee conjunctions:

| Case study | ASM conjuncts | ASM translate | GAR conjuncts | GAR translate |
| --- | ---: | ---: | ---: | ---: |
| Minepump Liveness | 4 | 0.33s (11 states) | 5 | 0.02s (3 states) |
| Gyro | 4 | 0.02s (5 states) | 8 | 0.03s (4 states) |
| AMBA | 8 | 0.10s (9 states) | 55 | **timeout** |
| GenBuf | **28** | **timeout** | **81** | **timeout** |

This is the whole story, and it lines up exactly with which runs finish.

## Why AMBA survives its own untranslatable guarantees

AMBA's GAR conjunction has 55 conjuncts and does not translate either — yet
AMBA's `gar` graphs drew fine in 35 minutes. That looked like a contradiction,
so I checked it.

The 21 AMBA final specifications are 21 distinct files, but their **guarantee
formulas are byte-identical** — 27,421 bytes, the same in every one. AMBA's
repairs weaken assumptions only and never touch the guarantees. So every GAR
comparison hits Spot's syntactic fast path and returns in **0.04s** without ever
building an automaton. The formula being untranslatable never comes up.

That also explains the six-hour `gr1` hang from 09-04. `gr1` is
`(assumptions) -> (guarantees)`, so the two sides are coupled and the specs
*differ* on the assumption side. The syntactic shortcut no longer applies, Spot
has to build the automaton for the 55-conjunct guarantee formula, and it does not
come back.

## Why GenBuf does not survive

GenBuf is the one case study where the formula that **changes** is also the one
that is **too big to translate**. Its repairs weaken assumptions, its assumption
conjunction is 28 conjuncts, and so no comparison can take the fast path. Every
semantic operation — the visited-set check in the search, `are_equivalent` in
post-processing step 2, every edge of every graph — needs a translation that does
not terminate in any useful time.

That is why GenBuf sits at node 1 for days: it is not stuck in a loop, it is
waiting on an automaton that will not finish. The 133% CPU is Spot and the JVM
doing real work on an intractable input.

So the two bottlenecks in this experiment are now fully separated:

* **Gyro, Minepump Liveness** — formulas translate in milliseconds. What kills
  them is the O(V²) visited-set scan from Part 2. Python-side, fixable.
* **GenBuf** — the O(V²) scan is irrelevant; it never gets far enough to matter.
  What kills it is exponential LTL-to-automaton translation on a 28-conjunct
  assumption set. Not fixable by touching the dedup.
* **AMBA** — sits on the boundary and only passes because its repairs happen to
  leave the large formula untouched. That is luck, not headroom: any repair that
  touched AMBA's guarantees would put it in GenBuf's position.

## What follows from this

Semantic comparison by automaton translation does not scale to GenBuf, and AMBA
only clears it on a technicality. Bigger machines and longer waits will not
change that — the curve above is exponential, and GenBuf is five conjuncts past
where it goes vertical.

If GenBuf has to be in the results, the comparison has to stop going through
whole-specification translation — comparing formula-by-formula rather than
conjunction-to-conjunction would keep every individual translation small, at the
cost of a weaker (sound but incomplete) notion of equivalence. That is a
methodology decision, not a bug fix, so it is not one I have made.

The alternative is honest and cheap: report GenBuf as out of scope for semantic
post-processing, with the conjunct-count table above as the reason.

## All eleven case studies, not four

The atlas showed four case studies, which was wrong as a picture of the
experiment. There are **eleven**, and 55 runs. Only AMBA, GenBuf, Gyro and
Minepump Liveness appear in the 2026-08-29 re-run because the disjunction bug
only invalidated those 18 runs; the other seven were never re-run and their
latest results are from **2026-08-13**.

Those seven have valid searches. What they do not have is comparable
post-processing: the 08-13 runs went through the pre-2026-08-18 pipeline, which
merged before filtering and wrote `merged_specs/` rather than `unique_specs/`.
Their stage counts are marked *old* in the atlas rather than silently mixed in
with the 08-29 numbers.

### The root-node finding holds across all 55 runs

| | runs | complete | of those, past depth 0 |
| --- | ---: | ---: | ---: |
| all case studies | 55 | 28 | **0** |

Every one of the 28 complete runs terminated at `Explored 1, Depth 0`. Adding
seven more case studies did not produce a single counter-example. Elevator, Lift
and Traffic Updated finish all five traces in under a minute each — and all of
them at the root node.

The stopped runs are worse than the 08-29 four suggested. PCar 4 ran **238
hours** and was stopped with **263,266** nodes queued, at depth 2. Traffic Single
3 ran 303 hours. PCar's four unfinished traces each sit above 200,000 queued.

### ColorSort is past the translation cliff, and that explains the zero specs

ColorSort has produced **zero** specifications on every trace of every date, and
that has been open since July. Measuring it against the cliff:

| Case study | ASM conjuncts | ASM translate | GAR conjuncts | GAR translate |
| --- | ---: | ---: | ---: | ---: |
| Traffic Single | 3 | 0.02s | 2 | 0.02s |
| Elevator | 2 | 0.02s | 5 | 0.02s |
| Minepump | 3 | 0.02s | 3 | 0.02s |
| Gyro | 4 | 0.02s | 8 | 0.03s |
| PCar | 4 | 0.02s | 5 | 0.02s |
| Minepump Liveness | 4 | 0.33s | 5 | 0.02s |
| Traffic Updated | 5 | 0.02s | 4 | 0.02s |
| AMBA | 8 | 0.10s | 55 | **timeout** |
| Lift | 11 | 0.03s | 7 | 0.02s |
| **ColorSort** | **25** | **timeout** | **52** | **timeout** |
| **GenBuf** | **28** | **timeout** | **81** | **timeout** |

ColorSort and GenBuf are the only two case studies whose *assumptions* are past
the cliff, and they are precisely the two that return nothing and sit at node 1
in `verifying d1 candidate` — ColorSort for 20 minutes to 2 hours before being
stopped, GenBuf for days. Same signature, same cause: waiting on an automaton
that does not arrive.

That is a much better answer than "ColorSort produces no specs". It produces no
specs because it cannot complete a single semantic comparison, and no amount of
waiting or memory changes that. It also predicts the fix is the same one GenBuf
needs — comparison that does not go through whole-specification translation.

Note the ordering: it is the **assumption** conjunct count that decides. AMBA has
a worse guarantee formula than ColorSort (55 vs 52) and still runs, because AMBA's
repairs never touch its guarantees. Lift has 11 assumption conjuncts, more than
AMBA's 8, and is entirely fine — the cliff is between 20 and 23, and nothing sits
in that gap.

### Post-processing launched for the six runs that had no graphs

Minepump 1–4 (23,201–27,589 specs) and Traffic Single 1 and 3 (55,145 and
15,504) had no graphs at all. Post-processing is now running for all six, one per
box on gpu01/04/05/06/20/21, against their 2026-08-13 output. ColorSort is
skipped: there is nothing to post-process.

These are step-2 bound in exactly the way Part 2 describes, and Traffic Single 1
at 55,145 specifications is larger than anything that has finished. They are not
quick.
