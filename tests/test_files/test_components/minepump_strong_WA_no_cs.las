%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Mode Declaration
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#modeh(antecedent_exception(const(expression_v), const(index), var(time), var(trace))).
#modeb(2,timepoint_of_op(const(temp_op_v), var(time), var(time), var(trace)), (positive)).
#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (positive)).
#modeb(2,not_holds_at(const(usable_atom), var(time), var(trace)), (positive)).
#modeh(ev_temp_op(const(expression_v))).
#constant(usable_atom,highwater).
#constant(usable_atom,methane).
#constant(usable_atom,pump).
#constant(index,0..1).
#constant(temp_op_v,current).
#constant(temp_op_v,next).
#constant(temp_op_v,prev).
#constant(temp_op_v,eventually).
#constant(expression_v, assumption2_1).
#bias("
:- constraint.
:- head(antecedent_exception(_,_,V1,V2)), body(timepoint_of_op(_,V3,_,V4)), (V1, V2) != (V3, V4).
:- head(antecedent_exception(_,_,_,V1)), body(holds_at(_,_,V2)), V1 != V2.
:- head(antecedent_exception(_,_,_,V1)), body(not_holds_at(_,_,V2)), V1 != V2.
:- body(timepoint_of_op(_,_,V1,_)), body(holds_at(_,V2,_)), V1 != V2.
:- body(timepoint_of_op(_,_,V1,_)), body(not_holds_at(_,V2,_)), V1 != V2.
:- body(timepoint_of_op(_,_,_,_)), not body(not_holds_at(_,_,_)), not body(holds_at(_,_,_)).
:- body(timepoint_of_op(current,V1,V2,_)), V1 != V2.
:- body(timepoint_of_op(next,V1,V2,_)), V1 == V2.
:- body(timepoint_of_op(prev,V1,V2,_)), V1 == V2.
:- body(timepoint_of_op(eventually,V1,V2,_)), V1 == V2.
:- body(holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).
:- body(not_holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(next,_,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(prev,_,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(eventually,_,_,_)).
:- head(ev_temp_op(_)), body(timepoint_of_op(_,_,_,_)).
:- head(ev_temp_op(_)), body(holds_at(_,_,_)).
:- head(ev_temp_op(_)), body(not_holds_at(_,_,_)).
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
    timepoint(T1,S),
    not weak_timepoint(T1,S).

timepoint_of_op(next,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S),
    timepoint(T2,S),
    next(T2,T1,S).

timepoint_of_op(prev,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    not weak_timepoint(T1,S),
    not weak_timepoint(T2,S),
    prev(T2,T1,S).

timepoint_of_op(eventually,T1,T1,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S).

timepoint_of_op(eventually,T1,T2,S) :-
    trace(S),
    timepoint(T1,S),
    not weak_timepoint(T1,S),
    timepoint(T2,S),
    after(T2,T1,S).

% Weak Timepoint Definitions

weak_timepoint_atom(weak_t).

next_timepoint_exists(T1,S):-
    timepoint(T1,S),
    timepoint(T2,S),
    not weak_timepoint(T2,S),
    next(T2,T1,S).

weak_timepoint(X,S):-
    weak_timepoint_atom(X),
    timepoint(T,S),
    not next_timepoint_exists(T,S).

timepoint(T,S):-
    trace(S),
    weak_timepoint(T,S).

next(X,T,S):-
    weak_timepoint(X,S),
    timepoint(T,S),
    not weak_timepoint(T,S),
    not next_timepoint_exists(T,S).

holds_at(A,T,S):-
    atom(A),
    weak_timepoint(T,S),
    trace(S).

not_holds_at(A,T,S):-
    atom(A),
    weak_timepoint(T,S),
    trace(S).

root_consequent_holds(OP,E,T,S):-
    root_consequent_holds(OP,E,I,T,S).

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

%assumption -- initial_assumption
%	ini(highwater=false&methane=false);

assumption(initial_assumption).

antecedent_holds(initial_assumption,0,S):-
	trace(S),
	timepoint(0,S).

consequent_holds(initial_assumption,0,S):-
	trace(S),
	timepoint(0,S),
	root_consequent_holds(current,initial_assumption,0,0,S).

root_consequent_holds(OP,initial_assumption,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S),
	not_holds_at(methane,T2,S).

%assumption -- assumption1_1
%	G(PREV(pump=true)&pump=true->next(highwater=false));

assumption(assumption1_1).

antecedent_holds(assumption1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(prev,assumption1_1,0,T,S),
	root_antecedent_holds(current,assumption1_1,1,T,S).

root_antecedent_holds(OP,assumption1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).

root_antecedent_holds(OP,assumption1_1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).

consequent_holds(assumption1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,assumption1_1,0,T,S).

root_consequent_holds(OP,assumption1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S).

%assumption -- assumption2_1
%	G(highwater=false|methane=false);

assumption(assumption2_1).

antecedent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not antecedent_exception(assumption2_1,0,T,S).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,assumption2_1,0,T,S),
	not ev_temp_op(assumption2_1).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,assumption2_1,0,T,S),
	ev_temp_op(assumption2_1).

root_consequent_holds(OP,assumption2_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,assumption2_1,1,T,S),
	not ev_temp_op(assumption2_1).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,assumption2_1,1,T,S),
	ev_temp_op(assumption2_1).

root_consequent_holds(OP,assumption2_1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(methane,T2,S).

%---*** Signature  ***---

atom(highwater).
atom(methane).
atom(pump).


%---*** Violation Trace ***---

#pos({entailed(trace_name_0)},{},{

trace(trace_name_0).
timepoint(0,trace_name_0).
timepoint(1,trace_name_0).
next(1,0,trace_name_0).
not_holds_at(highwater,0,trace_name_0).
not_holds_at(methane,0,trace_name_0).
not_holds_at(pump,0,trace_name_0).
holds_at(highwater,1,trace_name_0).
holds_at(methane,1,trace_name_0).
not_holds_at(pump,1,trace_name_0).
}).
