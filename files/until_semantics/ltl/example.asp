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

% Formula G(a → b v c)
root(0).
always(0,a_impl_disj_b_c).
implies(a_impl_disj_b_c,atom_a,disj_b_c).
atomic(atom_a,a).
disjunction(disj_b_c,disj_comp).
atomic(disj_comp,b).
atomic(disj_comp,c).

#show sat/1.
%#show holds/3.
