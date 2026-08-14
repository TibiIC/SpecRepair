# The SIGTERM was earlyoom

Report date: 2026-08-15. Follows
[2026-08-14](2026-08-14-where-the-rerun-stands.md).

The long-running mystery is solved, and it was never our code. Two other things
came out of the day that change what the corpus is worth: colorsort's failure is
a trace-generation artefact rather than a size limit, and the unrealisable-core
cache earns its place on deep searches.

## The SIGTERM

**`earlyoom` runs on every lab box**, configured in `/etc/default/earlyoom` as:

    EARLYOOM_ARGS="-r 60 -m 25 -s 25"

`-m 25` means: when available memory falls below **25%** - about 15.5GB of a
62GB box - send **SIGTERM** to the process with the highest OOM score. That is
the whole thing. Every unexplained exit 143 in these notes since 2026-08-08 is
earlyoom choosing the fattest process on a shared machine, and ours is reliably
the fattest.

Two details make it fit exactly where a kernel OOM did not:

* **SIGTERM, not SIGKILL.** The kernel's own OOM killer sends SIGKILL (137).
  earlyoom sends SIGTERM (143) by design, so it can be caught. That difference
  is what kept the diagnosis wrong for a week - 143 was read as "something
  stopped us deliberately", which was true, but the something was a memory
  daemon rather than a scheduler or a person.
* **It fires on *available* memory, not on our usage.** So a run is killed for
  being the biggest process when *somebody else's* work pushes the box under the
  threshold. It never needed our runs to be at fault, which is why isolating
  them did not help.

Confirmed on gpu09, gpu10 and gpu30, each of which had SIGTERMed a colorsort run
while that run was **alone on the box with 55GB free at launch**. earlyoom's
journal is not readable without `adm` group membership, so the evidence is the
configuration plus the exit-code pattern rather than a kill line.

**The compute nodes do not run it.** Checked under `srun`: no earlyoom, no
systemd-oomd. So Slurm avoids this, which is what
[2026-08-13](2026-08-13-what-is-actually-broken.md) set out to test and could
not, twice, because of environment failures.

colorsort traces 0, 1 and 4 are now running on Slurm at `--mem=48G`, carrying
`SPEC_REPAIR_RUN_DATE=2026-08-13` so their results join the existing tree.
Passing that date through `--export` fails the job outright on this cluster
(`user env retrieval failed requeued held`, array 274347); it has to be
inherited from the submitting environment.

## colorsort is not too big - its traces are wrong

The specification is **byte-identical** to case_study_2's (same md5, 39
variables, 77 formulas), and case_study_2's colorsort runs *finished*, with 21
final specifications each. What differs is the traces:

| setup | assumptions violated per trace |
| --- | --- |
| case_study_2 | **exactly 1** |
| case_study_3 | **20**, the same 20 in all five traces |

At the violating step of every case_study_3 trace, *all five* colours and *all
five* detect values are true at once:

    t=4   color: [yellow]                     detect: [red]
    t=5   color: [black,blue,green,red,yellow] detect: [black,blue,green,red,yellow]

That breaks all ten `color_mutual_exclusion_*` and all ten
`detect_mutual_exclusion_*` at a stroke.

`max_targets: 1` **is** set, and the manifest confirms one target per trace. It
constrains what the generator *aims* at, not what it *collaterally breaks*, and
the ASP program says so in as many words:

    % The target must break. Nothing says it has to break *alone*: requiring
    % that made the target unreachable wherever assumptions overlap...
    :- to_violate(E), trace(S), not violated_exp(E,S).

There is no `#minimize`, so among all models breaking the target, clingo returns
one - and it returns the maximal one.

That relaxation was right for amba, where overlap is incidental. For colorsort
the overlap is *structural*: the twenty mutual-exclusion constraints are the
scaffolding that encodes two 5-valued enums as booleans. Breaking one pair is a
perturbation; breaking all twenty dissolves the encoding, leaving `color` and
`detect` as free 5-bit vectors. The repair search is then handed a far harder
problem than case_study_2 ever posed - which is why it produces 30GB+ of BDD,
discards candidates as "Spectra cannot verify", and finds nothing.

**Not yet fixed**, because it invalidates the current traces. The shape would be
a soft constraint - `#minimize { 1,E : violated_exp(E,S), not to_violate(E) }` -
preferring models that break fewest assumptions beyond the target while leaving
every target reachable.

### What colorsort cost, and what it is worth

Ten runs, **zero repairs**: five ILASP all exit 1, two FastLAS exit 1, three
FastLAS SIGTERMed. And since all five traces violate the identical twenty
assumptions, colorsort contributes *one case repeated five times* even if it
completes.

