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

%assumption -- a_always
%	G(a=true);

assumption(a_always).

antecedent_holds(a_always,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(a_always,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a_always,0,T,S),
	not ev_temp_op(a_always).

root_consequent_holds(OP,a_always,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(a,T2,S).

%guarantee -- guarantee1_1
%	G(r1=true->F(g1=true));

guarantee(guarantee1_1).

antecedent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,guarantee1_1,0,T,S).

root_antecedent_holds(OP,guarantee1_1,0,T1,S):-
    trace(S),
    timepoint(T1,S),
    timepoint(T2,S),
    temporal_operator(OP),
    timepoint_of_op(OP,T1,T2,S),
	holds_at(r1,T2,S).

ev_temp_op(guarantee1_1).
consequent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,guarantee1_1,0,T,S).

root_consequent_holds(OP,guarantee1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(g1,T2,S).

%guarantee -- guarantee2_1
%	G(r2=true->F(g2=true));

guarantee(guarantee2_1).

antecedent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,guarantee2_1,0,T,S).

root_antecedent_holds(OP,guarantee2_1,0,T1,S):-
    trace(S),
    temporal_operator(OP),
    timepoint(T1,S),
    timepoint(T2,S),
    timepoint_of_op(OP,T1,T2,S),
	holds_at(r2,T2,S).

ev_temp_op(guarantee2_1).
consequent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,guarantee2_1,0,T,S).

root_consequent_holds(OP,guarantee2_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(g2,T2,S).

%guarantee -- guarantee3_1
%	G(a=false->g1=false&g2=false);

guarantee(guarantee3_1).

antecedent_holds(guarantee3_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,guarantee3_1,0,T,S).

root_antecedent_holds(OP,guarantee3_1,0,T1,S):-
    trace(S),
    temporal_operator(OP),
    timepoint(T1,S),
    timepoint(T2,S),
    timepoint_of_op(OP,T1,T2,S),
	not_holds_at(a,T2,S).

consequent_holds(guarantee3_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,guarantee3_1,0,T,S),
	not ev_temp_op(guarantee3_1).

root_consequent_holds(OP,guarantee3_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(g1,T2,S),
	not_holds_at(g2,T2,S).

%guarantee -- guarantee4
%	G(g1=false|g2=false);

guarantee(guarantee4).

antecedent_holds(guarantee4,T,S):-
	trace(S),
	timepoint(T,S).

consequent_holds(guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,guarantee4,0,T,S),
	not ev_temp_op(guarantee4).

consequent_holds(guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(current,guarantee4,1,T,S),
	not ev_temp_op(guarantee4).

root_consequent_holds(OP,guarantee4,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(g1,T2,S).

root_consequent_holds(OP,guarantee4,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(g2,T2,S).

%---*** Signature  ***---

atom(a).
atom(g1).
atom(g2).
atom(r1).
atom(r2).


%---*** Violation Trace ***---

trace(trace_name_0).

timepoint(0,trace_name_0).

not_holds_at(a,0,trace_name_0).
not_holds_at(g1,0,trace_name_0).
not_holds_at(g2,0,trace_name_0).
not_holds_at(r1,0,trace_name_0).
not_holds_at(r2,0,trace_name_0).

#show violation_holds/3.

#show assumption/1.

#show guarantee/1.

#show entailed/1.
