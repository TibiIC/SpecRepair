#!/usr/bin/env python3

import re
from collections import defaultdict


# -----------------------------
# PARITY GAME STRUCTURE
# -----------------------------

class PG:
    def __init__(self):
        self.owner = {}
        self.succ = {}
        self.label = {}


def parse_pg(path):
    pg = PG()

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("parity"):
                continue

            line = line.rstrip(";")

            m = re.match(r'(\d+)\s+(\d+)\s+(\d+)\s+([^\"]*)\s*"(.*)"', line)
            if not m:
                continue

            v = int(m.group(1))
            owner = int(m.group(2))
            succs = m.group(4).strip()

            pg.owner[v] = owner
            pg.succ[v] = list(map(int, succs.split(","))) if succs else []
            pg.label[v] = m.group(5)

    return pg


# -----------------------------
# STEP 1: initial partition
# -----------------------------

def initial_partition(pg):
    blocks = defaultdict(set)

    for v in pg.owner:
        key = (pg.owner[v], len(pg.succ[v]))
        blocks[key].add(v)

    return list(blocks.values())


# -----------------------------
# STEP 2: refinement step
# -----------------------------

def refine(pg, partition):
    block_index = {}

    for i, block in enumerate(partition):
        for v in block:
            block_index[v] = i

    new_blocks = defaultdict(set)

    for v in pg.owner:
        signature = (
            pg.owner[v],
            tuple(sorted(block_index[u] for u in pg.succ[v] if u in block_index))
        )
        new_blocks[signature].add(v)

    return list(new_blocks.values())


# -----------------------------
# FIXPOINT PARTITIONING
# -----------------------------

def compute_stable_partition(pg):
    partition = initial_partition(pg)

    while True:
        new_partition = refine(pg, partition)

        if len(new_partition) == len(partition):
            stable = True
            for a in new_partition:
                if a not in partition:
                    stable = False
                    break
            if stable:
                return new_partition

        partition = new_partition


# -----------------------------
# COUNTER-STRATEGY EXTRACTION
# -----------------------------

def env_region(pg):
    region = set(pg.owner.keys())

    changed = True
    while changed:
        changed = False
        for v in list(region):
            if pg.owner[v] == 1:
                if not any(u in region for u in pg.succ[v]):
                    region.remove(v)
                    changed = True
            else:
                if all(u not in region for u in pg.succ[v]):
                    region.remove(v)
                    changed = True

    return region


def extract_strategy(pg, region):
    strat = {}

    for v in region:
        if pg.owner[v] != 1:
            continue

        for u in pg.succ[v]:
            if u in region:
                strat[v] = u
                break

    return strat


# -----------------------------
# INTERPRETATION LAYER
# -----------------------------

def print_structure(partition):
    print("\n# Inferred state structure (minimal bisimulation partition)\n")

    for i, block in enumerate(partition):
        print(f"LatentBlock {i}: {sorted(block)}")


def print_strategy(pg, strat):
    print("\n# Counter-strategy\n")
    print("state S0[initial];")

    for v, u in strat.items():
        print(f"S{v} -> S{u};")


# -----------------------------
# MAIN
# -----------------------------

def main(path):
    pg = parse_pg(path)

    partition = compute_stable_partition(pg)
    print_structure(partition)

    region = env_region(pg)
    strat = extract_strategy(pg, region)

    print_strategy(pg, strat)


if __name__ == "__main__":
    import sys
    main(sys.argv[1])