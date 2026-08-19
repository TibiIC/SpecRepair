# Every failure was one failure

Report date: 2026-08-18. Follows
[2026-08-17](2026-08-17-the-filters-came-after-the-merge.md).

Post-processing went from 25 merged runs to 31, the corrected pipeline replaced
the inverted one everywhere, and the reason the largest pools cannot be filtered
was finally identified. It is not two problems. It is one, and it is ours.

## The population was never 40

The count of runs with results is **47**, and 45 of those also have trivial
solutions - genbuf traces 0 and 2 are the two without. Both numbers had been
reported correctly before and were contradicted during this session by a
counting bug of my own:

    n=$(ls "$d/final_specs"/*.spectra 2>/dev/null | wc -l)

Past `ARG_MAX` - about 2MB of argv, roughly 20k paths here - the shell cannot
expand the glob, `ls` exits with *Argument list too long* printing nothing,
`wc -l` reports **0**, and `2>/dev/null` swallows the error. Every pool past
that size read as empty. minepump_trace2 reads 0 that way and 23,455 via `find`;
traffic_single_trace1 reads 0 and 30,808.

That produced an hour of investigation into seven runs that had supposedly lost
their results, complete with a theory about a selective sweep hitting only the
large directories. Nothing had been deleted. The tell was there throughout and
was explained away: a directory reading 0 while its `intermediate_specs/` and
`progress.log` advanced normally only makes sense if the count is lying. The
repository had already fixed this same failure twice in the merge code
(`256c714`, *Long formulas exceed argv*).

`ftm_runner.sh` had the same guard, so the largest runs were being skipped as
though they had produced nothing - which is why the biggest pools never appeared
in any ftm log. Now `find -maxdepth 1 -name '*.spectra'`.

## The old order is gone, not just unused

`run_experiment_pipeline.py` still did merge -> maximal -> unique. It now does
`step_2_unique` -> `step_3_maximal` -> `step_4_merge`, writing `unique_specs/`
-> `max_unique_specs/` -> `filtered_merged_specs/`, sharing that last name with
`filter_then_merge.py` so the graph step reads either. Verified against the
standalone script on minepump_trace0: **17 -> 11 -> 11 -> 1** from both.

Two consumers were still reading the old order's output:

| consumer | was reading | consequence |
| --- | --- | --- |
| `report_repair_modifications.py` | `unique_max_merged_specs/` | every reported modification came from merge-then-filter |
| `visualise_resulting_specs.py` | `unique_max_merged` in its colour key and usage example | which is what invited a 5h graph run onto those directories |

Anything derived from the modifications report needs regenerating. No `.py`
under `scripts/`, `spec_repair/` or `main/` mentions the old directories now.
The directories themselves still exist in ~25 run folders on the cluster and are
not results.

A `postprocess_finished.sh` driver had been running the inverted pipeline on
elevator and amba for 23h21m and was cancelled.

## `--max-inputs` removed

A pool is never refused for its size. The cap had been hiding the best
reduction measured so far: **pcar_trace4, 860 -> 96 semantically unique**, an
89% collapse on a pool the cap had refused outright.

## Maximal specifications, incrementally

`strongest_guarantees` compared all n^2 pairs. "Strictly stronger guarantees" is
a strict partial order - transitive because implication is, asymmetric by
construction - so the maximal set builds incrementally: compare each
specification against the maxima so far, stop at the first dominator, evict any
maxima it dominates. O(n * |maxima|).

`--strongest-first` runs it before the equivalence filter. The final set is
unchanged, because equivalent specifications imply each other in both directions
and so are never separated by the guarantee filter - it keeps all of a class or
none of it. Verified: 17 -> 11 -> 11 -> 1 one way, 17 -> 17 -> 11 -> 1 the
other, same 11 survivors, same merge.

I had argued the opposite earlier in the session - that the guarantee filter
cannot shrink a pool because it cannot remove duplicates. It cannot remove
duplicates; it removes *dominated* specifications, and the evidence I
generalised from was 21-specification pools that had already been through the
equivalence filter, which says nothing about a raw pool of 22,000.

## The two failure modes were the same failure mode

Ten runs failed. They had been reported as two classes:

| reported as | runs | actually |
| --- | --- | --- |
| `exit -15`, earlyoom | 4 | out of memory |
| `exit 2`, "ltl2tgba tool error" | 2 | out of memory |

The crash dump settles it. `SPEC_REPAIR_CRASH_DIR` held the amba_trace3 formula:
**178,669 characters, 59,010 `X` operators, paren depth 9,854**. At the default
stack it segfaults; with the raised `RLIMIT_STACK` from `88f97de` it reports

    /vol/bitbucket/tg4018/spot-maxacc/bin/ltl2tgba: std::bad_alloc

so the stack fix converted a crash into an allocation failure without touching
the cause. `ltlfilt --simplify` on the same formula emits **0 bytes** at exit 0 -
simplification cannot carry it either, so there is no workaround at the tool
level.

Both exit codes are one condition: the formula does not fit in memory. Which
code you get depends only on whether earlyoom reaches the process before Spot's
allocator does. `--workers 2` was therefore never going to help, and did not -
a single 178KB formula with 9,854 levels of nesting does not fit however few run
at once. genbuf_trace0 dying on a **2-specification** pool was the clinching
evidence and was noted at the time as "not a concurrency effect", then still
filed under a separate cause.

The overnight run settled the last hope: `--strongest-first` does not rescue
these either. minepump_liveness_trace1 cleared stage 1 at 17 -> 17 and then died
in the equivalence check; minepump_trace1/2 and traffic_single_trace1/3 died
`during the comparison` - the GAR-only implication - so even guarantees alone
are too large on those runs. All ten failed by 01:28.

### The cause

`shift_prev_to_next` wraps **every variable occurrence** in `X(...)`. That is
what turns a specification containing no `next(` at all into 59,010 of them, and
it is the same rewrite behind the four merge crashes of 2026-08-17, which were
contained rather than fixed. Shifting the formula once instead of per occurrence
is the repair, and it is not yet done.

## Where post-processing stands

| | |
| --- | --- |
| runs with results | 47 (45 with trivial solutions) |
| merged | **31** |
| graphs | 29 asm, 29 gar, 25 gr1 |
| failing on memory | 10 |
| genbuf gr1 | still impossible; amba gr1 now times out at 3600s too |

The 31 merges are drawn in an atlas artifact; amba 0/1/2/4 and pcar 0/4 are
merged but not yet fully graphed.

`scripts/filter_then_merge.py` carrying the incremental maxima and
`--strongest-first` **is not committed** - git began failing in the working
shell with `getcwd: Operation not permitted` partway through the session. The
cluster copy is deployed and every job ran against it.
