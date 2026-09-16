#!/usr/bin/env python3
"""Enumerate what a .las task's mode declaration can actually build, without ILASP.

ILASP's search is the expensive way to find out that a mode declaration admits
nonsense (or admits nothing at all) -- an ill-formed bias gives an effectively
unbounded space, so the solver does not fail, it just never returns. This does
the same reconnaissance with plain clingo in a second: it reads the `#modeh` and
`#constant` declarations, turns them into choice rules over the declared node
pool, runs them against the task's own background knowledge, and prints every
well-formed candidate the constraints leave standing.

    conda activate arm_env
    python scripts/inspect_hypothesis_space.py files/until_semantics/antecedent_exception.las
    python scripts/inspect_hypothesis_space.py files/until_semantics/*.las --max-literals 4
    python scripts/inspect_hypothesis_space.py files/until_semantics/consequent_exception.las --count

Read the output for two failures in particular:

  * a candidate you would never want to learn  -- the bias is too loose;
  * a repair you *do* want that never appears  -- the bias is too tight, and no
    amount of solver time will produce it. A pool one node too small is the
    quiet version of this: the operator sits in `#modeh` looking available while
    every tree that uses it needs a node that was never declared.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict

MODEH = re.compile(r'^#modeh\(\s*(\w+)\(\s*const\((\w+)\)\s*,\s*const\((\w+)\)\s*\)\s*\)\s*\.')
CONST = re.compile(r'^#constant\(\s*(\w+)\s*,\s*([\w\d_]+)\s*\)\s*\.')
ATOM = re.compile(r'(\w+)\(([\w\d_]+),([\w\d_]+)\)')


def parse(path):
    """Pull the mode declarations, the constant pools and the background out of a .las."""
    modeh, pools, bk = [], defaultdict(list), []
    in_bk = False
    for line in open(path):
        s = line.strip()
        if s.startswith("%"):
            # section banners are comments; the background runs to the examples
            if "Background Knowledge" in s:
                in_bk = True
            elif "Examples" in s:
                in_bk = False
            continue
        if m := MODEH.match(s):
            modeh.append(m.groups())
        elif m := CONST.match(s):
            pools[m.group(1)].append(m.group(2))
        elif in_bk and s and not s.startswith("#"):
            bk.append(s)
    return modeh, pools, bk


def program(modeh, pools, bk, max_literals):
    """The background knowledge, plus a choice over every ground head the modes allow."""
    out = list(bk)
    out.append("")
    for ty, vals in pools.items():
        for v in vals:
            out.append(f"ty_{ty}({v}).")
    for pred, t1, t2 in modeh:
        out.append(f"{{ {pred}(A,B) : ty_{t1}(A), ty_{t2}(B) }}.")
    # A hypothesis atom is one that mentions a spare node -- that is what the
    # learner gets to choose. The formula already in the background does not count.
    for pred, _, _ in modeh:
        out.append(f"hyp({pred}(A,B)) :- {pred}(A,B), spare(A).")
        out.append(f"hyp({pred}(A,B)) :- {pred}(A,B), spare(B).")
    out.append(f":- #count{{ X : hyp(X) }} > {max_literals}.")
    out.append("#show hyp/1.")
    return "\n".join(out) + "\n"


def render(atoms, roots):
    """Print a candidate as a formula tree rather than a bag of facts."""
    kids = defaultdict(list)
    kind, label = {}, {}
    for a in atoms:
        m = ATOM.match(a)
        if not m:
            continue
        pred, n, c = m.groups()
        if pred == "atomic":
            kind[n] = "atomic"
            label[n] = label.get(n, "") + ("|" if n in label else "") + c
        else:
            kind.setdefault(n, pred)
            kids[n].append(c)

    def show(n, depth=0):
        if depth > 8:
            return ["  " * depth + "..."]
        if kind.get(n) == "atomic":
            return ["  " * depth + f"{label[n]}  <{n}>"]
        lines = ["  " * depth + f"{kind.get(n, n)}  <{n}>"]
        for c in kids.get(n, []):
            lines += show(c, depth + 1)
        return lines

    # only render from nodes nothing points at, or each subtree prints twice
    child = {c for cs in kids.values() for c in cs}
    seen = list(dict.fromkeys(r for r in roots + sorted(kids)
                              if r in kids and r not in child))
    return "\n".join(l for r in seen for l in show(r)) or "    (empty)"


def inspect(path, max_literals, models, count_only):
    modeh, pools, bk = parse(path)
    spares = pools.get("spare", [])
    roots = [v for ty, vs in pools.items() if ty != "spare" and ty != "atom" for v in vs]

    print(f"\n=== {path} ===")
    print(f"  heads    : {', '.join(sorted({p for p, _, _ in modeh}))}")
    print(f"  spares   : {', '.join(spares) or '(none)'}")
    print(f"  atoms    : {', '.join(pools.get('atom', [])) or '(none)'}")
    print(f"  attaches : {', '.join(roots) or '(none)'}")

    prog = program(modeh, pools, bk, max_literals)
    n = "0" if count_only else str(models)
    r = subprocess.run(["clingo", "-", n, "--outf=0"], input=prog,
                       capture_output=True, text=True)
    if "UNSATISFIABLE" in r.stdout:
        print("\n  the space is EMPTY -- the constraints admit no candidate at all")
        return 1
    if r.returncode not in (10, 30):
        print(f"\n  clingo failed:\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
        return 1

    found = [l.strip() for l in r.stdout.splitlines() if l.startswith("hyp(")]
    total = re.search(r"Models\s*:\s*(\d+)(\+?)", r.stdout)
    if count_only:
        more = "+" if total and total.group(2) else ""
        print(f"\n  {total.group(1) if total else '?'}{more} well-formed candidates "
              f"at up to {max_literals} literals")
        return 0

    print(f"\n  showing {len(found)} of "
          f"{total.group(1) + ('+' if total.group(2) else '') if total else '?'} "
          f"candidates, up to {max_literals} literals\n")
    for i, model in enumerate(found, 1):
        atoms = re.findall(r'hyp\((\w+\([\w\d_]+,[\w\d_]+\))\)', model)
        print(f"  [{i}]")
        print("\n".join("    " + l for l in render(atoms, roots).splitlines()))
        print()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("las", nargs="+", help="the .las task(s) to inspect")
    ap.add_argument("--max-literals", type=int, default=3,
                    help="largest candidate to consider (default 3)")
    ap.add_argument("--models", type=int, default=15,
                    help="how many candidates to print (default 15)")
    ap.add_argument("--count", action="store_true",
                    help="only count the space, do not print it")
    a = ap.parse_args(argv)
    return max(inspect(p, a.max_literals, a.models, a.count) for p in a.las)


if __name__ == "__main__":
    raise SystemExit(main())
