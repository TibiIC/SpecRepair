# The pre-merge views, and where the structure actually is — session notes

Session date: 2026-09-09. One deliverable: a second implication graph per run
that plots the repair solutions *before* the merge alongside the original, the
trivial floor and the merged result. Drawn for guarantees first, then for
assumptions — and the pair of them together says something the merged-only
graphs could not.

Continues [2026-09-08](2026-09-08-the-translation-cliff-and-all-eleven-case-studies.md).

## The same view for assumptions, which is where the structure is

`implication_graph_asm_with_unique_min.png` now sits beside the guarantee
version: same four groups, compared on assumptions instead. **34 of 36 drawn, no
failures**; the two missing are GenBuf, for the reason below.

The contrast with the guarantee view is the point:

| | Gyro trace 0 |
| --- | --- |
| guarantees | one flat equivalence bubble, 26 nodes wide, 5797&times;310 px |
| assumptions | a lattice **six levels deep**, 2156&times;790 px |

The same 24 specifications. On guarantees they are all equivalent; on
assumptions they order into a deep lattice. Everything that distinguishes one
repair from another is on the assumption side, and the guarantee view was flat
because there was nothing there to see.

That also settles why `unique == min` in 21 of 21 newly generated runs: step 3
filters on *guarantees*, and on guarantees no solution is strictly stronger than
another, so it has nothing to drop. The filter is not broken — it is looking at
the axis where these repairs do not differ.

### Where the merge lands: two shapes

The merged specification is a conjunction, so it is the strongest thing in the
solution lattice. It gets there two different ways:

* **Strictly stronger than every input.** AMBA trace 0: `original` →
  `unique_min_merged_0` → all 21 solutions below it, mostly one level with a few
  three-node chains. Traffic Updated trace 1 is the same shape with 12 solutions.
* **Equivalent to one particular input.** Gyro trace 0: the merged spec shares a
  bubble with `unique_min_6`, and the other 23 solutions are strictly weaker.

Trivial moves too, and is not always the floor:

* Traffic Updated 1 — trivial sits at the **bottom**, in a bubble with
  `unique_min_8`. One repair is exactly the trivial assumption.
* Gyro 0 — trivial is **incomparable** with every solution, hanging off the
  original on its own branch beside the merged bubble.

So "the merge collapses everything to 1" now has a precise meaning: on
guarantees the collapse is free, because the inputs were already equivalent; on
assumptions it is a real choice of the strongest point in a lattice that is up
to six levels deep, and the 23 or 65 weaker alternatives are genuinely distinct
repairs that the merged result does not represent.

### GenBuf, again

GenBuf traces 0 and 1 are the only two that did not draw. Their assumption
formula is the 28-conjunct one from the cliff table, and the graph run sat with
a single `ltlfilt` at 99.7% CPU. Their `gar` versions drew fine, because on
guarantees the comparison takes Spot's syntactic fast path — exactly the
asymmetry the cliff section predicts. Left running rather than killed; the graph
only has three nodes, so it may yet finish.

Atlas (177 graphs): <https://claude.ai/code/artifact/2fb2b369-3b4e-48e1-bfec-7f0f1ecae76b>

## Progress on everything else, as of 2026-09-09 18:15

Nothing has died. Every job launched on 09-04 and 09-08 is alive and holding
41–46% CPU, which is the signature of a subprocess-bound loop rather than a
stall.

| job | age | state |
| --- | ---: | --- |
| pcar | 1d12h | **2,555 → 764 semantically unique** — the only one to emit a stage line |
| mp_t0 / mp_t2 / mp_t4 (08-29) | 4d22h | step 2 over 34,651 / 21,456 / 35,603 |
| mp_t1 / mp_t2b / mp_t3 / mp_t4b (08-13) | 1d0h | step 2 over 23,201–27,589 |
| ts_t1 / ts_t3 | 1d0h | step 2 over 55,145 / 15,504 |
| genbuf | 4d10h | step 2 over **21** specs |

Step 2 prints only on completion, so silence is expected rather than a fault.
The nine large runs are all bound by the same O(n²) `ltlfilt` cost from
[2026-09-04](2026-09-04-stopping-the-non-terminating-searches.md) Part 2.

### The spread in comparison cost is enormous

Sampling GenBuf's step 2 at 18:13 caught a single `ltlfilt` that had been
running **2h13m and had reached 12.1 GB resident**. Two minutes later it was
gone and the job was cycling comparisons that finish in under three seconds,
with the host back to 60 GB free.

So it is not a memory leak and not a hang — it is that on a specification past
the translation cliff, individual comparisons range over four orders of
magnitude, from seconds to hours, and the expensive ones are expensive in memory
as well as time. That is the same cliff as
[2026-09-08](2026-09-08-the-translation-cliff-and-all-eleven-case-studies.md),
seen from inside a single run rather than across case studies.

### Two more stale jobs

Adding to the four recorded on 09-08, gpu14 carries a `filter_then_merge.py`
started **2026-08-20**, running 20 days at 101% CPU, and gpu11 is holding
defunct `ltlfilt` zombies 92 and 31 days old. None of these are from this work;
they survived the 09-04 cleanup because that only targeted `test_case_study`
searches. The trivial-solution generators on gpu06 and gpu04 have still written
nothing since 2026-08-19.

### A mixed Spot build to be aware of

The graph runs are calling **two different `ltlfilt` binaries**: the conda one on
`PATH`, and `/vol/bitbucket/tg4018/spot-maxacc/bin/ltlfilt`. Neither is the
`spot-acc128` build from 09-04, which is only reached when
`SPEC_REPAIR_LTLFILT` is exported — as it was for the gyro `gr1` redraw and not
since. Worth pinning deliberately before any timing numbers from these runs are
quoted, because the builds differ in their acceptance-set ceiling and therefore
in what they can decide at all.
