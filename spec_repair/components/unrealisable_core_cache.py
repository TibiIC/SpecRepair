"""
Memoisation for Spectra's unrealisable-core search.

The search is the most expensive call in the system: `exploreAllCores` is
exponential in the number of expressions, and was measured on genbuf at over
thirteen hours inside `Checker$Memoize.seek` without returning. The same
specification reaches it repeatedly - `filter_counter_traces` and
`new_spec_encoder` both ask for the cores of the node's specification, and
trivial solution generation asks again for its own.

Kept as a component rather than a module-level dictionary so that a caller owns
it, can reset it, and can substitute a disabled one, instead of the wrapper
carrying hidden state that survives between runs and between tests.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

Cores = List[Set[str]]


@dataclass(frozen=True)
class CacheStats:
    """What the cache did, for deciding whether it earns its place."""
    calls: int = 0
    hits: int = 0
    misses: int = 0

    @property
    def hit_rate(self) -> float:
        return self.hits / self.calls if self.calls else 0.0

    def __str__(self) -> str:
        return (f"{self.calls} call(s), {self.hits} hit(s), {self.misses} miss(es), "
                f"{self.hit_rate:.0%} hit rate")


@dataclass
class UnrealisableCoreCache:
    """
    Cores keyed on the exact specification text, and on the BDD package.

    **Syntactic identity, deliberately.** Spectra reports cores as sets of
    expression *names*, so two semantically equivalent specifications are not
    interchangeable here: they can name their formulas differently, or be
    covered by different subsets of formulas, and a semantic hit would hand back
    names the caller cannot map onto its own specification. Syntactic identity
    also needs no comparison - `to_str(is_to_compile=True)` is already canonical,
    so the hash of that text *is* the identity and a lookup is a dict hit.

    **The BDD package is part of the key** because it is part of the
    computation: CUDD and JTLV can report different cores, and one must never be
    served for the other.

    Sound because the answer is a function of the key: same text, same package,
    same cores.
    """
    enabled: bool = True
    _entries: Dict[str, Cores] = field(default_factory=dict, repr=False)
    _calls: int = field(default=0, repr=False)
    _hits: int = field(default=0, repr=False)

    @staticmethod
    def key_for(spectra_str: str, bdd_package: str) -> str:
        digest = hashlib.sha256(spectra_str.encode("utf-8")).hexdigest()
        return f"{bdd_package}:{digest}"

    def get(self, key: str) -> Optional[Cores]:
        """The cores for `key`, or None. Copied out, so a caller cannot mutate the entry."""
        entry = self._entries.get(key)
        return None if entry is None else [set(core) for core in entry]

    def put(self, key: str, cores: Cores) -> None:
        """Record `cores` under `key`. Copied in, for the same reason."""
        if self.enabled:
            self._entries[key] = [set(core) for core in cores]

    def lookup_or_compute(self, spectra_str: str, bdd_package: str,
                          compute: Callable[[], Cores]) -> Cores:
        """
        The cores for this specification, computing them only on a miss.

        `compute` is passed in rather than imported so this component knows
        nothing about Spectra, the JVM, or temporary files - which is what makes
        it testable without any of them.
        """
        if not self.enabled:
            return compute()

        self._calls += 1
        key = self.key_for(spectra_str, bdd_package)
        hit = self.get(key)
        if hit is not None:
            self._hits += 1
            return hit

        cores = compute()
        self.put(key, cores)
        return cores

    def reset(self) -> None:
        """Forget every entry and every statistic."""
        self._entries.clear()
        self._calls = 0
        self._hits = 0

    @property
    def stats(self) -> CacheStats:
        return CacheStats(calls=self._calls, hits=self._hits,
                          misses=self._calls - self._hits)

    def __len__(self) -> int:
        return len(self._entries)
