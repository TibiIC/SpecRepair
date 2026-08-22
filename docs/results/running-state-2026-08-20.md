# What is running, as of 2026-08-20 22:45

> **Superseded 2026-08-21 09:00.** This file sweeps gpu01-gpu20 only, and six live
> searches were found outside that range - `genbuf_0`/`genbuf_1` on gpu26,
> `genbuf_4`/`traffic_single_1`/`minepump_liveness_4` on gpu27, `pcar_3` on gpu29,
> all running since 2026-08-14. `minepump_liveness_4` is therefore *not* stopped,
> and `genbuf_1`/`genbuf_4` each have their original search running alongside the
> MARCO re-run in the same directory. gpu22 and gpu28 refuse ssh and are unchecked.
> Sweep gpu01-gpu30, and see
> [the 2026-08-21 update](experiment-status-2026-08-19.md#update-2026-08-21-morning).

Everything below runs on the lab machines under `setsid nohup`, so it is
**unaffected by the laptop restarting**. Nothing here needs a live ssh session.
This file exists so the state can be picked up cold.

## How to check anything

    ssh gpu03 'cd /vol/bitbucket/tg4018 && tail -3 <log>'

| what | log directory |
| --- | --- |
| main-chain merges | `/vol/bitbucket/tg4018/pp_logs/<run>.big.log` |
| bounded merges | `/vol/bitbucket/tg4018/pp_logs/<run>.bounded.log` |
| unique-from-final | `/vol/bitbucket/tg4018/uniq_logs/<run>.uniq.log` |
| trivial solutions (MARCO) | `/vol/bitbucket/tg4018/pp_logs/triv_<run>.log` |
| genbuf re-runs | `/vol/bitbucket/tg4018/rerun_logs/<run>.marco.log` |

A finished job appends `rc=<code> finished <timestamp>`. No `rc=` line means it
is still going - check the process, not the log, since some stages print only on
completion.

Sweep every box at once:

    for h in gpu01 ... gpu20; do ssh $h 'hostname -s; ps -u tg4018 -o etime=,cmd= \
      | grep -E "test_case_study_3|filter_then_merge|generate_trivial" | grep -v grep'; done

## Running now

### merge-first (maximal realisable subsets) - added 2026-08-22 12:41

The new `--maximal` pipeline, on all five minepump traces. Trace 0 finished in
24 seconds (17 -> 1, guarantees equivalent to the original). The rest are pools
of 23-28k specifications and are expected to take days; there is deliberately no
bound on the enumeration, since a truncated one loses the maximality guarantee.

| run | box | pool |
| --- | --- | --- |
| minepump_trace0 | gpu07 | 17 - **done**, 1 merge |
| minepump_trace1 | gpu21 | 26,877 |
| minepump_trace2 | gpu23 | 23,598 |
| minepump_trace3 | gpu24 | 23,201 |
| minepump_trace4 | gpu25 | 27,589 |

Launcher: `/vol/bitbucket/tg4018/maximal_runner.sh <run> [<run>...]`, logs in
`/vol/bitbucket/tg4018/max_logs/<run>.max.log`, output written to each run's
`maximal_merged_specs/`. Same `rc=` convention as the other queues.

### genbuf re-runs, with MARCO cores (the 48 -> 50 work)

| run | box | started | state |
| --- | --- | --- | --- |
| genbuf_trace1 | gpu03 | 08-19 14:55 | 1 final spec, in `gr1Game0` |
| genbuf_trace3 | gpu11 | 08-20 ~11:00 | first verification |
| genbuf_trace4 | gpu13 | 08-19 14:55 | in `gr1Game0`, no leaf yet |

Launcher: `/vol/bitbucket/tg4018/rerun_marco.sh genbuf <trace>` - sets
`SPEC_REPAIR_RUN_DATE=2026-08-13`, `SPEC_REPAIR_MARCO_CORES=1`,
`SPEC_REPAIR_LEARNER=fastlas`, `SPEC_REPAIR_FASTLAS_RUNS=10`, so output lands in
the original directories with the original settings.

### unique-from-final (the paper's "unique" number)

minepump 1-4 restarted 2026-08-20 ~18:05 with **8 workers** and progress output:
gpu15, gpu17, gpu18, gpu14. Exact - deliberately no equivalence timeout on
these, so the counts are not upper bounds.

Six queues continue their remaining runs on gpu01, gpu02, gpu06, gpu09, gpu16,
gpu19 (currently minepump_liveness_trace4, amba_trace3, traffic_single_trace3,
traffic_single_trace1, pcar_trace3, amba_trace4). Launcher:
`UNIQ_WORKERS=8 /vol/bitbucket/tg4018/uniq_runner.sh <run> [<run>...]` - it works
through its list in order, so killing the current job advances it to the next.

### trivial solutions via MARCO

genbuf 0/1/3/4 on gpu13, gpu04, gpu10, gpu05, running since 2026-08-19 12:20 -
over 34 hours. These predate the progress output, so they will stay silent until
they finish. genbuf trace 2 is already done (15 seconds; no cores to hit).

### searches that never stopped

traffic_single 1/3, pcar 2/3/4, gyro 2/3, minepump 1/3, minepump_liveness 0,
genbuf 3 - six days and counting. `traffic_single_3` has **two** processes
(gpu12 and gpu20) writing one directory; nothing locks a run directory.

## Not started

`asm_merge` (`scripts/merge_assumptions.py`) has not run on any of the 47, by
the scheduling decision to give unique-from-final the free boxes first.

## Two orphan processes to leave alone or kill deliberately

`generate_trivial_solutions.py 2026-08-12` on gpu03 (7 days) and the
`2026-08-13` one on gpu06 (7 days) are the original `exploreAllCores` runs,
stuck and superseded by the MARCO ones. Killing them is safe; they have produced
everything they are going to.

Kill the **children** too, by PID - `pkill` on the parent leaves `ltlfilt`
running, and one such orphan burned a core for 1 day 17 hours unnoticed.
