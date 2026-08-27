r"""
Minimal hitting sets, enumerated by clingo rather than by brute force.

`set_util.all_minimal_hitting_sets` walks *every subset of the universe* in
increasing size order and tests each against every input set. That is fine for
the trivial-solution path, where the sets are a handful of guarantee names, and
it is hopeless where the five-step merge needs it: minepump trace 3 reaches step
5 with 79 pooled guarantees and **7,056 unrealisable cores**, so the brute force
is enumerating `combinations(79, k)` - 24 million candidates at k=5 alone, each
tested against 7,056 sets - and never returns.

The same job as an answer-set program is small. One choice atom per element, one
constraint per set saying at least one of its elements must be picked, and
clingo's subset-minimal enumeration to keep only the minimal ones:

    { hit(e) } for each element e
    :- not hit(e1), ..., not hit(ek)      for each set {e1..ek}

Subset-minimality comes from `--enum-mode=domRec` with a domain heuristic that
prefers not to select atoms, which is the standard clingo idiom for
enumerating minimal models. That the result is the same as the brute force is
checked directly, on families small enough for both to run.

clingo is already a dependency and already runs the MARCO map, so this adds
nothing to the environment.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Sequence, Set

from spec_repair.util.asp_trace_util import run_subprocess
from spec_repair.util.file_util import (
    discard_temp_file,
    generate_temp_filename,
    write_to_file,
)

_MODEL_ATOM = re.compile(r"hit\((v\d+)\)")
# clingo reports SAT/UNSAT/OPTIMUM through its exit code rather than 0.
_VERDICT_CODES = (0, 10, 20, 30)


def _program(sets: Sequence[Set[str]], names: Sequence[str]) -> str:
    lines = [f"{{ hit({n}) }}." for n in names]
    for group in sets:
        if not group:
            # An empty set cannot be hit by anything; the family has no hitting
            # set at all, and saying so with an unsatisfiable constraint is
            # clearer than silently returning nothing.
            return "\n".join(lines + [":- #true.", "#show hit/1."]) + "\n"
        body = ", ".join(f"not hit({n})" for n in sorted(group))
        lines.append(f":- {body}.")
    lines.append("#show hit/1.")
    return "\n".join(lines) + "\n"


def minimal_hitting_sets(sets: Iterable[Iterable[str]]) -> List[Set[str]]:
    """
    Every subset-minimal hitting set of `sets`.

    Elements may be any strings; they are mapped to `v0`, `v1`, ... before
    reaching clingo, because a guarantee name is not always a valid ASP constant
    and a formula certainly is not.

    Returns `[]` when the family cannot be hit, and `[set()]` when there is
    nothing to hit - the empty set hits an empty family, and that is the right
    answer rather than an edge case to reject.
    """
    groups = [set(s) for s in sets]
    if not groups:
        return [set()]

    universe = sorted(set().union(*groups)) if any(groups) else []
    if not universe:
        return []                      # some set is empty: nothing can hit it

    ids = {element: f"v{i}" for i, element in enumerate(universe)}
    back = {v: k for k, v in ids.items()}
    encoded = [{ids[e] for e in group} for group in groups]

    path = generate_temp_filename(ext=".lp")
    write_to_file(path, _program(encoded, list(ids.values())))
    try:
        cmd = ["clingo", "--models=0", "--enum-mode=domRec",
               "--heuristic=Domain", "--dom-mod=5,16", path]
        output = run_subprocess(cmd, ok_returncodes=_VERDICT_CODES)
    finally:
        discard_temp_file(path)

    if "UNSATISFIABLE" in output:
        return []

    found: List[Set[str]] = []
    for line in output.splitlines():
        if "hit(" not in line:
            continue
        picked = {back[v] for v in _MODEL_ATOM.findall(line)}
        if picked not in found:
            found.append(picked)
    # domRec yields minimal models, but a family with a single empty-hitting
    # answer prints a blank model line that the regex simply misses; treat "no
    # atoms at all, and satisfiable" as the empty hitting set.
    if not found and "SATISFIABLE" in output:
        return [set()]
    return found
