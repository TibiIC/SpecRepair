#!/usr/bin/env python3

import re
from collections import defaultdict


# -----------------------------
# HOA PARSER
# -----------------------------

class HOA:
    def __init__(self):
        self.ap = []
        self.ctrl = set()
        self.states = {}
        self.start = 0


def parse_hoa(path):
    hoa = HOA()

    with open(path) as f:
        lines = [l.strip() for l in f if l.strip()]

    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("Start:"):
            hoa.start = int(line.split()[1])

        elif line.startswith("AP:"):
            parts = line.split('"')
            hoa.ap = [p for p in parts if p and p not in ["AP:", " "]]

        elif line.startswith("controllable-AP:"):
            idxs = list(map(int, line.split()[1:]))
            hoa.ctrl = set(idxs)

        elif line.startswith("State:"):
            state_id = int(line.split()[1])
            i += 1

            transitions = []

            while i < len(lines) and not lines[i].startswith("State:"):
                if lines[i].startswith("--END--"):
                    break

                m = re.match(r'\[(.*)\]\s+(\d+)', lines[i])
                if m:
                    guard = m.group(1)
                    nxt = int(m.group(2))
                    transitions.append((guard, nxt))

                i += 1

            hoa.states[state_id] = transitions
            continue

        i += 1

    return hoa


# -----------------------------
# BOOLEAN EVAL (symbolic)
# -----------------------------

def simplify_guard(g):
    g = g.replace(" ", "")
    g = g.replace("!", "not ")
    g = g.replace("&", " and ")
    g = g.replace("|", " or ")
    return g


import re

AP_MAP = {
    "0": "methane",
    "1": "highwater",
    "2": "pump"
}

def render_guard(guard: str) -> str:
    """
    Correct and consistent HOA guard renderer.
    Works on full Boolean formulas, not token splits.
    """

    # preserve operators first (avoid accidental replacement issues)
    guard = guard.replace("&", " & ")
    guard = guard.replace("|", " | ")
    guard = guard.replace("!", " ! ")

    # normalize spacing
    guard = re.sub(r"\s+", " ", guard).strip()

    # replace standalone AP indices only
    def repl(match):
        token = match.group(0)
        return AP_MAP.get(token, token)

    # IMPORTANT:
    # only replace standalone numbers (0,1,2), not inside words
    guard = re.sub(r"\b0\b|\b1\b|\b2\b", repl, guard)

    return guard


# -----------------------------
# COUNTER-STRATEGY EXTRACTION
# -----------------------------

def build_counter_strategy(hoa):
    strategy = defaultdict(list)

    for s, trans in hoa.states.items():
        for guard, nxt in trans:
            strategy[s].append((guard, nxt))

    return strategy


# -----------------------------
# PRINT SPECTRA-LIKE OUTPUT
# -----------------------------

def print_strategy(hoa, strat):
    print("\n# Counter-strategy (Spectra-like reconstruction)\n")

    print(f"ENV vars: methane, highwater")
    print(f"SYS vars: pump\n")

    print(f"initial state: S{hoa.start}\n")

    for s, trans in strat.items():
        for guard, nxt in trans:
            readable = render_guard(guard)
            print(f"S{s} --[{readable}]--> S{nxt}")


# -----------------------------
# MAIN
# -----------------------------

def main(path):
    hoa = parse_hoa(path)
    strat = build_counter_strategy(hoa)
    print_strategy(hoa, strat)


if __name__ == "__main__":
    import sys

    main(sys.argv[1])