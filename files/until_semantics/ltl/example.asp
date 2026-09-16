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

% Formula G(a ^ c → b)
root(0).
always(0,f_implication).
implies(f_implication,f_antecedent,f_consequent).

disjunction(f_antecedent,f_antecedent_conjunct_0).
conjunction(f_antecedent_conjunct_0,f_antecedent_conjunct_formula_0).
atomic(f_antecedent_conjunct_formula_0,a).

% conjunction(f_antecedent_conjunct_0,f_antecedent_conjunct_formula_1).
% atomic(f_antecedent_conjunct_formula_1,c).

disjunction(f_consequent, f_consequent_conjunct_0).
conjunction(f_consequent_conjunct_0, f_consequent_atom_b).
atomic(f_consequent_atom_b, b).

% disjunction(f_consequent, f_consequent_conjunct_1).
% conjunction(f_consequent_conjunct_1, f_consequent_atom_c).
% atomic(f_consequent_atom_c, c).

#show sat/1.
%#show holds/3.
