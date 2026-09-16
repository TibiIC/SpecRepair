% What it means for a trace to satisfy the formula.
%
% `sat/1` is silence-on-failure: a trace absent from the answer set is not
% satisfied. `unsat/1` is derived alongside it so that a trace which was never
% defined - a typo in trace_name, say - is distinguishable from one that is
% genuinely violated, instead of both looking the same.

sat(S)   :- trace_name(S), root(X), holds(0,X,S).
unsat(S) :- trace_name(S), not sat(S).
