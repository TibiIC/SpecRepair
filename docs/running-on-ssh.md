# Running things on the GPU boxes

Everything here assumes the lab machines `gpuNN.doc.ic.ac.uk`, reachable as
`ssh gpu03` because `~/.ssh/config` maps `Host gpu*` to `%h.doc.ic.ac.uk`.

## The one thing to know first

`/vol/bitbucket/tg4018/PhD/SpecRepair` is on **shared NFS**. Every box sees the
same checkout, the same `input-files/`, the same `logs/`, the same
`tests/test_files/out/`. So:

* a `git pull` on one box updates the code for all of them;
* two sweeps on different boxes write into the *same* output tree;
* `ls logs/...` gives the same answer wherever you run it, which makes it easy
  to think you are looking at one box's results when you are looking at
  another's. Name the log directory explicitly rather than using `ls -t`.

What is *not* shared: processes, memory, tmux sessions.

## Getting a working shell

The environment does not come up on its own in a non-interactive `ssh`. This
fails with `conda: command not found`:

    ssh gpu03 'conda activate logic && python ...'

Use tmux and send a full setup line. This is the incantation, and it is the
same one every runner script uses:

    ssh gpu03
    tmux new-session -s work
    source ~/.sdkman/bin/sdkman-init.sh
    source ~/phd_work.sh
    conda activate logic
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
    cd /vol/bitbucket/tg4018/PhD/SpecRepair

`LD_LIBRARY_PATH` matters: without it clingo cannot find `libclingo.so`.

Detach with `Ctrl-b d`, come back with `tmux attach -t work`. Work that should
survive your ssh dropping **must** be inside tmux.

## Why to prefer a GPU box over the laptop

Spectra picks its BDD package at startup. On Linux the jars carry `libcudd.so`
and it is extracted and used; on macOS they ship no `.dylib`, so it falls back
to JTLV, whose node table is fixed at 100k and never grows. A large
specification - amba, colorsort, genbuf - then reaches an equilibrium where it
garbage-collects forever without erroring or finishing.

So: anything touching a large specification (realisability, synthesis, merging,
graphs) belongs on a GPU box. Small ones (minepump, traffic_*, elevator, lift)
are fine locally.

You can tell which package is in use:

    grep -o "Using BDD Package: [A-Za-z]*" <a log> | sort -u

`CUDDFactory` is what you want. `JTLVJavaFactory` on a big case study means it
will not finish.

## Picking a box

    for h in gpu01 gpu03 gpu06 gpu11 gpu12 gpu13 gpu14 gpu15 gpu20; do
      printf "%-6s " $h
      ssh -o ConnectTimeout=8 $h 'echo "mem=$(free -g | awk "/Mem:/{print \$7}")GB \
        cores=$(nproc) sweeps=$(pgrep -u $USER -f "[t]ests.test_main.test_case_study" | wc -l)"'
    done

A repair run holds **5-9GB** once its search is a few thousand nodes deep, so
divide free memory by 9 to get a safe concurrency. The bracket in
`[t]ests` stops `pgrep` matching its own command line - without it you always
see one phantom process.

## Checking on something that is running

    tmux list-sessions
    tmux list-windows -t <session>
    tmux attach -t <session>          # Ctrl-b d to leave it running

Per-run state, without attaching:

    D=logs/case_study_3/all_fastlas_2026-08-12_161741
    ls $D/*.exitcode | wc -l                     # how many finished
    for f in $D/*.exitcode; do echo "$(basename $f .exitcode)=$(cat $f)"; done

Exit codes, which are the whole point of those files:

| code | meaning |
| --- | --- |
| 0 | finished, produced repaired specifications |
| 1 | finished, produced none - the assertion failed |
| 137 | killed with SIGKILL |
| 143 | killed with SIGTERM |
| 139 | segmentation fault |

A run with **no** `.exitcode` file has not finished. Before these existed, a
killed run and a queued run were indistinguishable.

## Killing things

`pkill -f` matches your own ssh command line, which is how you kill the shell
you are typing into. Two defences:

    pkill -9 -u $USER -f "[g]enerate_case_study_3"     # bracket the first letter

and never put the pattern and the thing you are launching in the same command -
`pkill ... && tmux send-keys "... generate_case_study_3.py ..."` kills itself
before the launch, silently.

To stop a whole sweep: `tmux kill-session -t <name>`, then check for survivors,
because killing the session does not always take the JVM with it:

    pgrep -u $USER -f "[t]ests.test_main.test_case_study" | wc -l

## Moving code and results

Code goes through git; the remote has no push access, so pull only, and use
agent forwarding for the fetch:

    ssh -A gpu03 'cd /vol/bitbucket/tg4018/PhD/SpecRepair && git pull --ff-only'

**Never `git stash` to clear a blocked merge.** It has twice swept away
untracked case_study_3 traces that experiments were running against. Move the
directory aside (`mv dir dir.bak`) or commit it.

Results come back with the pull script, which globs `*_<date>`:

    REMOTE_SUBDIR=case_study_3 ./scripts/pull_experiment_from_ssh.sh 2026-08-12 gpu12

## The trap that has cost the most

**Run directories are not cleared between sweeps.** Two sweeps of the same case
study on the same date write into the same `<case>_trace<N>_<date>/`, and
`final_specs/` accumulates across both. Nothing warns you. Check file mtimes
against `status.txt`'s `started` line before trusting a directory:

    d=tests/test_files/out_ssh/2026-08-12/amba_trace0_fastlas_2026-08-12
    grep started $d/status.txt
    ls -l --time-style=+%m-%d\ %H:%M $d/final_specs | head

Anything older than `started` is left over from a previous run.
