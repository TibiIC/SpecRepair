from collections import defaultdict

# ----------------------------
# BUILD GRAPH FROM HOA
# ----------------------------
def build_graph(raw):
    graph = defaultdict(list)
    for s, label, t in raw:
        graph[s].append((label, t))
    return graph


# ----------------------------
# REACHABILITY (ONLY REAL PRUNING STEP)
# ----------------------------
def reachable(graph, start="0"):
    seen = set()
    stack = [start]

    while stack:
        s = stack.pop()
        if s in seen:
            continue
        seen.add(s)

        for _, t in graph.get(s, []):
            if t not in seen:
                stack.append(t)

    return seen


# ----------------------------
# PRUNE ONLY UNREACHABLE STATES
# ----------------------------
def prune(graph, alive_states):
    new_graph = defaultdict(list)

    for s, edges in graph.items():
        if s not in alive_states:
            continue

        for label, t in edges:
            if t in alive_states:
                new_graph[s].append((label, t))

    return new_graph


# ----------------------------
# SPECTRA STYLE OUTPUT
# ----------------------------
def print_cs(graph, env, sys, init="0"):
    print("# Counter-strategy (correct HOA projection)")
    print(f"ENV vars: {', '.join(env)}")
    print(f"SYS vars: {', '.join(sys)}\n")
    print(f"initial state: S{init}\n")

    for s, edges in graph.items():
        for label, t in edges:
            print(f"S{s} --[{label}]--> S{t}")


# ----------------------------
# INPUT (your HOA fragment)
# ----------------------------
raw = [
    ('0', '(!(0 | 1)) & (!2)', '1'),
    ('0', '(!(0 | 1)) & (2)', '2'),
    ('1', '(0 & 1) & (!2)', '3'),
    ('1', '(0 & 1) & (2)', '2'),
    ('2', '(t) & (!2)', '3'),
    ('2', '(t) & (2)', '4'),
    ('3', '(t) & (!2)', '3'),
    ('3', '(t) & (2)', '2'),
    ('4', '(!1) & (!2)', '3'),
    ('4', '(!1) & (2)', '4'),
]

graph = build_graph(raw)
alive = reachable(graph, "0")
graph = prune(graph, alive)

print_cs(graph, ["methane", "highwater"], ["pump"])