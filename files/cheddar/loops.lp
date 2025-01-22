% Define the nodes
node(a).
node(b).
node(c).
node(d).
node(e).
node(f).
node(g).

% Define the graph edges.
edge(a, b).
edge(b, c).
edge(c, d).
edge(d, b). % Cycle 1: b -> c -> d -> b
edge(e, f).
edge(f, g).
edge(g, e). % Cycle 2: e -> f -> g -> e

% Define paths in the graph.
path(X, Y) :- edge(X, Y).
path(X, Y) :- edge(X, Z), path(Z, Y).

% Detect cycle starts (nodes that are part of a cycle).
cycle_start(X) :- path(X, X).

% Check if two cycle starts are connected.
connected(X, Y) :- cycle_start(X), cycle_start(Y), path(X, Y), path(Y, X).

% Identify cycle starts that are not connected to any other cycle start.
isolated_cycle_start(X) :- cycle_start(X), isolated_cycle_start(Y), not connected(X, Y), X != Y.

% Randomly select one of the isolated cycle starts (optional).
{ selected_root(X) : isolated_cycle_start(X) } = 1.

% Output all isolated cycle starts and the selected root.
#show isolated_cycle_start/1.
#show selected_root/1.
#show connected/2.
