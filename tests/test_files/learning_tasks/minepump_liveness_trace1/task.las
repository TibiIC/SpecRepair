%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Mode Declaration
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#modeh(antecedent_exception(const(expression_v), const(index), var(time), var(trace))).
#modeb(2,timepoint_of_op(const(temp_op_v), var(time), var(time), var(trace)), (positive)).
#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (positive)).
#modeb(2,not_holds_at(const(usable_atom), var(time), var(trace)), (positive)).
#constant(usable_atom,flag).
#constant(usable_atom,highwater).
#constant(usable_atom,methane).
#constant(usable_atom,pump).
#constant(index,0..1).
#constant(temp_op_v,current).
#constant(temp_op_v,next).
#constant(temp_op_v,prev).
#constant(temp_op_v,eventually).
#constant(expression_v, assumption3_1).
#bias("
:- constraint.
:- head(antecedent_exception(_,_,V1,V2)), body(timepoint_of_op(_,V3,_,V4)), (V1, V2) != (V3, V4).
:- head(antecedent_exception(_,_,_,V1)), body(holds_at(_,_,V2)), V1 != V2.
:- head(antecedent_exception(_,_,_,V1)), body(not_holds_at(_,_,V2)), V1 != V2.
:- body(holds_at(E1, _, _)), body(holds_at(E2, _, _)), E1 != E2.
:- body(holds_at(_, _, _)), body(not_holds_at(_, _, _)).
:- body(not_holds_at(_, _, _)), body(holds_at(_, _, _)).
:- body(not_holds_at(E1, _, _)), body(not_holds_at(E2, _, _)), E1 != E2.
:- body(timepoint_of_op(_,_,V1,_)), body(holds_at(_,V2,_)), V1 != V2.
:- body(timepoint_of_op(_,_,V1,_)), body(not_holds_at(_,V2,_)), V1 != V2.
:- body(timepoint_of_op(_,_,_,_)), not body(not_holds_at(_,_,_)), not body(holds_at(_,_,_)).
:- body(timepoint_of_op(current,V1,V2,_)), V1 != V2.
:- body(timepoint_of_op(next,V1,V2,_)), V1 == V2.
:- body(timepoint_of_op(prev,V1,V2,_)), V1 == V2.
:- body(timepoint_of_op(eventually,V1,V2,_)), V1 == V2.
:- body(holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).
:- body(not_holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).
:- body(holds_at(A1,_,_)), body(not_holds_at(A2,_,_)), A1 == A2.
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(next,_,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(eventually,_,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(prev,_,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(next,_,_,_)), body(holds_at(flag,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(next,_,_,_)), body(not_holds_at(flag,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(next,_,_,_)), body(holds_at(pump,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(next,_,_,_)), body(not_holds_at(pump,_,_)).
").

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Background Knowledge
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% ---*** Domain independent Axioms ***---

% Time Relations Definitions
after(T2,T1,S):- % Base Case
    next(T2,T1,S).

after(T3,T1,S):- % Recursive Step
    next(T2,T1,S),
    after(T3,T2,S).

prev(T1,T2,S):-
    next(T2,T1,S).

% Temporal Operator Definitions
temporal_operator(current).
temporal_operator(next).
temporal_operator(prev).
temporal_operator(eventually).

% Timepoint of operation definitions

timepoint_of_op(current,T1,T1,S) :-
    trace(S),
    timepoint(T1,S).

timepoint_of_op(next,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    next(T2,T1,S).

timepoint_of_op(prev,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    prev(T2,T1,S).

% True at T1 iff it has a real predecessor - the start-of-trace counterpart
% to the next_timepoint_exists idea used by the weak-timepoint extension
% below, but for Prev instead of Next/Eventually. Used to give !Prev(x) its
% vacuously-true value at the very first timepoint (see asp_exception_
% formatter.py's not_prev handling and the truth table in
% docs/session-notes/2026-07-23-next-antecedent-prev-consequent-asp-gaps.md).
prev_timepoint_exists(T1,S):-
    trace(S),
    prev(T2,T1,S),
    timepoint(T2,S).

timepoint_of_op(eventually,T1,T1,S) :-
    trace(S),
    timepoint(T1,S).

timepoint_of_op(eventually,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    after(T2,T1,S).

% Weak Timepoint Definitions

weak_timepoint_atom(weak_t).

timepoint(T,S):-
    trace(S),
    weak_timepoint(T,S).

holds_at(A,T,S):-
    atom(A),
    weak_timepoint(T,S),
    trace(S).

not_holds_at(A,T,S):-
    atom(A),
    weak_timepoint(T,S),
    trace(S).

% GR(1) Rules

:- 	contradiction_holds(A,T,S).

contradiction_holds(A,T,S) :-
    atom(A),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
    not_holds_at(A,T,S),
    holds_at(A,T,S).

holds_non_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	antecedent_holds(E, T, S),
	consequent_holds(E, T, S).

holds_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	not antecedent_holds(E, T, S).

holds(G, T, S):-
	timepoint(T,S),
	not weak_timepoint(T,S),
	trace(S),
	exp(G),
	holds_non_vacuously(G, T, S).

holds(G, T, S):-
	timepoint(T,S),
	not weak_timepoint(T,S),
	trace(S),
	exp(G),
	holds_vacuously(G, T, S).

violation_holds(G,T,S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	not holds(G,T,S).

violated(S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	violation_holds(G,T,S).

entailed(S):-
	trace(S),
	not violated(S).

exp(E):-
	guarantee(E).

exp(E):-
	assumption(E).

% ---*** Domain dependent Axioms ***---

%assumption -- assumption1_1
%	G(((PREV(pump=true)&pump=true)->next(highwater=false)))

assumption(assumption1_1).

antecedent_holds(assumption1_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(prev,assumption1_1,0,T,S),
	root_antecedent_holds(current,assumption1_1,1,T,S).

root_antecedent_holds(OP,assumption1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).

root_antecedent_holds(OP,assumption1_1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).

consequent_holds(assumption1_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,assumption1_1,0,0,T,S).

root_consequent_holds(OP,assumption1_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S).

%assumption -- assumption3_1
%	G((((highwater=true&PREV(pump=false))|(highwater=true&pump=false))->next(highwater=true)))

assumption(assumption3_1).

antecedent_holds(assumption3_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,assumption3_1,0,T,S),
	root_antecedent_holds(prev,assumption3_1,1,T,S),
	not antecedent_exception(assumption3_1,0,T,S).

root_antecedent_holds(OP,assumption3_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(highwater,T2,S).

root_antecedent_holds(OP,assumption3_1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(pump,T2,S).

antecedent_holds(assumption3_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,assumption3_1,2,T,S),
	not antecedent_exception(assumption3_1,1,T,S).

root_antecedent_holds(OP,assumption3_1,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(highwater,T2,S),
	not_holds_at(pump,T2,S).

consequent_holds(assumption3_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,assumption3_1,0,0,T,S).

root_consequent_holds(OP,assumption3_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(highwater,T2,S).



%---*** Signature  ***---

atom(flag).
atom(highwater).
atom(methane).
atom(pump).


%---*** Violation Trace ***---

#pos({entailed(trace_name_1)},{},{

trace(trace_name_1).
timepoint(0,trace_name_1).
timepoint(1,trace_name_1).
timepoint(2,trace_name_1).
timepoint(3,trace_name_1).
timepoint(4,trace_name_1).
timepoint(5,trace_name_1).
timepoint(6,trace_name_1).
timepoint(7,trace_name_1).
timepoint(8,trace_name_1).
weak_timepoint(weak_t,trace_name_1).
next(1,0,trace_name_1).
next(2,1,trace_name_1).
next(3,2,trace_name_1).
next(4,3,trace_name_1).
next(5,4,trace_name_1).
next(6,5,trace_name_1).
next(7,6,trace_name_1).
next(8,7,trace_name_1).
next(weak_t,8,trace_name_1).
next(weak_t,weak_t,trace_name_1).
holds_at(flag,0,trace_name_1).
not_holds_at(highwater,0,trace_name_1).
not_holds_at(methane,0,trace_name_1).
not_holds_at(pump,0,trace_name_1).
holds_at(flag,1,trace_name_1).
holds_at(highwater,1,trace_name_1).
holds_at(methane,1,trace_name_1).
holds_at(pump,1,trace_name_1).
holds_at(flag,2,trace_name_1).
holds_at(highwater,2,trace_name_1).
not_holds_at(methane,2,trace_name_1).
not_holds_at(pump,2,trace_name_1).
holds_at(flag,3,trace_name_1).
holds_at(highwater,3,trace_name_1).
not_holds_at(methane,3,trace_name_1).
holds_at(pump,3,trace_name_1).
holds_at(flag,4,trace_name_1).
holds_at(highwater,4,trace_name_1).
not_holds_at(methane,4,trace_name_1).
holds_at(pump,4,trace_name_1).
not_holds_at(flag,5,trace_name_1).
not_holds_at(highwater,5,trace_name_1).
holds_at(methane,5,trace_name_1).
holds_at(pump,5,trace_name_1).
not_holds_at(flag,6,trace_name_1).
not_holds_at(highwater,6,trace_name_1).
holds_at(methane,6,trace_name_1).
not_holds_at(pump,6,trace_name_1).
holds_at(flag,7,trace_name_1).
holds_at(highwater,7,trace_name_1).
not_holds_at(methane,7,trace_name_1).
not_holds_at(pump,7,trace_name_1).
holds_at(flag,8,trace_name_1).
not_holds_at(highwater,8,trace_name_1).
holds_at(methane,8,trace_name_1).
not_holds_at(pump,8,trace_name_1).
}).
