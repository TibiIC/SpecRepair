# Where the rerun stands

Report date: 2026-08-14. Follows
[2026-08-13](2026-08-13-what-is-actually-broken.md).

This is the starting point for today: every case_study_3 (specification, trace)
pair and what has happened to it. The sweeps launched at 21:57 and 21:58 last
night and are still running, so most of the table is still `queued` - that is
the point of writing it down now rather than at the end.

Both arms run **under CUDD**, with the counter-strategy expansion capped. Nothing
here is comparable with anything measured before 2026-08-13.

## Status of all 55 pairs, both learners

Read the codes as: **repaired** is exit 0, a run that finished and produced at
least one repaired specification; **no repair** is exit 1, a run that finished
and produced none, which is a result rather than a failure; **SIGTERM** is exit
143, the run being stopped by something outside itself.

| case study | trace | FastLAS (gpu20) | ILASP (gpu12) |
| --- | --- | --- | --- |
| **amba** | 0 | repaired, 12m40s | no repair, 14m17s |
| **amba** | 1 | repaired, 13m53s | no repair, 13m56s |
| **amba** | 2 | repaired, 12m53s | no repair, 13m55s |
| **amba** | 3 | repaired, 13m47s | no repair, 14m03s |
| **amba** | 4 | repaired, 11m22s | **repaired, 13m08s** |
| **genbuf** | 0 | queued | no repair, 10m27s |
| **genbuf** | 1 | queued | no repair, 10m44s |
| **genbuf** | 2 | repaired, 1m21s | **repaired, 10m08s** |
| **genbuf** | 3 | running, 13h30m | queued |
| **genbuf** | 4 | queued | no repair, 10m22s |
| **minepump** | 0 | queued | queued |
| **minepump** | 1 | queued | queued |
| **minepump** | 2 | queued | queued |
| **minepump** | 3 | queued | queued |
| **minepump** | 4 | queued | queued |
| colorsort | 0 | **SIGTERM**, at 28.5GB | queued |
| colorsort | 1 | queued | queued |
| colorsort | 2 | queued | no repair, 10m57s |
| colorsort | 3 | queued | queued |
| colorsort | 4 | queued | queued |
| elevator | 0 | queued | queued |
| elevator | 1 | repaired, 21.7s | queued |
| elevator | 2 | repaired, 15.8s | queued |
| elevator | 3 | queued | queued |
| elevator | 4 | queued | queued |
| gyro | 0 | queued | running, 13h09m |
| gyro | 1 | queued | queued |
| gyro | 2 | queued | running, 2h23m |
| gyro | 3 | queued | queued |
| gyro | 4 | queued | queued |
| lift | 0 | queued | repaired, 25.6s |
| lift | 1-4 | queued | queued |
| minepump_liveness | 0 | running, 13h32m | repaired, 5h01m |
| minepump_liveness | 1 | queued | queued |
| minepump_liveness | 2 | no repair, 9m21s | no repair, 6m00s |
| minepump_liveness | 3 | queued | queued |
| minepump_liveness | 4 | queued | repaired, 5h32m |
| pcar | 0 | queued | running, 13h17m |
| pcar | 1 | queued | repaired, 16.8s |
| pcar | 2 | queued | queued |
| pcar | 3 | queued | queued |
| pcar | 4 | running, 10h17m | queued |
| traffic_single | 0 | repaired, 17.1s | queued |
| traffic_single | 1 | queued | queued |
| traffic_single | 2 | queued | queued |
| traffic_single | 3 | running, 13h18m | running, 13h17m |
| traffic_single | 4 | queued | queued |
| traffic_updated | 0 | queued | queued |
| traffic_updated | 1 | queued | queued |
| traffic_updated | 2 | queued | repaired, 7.8s |
| traffic_updated | 3 | queued | repaired, 13.6s |
| traffic_updated | 4 | queued | queued |

Totals: **FastLAS 11 of 55 finished**, 4 running. **ILASP 17 of 55 finished**,
4 running. Four concurrent per box, so the rest are waiting on a slot rather
than on anything being wrong.

## What the finished rows already say

**genbuf completes.** It had never finished once, on any machine, under either
learner - it was OOM-killed every time. Five of its ten runs are in, at around
ten minutes each. Both fixes were needed: the counter-trace cap for the 53GB,
CUDD for the JTLV thrash.

**ILASP repairs amba.** [results/case-study-3-amba.md](../results/case-study-3-amba.md)
records ILASP at 0/5 for amba at both 600s and 3600s. Under CUDD `amba_4` comes
back exit 0. Those earlier runs were dying rather than failing to learn, so that
finding does not survive and the file needs rewriting from this data.

**The learners differ, but not the way it was written up.** On amba FastLAS
repairs all five and ILASP one of five; on genbuf both repair trace 2 and
neither repairs the others so far. "ILASP cannot repair these two at a practical
budget" was measuring the crash, not the learner.

**Run times are bimodal.** Most finish in seconds or ten-ish minutes;
`minepump_liveness` takes five hours on ILASP and four runs have passed thirteen
on FastLAS. Long is expected here and is not itself evidence of a fault.

## Open, and unchanged from last night

* **`exploreAllCores` has no bound.** `genbuf_3` on FastLAS is 13h30m inside
  `Checker$Memoize.seek`; genbuf's trivial solutions are 13h13m into the same
  call. Sibling genbuf traces cleared it in minutes. This is what blocks
  genbuf's graphs, since it is the trivial solutions that are stuck.
* **colorsort died on SIGTERM at 28.5GB.** Exit 143, not the kernel's 137, so
  the unexplained SIGTERM is still unexplained. The growth itself is steady with
  elapsed time, which is what CUDD's native uncapped BDD tables do - not the
  expansion bug, which is capped.
* **Trivial solutions: 50 of 55.** 146 specification files, no empty
  directories. genbuf is the missing five.
