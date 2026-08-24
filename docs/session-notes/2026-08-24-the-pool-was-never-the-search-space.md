# The pool was never the search space

Report date: 2026-08-24. Follows
[2026-08-20](2026-08-20-the-walls-behind-the-wall.md).

The merge-first pipeline built on 2026-08-22 crashed one run and hung three. The
reason is a number nobody had measured: minepump trace 1's 26,877
specifications carry **10,223 distinct guarantees** between them, and trace 4's
carry 12,148. The enumeration searched those directly. The original
specification has three guarantees.

## What the merge-first pipeline did

`maximal_merging` pools every distinct guarantee in a run and enumerates the
maximal realisable subsets with MARCO. The reasoning is sound - realisability is
antitone under conjunction, so the realisable subsets are downward-closed and
their maximal elements are the strongest merges, whatever order the input
arrived in. The mistake was never checking how big the pool was.

Its first act is one realisability check over the whole pool, on the grounds
that if it passes there is a unique maximum and nothing left to enumerate. On
these runs that is a single Spectra synthesis over ten thousand guarantees.
MARCO would not have helped: it maximises its seeds, so its first probe is the
same specification.

| run | specs | distinct guarantees | outcome |
| --- | --- | --- | --- |
| minepump_trace0 | 17 | **3** | done in 24s |
| minepump_trace3 | 23,201 | 8,900 | 2 days, still stage 0 |
| minepump_trace2 | 23,598 | 9,226 | 2 days, still stage 0 |
| minepump_trace1 | 26,877 | 10,223 | 2 days, still stage 0 |
| minepump_trace4 | 27,589 | **12,148** | **rc=139**, 7 hours |

Trace 4 has the largest pool and is the one whose JVM died, which is what makes
this a size limit rather than an unlucky crash.

Two things made this avoidable and were not done. The module docstring asserted
"roughly a thousand for minepump" - a guess, an order of magnitude low, written
as though measured. And the smoke tests were trace 0 (three distinct guarantees,
nineteen assumptions) and genbuf trace 1 (two specifications). Both took the
one-call fast path in seconds and exercised none of the enumeration. Trace 0 is
in fact the *inverse* shape of the problem: its repairs vary only on the
assumption side.

There was also no way to tell. The whole-pool check sits ahead of the progress
reporting, so a run that cannot get past it prints `stage 0` and nothing else,
for as long as it lasts.

## The crash, separately

62GB box, 60GB free, nothing in the kernel log, and no JVM fatal-error log
written anywhere - which `jvm.py`'s own comment says has happened before. But
unset, the JVM takes a quarter of RAM (~15.5GB) and that file already names that
default as what stops colorsort. The runner now asks for 48g and points
`-XX:ErrorFile` at `max_logs/jvm`, so a repeat leaves a diagnosis. Whether that
alone would carry a 12,148-guarantee synthesis is untested and doubtful; it
removes one known cause, it does not make the call tractable.

## The redesign: descend from the original, not up from the pool

The pool is thousands of alternative weakenings of a handful of named formulas.
The strongest possible answer is the original specification itself, so start
there and weaken only where forced:

    base   = pooled assumptions + the ORIGINAL guarantees
    if realisable(base): base is the unique maximum, and we are done
    cores  = minimal unrealisable cores of base          (MARCO, over ~3-5)
    for each minimal hitting set H of those cores:
        every name in H must give way; weaken it from the pool

Measured on trace 4, the run that crashed:

    pool: 27589 spec(s), 5 distinct assumption(s), 12148 guarantee variant(s)
    base: 5 assumption(s) + 3 ORIGINAL guarantee(s) - one check
    cores over the original guarantees: 1 (26.6s)
       core: ['guarantee1_1', 'guarantee2_1']
    minimal hitting sets: 2 - one branch each

Twenty-seven seconds to the whole structure, against seven hours to a segfault.
The core is the one derived by hand on 2026-08-22: `guarantee1_1` and
`guarantee2_1` conflict as soon as `assumption2_1` stops forbidding
`highwater & methane`. Its two minimal hitting sets give two branches - weaken
one guarantee or the other - which matches the old pipeline's output, where 11
of the 50 merged specifications kept `guarantee1_1` intact and 6 kept
`guarantee2_1`.

