# SpecRepair

Automated repair of GR(1) reactive specifications, driven by Inductive Logic
Programming.

A GR(1) specification splits into *assumptions* about the environment and
*guarantees* the controller must uphold. Such a specification can fail in two
ways, and both are common in practice. It can be **unrealisable** — no
controller satisfies the guarantees against those assumptions — or it can be
realisable but **contradicted by reality**: a trace observed from the deployed
system violates an assumption the engineer believed to hold. Either way, the
specification, not the world, is what has to change.

SpecRepair takes a specification in [Spectra](https://github.com/SpectraSynthesizer)
together with a violating trace, and returns repaired specifications that no
longer admit the observed behaviour. Repair proceeds by *weakening*: the tool
diagnoses which formulas are at fault (from a violating trace, or from the
unrealisable cores Spectra reports), encodes the specification and the trace as
an Answer Set Programming learning task, and asks an ILP learner
([ILASP](https://github.com/ilaspltd/ILASP-releases) or
[FastLAS](https://github.com/spike-imperial/FastLAS)) for the weakest
modifications that resolve the fault. Each learned repair is fed back into the
loop until the specification is consistent with the trace and realisable again.

Repair is rarely unique. Rather than committing to one arbitrary fix, the
orchestrator explores the whole space of repair choices, deduplicating along the
way by semantic rather than syntactic equivalence, and post-processes the
results into the set of *maximal* (i.e. weakest-necessary) repairs — merging
solutions where their conjunction stays realisable, and filtering out those
implied by others. The result is a lattice of genuinely distinct repair options,
which can be rendered as an implication graph for a human to choose from.

## What is in this repository

- `spec_repair/` — the library: specification model and parsers, ASP/ILP
  encoders, learner and oracle wrappers, the repair orchestrators, and the
  post-processing pipeline (`spec_repair/diagnosis/`).
- `scripts/` — thin command-line entry points and experiment runners.
- `case_studies/`, `input-files/` — the benchmark specifications (minepump,
  lift, arbiter, traffic, genbuf, AMBA, …) and the mutated variants used to
  generate repair tasks.
- `docs/` — the experiment methodology, notably [the end-to-end pipeline](docs/experiment-pipeline.md),
  plus session notes recording why individual design decisions were made.
- `tests/` — the test suite, and the fixtures the experiments read and write.

The code targets Python 3.10.11. Older functionality lives under
`spec_repair/legacy/` and is kept for reference only.

Most of this repo continues the work of "Adapting Specifications for Reactive
Controllers", available [here](https://ieeexplore.ieee.org/abstract/document/10174043).

## Results

The implication graphs and stage counts for the current case-study-3 run
(2026-08-29) are published as a single self-contained page, readable on a phone:

**[Spectra Repair Atlas](https://claude.ai/code/artifact/2fb2b369-3b4e-48e1-bfec-7f0f1ecae76b)**

It is a snapshot rather than a live view. For live status of the searches and
the post-processing jobs on the lab machines:

```bash
ssh gpu20 bash /vol/bitbucket/tg4018/postproc_logs/status.sh
```

The reasoning behind those numbers is in
[docs/session-notes/](docs/session-notes/2026-09-04-stopping-the-non-terminating-searches.md).

## Setup

In order to run the code it is necessary to install the following:
### Spectra CLI:
    Available:
        https://github.com/SpectraSynthesizer/spectra-cli
    Set macro PATH_TO_CLI at beginning of config.py

### Install clingo version 5.6.2
A new version of Potassco's Clingo tool should be installed. As mentioned on the [website](https://potassco.org/clingo/),
you may install it via conda or pip, but you will see the following message:
```bash
> clingo -v
clingo version 5.6.2
...
Configuration: with Python 3.11.0, without Lua
...
```

The installation with Lua is mandatory for our usage, so conda won't work for us.
Instead, we will either install it from [source](https://github.com/potassco/clingo/releases/),
or, much easier, use your machine's installer.
#### Ubuntu:
Using apt
```bash
sudo add-apt-repository ppa:potassco/stable
sudo apt update
sudo apt install clingo
```

#### MacOS:
Using Homebrew
```bash
brew install clingo
```

### Install ILASP version 4.4.0

Download the appropriate version of the ILASP learner from their
[releases page](https://github.com/ilaspltd/ILASP-releases/releases).

### Install FastLAS version 2.1.0

Download the appropriate version of the FastLAS learner from their
[releases page](https://github.com/spike-imperial/FastLAS/releases).

### Install Spot
It's a tool that allows us to process ltl as strings, and has many uses in the
repair tool. To install it, follow its installation instruction on its [page](https://spot.lre.epita.fr/install.html).
For ease though:

```bash
# Make sure to update the link to the latest version on their website.
cd ~/Downloads # You may delete this later
wget http://www.lrde.epita.fr/dload/spot/spot-2.11.6.tar.gz 
tar -xf spot-2.11.6.tar.gz
cd spot-2.11.6/
# ./configure --prefix /path/to/your/tools
./configure # use the one above for more control over installation directory
make
make check # Only to test it works
make install
```

### Old Description
Java

Change macro SETUP_DICT at beginning of Specification.py to reflect your system setup.
This should indicate whether your system utilises Windows Subsystem for Linux (WSL)
as well as the paths for clingo and ILASP.

Before any of the scripts within the `/scripts` directory may be run, the packages within `spec_repair` have to be
locally pip installed, as explained in this
[tutorial](https://medium.com/mlearning-ai/a-practical-guide-to-python-project-structure-and-packaging-90c7f7a04f95),
using the following command within the main project directory:
```
pip install -e .
```

## Scripts

Documentation on each of the scripts' main purpose.

### Repair Spec
The `repair_spec` script, given an LTL specification written in Spectra and a log of a supposed assumption violation,
the command will return a repair version of the specification, which does not allow the same violation as before.

Example usage:
```
python repair_spec -s <spec_path> -t <trace_log_path> [-o <repaired_spec_path>]
```

### Choices Walker
Given a specification and a stronger version of this specification, the `choices_walker` will
attempt to run all possible choices within the specification repair pipeline, assuming
the pipeline allows manual choices to be made.

It is recommended to capture the output of the walker, since it contains information that can be
used to process statistics with.

Example usage:
```
python choices_walker > choices_output.txt
```

### Process Statistics
Given the printed output text of a `choices_walker` script, `process_statistics` will
extract a .csv file containing rows of information for each choice.
This script is useful in extracting meaningful statistics about the possible
outcomes of the specification repair run.

Example usage:
```
python process_statistics -i choices_output.txt -o choices_statistics.csv
```

### Visualise Resulting Specs
Given the path to all possible semantically-distinct repaired specifications that have been
produced in the runtime of `choices_walker`, `visualise_resulting_specs` allows the generation of
trees of entailment between specifications. The entailment is based on whether a specification's
assumption, guarantee or GR(1) formula is weaker than the other's.

Example usage:
```
python visualise_resulting_specs
```

### Visualise Tree
Given the paths of all possible choices, `visualise_tree` generates a simplified version
of the tree of choices that were taken, and the resulting states and repaired specs that
those choices led to


Example usage:
```
python visualise_tree
```
