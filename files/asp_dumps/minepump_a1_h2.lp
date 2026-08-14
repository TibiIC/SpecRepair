% minepump (case_study_2)
% environment variables : highwater, methane
% system variables      : pump
% target                : assumption1_1
% timepoints            : 1..2 (first new one is 1)
% read the environment values at timepoint 1

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

%assumption -- initial_assumption
%	(highwater=false&methane=false)

assumption(initial_assumption).

antecedent_holds(initial_assumption,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(initial_assumption,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,initial_assumption,0,0,0,S).

root_consequent_holds(OP,initial_assumption,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S),
	not_holds_at(methane,T2,S).

%guarantee -- initial_guarantee
%	pump=false

guarantee(initial_guarantee).

antecedent_holds(initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,initial_guarantee,0,0,0,S).

root_consequent_holds(OP,initial_guarantee,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(pump,T2,S).

%guarantee -- guarantee1_1
%	G((highwater=true->next(pump=true)))

guarantee(guarantee1_1).

antecedent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,guarantee1_1,0,T,S).

root_antecedent_holds(OP,guarantee1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(highwater,T2,S).

consequent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,guarantee1_1,0,0,T,S).

root_consequent_holds(OP,guarantee1_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).

%guarantee -- guarantee2_1
%	G((methane=true->next(pump=false)))

guarantee(guarantee2_1).

antecedent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,guarantee2_1,0,T,S).

root_antecedent_holds(OP,guarantee2_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(methane,T2,S).

consequent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,guarantee2_1,0,0,T,S).

root_consequent_holds(OP,guarantee2_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(pump,T2,S).

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

%assumption -- assumption2_1
%	G((highwater=false|methane=false))

assumption(assumption2_1).

antecedent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,assumption2_1,0,0,T,S).

root_consequent_holds(OP,assumption2_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(highwater,T2,S).

consequent_holds(assumption2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,assumption2_1,0,1,T,S).

root_consequent_holds(OP,assumption2_1,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(methane,T2,S).

%---*** Signature  ***---

atom(highwater).
atom(methane).
atom(pump).


trace(trace_name_0).

timepoint(0,trace_name_0).
timepoint(1,trace_name_0).
timepoint(2,trace_name_0).
weak_timepoint(weak_t,trace_name_0).
next(1,0,trace_name_0).
next(2,1,trace_name_0).
next(weak_t,2,trace_name_0).
next(weak_t,weak_t,trace_name_0).


%---*** Environment step construction ***---

1 { holds_at(A,T,S) ; not_holds_at(A,T,S) } 1 :-
    atom(A),
    trace(S),
    timepoint(T,S),
    not weak_timepoint(T,S).

#show holds_at/3.
#show not_holds_at/3.
not_holds_at(highwater,0,trace_name_0).
not_holds_at(methane,0,trace_name_0).
not_holds_at(pump,0,trace_name_0).

to_violate(assumption1_1).

is_guarantee(guarantee1_1).
is_guarantee(guarantee2_1).
is_guarantee(initial_guarantee).

violated_exp(E,S) :- violation_holds(E,T,S), trace(S), timepoint(T,S).

% The system's moves in a plan are guesses - the controller has not made them
% yet - so they have to be guesses the controller could actually make. A
% synthesised controller satisfies its guarantees by construction, so a plan
% that relies on one breaking is a plan against a system that does not exist.
% Without this the solver was free to invent a cooperative system, propose the
% input that suited it, and be contradicted the moment the real controller
% answered - which is why deepening the horizon alone changed nothing.
:- violation_holds(E,T,S), is_guarantee(E).

% The target must break. Nothing says it has to break *alone*: requiring that
% made the target unreachable wherever assumptions overlap - a step that breaks
% a mutual-exclusion assumption may be the only way to reach the state where
% the intended one can break at all. The trace records everything it violated,
% so a repair still knows what it is being asked for.
:- to_violate(E), trace(S), not violated_exp(E,S).