The desugaring penalty behind it: 39 boolean variables, of which only **7 are
genuinely boolean**. `spec` (15), `color` (5), `detect` (5), `botMot` (3), `ack`
(2) and `motSpeed` (2) are enums encoded as booleans, so 2^39 states stand in
for roughly 2^13 - a factor of about 67 million. That is the boolean-desugar
branch's cost, not colorsort's.

## The unrealisable-core cache

`exploreAllCores` is reached from four places - `trivial_solution.py:43`,
`new_spec_encoder.py:115`, `filter_counter_traces`, and its duplicate in
`strix_gr1_revised_oracle.py` - and the same specification text reaches it
repeatedly, because the recheck loop revisits trivialisations that sibling
branches already produced by removing the same guarantees in a different order.

Now memoised, as a component (`spec_repair/components/unrealisable_core_cache.py`)
rather than module state: constructed enabled or disabled, `reset()`, stats as a
value object, copies in and out so a caller mutating a returned set cannot
poison an entry. It takes `compute` as a parameter, so it knows nothing about
Spectra or the JVM and its tests run in 0.07s without one.

Keyed on **canonical** specification text, so `asm A; gar B` and `gar B; asm A`
share an entry. Only the key is canonicalised - the search still receives the
caller's text verbatim, because cores are mapped back to names *by line number*.
Whether the tool is order-sensitive was checked against the real thing rather
than assumed: permuting the formulas of a two-core specification returns the same
two cores every time.

Measured on minepump trace 2, the trace that violates both assumptions:

| elapsed | calls | hits | hit rate |
| --- | --- | --- | --- |
| 60s | 24 | 3 | 12% |
| 180s | 95 | 50 | 53% |
| 390s | 330 | 240 | 73% |
| 2h03m | 4365 | 3568 | **82%** |

It climbs with depth and plateaus around four-fifths: 3,568 searches avoided in
one run. On minepump each search is milliseconds, so the wall-clock saving is
small - what transfers to the large case studies is the repetition rate. On
minepump trace 0 the cache sees **zero** calls, because a run that succeeds on
assumption weakening never reaches a core search at all.

**It is not a fix for genbuf.** There, one call has never returned, and there is
no repeat to serve.

## `exploreAllCores` on genbuf, measured directly

Five intermediates - the original minus each trace's violated assumptions, which
is what trivial solution generation actually hands to the search. All five are
distinct; the traces violate different assumption sets, so there was nothing to
deduplicate.

| intermediate | traces | result |
| --- | --- | --- |
| 2 | 2 | **returned in 3.6s**, 0 cores - the specification is realizable |
| 0, 1, 3, 4 | 0, 1, 3, 4 | unrealisable; **no result after 2h+**, flat at ~1.5GB |

So genbuf's wall is `exploreAllCores` on *unrealisable* intermediates
specifically, not genbuf's size. Trace 2 sails through because removing its
assumptions leaves a realizable specification and the fast path skips the search
entirely.

**It is not to be bounded** - see
[2026-08-13](2026-08-13-what-is-actually-broken.md). A truncated core set cannot
be told from a complete one and breaks the hitting-set argument the trivial
solution algorithm is proven on.

## Two workflow faults

**ILASP wrote to unsuffixed directories.** `learner_suffix` returned `""` for
the default learner, so the arms were shaped differently -
`gyro_trace0_fastlas_<date>` beside `gyro_trace0_<date>`. Querying a live sweep
for its ILASP results reported `NO_DIR` for all thirteen running jobs, which
reads exactly like "produced nothing". Fixed to `_ilasp`; **not yet deployed**,
because `learner_suffix` is shared with case_study_1 and case_study_2 and those
sweeps still have queued jobs that would split across two naming schemes.

**The queue was the bottleneck, not the machines.** 55 runs per arm behind a
4-slot semaphore on one box each, while 19 machines sat idle. Redistributed with
`scripts/run_case_study_3_pairs.sh`, which takes explicit `case:trace` pairs and
starts them all at once, sized by hand - five light traces on a small box, one
colorsort on a large one. 83 concurrent, nothing queued.

## Where the experiments stand

repaired **55**, no repair 18, killed 3, running 34.

Complete on both arms: **elevator 10/10**, **lift 10/10**, **traffic_updated
10/10**. amba: FastLAS 5/5, ILASP 1/5. colorsort: 0 of 10.

Longest running, all past a day: `genbuf_3` (FastLAS), `minepump_liveness_0`,
`pcar_0` (ILASP, 21GB), `gyro_0`, `traffic_single_3` - both arms.
