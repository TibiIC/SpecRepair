% Extra traces for the formula already encoded in ltl2asp_ext.asp: G(a -> b).
% Kept in a separate file so the encoder and the data stay apart; clingo takes
% both at once:
%
%     clingo files/until_semantics/ltl2asp_ext.asp \
%            files/until_semantics/traces_g_a_implies_b.asp
%
% `trace(T,A,S)` lists only the atoms TRUE at T - anything absent is false, by
% negation as failure through the `negate` rule.
%
% Expected: sat(g3) sat(g5) sat(g6) sat(g7) sat(g8) sat(g10) sat(g12)
% and NO sat for g4, g9, g11.  (g1/g2 live in ltl2asp_ext.asp; only g2 is sat.)

% Trace {a,b}                    sat     one instant, antecedent met and honoured
trace_name(g3).
time(0..0,g3).
trace(0,a,g3). trace(0,b,g3).

% Trace {a}                      NO sat  one instant, antecedent met, consequent absent
trace_name(g4).
time(0..0,g4).
trace(0,a,g4).

% Trace {}                       sat     one instant, antecedent never fires
trace_name(g5).
time(0..0,g5).

% Trace {b}                      sat     consequent true without the antecedent
trace_name(g6).
time(0..0,g6).
trace(0,b,g6).

% Trace {} · {} · {}             sat     three instants, vacuous throughout
trace_name(g7).
time(0..2,g7).

% Trace {a,b} · {a,b} · {a,b}    sat     antecedent fires every instant, always honoured
trace_name(g8).
time(0..2,g8).
trace(0,a,g8). trace(0,b,g8).
trace(1,a,g8). trace(1,b,g8).
trace(2,a,g8). trace(2,b,g8).

% Trace {b} · {a} · {b}          NO sat  violation in the MIDDLE instant
trace_name(g9).
time(0..2,g9).
trace(0,b,g9).
trace(1,a,g9).
trace(2,b,g9).

% Trace {a,b} · {} · {a,b}       sat     antecedent fires at both ends, honoured
trace_name(g10).
time(0..2,g10).
trace(0,a,g10). trace(0,b,g10).
trace(2,a,g10). trace(2,b,g10).

% Trace {} · {} · {a}            NO sat  violation at the LAST instant only
trace_name(g11).
time(0..2,g11).
trace(2,a,g11).

% Trace {a,b} · {b} · {a,b} · {} sat     four instants, every antecedent honoured
trace_name(g12).
time(0..3,g12).
trace(0,a,g12). trace(0,b,g12).
trace(1,b,g12).
trace(2,a,g12). trace(2,b,g12).