### It is the trivial-solution methodology, generalised

`trivial_solution.get_all_trivial_solutions_marco` already does cores, then
every minimal hitting set, then realisable-by-construction. It **deletes** each
implicated guarantee. This **weakens** it from the pool instead, deleting only
when nothing works - so deletion is the limiting case where the replacement is
`true`. Same skeleton, same completeness argument, one gives the floor and the
other the ceiling. That is a better story for the paper than a second, unrelated
merge, and it is why the flat enumeration was the wrong shape: it discarded a
skeleton this codebase already uses successfully.

### Why it can be lossless and still cheap

By the MUS/MCS duality the maximal realisable subsets are the complements of the
minimal hitting sets of the cores. They are read off combinatorially rather than
reached by *growing* a seed one oracle call at a time, which is what makes the
flat enumeration hopeless at ten thousand elements.

Losslessness rests on the same condition as the trivial-solution path: every
core, each one minimal. Truncating breaks the hitting-set argument silently,
which is why nothing here is bounded.

* Liffiton, Previti, Malik, Marques-Silva, *Fast, flexible MUS enumeration*,
  Constraints 21(2), 2016. https://doi.org/10.1007/s10601-015-9183-0
* Liffiton, Sakallah, *Algorithms for computing minimal unsatisfiable subsets of
  constraints*, JAR 40(1), 2008. https://doi.org/10.1007/s10817-007-9084-z

### What is not yet proven

Each branch still has to choose *how* to weaken its implicated guarantee, and a
conjunction of several variants of one name can be stronger than any single one
- that is the cs1 `merged_5` effect, where `g2_0 & g2_11 & g2_8` recovered the
original `guarantee2_1`. So the inner step is itself a maximal-subset problem,
scoped to one name's variants with everything else held fixed. On trace 4 branch
1 that is 6,162 variants, which is far better than 12,148 but not small. This is
the part to watch, and the part to prove rather than assert.

## Which runs this applies to

Only four. `scripts/report_guarantee_degradation.py` compares each run's merged
guarantees against the original's, parsing both sides:

| runs | merged | guarantees |
| --- | --- | --- |
| minepump 1-4 | 50 / 35 / 40 / 48 | weakened, one dropped outright in each |
| the other 43 | 1 | identical to the original's |

A merge that already reaches the original's guarantees has hit the ceiling -
every repair weakens, so nothing stronger exists and no filter ahead of it can
have cost anything. Those 43 are unaffected by construction, not merely
untested.

The first version of that check compared hand-written `original.spectra` text
against model-serialised merge output and reported **40 of 47** runs degraded,
including minepump trace 0, whose guarantees are provably equivalent to the
original's. Parsing both sides drops it to four. The second version still could
not see a guarantee the merge had *dropped entirely*, because it iterated over
what the merge kept; adding that found minepump 1-4 had each dropped one, and
changed nothing else.

## State at the end of the day

| what | where | state |
| --- | --- | --- |
| merge-first, minepump 1/2/3 | gpu21, gpu23, gpu24 | running, 2 days, still stage 0 |
| merge-first, minepump 4 | gpu25 | relaunched 12:56 with 48g heap |
| **directed**, minepump 4 | gpu07 | running, past cores in 26.6s, branch 1/2 |
| merge-first, minepump 0 / genbuf 1 | done | 17 -> 1 and 2 -> 1 |
| unique-from-final | six queues | 19 finished, 7 still going |
| genbuf MARCO re-runs | gpu03, gpu11, gpu13 | running |
| trivial solutions (MARCO) | gpu04, gpu05, gpu10, gpu13 | running |

The directed run writes `directed_merged_specs/` and the merge-first run writes
`maximal_merged_specs/`, so both can be in flight on the same run directory
without colliding - which is why trace 4 has one of each rather than one being
killed for the other.
