% The worked example that used to live at the bottom of ltl2asp_ext.asp.
%   clingo ltl2asp_ext.asp ltl/example.asp

semantics(weak).
% semantics(strong).

symbol(a).
symbol(b).
symbol(c).

% Trace {} · {a}
trace_name(g1).
time(0..1,g1).
trace(1,a,g1).

% Trace {} · {b,c}
trace_name(g2).
time(0..1,g2).
trace(1,c,g2).

% Formula G(a → b v c)
root(0).
always(0,1).
implies(1,2,3).
atomic(2,a).
disjunction(3,4).
atomic(4,b).
atomic(4,c).

#show sat/1.
%#show holds/3.
