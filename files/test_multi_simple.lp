%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Background Knowledge
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% ---*** Domain independent Axioms ***---

% Current timestep definitions
temporal_operator(current).

holds_at(current,F,P,S):-
    holds_at(F,P,S).

not_holds_at(current,F,P,S):-
    not_holds_at(F,P,S).

% Next timestep definitions
temporal_operator(next).

next_timepoint_exists(T1,S):-
    next(T2,T1,S).

% If the next time point does not exist,
% atom F holds and not holds weakly
common_weak(next,F,P,S):-
    trace(S),
    atom(F),
    timepoint(P,S),
    not next_timepoint_exists(P,S).

holds_at_weak(next,F,P,S):-
    common_weak(next,F,P,S).

not_holds_at_weak(next,F,P,S):-
    common_weak(next,F,P,S).

holds_at(next,F,P,S):-  % Weak Definition
    holds_at_weak(next,F,P,S).

not_holds_at(next,F,P,S):-  % Weak Definition
    not_holds_at_weak(next,F,P,S).

holds_at(next,F,P,S):- % Strong Definition
	next(P2,P,S),
	holds_at(current,F,P2,S).

not_holds_at(next,F,P,S):- % Strong Definition
	next(P2,P,S),
	not_holds_at(current,F,P2,S).

% Prev timestep definitions
temporal_operator(prev).

holds_at(prev,F,P,S):-
	next(P,P2,S),
	holds_at(current,F,P2,S).

not_holds_at(prev,F,P,S):-
	next(P,P2,S),
	not_holds_at(current,F,P2,S).

% Eventually timestep definitions
temporal_operator(eventually).

after(T2,T1,S):- % Base Case
    next(T2,T1,S).

after(T3,T1,S):- % Recursive Step
    next(T2,T1,S),
    after(T3,T2,S).

holds_at_weak(eventually,F,P,S):-
    trace(S),
    atom(F),
    timepoint(P,S),
    not next_timepoint_exists(P,S).

holds_at(eventually,F,P,S):- % Weak Definition
    holds_at_weak(eventually,F,P,S).

not_holds_at(eventually,F,P,S):- % Weak Definition
    holds_at_weak(eventually,F,P,S).

holds_at(eventually,F,P,S):- % Base Case (holds now)
    trace(S),
    atom(F),
    timepoint(P,S),
    holds_at(current,F,P,S).

holds_at(eventually,F,P,S):- % Strong Definition
    trace(S),
    atom(F),
    timepoint(P,S),
    after(P2,P,S),
    holds_at(current,F,P2,S).

not_holds_at(eventually,F,P,S):- % Base Case (not_holds now)
    trace(S),
    atom(F),
    timepoint(P,S),
    not_holds_at(current,F,P,S).

not_holds_at(eventually,F,P,S):- % Strong Definition
    trace(S),
    atom(F),
    timepoint(P,S),
    after(P2,P,S),
    not_holds_at(current,F,P2,S).

eq(T1,T2):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	T1 == T2.

:- 	contradiction_holds(current,F,T,S).
:- 	contradiction_holds(next,F,T,S),
    next_timepoint_exists(T,S).
:-  contradiction_holds(prev,F,T,S),
    not exist_diff_prev_timepoints(T,S).

contradiction_holds(OP,F,T,S) :-
    atom(F),
	trace(S),
	timepoint(T,S),
    not_holds_at(OP,F,T,S),
    holds_at(OP,F,T,S).

exist_diff_prev_timepoints(T,S) :-
	trace(S),
	timepoint(T,S),
	timepoint(T1,S),
	timepoint(T2,S),
	next(T,T1,S),
	next(T,T2,S),
	T1 != T2.

ev_temp_op(E) :-
    trace(S),
	timepoint(T,S),
    consequent_holds(eventually,E,T,S).

holds_non_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	antecedent_holds(E, T, S),
	consequent_holds(OP, E, T, S).

holds_vacuously(E, T, S):-
	exp(E),
	trace(S),
	timepoint(T,S),
	not antecedent_holds(E, T, S).

holds(G, T, S):-
	timepoint(T,S),
	trace(S),
	exp(G),
	holds_non_vacuously(G, T, S).

holds(G, T, S):-
	timepoint(T,S), trace(S),
	exp(G),
	holds_vacuously(G, T, S).

violation_holds(G,T,S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	not holds(G,T,S).

violated(S):-
	exp(G),
	trace(S),
	timepoint(T,S),
	violation_holds(G,T,S).

entailed(S):-
	trace(S),
	not violated(S).

exp(E):-
	guarantee(E).

exp(E):-
	assumption(E).

% ---*** Domain dependent Axioms ***---
%   G(a=true->next(c=true));

guarantee(guarantee1_1).

antecedent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	holds_at(current,a,T,S).

consequent_holds(next,guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,guarantee1_1,T,S),
	not ev_temp_op(guarantee1_1).

root_consequent_holds(OP,guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	holds_at(OP,c,T,S).

%guarantee -- guarantee2_1
%	G(b=true->next(c=false));

guarantee(guarantee2_1).

antecedent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	holds_at(current,b,T,S).

consequent_holds(next,guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,guarantee2_1,T,S),
	not ev_temp_op(guarantee2_1).

root_consequent_holds(OP,guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	temporal_operator(OP),
	not_holds_at(OP,c,T,S).

%---*** Signature  ***---

atom(a).
atom(b).
atom(c).

%---*** Violation Trace ***---

trace(trace_name_0).

timepoint(0,trace_name_0).
timepoint(1,trace_name_0).
next(1,0,trace_name_0).

not_holds_at(a,0,trace_name_0).
not_holds_at(b,0,trace_name_0).
not_holds_at(c,0,trace_name_0).
holds_at(a,1,trace_name_0).
holds_at(b,1,trace_name_0).
not_holds_at(c,1,trace_name_0).

%---*** Violation Trace ***---

counter_trace(counter_strat_0_0).

timepoint(0,counter_strat_0_0).
timepoint(1,counter_strat_0_0).
timepoint(2,counter_strat_0_0).
next(1,0,counter_strat_0_0).
next(2,1,counter_strat_0_0).

not_holds_at(a,0,counter_strat_0_0).
not_holds_at(b,0,counter_strat_0_0).
not_holds_at(c,0,counter_strat_0_0).
holds_at(a,1,counter_strat_0_0).
holds_at(b,1,counter_strat_0_0).
holds_at(c,1,counter_strat_0_0).

#show violation_holds/3.