"""
Every minimal unrealisable core of a specification, computed here rather than by
Spectra.

An unrealisable core is a subset of the guarantees that is already unrealisable
against the assumptions; minimal means no proper subset of it is. Enumerating
all of them is the same problem as enumerating all MUSes (minimal unsatisfiable
subsets) of a constraint set, with "unrealisable" in place of "unsatisfiable",
so the MUS literature applies directly.

**Why not Spectra's.** `cores.SpectraToolbox.exploreAllCores` does compute this,
and for small specifications it is fast. Its memoisation is the problem:
`Checker$Memoize` keeps every previously-checked subset in two `SortedSet`s and
`lookupPos` walks the whole set calling `isSubset` on each entry, so a check
costs O(|memo| x n) and |memo| grows with every check. Disassembled from the
shipped jar on 2026-08-17 - the loop is plainly linear. Measured consequence: on
genbuf it ran over fifteen hours at 100% CPU with memory flat at 1.5GB, never
returning, because it was rescanning its own cache rather than computing cores.
It also returns neither all cores nor only minimal ones, which
`get_all_trivial_solutions_guarantee_only` has to compensate for with a recheck
loop.

**Algorithm: MARCO.** Keep the unexplored region as a *formula* over which
guarantees are selected, not as a list of subsets, and ask a solver for a
maximal unexplored seed. A realisable seed grows to a maximal realisable subset
and blocks everything below it; an unrealisable seed shrinks to a minimal core
and blocks everything above it. Each iteration removes a region rather than a
point, and the bookkeeping is a solver call rather than a linear scan.

* Liffiton, Previti, Malik, Marques-Silva, *Fast, flexible MUS enumeration*,
  Constraints 21(2), 2016. https://doi.org/10.1007/s10601-015-9183-0
* Reference implementation: https://github.com/liffiton/MARCO
* Liffiton, Sakallah, *Algorithms for computing minimal unsatisfiable subsets of
  constraints*, JAR 40(1), 2008 - CAMUS, the predecessor.
  https://doi.org/10.1007/s10817-007-9084-z
* Zeller, Hildebrandt, *Simplifying and isolating failure-inducing input*, IEEE
  TSE 28(2), 2002 - delta debugging, which is what Spectra's `ddmin` shrink step
  is. https://doi.org/10.1109/32.988498

On unrealisable cores for GR(1) specifically:

* Cimatti, Roveri, Schuppan, Tchaltsev, *Diagnostic information for
  realizability*, VMCAI 2008. https://doi.org/10.1007/978-3-540-78163-9_9
* Konighofer, Hofferek, Bloem, *Debugging formal specifications: a practical
  approach using model-based diagnosis and counterstrategies*, STTT 15(5-6),
  2013. https://doi.org/10.1007/s10009-011-0221-y
* Spectra: https://github.com/SpectraSynthesizer

The map solver is clingo, already a dependency, and every step is deterministic:
guarantee names are sorted, the seed is the lexicographically first among the
maximal models, and no randomness is involved anywhere. Two runs on the same
specification return the same cores in the same order.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Set

from spec_repair.ltl_types import GR1FormulaType
from spec_repair.util.asp_trace_util import run_clingo_raw
from spec_repair.util.file_util import discard_temp_file, generate_temp_filename, write_to_file

# A predicate over guarantee names: True when the specification restricted to
# exactly those guarantees (with all assumptions) is realisable.
RealisabilityOracle = Callable[[Set[str]], bool]

_MODEL_ATOM = re.compile(r"sel\(([^)]+)\)")


@dataclass
class CoreSearchStats:
    """What the search did, for reporting alongside the cores."""
    oracle_calls: int = 0
    seeds: int = 0
    cores: int = 0
    maximal_realisable: int = 0

    def __str__(self) -> str:
        return (f"{self.cores} core(s) from {self.seeds} seed(s), "
                f"{self.oracle_calls} realisability check(s), "
                f"{self.maximal_realisable} maximal realisable subset(s)")


@dataclass
class AllUnrealisableCores:
    """
    MARCO over a realisability oracle.

    Constructed with the guarantee names and the oracle, so it knows nothing
    about Spectra, the JVM or specifications - which is what makes it testable
    without any of them.

    :param names: every guarantee that may appear in a core, in any order; they
        are sorted internally so the enumeration is reproducible.
    :param oracle: called with a set of guarantee names, returns whether that
        subset is realisable. Assumed *monotone*: adding guarantees can only
        make a specification less realisable. That is what lets a single core
        block all its supersets.
    """
    names: Sequence[str]
    oracle: RealisabilityOracle
    stats: CoreSearchStats = field(default_factory=CoreSearchStats)
    _blocked_up: List[Set[str]] = field(default_factory=list, repr=False)
    _blocked_down: List[Set[str]] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._names = sorted(set(self.names))

    def _check(self, subset: Set[str]) -> bool:
        self.stats.oracle_calls += 1
        return self.oracle(subset)

    def _map_program(self) -> str:
        """
        The unexplored region, as ASP.

        One choice atom per guarantee. Each core found forbids selecting all of
        it (blocking every superset); each maximal realisable subset forbids
        selecting nothing outside it (blocking every subset). Maximising the
        selection makes the seed maximal, which is what makes an unrealisable
        seed shrink to a core quickly.
        """
        lines = [f"g({_atom(n)})." for n in self._names]
        lines.append("{ sel(G) } :- g(G).")
        for core in self._blocked_up:
            body = ", ".join(f"sel({_atom(n)})" for n in sorted(core))
            lines.append(f":- {body}.")
        for mss in self._blocked_down:
            outside = [n for n in self._names if n not in mss]
            if not outside:
                # Everything is realisable together: nothing left unexplored.
                lines.append(":- #true.")
                continue
            body = ", ".join(f"not sel({_atom(n)})" for n in sorted(outside))
            lines.append(f":- {body}.")
        lines.append("#maximize { 1,G : sel(G) }.")
        lines.append("#show sel/1.")
        return "\n".join(lines) + "\n"

    def _next_seed(self) -> Optional[Set[str]]:
        """A maximal unexplored subset, or None when the region is empty."""
        program = self._map_program()
        path = generate_temp_filename(ext=".lp")
        write_to_file(path, program)
        try:
            output = run_clingo_raw(path, n_models=0)
        finally:
            discard_temp_file(path)
        if "UNSATISFIABLE" in output:
            return None
        # With #maximize, clingo prints improving models in order; the last is
        # optimal. Taking the last keeps the seed maximal and deterministic.
        models = [line for line in output.splitlines() if "sel(" in line]
        if not models:
            return set() if "SATISFIABLE" in output else None
        self.stats.seeds += 1
        return {_unatom(m) for m in _MODEL_ATOM.findall(models[-1])}

    def _shrink_to_core(self, seed: Set[str]) -> Set[str]:
        """
        Remove guarantees while the subset stays unrealisable.

        Plain deletion-based minimisation, one oracle call per element. `ddmin`
        would take fewer calls on a large seed, but each call here is a Spectra
        synthesis and the seeds are guarantee-sized, so the simpler loop is
        easier to trust and rarely slower in practice.
        """
        core = set(seed)
        for name in sorted(seed):
            candidate = core - {name}
            if candidate and not self._check(candidate):
                core = candidate
        return core

    def _grow_to_maximal(self, seed: Set[str]) -> Set[str]:
        """Add guarantees while the subset stays realisable."""
        grown = set(seed)
        for name in self._names:
            if name in grown:
                continue
            candidate = grown | {name}
            if self._check(candidate):
                grown = candidate
        return grown

    def enumerate(self, progress_every: float = 60.0) -> List[Set[str]]:
        """
        Every minimal unrealisable core, each returned once.

        Terminates because each iteration blocks a region of the subset lattice
        that no later seed can revisit, and the lattice is finite. How long that
        takes is bounded by the *number* of cores, not by the cost of a single
        realisability check, so a specification with a cheap oracle can still
        run for hours - which is why it reports progress rather than going
        silent. `progress_every` is in seconds; 0 turns the reporting off.
        """
        import time
        cores: List[Set[str]] = []
        started = last_report = time.time()
        while True:
            if progress_every and time.time() - last_report >= progress_every:
                last_report = time.time()
                print(f"         cores: {self.stats} "
                      f"({last_report - started:.0f}s elapsed)", flush=True)
            seed = self._next_seed()
            if seed is None:
                break
            if self._check(seed):
                mss = self._grow_to_maximal(seed)
                self._blocked_down.append(mss)
                self.stats.maximal_realisable += 1
            else:
                core = self._shrink_to_core(seed)
                if core not in cores:
                    cores.append(core)
                    self.stats.cores += 1
                self._blocked_up.append(core)
        return cores


def _atom(name: str) -> str:
    """Guarantee names are not always valid ASP constants, so quote them."""
    return f'"{name}"'


def _unatom(atom: str) -> str:
    return atom.strip().strip('"')


def all_unrealisable_cores(spec, oracle: Optional[RealisabilityOracle] = None
                           ) -> List[Set[str]]:
    """
    Cores of `spec`, as sets of guarantee names - the same shape
    `run_all_unrealisable_cores` returns, so callers can be swapped over.

    The default oracle asks Spectra whether the specification restricted to a
    subset of its guarantees is realisable, keeping every assumption.
    """
    names = [row["name"] for _, row in spec._formulas_df.iterrows()
             if row["type"] == GR1FormulaType.GAR]
    if oracle is None:
        oracle = _spectra_oracle(spec)
    return AllUnrealisableCores(names, oracle).enumerate()


def _spectra_oracle(spec) -> RealisabilityOracle:
    """Realisability of `spec` with its guarantees restricted to `keep`."""
    from spec_repair.wrappers.spectra_toolbox import is_realizable

    def check(keep: Set[str]) -> bool:
        sub = spec.extract_sub_specification(
            lambda x: (x["type"] == GR1FormulaType.ASM) | (x["name"].isin(keep)))
        path = generate_temp_filename(ext=".spectra")
        write_to_file(path, sub.to_str(is_to_compile=True))
        try:
            verdict = is_realizable(path, suppress=True)
        finally:
            discard_temp_file(path)
        # `is_realizable` returns None when the CLI cannot judge the file.
        # Treating that as realisable would silently drop cores, so it is an
        # error rather than a guess.
        if verdict is None:
            raise RuntimeError(
                "Spectra could not judge realisability of a guarantee subset; "
                "the core enumeration cannot continue without a verdict.")
        return verdict

    return check
