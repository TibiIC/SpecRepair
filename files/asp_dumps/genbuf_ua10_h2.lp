% genbuf (case_study_2)
% environment variables : eMPTY, fULL, rtoB_ACK0, rtoB_ACK1, stoB_REQ0, stoB_REQ1, stoB_REQ2, stoB_REQ3, stoB_REQ4
% system variables      : btoR_REQ0, btoR_REQ1, btoS_ACK0, btoS_ACK1, btoS_ACK2, btoS_ACK3, btoS_ACK4, dEQ, eNQ, sLC0, sLC1, sLC2, stateG12, stateG7_0, stateG7_1
% target                : unnamed_assumption_10
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

%assumption -- unnamed_assumption_1
%	stoB_REQ0=false

assumption(unnamed_assumption_1).

antecedent_holds(unnamed_assumption_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_1,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ0,T2,S).

%assumption -- unnamed_assumption_2
%	stoB_REQ1=false

assumption(unnamed_assumption_2).

antecedent_holds(unnamed_assumption_2,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_2,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_2,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_2,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ1,T2,S).

%assumption -- unnamed_assumption_3
%	stoB_REQ2=false

assumption(unnamed_assumption_3).

antecedent_holds(unnamed_assumption_3,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_3,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_3,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_3,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ2,T2,S).

%assumption -- unnamed_assumption_4
%	stoB_REQ3=false

assumption(unnamed_assumption_4).

antecedent_holds(unnamed_assumption_4,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_4,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_4,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_4,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ3,T2,S).

%assumption -- unnamed_assumption_5
%	stoB_REQ4=false

assumption(unnamed_assumption_5).

antecedent_holds(unnamed_assumption_5,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_5,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_5,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_5,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ4,T2,S).

%assumption -- unnamed_assumption_6
%	rtoB_ACK0=false

assumption(unnamed_assumption_6).

antecedent_holds(unnamed_assumption_6,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_6,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_6,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_6,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK0,T2,S).

%assumption -- unnamed_assumption_7
%	rtoB_ACK1=false

assumption(unnamed_assumption_7).

antecedent_holds(unnamed_assumption_7,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_7,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_7,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_7,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK1,T2,S).

%assumption -- unnamed_assumption_8
%	fULL=false

assumption(unnamed_assumption_8).

antecedent_holds(unnamed_assumption_8,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_8,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_8,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_8,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(fULL,T2,S).

%assumption -- unnamed_assumption_9
%	eMPTY=true

assumption(unnamed_assumption_9).

antecedent_holds(unnamed_assumption_9,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_assumption_9,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_assumption_9,0,0,0,S).

root_consequent_holds(OP,unnamed_assumption_9,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eMPTY,T2,S).

%assumption -- unnamed_assumption_10
%	G(((stoB_REQ0=true&btoS_ACK0=false)->next(stoB_REQ0=true)))

assumption(unnamed_assumption_10).

antecedent_holds(unnamed_assumption_10,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_10,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_10,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ0,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_assumption_10,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_10,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_10,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ0,T2,S).

%assumption -- unnamed_assumption_11
%	G((btoS_ACK0=true->next(stoB_REQ0=false)))

assumption(unnamed_assumption_11).

antecedent_holds(unnamed_assumption_11,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_11,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_11,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_assumption_11,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_11,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_11,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ0,T2,S).

%assumption -- unnamed_assumption_12
%	G(((stoB_REQ1=true&btoS_ACK1=false)->next(stoB_REQ1=true)))

assumption(unnamed_assumption_12).

antecedent_holds(unnamed_assumption_12,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_12,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_12,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

consequent_holds(unnamed_assumption_12,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_12,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_12,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ1,T2,S).

%assumption -- unnamed_assumption_13
%	G((btoS_ACK1=true->next(stoB_REQ1=false)))

assumption(unnamed_assumption_13).

antecedent_holds(unnamed_assumption_13,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_13,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_13,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S).

consequent_holds(unnamed_assumption_13,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_13,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_13,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ1,T2,S).

%assumption -- unnamed_assumption_14
%	G(((stoB_REQ2=true&btoS_ACK2=false)->next(stoB_REQ2=true)))

assumption(unnamed_assumption_14).

antecedent_holds(unnamed_assumption_14,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_14,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_14,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ2,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

consequent_holds(unnamed_assumption_14,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_14,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_14,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ2,T2,S).

%assumption -- unnamed_assumption_15
%	G((btoS_ACK2=true->next(stoB_REQ2=false)))

assumption(unnamed_assumption_15).

antecedent_holds(unnamed_assumption_15,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_15,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_15,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S).

consequent_holds(unnamed_assumption_15,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_15,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_15,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ2,T2,S).

%assumption -- unnamed_assumption_16
%	G(((stoB_REQ3=true&btoS_ACK3=false)->next(stoB_REQ3=true)))

assumption(unnamed_assumption_16).

antecedent_holds(unnamed_assumption_16,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_16,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_16,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ3,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

consequent_holds(unnamed_assumption_16,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_16,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_16,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ3,T2,S).

%assumption -- unnamed_assumption_17
%	G((btoS_ACK3=true->next(stoB_REQ3=false)))

assumption(unnamed_assumption_17).

antecedent_holds(unnamed_assumption_17,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_17,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_17,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S).

consequent_holds(unnamed_assumption_17,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_17,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_17,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ3,T2,S).

%assumption -- unnamed_assumption_18
%	G(((stoB_REQ4=true&btoS_ACK4=false)->next(stoB_REQ4=true)))

assumption(unnamed_assumption_18).

antecedent_holds(unnamed_assumption_18,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_18,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_18,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ4,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

consequent_holds(unnamed_assumption_18,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_18,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_18,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ4,T2,S).

%assumption -- unnamed_assumption_19
%	G((btoS_ACK4=true->next(stoB_REQ4=false)))

assumption(unnamed_assumption_19).

antecedent_holds(unnamed_assumption_19,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_19,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_19,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S).

consequent_holds(unnamed_assumption_19,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_19,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_19,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ4,T2,S).

%assumption -- unnamed_assumption_20
%	G((btoR_REQ0=false->next(rtoB_ACK0=false)))

assumption(unnamed_assumption_20).

antecedent_holds(unnamed_assumption_20,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_20,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_20,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ0,T2,S).

consequent_holds(unnamed_assumption_20,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_20,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_20,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK0,T2,S).

%assumption -- unnamed_assumption_21
%	G(((btoR_REQ0=true&rtoB_ACK0=true)->next(rtoB_ACK0=true)))

assumption(unnamed_assumption_21).

antecedent_holds(unnamed_assumption_21,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_21,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_21,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ0,T2,S),
	holds_at(rtoB_ACK0,T2,S).

consequent_holds(unnamed_assumption_21,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_21,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_21,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK0,T2,S).

%assumption -- unnamed_assumption_22
%	G((btoR_REQ1=false->next(rtoB_ACK1=false)))

assumption(unnamed_assumption_22).

antecedent_holds(unnamed_assumption_22,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_22,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_22,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_assumption_22,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_22,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_22,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK1,T2,S).

%assumption -- unnamed_assumption_23
%	G(((btoR_REQ1=true&rtoB_ACK1=true)->next(rtoB_ACK1=true)))

assumption(unnamed_assumption_23).

antecedent_holds(unnamed_assumption_23,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_23,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_23,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ1,T2,S),
	holds_at(rtoB_ACK1,T2,S).

consequent_holds(unnamed_assumption_23,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_23,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_23,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK1,T2,S).

%assumption -- unnamed_assumption_24
%	G(((eNQ=true&dEQ=false)->next(eMPTY=false)))

assumption(unnamed_assumption_24).

antecedent_holds(unnamed_assumption_24,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_24,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_24,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eNQ,T2,S),
	not_holds_at(dEQ,T2,S).

consequent_holds(unnamed_assumption_24,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_24,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_24,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(eMPTY,T2,S).

%assumption -- unnamed_assumption_25
%	G(((dEQ=true&eNQ=false)->next(fULL=false)))

assumption(unnamed_assumption_25).

antecedent_holds(unnamed_assumption_25,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_25,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_25,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(dEQ,T2,S),
	not_holds_at(eNQ,T2,S).

consequent_holds(unnamed_assumption_25,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_assumption_25,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_25,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(fULL,T2,S).

%assumption -- unnamed_assumption_26
%	G((((eNQ=true&dEQ=true)|(!(eNQ=true)&!(dEQ=true)))->(((((fULL=true&eMPTY=true)&next((fULL=true&eMPTY=true)))|((fULL=true&!(eMPTY=true))&next((fULL=true&!(eMPTY=true)))))|((!(fULL=true)&eMPTY=true)&next((!(fULL=true)&eMPTY=true))))|((!(fULL=true)&!(eMPTY=true))&next((!(fULL=true)&!(eMPTY=true)))))))

assumption(unnamed_assumption_26).

antecedent_holds(unnamed_assumption_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_26,0,T,S).

root_antecedent_holds(OP,unnamed_assumption_26,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eNQ,T2,S),
	holds_at(dEQ,T2,S).

antecedent_holds(unnamed_assumption_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_assumption_26,1,T,S).

root_antecedent_holds(OP,unnamed_assumption_26,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(eNQ,T2,S),
	not_holds_at(dEQ,T2,S).

consequent_holds(unnamed_assumption_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_assumption_26,0,0,T,S),
	root_consequent_holds(next,unnamed_assumption_26,0,1,T,S).

root_consequent_holds(OP,unnamed_assumption_26,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(fULL,T2,S),
	holds_at(eMPTY,T2,S).

root_consequent_holds(OP,unnamed_assumption_26,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(fULL,T2,S),
	holds_at(eMPTY,T2,S).

consequent_holds(unnamed_assumption_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_assumption_26,0,2,T,S),
	root_consequent_holds(next,unnamed_assumption_26,0,3,T,S).

root_consequent_holds(OP,unnamed_assumption_26,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(fULL,T2,S),
	not_holds_at(eMPTY,T2,S).

root_consequent_holds(OP,unnamed_assumption_26,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(fULL,T2,S),
	not_holds_at(eMPTY,T2,S).

consequent_holds(unnamed_assumption_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_assumption_26,0,4,T,S),
	root_consequent_holds(next,unnamed_assumption_26,0,5,T,S).

root_consequent_holds(OP,unnamed_assumption_26,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(fULL,T2,S),
	holds_at(eMPTY,T2,S).

root_consequent_holds(OP,unnamed_assumption_26,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(fULL,T2,S),
	holds_at(eMPTY,T2,S).

consequent_holds(unnamed_assumption_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_assumption_26,0,6,T,S),
	root_consequent_holds(next,unnamed_assumption_26,0,7,T,S).

root_consequent_holds(OP,unnamed_assumption_26,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(fULL,T2,S),
	not_holds_at(eMPTY,T2,S).

root_consequent_holds(OP,unnamed_assumption_26,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(fULL,T2,S),
	not_holds_at(eMPTY,T2,S).

%assumption -- unnamed_assumption_27
%	GF(((btoR_REQ0=true&rtoB_ACK0=true)|(!(btoR_REQ0=true)&!(rtoB_ACK0=true))))

assumption(unnamed_assumption_27).

antecedent_holds(unnamed_assumption_27,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_assumption_27,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_assumption_27,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_27,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_assumption_27,1,0,T2,S).

root_consequent_holds(OP,unnamed_assumption_27,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ0,T2,S),
	holds_at(rtoB_ACK0,T2,S).

root_consequent_holds(OP,unnamed_assumption_27,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_assumption_27,1,1,T2,S).

root_consequent_holds(OP,unnamed_assumption_27,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ0,T2,S),
	not_holds_at(rtoB_ACK0,T2,S).

%assumption -- unnamed_assumption_28
%	GF(((btoR_REQ1=true&rtoB_ACK1=true)|(!(btoR_REQ1=true)&!(rtoB_ACK1=true))))

assumption(unnamed_assumption_28).

antecedent_holds(unnamed_assumption_28,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_assumption_28,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_assumption_28,0,0,T,S).

root_consequent_holds(OP,unnamed_assumption_28,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_assumption_28,1,0,T2,S).

root_consequent_holds(OP,unnamed_assumption_28,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ1,T2,S),
	holds_at(rtoB_ACK1,T2,S).

root_consequent_holds(OP,unnamed_assumption_28,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_assumption_28,1,1,T2,S).

root_consequent_holds(OP,unnamed_assumption_28,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ1,T2,S),
	not_holds_at(rtoB_ACK1,T2,S).

%guarantee -- unnamed_guarantee_1
%	btoS_ACK0=false

guarantee(unnamed_guarantee_1).

antecedent_holds(unnamed_guarantee_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_1,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

%guarantee -- unnamed_guarantee_2
%	btoS_ACK1=false

guarantee(unnamed_guarantee_2).

antecedent_holds(unnamed_guarantee_2,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_2,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_2,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_2,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

%guarantee -- unnamed_guarantee_3
%	btoS_ACK2=false

guarantee(unnamed_guarantee_3).

antecedent_holds(unnamed_guarantee_3,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_3,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_3,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_3,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

%guarantee -- unnamed_guarantee_4
%	btoS_ACK3=false

guarantee(unnamed_guarantee_4).

antecedent_holds(unnamed_guarantee_4,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_4,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_4,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_4,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_5
%	btoS_ACK4=false

guarantee(unnamed_guarantee_5).

antecedent_holds(unnamed_guarantee_5,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_5,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_5,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_5,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_6
%	btoR_REQ0=false

guarantee(unnamed_guarantee_6).

antecedent_holds(unnamed_guarantee_6,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_6,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_6,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_6,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ0,T2,S).

%guarantee -- unnamed_guarantee_7
%	btoR_REQ1=false

guarantee(unnamed_guarantee_7).

antecedent_holds(unnamed_guarantee_7,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_7,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_7,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_7,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

%guarantee -- unnamed_guarantee_8
%	stateG7_0=false

guarantee(unnamed_guarantee_8).

antecedent_holds(unnamed_guarantee_8,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_8,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_8,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_8,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_0,T2,S).

%guarantee -- unnamed_guarantee_9
%	stateG7_1=true

guarantee(unnamed_guarantee_9).

antecedent_holds(unnamed_guarantee_9,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_9,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_9,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_9,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S).

%guarantee -- unnamed_guarantee_10
%	eNQ=false

guarantee(unnamed_guarantee_10).

antecedent_holds(unnamed_guarantee_10,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_10,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_10,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_10,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_11
%	dEQ=false

guarantee(unnamed_guarantee_11).

antecedent_holds(unnamed_guarantee_11,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_11,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_11,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_11,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(dEQ,T2,S).

%guarantee -- unnamed_guarantee_12
%	stateG12=false

guarantee(unnamed_guarantee_12).

antecedent_holds(unnamed_guarantee_12,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_12,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_12,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_12,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S).

%guarantee -- unnamed_guarantee_13
%	sLC0=false

guarantee(unnamed_guarantee_13).

antecedent_holds(unnamed_guarantee_13,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_13,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_13,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_13,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC0,T2,S).

%guarantee -- unnamed_guarantee_14
%	sLC1=false

guarantee(unnamed_guarantee_14).

antecedent_holds(unnamed_guarantee_14,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_14,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_14,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_14,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC1,T2,S).

%guarantee -- unnamed_guarantee_15
%	sLC2=false

guarantee(unnamed_guarantee_15).

antecedent_holds(unnamed_guarantee_15,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(unnamed_guarantee_15,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,unnamed_guarantee_15,0,0,0,S).

root_consequent_holds(OP,unnamed_guarantee_15,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC2,T2,S).

%guarantee -- unnamed_guarantee_16
%	G(((stoB_REQ0=false&next(stoB_REQ0=true))->next(btoS_ACK0=false)))

guarantee(unnamed_guarantee_16).

antecedent_holds(unnamed_guarantee_16,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_16,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_16,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_16,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ0,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_16,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ0,T2,S).

consequent_holds(unnamed_guarantee_16,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_16,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_16,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

%guarantee -- unnamed_guarantee_17
%	G(((btoS_ACK0=false&stoB_REQ0=false)->next(btoS_ACK0=false)))

guarantee(unnamed_guarantee_17).

antecedent_holds(unnamed_guarantee_17,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_17,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_17,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(stoB_REQ0,T2,S).

consequent_holds(unnamed_guarantee_17,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_17,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_17,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

%guarantee -- unnamed_guarantee_18
%	G(((btoS_ACK0=true&stoB_REQ0=true)->next(btoS_ACK0=true)))

guarantee(unnamed_guarantee_18).

antecedent_holds(unnamed_guarantee_18,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_18,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_18,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(stoB_REQ0,T2,S).

consequent_holds(unnamed_guarantee_18,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_18,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_18,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S).

%guarantee -- unnamed_guarantee_19
%	G((btoS_ACK0=false|btoS_ACK1=false))

guarantee(unnamed_guarantee_19).

antecedent_holds(unnamed_guarantee_19,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_19,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_19,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_19,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_guarantee_19,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_19,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_19,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

%guarantee -- unnamed_guarantee_20
%	G((btoS_ACK0=false|btoS_ACK2=false))

guarantee(unnamed_guarantee_20).

antecedent_holds(unnamed_guarantee_20,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_20,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_20,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_20,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_guarantee_20,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_20,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_20,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

%guarantee -- unnamed_guarantee_21
%	G((btoS_ACK0=false|btoS_ACK3=false))

guarantee(unnamed_guarantee_21).

antecedent_holds(unnamed_guarantee_21,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_21,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_21,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_21,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_guarantee_21,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_21,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_21,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_22
%	G((btoS_ACK0=false|btoS_ACK4=false))

guarantee(unnamed_guarantee_22).

antecedent_holds(unnamed_guarantee_22,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_22,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_22,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_22,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_guarantee_22,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_22,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_22,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_23
%	G(((stoB_REQ1=false&next(stoB_REQ1=true))->next(btoS_ACK1=false)))

guarantee(unnamed_guarantee_23).

antecedent_holds(unnamed_guarantee_23,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_23,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_23,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_23,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ1,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_23,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ1,T2,S).

consequent_holds(unnamed_guarantee_23,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_23,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_23,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

%guarantee -- unnamed_guarantee_24
%	G(((btoS_ACK1=false&stoB_REQ1=false)->next(btoS_ACK1=false)))

guarantee(unnamed_guarantee_24).

antecedent_holds(unnamed_guarantee_24,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_24,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_24,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(stoB_REQ1,T2,S).

consequent_holds(unnamed_guarantee_24,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_24,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_24,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

%guarantee -- unnamed_guarantee_25
%	G(((btoS_ACK1=true&stoB_REQ1=true)->next(btoS_ACK1=true)))

guarantee(unnamed_guarantee_25).

antecedent_holds(unnamed_guarantee_25,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_25,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_25,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(stoB_REQ1,T2,S).

consequent_holds(unnamed_guarantee_25,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_25,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_25,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S).

%guarantee -- unnamed_guarantee_26
%	G((btoS_ACK1=false|btoS_ACK2=false))

guarantee(unnamed_guarantee_26).

antecedent_holds(unnamed_guarantee_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_26,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_26,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

consequent_holds(unnamed_guarantee_26,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_26,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_26,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

%guarantee -- unnamed_guarantee_27
%	G((btoS_ACK1=false|btoS_ACK3=false))

guarantee(unnamed_guarantee_27).

antecedent_holds(unnamed_guarantee_27,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_27,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_27,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_27,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

consequent_holds(unnamed_guarantee_27,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_27,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_27,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_28
%	G((btoS_ACK1=false|btoS_ACK4=false))

guarantee(unnamed_guarantee_28).

antecedent_holds(unnamed_guarantee_28,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_28,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_28,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_28,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

consequent_holds(unnamed_guarantee_28,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_28,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_28,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_29
%	G(((stoB_REQ2=false&next(stoB_REQ2=true))->next(btoS_ACK2=false)))

guarantee(unnamed_guarantee_29).

antecedent_holds(unnamed_guarantee_29,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_29,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_29,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_29,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ2,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_29,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ2,T2,S).

consequent_holds(unnamed_guarantee_29,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_29,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_29,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

%guarantee -- unnamed_guarantee_30
%	G(((btoS_ACK2=false&stoB_REQ2=false)->next(btoS_ACK2=false)))

guarantee(unnamed_guarantee_30).

antecedent_holds(unnamed_guarantee_30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_30,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_30,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(stoB_REQ2,T2,S).

consequent_holds(unnamed_guarantee_30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_30,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_30,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

%guarantee -- unnamed_guarantee_31
%	G(((btoS_ACK2=true&stoB_REQ2=true)->next(btoS_ACK2=true)))

guarantee(unnamed_guarantee_31).

antecedent_holds(unnamed_guarantee_31,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_31,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_31,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(stoB_REQ2,T2,S).

consequent_holds(unnamed_guarantee_31,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_31,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_31,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S).

%guarantee -- unnamed_guarantee_32
%	G((btoS_ACK2=false|btoS_ACK3=false))

guarantee(unnamed_guarantee_32).

antecedent_holds(unnamed_guarantee_32,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_32,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_32,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_32,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

consequent_holds(unnamed_guarantee_32,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_32,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_32,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_33
%	G((btoS_ACK2=false|btoS_ACK4=false))

guarantee(unnamed_guarantee_33).

antecedent_holds(unnamed_guarantee_33,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_33,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_33,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_33,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

consequent_holds(unnamed_guarantee_33,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_33,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_33,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_34
%	G(((stoB_REQ3=false&next(stoB_REQ3=true))->next(btoS_ACK3=false)))

guarantee(unnamed_guarantee_34).

antecedent_holds(unnamed_guarantee_34,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_34,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_34,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_34,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_34,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ3,T2,S).

consequent_holds(unnamed_guarantee_34,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_34,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_34,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_35
%	G(((btoS_ACK3=false&stoB_REQ3=false)->next(btoS_ACK3=false)))

guarantee(unnamed_guarantee_35).

antecedent_holds(unnamed_guarantee_35,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_35,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_35,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(stoB_REQ3,T2,S).

consequent_holds(unnamed_guarantee_35,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_35,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_35,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_36
%	G(((btoS_ACK3=true&stoB_REQ3=true)->next(btoS_ACK3=true)))

guarantee(unnamed_guarantee_36).

antecedent_holds(unnamed_guarantee_36,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_36,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_36,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(stoB_REQ3,T2,S).

consequent_holds(unnamed_guarantee_36,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_36,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_36,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_37
%	G((btoS_ACK3=false|btoS_ACK4=false))

guarantee(unnamed_guarantee_37).

antecedent_holds(unnamed_guarantee_37,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_37,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_37,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_37,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

consequent_holds(unnamed_guarantee_37,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_37,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_37,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_38
%	G(((stoB_REQ4=false&next(stoB_REQ4=true))->next(btoS_ACK4=false)))

guarantee(unnamed_guarantee_38).

antecedent_holds(unnamed_guarantee_38,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_38,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_38,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_38,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_38,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ4,T2,S).

consequent_holds(unnamed_guarantee_38,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_38,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_38,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_39
%	G(((btoS_ACK4=false&stoB_REQ4=false)->next(btoS_ACK4=false)))

guarantee(unnamed_guarantee_39).

antecedent_holds(unnamed_guarantee_39,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_39,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_39,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S),
	not_holds_at(stoB_REQ4,T2,S).

consequent_holds(unnamed_guarantee_39,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_39,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_39,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_40
%	G(((btoS_ACK4=true&stoB_REQ4=true)->next(btoS_ACK4=true)))

guarantee(unnamed_guarantee_40).

antecedent_holds(unnamed_guarantee_40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_40,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_40,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S),
	holds_at(stoB_REQ4,T2,S).

consequent_holds(unnamed_guarantee_40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_40,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_40,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_41
%	G(((btoR_REQ0=true&rtoB_ACK0=false)->next(btoR_REQ0=true)))

guarantee(unnamed_guarantee_41).

antecedent_holds(unnamed_guarantee_41,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_41,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_41,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ0,T2,S),
	not_holds_at(rtoB_ACK0,T2,S).

consequent_holds(unnamed_guarantee_41,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_41,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_41,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ0,T2,S).

%guarantee -- unnamed_guarantee_42
%	G((btoR_REQ0=false|btoR_REQ1=false))

guarantee(unnamed_guarantee_42).

antecedent_holds(unnamed_guarantee_42,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_42,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_42,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_42,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ0,T2,S).

consequent_holds(unnamed_guarantee_42,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_42,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_42,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

%guarantee -- unnamed_guarantee_43
%	G((rtoB_ACK0=true->next(btoR_REQ0=false)))

guarantee(unnamed_guarantee_43).

antecedent_holds(unnamed_guarantee_43,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_43,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_43,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK0,T2,S).

consequent_holds(unnamed_guarantee_43,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_43,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_43,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ0,T2,S).

%guarantee -- unnamed_guarantee_44
%	G(((btoR_REQ1=true&rtoB_ACK1=false)->next(btoR_REQ1=true)))

guarantee(unnamed_guarantee_44).

antecedent_holds(unnamed_guarantee_44,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_44,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_44,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ1,T2,S),
	not_holds_at(rtoB_ACK1,T2,S).

consequent_holds(unnamed_guarantee_44,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_44,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_44,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ1,T2,S).

%guarantee -- unnamed_guarantee_45
%	G((rtoB_ACK1=true->next(btoR_REQ1=false)))

guarantee(unnamed_guarantee_45).

antecedent_holds(unnamed_guarantee_45,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_45,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_45,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK1,T2,S).

consequent_holds(unnamed_guarantee_45,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_45,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_45,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

%guarantee -- unnamed_guarantee_46
%	G(((btoR_REQ0=true&btoR_REQ1=true)->FALSE=true))

guarantee(unnamed_guarantee_46).

antecedent_holds(unnamed_guarantee_46,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_46,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_46,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoR_REQ0,T2,S),
	holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_46,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_46,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_46,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(FALSE,T2,S).

%guarantee -- unnamed_guarantee_47
%	G((((stateG7_1=false&btoR_REQ0=false)&btoR_REQ1=true)->next((stateG7_1=true&stateG7_0=false))))

guarantee(unnamed_guarantee_47).

antecedent_holds(unnamed_guarantee_47,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_47,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_47,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_1,T2,S),
	not_holds_at(btoR_REQ0,T2,S),
	holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_47,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_47,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_47,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S),
	not_holds_at(stateG7_0,T2,S).

%guarantee -- unnamed_guarantee_48
%	G((((stateG7_1=true&btoR_REQ0=true)&btoR_REQ1=false)->next((stateG7_1=false&stateG7_0=false))))

guarantee(unnamed_guarantee_48).

antecedent_holds(unnamed_guarantee_48,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_48,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_48,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S),
	holds_at(btoR_REQ0,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_48,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_48,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_48,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_1,T2,S),
	not_holds_at(stateG7_0,T2,S).

%guarantee -- unnamed_guarantee_49
%	G((((stateG7_1=false&btoR_REQ0=false)&btoR_REQ1=false)->next((stateG7_1=false&stateG7_0=true))))

guarantee(unnamed_guarantee_49).

antecedent_holds(unnamed_guarantee_49,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_49,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_49,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_1,T2,S),
	not_holds_at(btoR_REQ0,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_49,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_49,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_49,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_1,T2,S),
	holds_at(stateG7_0,T2,S).

%guarantee -- unnamed_guarantee_50
%	G((((stateG7_1=true&btoR_REQ0=false)&btoR_REQ1=false)->next((stateG7_1=true&stateG7_0=true))))

guarantee(unnamed_guarantee_50).

antecedent_holds(unnamed_guarantee_50,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_50,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_50,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S),
	not_holds_at(btoR_REQ0,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_50,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_50,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_50,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S),
	holds_at(stateG7_0,T2,S).

%guarantee -- unnamed_guarantee_51
%	G(((((stateG7_1=false&stateG7_0=false)&btoR_REQ0=true)&btoR_REQ1=false)->next((stateG7_1=false&stateG7_0=false))))

guarantee(unnamed_guarantee_51).

antecedent_holds(unnamed_guarantee_51,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_51,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_51,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_1,T2,S),
	not_holds_at(stateG7_0,T2,S),
	holds_at(btoR_REQ0,T2,S),
	not_holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_51,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_51,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_51,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_1,T2,S),
	not_holds_at(stateG7_0,T2,S).

%guarantee -- unnamed_guarantee_52
%	G(((((stateG7_1=true&stateG7_0=false)&btoR_REQ0=false)&btoR_REQ1=true)->next((stateG7_1=true&stateG7_0=false))))

guarantee(unnamed_guarantee_52).

antecedent_holds(unnamed_guarantee_52,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_52,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_52,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S),
	not_holds_at(stateG7_0,T2,S),
	not_holds_at(btoR_REQ0,T2,S),
	holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_52,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_52,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_52,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S),
	not_holds_at(stateG7_0,T2,S).

%guarantee -- unnamed_guarantee_53
%	G((((stateG7_1=false&stateG7_0=true)&btoR_REQ0=true)->FALSE=true))

guarantee(unnamed_guarantee_53).

antecedent_holds(unnamed_guarantee_53,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_53,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_53,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG7_1,T2,S),
	holds_at(stateG7_0,T2,S),
	holds_at(btoR_REQ0,T2,S).

consequent_holds(unnamed_guarantee_53,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_53,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_53,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(FALSE,T2,S).

%guarantee -- unnamed_guarantee_54
%	G((((stateG7_1=true&stateG7_0=true)&btoR_REQ1=true)->FALSE=true))

guarantee(unnamed_guarantee_54).

antecedent_holds(unnamed_guarantee_54,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_54,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_54,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG7_1,T2,S),
	holds_at(stateG7_0,T2,S),
	holds_at(btoR_REQ1,T2,S).

consequent_holds(unnamed_guarantee_54,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_54,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_54,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(FALSE,T2,S).

%guarantee -- unnamed_guarantee_55
%	G(((btoS_ACK0=false&next(btoS_ACK0=true))->next(eNQ=true)))

guarantee(unnamed_guarantee_55).

antecedent_holds(unnamed_guarantee_55,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_55,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_55,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_55,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_55,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_guarantee_55,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_55,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_55,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_56
%	G(((btoS_ACK0=false&next(btoS_ACK0=true))->next(((sLC0=false&sLC1=false)&sLC2=false))))

guarantee(unnamed_guarantee_56).

antecedent_holds(unnamed_guarantee_56,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_56,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_56,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_56,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_56,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S).

consequent_holds(unnamed_guarantee_56,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_56,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_56,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC0,T2,S),
	not_holds_at(sLC1,T2,S),
	not_holds_at(sLC2,T2,S).

%guarantee -- unnamed_guarantee_57
%	G(((btoS_ACK1=false&next(btoS_ACK1=true))->next(eNQ=true)))

guarantee(unnamed_guarantee_57).

antecedent_holds(unnamed_guarantee_57,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_57,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_57,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_57,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_57,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S).

consequent_holds(unnamed_guarantee_57,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_57,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_57,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_58
%	G((((((((btoS_ACK1=false&next((btoS_ACK1=true&((sLC0=true&sLC1=false)&sLC2=false))))|(!(btoS_ACK1=false)&next(!(sLC0=true))))|(!(btoS_ACK1=false)&next(!(sLC1=false))))|(!(btoS_ACK1=false)&next(!(sLC2=false))))|next((!(btoS_ACK1=true)&!(sLC0=true))))|next((!(btoS_ACK1=true)&!(sLC1=false))))|next((!(btoS_ACK1=true)&!(sLC2=false)))))

guarantee(unnamed_guarantee_58).

antecedent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_58,0,0,T,S),
	root_consequent_holds(next,unnamed_guarantee_58,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(sLC0,T2,S),
	not_holds_at(sLC1,T2,S),
	not_holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_58,0,2,T,S),
	root_consequent_holds(next,unnamed_guarantee_58,0,3,T,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_58,0,4,T,S),
	root_consequent_holds(next,unnamed_guarantee_58,0,5,T,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_58,0,6,T,S),
	root_consequent_holds(next,unnamed_guarantee_58,0,7,T,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_58,0,8,T,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_58,0,9,T,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_58,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_58,0,10,T,S).

root_consequent_holds(OP,unnamed_guarantee_58,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	holds_at(sLC2,T2,S).

%guarantee -- unnamed_guarantee_59
%	G(((btoS_ACK2=false&next(btoS_ACK2=true))->next(eNQ=true)))

guarantee(unnamed_guarantee_59).

antecedent_holds(unnamed_guarantee_59,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_59,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_59,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_59,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_59,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S).

consequent_holds(unnamed_guarantee_59,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_59,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_59,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_60
%	G((((((((btoS_ACK2=false&next((btoS_ACK2=true&((sLC0=false&sLC1=true)&sLC2=false))))|(!(btoS_ACK2=false)&next(!(sLC0=false))))|(!(btoS_ACK2=false)&next(!(sLC1=true))))|(!(btoS_ACK2=false)&next(!(sLC2=false))))|next((!(btoS_ACK2=true)&!(sLC0=false))))|next((!(btoS_ACK2=true)&!(sLC1=true))))|next((!(btoS_ACK2=true)&!(sLC2=false)))))

guarantee(unnamed_guarantee_60).

antecedent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_60,0,0,T,S),
	root_consequent_holds(next,unnamed_guarantee_60,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	not_holds_at(sLC0,T2,S),
	holds_at(sLC1,T2,S),
	not_holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_60,0,2,T,S),
	root_consequent_holds(next,unnamed_guarantee_60,0,3,T,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_60,0,4,T,S),
	root_consequent_holds(next,unnamed_guarantee_60,0,5,T,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_60,0,6,T,S),
	root_consequent_holds(next,unnamed_guarantee_60,0,7,T,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_60,0,8,T,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_60,0,9,T,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_60,0,10,T,S).

root_consequent_holds(OP,unnamed_guarantee_60,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	holds_at(sLC2,T2,S).

%guarantee -- unnamed_guarantee_61
%	G(((btoS_ACK3=false&next(btoS_ACK3=true))->next(eNQ=true)))

guarantee(unnamed_guarantee_61).

antecedent_holds(unnamed_guarantee_61,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_61,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_61,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_61,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_61,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S).

consequent_holds(unnamed_guarantee_61,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_61,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_61,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_62
%	G((((((((btoS_ACK3=false&next((btoS_ACK3=true&((sLC0=true&sLC1=true)&sLC2=false))))|(!(btoS_ACK3=false)&next(!(sLC0=true))))|(!(btoS_ACK3=false)&next(!(sLC1=true))))|(!(btoS_ACK3=false)&next(!(sLC2=false))))|next((!(btoS_ACK3=true)&!(sLC0=true))))|next((!(btoS_ACK3=true)&!(sLC1=true))))|next((!(btoS_ACK3=true)&!(sLC2=false)))))

guarantee(unnamed_guarantee_62).

antecedent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_62,0,0,T,S),
	root_consequent_holds(next,unnamed_guarantee_62,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(sLC0,T2,S),
	holds_at(sLC1,T2,S),
	not_holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_62,0,2,T,S),
	root_consequent_holds(next,unnamed_guarantee_62,0,3,T,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_62,0,4,T,S),
	root_consequent_holds(next,unnamed_guarantee_62,0,5,T,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_62,0,6,T,S),
	root_consequent_holds(next,unnamed_guarantee_62,0,7,T,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_62,0,8,T,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_62,0,9,T,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_62,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_62,0,10,T,S).

root_consequent_holds(OP,unnamed_guarantee_62,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	holds_at(sLC2,T2,S).

%guarantee -- unnamed_guarantee_63
%	G(((btoS_ACK4=false&next(btoS_ACK4=true))->next(eNQ=true)))

guarantee(unnamed_guarantee_63).

antecedent_holds(unnamed_guarantee_63,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_63,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_63,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_63,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_63,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S).

consequent_holds(unnamed_guarantee_63,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_63,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_63,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_64
%	G((((((((btoS_ACK4=false&next((btoS_ACK4=true&((sLC0=false&sLC1=false)&sLC2=true))))|(!(btoS_ACK4=false)&next(!(sLC0=false))))|(!(btoS_ACK4=false)&next(!(sLC1=false))))|(!(btoS_ACK4=false)&next(!(sLC2=true))))|next((!(btoS_ACK4=true)&!(sLC0=false))))|next((!(btoS_ACK4=true)&!(sLC1=false))))|next((!(btoS_ACK4=true)&!(sLC2=true)))))

guarantee(unnamed_guarantee_64).

antecedent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_64,0,0,T,S),
	root_consequent_holds(next,unnamed_guarantee_64,0,1,T,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S),
	not_holds_at(sLC0,T2,S),
	not_holds_at(sLC1,T2,S),
	holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_64,0,2,T,S),
	root_consequent_holds(next,unnamed_guarantee_64,0,3,T,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_64,0,4,T,S),
	root_consequent_holds(next,unnamed_guarantee_64,0,5,T,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_64,0,6,T,S),
	root_consequent_holds(next,unnamed_guarantee_64,0,7,T,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(sLC2,T2,S).

consequent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_64,0,8,T,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S),
	holds_at(sLC0,T2,S).

consequent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_64,0,9,T,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S),
	holds_at(sLC1,T2,S).

consequent_holds(unnamed_guarantee_64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_64,0,10,T,S).

root_consequent_holds(OP,unnamed_guarantee_64,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S),
	not_holds_at(sLC2,T2,S).

%guarantee -- unnamed_guarantee_65
%	G(((((((((((((((((((((((((((((((((((((btoS_ACK0=true&btoS_ACK1=true)&btoS_ACK2=true)&btoS_ACK3=true)&btoS_ACK4=true)|((((btoS_ACK0=true&btoS_ACK1=true)&btoS_ACK2=true)&btoS_ACK3=true)&next(btoS_ACK4=false)))|((((btoS_ACK0=true&btoS_ACK1=true)&btoS_ACK2=true)&btoS_ACK4=true)&next(btoS_ACK3=false)))|(((btoS_ACK0=true&btoS_ACK1=true)&btoS_ACK2=true)&next((btoS_ACK3=false&btoS_ACK4=false))))|((((btoS_ACK0=true&btoS_ACK1=true)&btoS_ACK3=true)&btoS_ACK4=true)&next(btoS_ACK2=false)))|(((btoS_ACK0=true&btoS_ACK1=true)&btoS_ACK3=true)&next((btoS_ACK2=false&btoS_ACK4=false))))|(((btoS_ACK0=true&btoS_ACK1=true)&btoS_ACK4=true)&next((btoS_ACK2=false&btoS_ACK3=false))))|((btoS_ACK0=true&btoS_ACK1=true)&next(((btoS_ACK2=false&btoS_ACK3=false)&btoS_ACK4=false))))|((((btoS_ACK0=true&btoS_ACK2=true)&btoS_ACK3=true)&btoS_ACK4=true)&next(btoS_ACK1=false)))|(((btoS_ACK0=true&btoS_ACK2=true)&btoS_ACK3=true)&next((btoS_ACK1=false&btoS_ACK4=false))))|(((btoS_ACK0=true&btoS_ACK2=true)&btoS_ACK4=true)&next((btoS_ACK1=false&btoS_ACK3=false))))|((btoS_ACK0=true&btoS_ACK2=true)&next(((btoS_ACK1=false&btoS_ACK3=false)&btoS_ACK4=false))))|(((btoS_ACK0=true&btoS_ACK3=true)&btoS_ACK4=true)&next((btoS_ACK1=false&btoS_ACK2=false))))|((btoS_ACK0=true&btoS_ACK3=true)&next(((btoS_ACK1=false&btoS_ACK2=false)&btoS_ACK4=false))))|((btoS_ACK0=true&btoS_ACK4=true)&next(((btoS_ACK1=false&btoS_ACK2=false)&btoS_ACK3=false))))|(btoS_ACK0=true&next((((btoS_ACK1=false&btoS_ACK2=false)&btoS_ACK3=false)&btoS_ACK4=false))))|((((btoS_ACK1=true&btoS_ACK2=true)&btoS_ACK3=true)&btoS_ACK4=true)&next(btoS_ACK0=false)))|(((btoS_ACK1=true&btoS_ACK2=true)&btoS_ACK3=true)&next((btoS_ACK0=false&btoS_ACK4=false))))|(((btoS_ACK1=true&btoS_ACK2=true)&btoS_ACK4=true)&next((btoS_ACK0=false&btoS_ACK3=false))))|((btoS_ACK1=true&btoS_ACK2=true)&next(((btoS_ACK0=false&btoS_ACK3=false)&btoS_ACK4=false))))|(((btoS_ACK1=true&btoS_ACK3=true)&btoS_ACK4=true)&next((btoS_ACK0=false&btoS_ACK2=false))))|((btoS_ACK1=true&btoS_ACK3=true)&next(((btoS_ACK0=false&btoS_ACK2=false)&btoS_ACK4=false))))|((btoS_ACK1=true&btoS_ACK4=true)&next(((btoS_ACK0=false&btoS_ACK2=false)&btoS_ACK3=false))))|(btoS_ACK1=true&next((((btoS_ACK0=false&btoS_ACK2=false)&btoS_ACK3=false)&btoS_ACK4=false))))|(((btoS_ACK2=true&btoS_ACK3=true)&btoS_ACK4=true)&next((btoS_ACK0=false&btoS_ACK1=false))))|((btoS_ACK2=true&btoS_ACK3=true)&next(((btoS_ACK0=false&btoS_ACK1=false)&btoS_ACK4=false))))|((btoS_ACK2=true&btoS_ACK4=true)&next(((btoS_ACK0=false&btoS_ACK1=false)&btoS_ACK3=false))))|(btoS_ACK2=true&next((((btoS_ACK0=false&btoS_ACK1=false)&btoS_ACK3=false)&btoS_ACK4=false))))|((btoS_ACK3=true&btoS_ACK4=true)&next(((btoS_ACK0=false&btoS_ACK1=false)&btoS_ACK2=false))))|(btoS_ACK3=true&next((((btoS_ACK0=false&btoS_ACK1=false)&btoS_ACK2=false)&btoS_ACK4=false))))|(btoS_ACK4=true&next((((btoS_ACK0=false&btoS_ACK1=false)&btoS_ACK2=false)&btoS_ACK3=false))))|next(((((btoS_ACK0=false&btoS_ACK1=false)&btoS_ACK2=false)&btoS_ACK3=false)&btoS_ACK4=false)))->next(eNQ=false)))

guarantee(unnamed_guarantee_65).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,1,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,2,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,3,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,4,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,5,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,6,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,7,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,8,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,9,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,10,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,11,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,12,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,13,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,14,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK1,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,15,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,16,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,17,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,18,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,19,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,20,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,21,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,22,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,23,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,24,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,25,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,26,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,27,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,28,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,29,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,30,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK0,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,31,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,32,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,33,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,34,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,34,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,35,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,36,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,35,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,36,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,37,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,38,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,37,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,38,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,39,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,40,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,39,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,40,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,41,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,42,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,41,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,42,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,43,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,44,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,43,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,44,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,45,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,46,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,45,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK1,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,46,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,47,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,48,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,47,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,48,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,49,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,50,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,49,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,50,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,51,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,52,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,51,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,52,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,53,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,54,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,53,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,54,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,55,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,56,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,55,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,56,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,57,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,58,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,57,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,58,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_65,59,T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,60,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,59,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_65,60,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

antecedent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(next,unnamed_guarantee_65,61,T,S).

root_antecedent_holds(OP,unnamed_guarantee_65,61,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btoS_ACK0,T2,S),
	not_holds_at(btoS_ACK1,T2,S),
	not_holds_at(btoS_ACK2,T2,S),
	not_holds_at(btoS_ACK3,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

consequent_holds(unnamed_guarantee_65,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_65,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_65,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_66
%	G(((rtoB_ACK0=true&next(rtoB_ACK0=false))->next(dEQ=true)))

guarantee(unnamed_guarantee_66).

antecedent_holds(unnamed_guarantee_66,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_66,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_66,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_66,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK0,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_66,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK0,T2,S).

consequent_holds(unnamed_guarantee_66,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_66,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_66,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(dEQ,T2,S).

%guarantee -- unnamed_guarantee_67
%	G(((rtoB_ACK1=true&next(rtoB_ACK1=false))->next(dEQ=true)))

guarantee(unnamed_guarantee_67).

antecedent_holds(unnamed_guarantee_67,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_67,0,T,S),
	root_antecedent_holds(next,unnamed_guarantee_67,1,T,S).

root_antecedent_holds(OP,unnamed_guarantee_67,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK1,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_67,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK1,T2,S).

consequent_holds(unnamed_guarantee_67,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_67,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_67,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(dEQ,T2,S).

%guarantee -- unnamed_guarantee_68
%	G((((((rtoB_ACK0=false&rtoB_ACK1=false)|(rtoB_ACK0=false&next(rtoB_ACK1=true)))|(rtoB_ACK1=false&next(rtoB_ACK0=true)))|next((rtoB_ACK0=true&rtoB_ACK1=true)))->next(dEQ=false)))

guarantee(unnamed_guarantee_68).

antecedent_holds(unnamed_guarantee_68,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_68,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_68,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK0,T2,S),
	not_holds_at(rtoB_ACK1,T2,S).

antecedent_holds(unnamed_guarantee_68,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_68,1,T,S),
	root_antecedent_holds(next,unnamed_guarantee_68,2,T,S).

root_antecedent_holds(OP,unnamed_guarantee_68,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK0,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_68,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK1,T2,S).

antecedent_holds(unnamed_guarantee_68,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_68,3,T,S),
	root_antecedent_holds(next,unnamed_guarantee_68,4,T,S).

root_antecedent_holds(OP,unnamed_guarantee_68,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(rtoB_ACK1,T2,S).

root_antecedent_holds(OP,unnamed_guarantee_68,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK0,T2,S).

antecedent_holds(unnamed_guarantee_68,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(next,unnamed_guarantee_68,5,T,S).

root_antecedent_holds(OP,unnamed_guarantee_68,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(rtoB_ACK0,T2,S),
	holds_at(rtoB_ACK1,T2,S).

consequent_holds(unnamed_guarantee_68,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_68,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_68,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(dEQ,T2,S).

%guarantee -- unnamed_guarantee_69
%	G(((fULL=true&dEQ=false)->eNQ=false))

guarantee(unnamed_guarantee_69).

antecedent_holds(unnamed_guarantee_69,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_69,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_69,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(fULL,T2,S),
	not_holds_at(dEQ,T2,S).

consequent_holds(unnamed_guarantee_69,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_69,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_69,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(eNQ,T2,S).

%guarantee -- unnamed_guarantee_70
%	G((eMPTY=true->dEQ=false))

guarantee(unnamed_guarantee_70).

antecedent_holds(unnamed_guarantee_70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_70,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_70,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(eMPTY,T2,S).

consequent_holds(unnamed_guarantee_70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,unnamed_guarantee_70,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_70,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(dEQ,T2,S).

%guarantee -- unnamed_guarantee_71
%	G(((stateG12=false&eMPTY=true)->next(stateG12=false)))

guarantee(unnamed_guarantee_71).

antecedent_holds(unnamed_guarantee_71,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_71,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_71,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S),
	holds_at(eMPTY,T2,S).

consequent_holds(unnamed_guarantee_71,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_71,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_71,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S).

%guarantee -- unnamed_guarantee_72
%	G(((stateG12=false&dEQ=true)->next(stateG12=false)))

guarantee(unnamed_guarantee_72).

antecedent_holds(unnamed_guarantee_72,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_72,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_72,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S),
	holds_at(dEQ,T2,S).

consequent_holds(unnamed_guarantee_72,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_72,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_72,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S).

%guarantee -- unnamed_guarantee_73
%	G((((stateG12=false&eMPTY=false)&dEQ=false)->next(stateG12=true)))

guarantee(unnamed_guarantee_73).

antecedent_holds(unnamed_guarantee_73,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_73,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_73,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S),
	not_holds_at(eMPTY,T2,S),
	not_holds_at(dEQ,T2,S).

consequent_holds(unnamed_guarantee_73,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_73,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_73,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG12,T2,S).

%guarantee -- unnamed_guarantee_74
%	G(((stateG12=true&dEQ=false)->next(stateG12=true)))

guarantee(unnamed_guarantee_74).

antecedent_holds(unnamed_guarantee_74,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_74,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_74,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG12,T2,S),
	not_holds_at(dEQ,T2,S).

consequent_holds(unnamed_guarantee_74,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_74,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_74,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG12,T2,S).

%guarantee -- unnamed_guarantee_75
%	G(((stateG12=true&dEQ=true)->next(stateG12=false)))

guarantee(unnamed_guarantee_75).

antecedent_holds(unnamed_guarantee_75,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,unnamed_guarantee_75,0,T,S).

root_antecedent_holds(OP,unnamed_guarantee_75,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stateG12,T2,S),
	holds_at(dEQ,T2,S).

consequent_holds(unnamed_guarantee_75,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,unnamed_guarantee_75,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_75,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S).

%guarantee -- unnamed_guarantee_76
%	GF(((stoB_REQ0=true&btoS_ACK0=true)|(!(stoB_REQ0=true)&!(btoS_ACK0=true))))

guarantee(unnamed_guarantee_76).

antecedent_holds(unnamed_guarantee_76,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_76,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_guarantee_76,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_76,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_76,1,0,T2,S).

root_consequent_holds(OP,unnamed_guarantee_76,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ0,T2,S),
	holds_at(btoS_ACK0,T2,S).

root_consequent_holds(OP,unnamed_guarantee_76,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_76,1,1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_76,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ0,T2,S),
	not_holds_at(btoS_ACK0,T2,S).

%guarantee -- unnamed_guarantee_77
%	GF(((stoB_REQ1=true&btoS_ACK1=true)|(!(stoB_REQ1=true)&!(btoS_ACK1=true))))

guarantee(unnamed_guarantee_77).

antecedent_holds(unnamed_guarantee_77,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_77,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_guarantee_77,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_77,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_77,1,0,T2,S).

root_consequent_holds(OP,unnamed_guarantee_77,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ1,T2,S),
	holds_at(btoS_ACK1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_77,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_77,1,1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_77,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ1,T2,S),
	not_holds_at(btoS_ACK1,T2,S).

%guarantee -- unnamed_guarantee_78
%	GF(((stoB_REQ2=true&btoS_ACK2=true)|(!(stoB_REQ2=true)&!(btoS_ACK2=true))))

guarantee(unnamed_guarantee_78).

antecedent_holds(unnamed_guarantee_78,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_78,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_guarantee_78,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_78,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_78,1,0,T2,S).

root_consequent_holds(OP,unnamed_guarantee_78,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ2,T2,S),
	holds_at(btoS_ACK2,T2,S).

root_consequent_holds(OP,unnamed_guarantee_78,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_78,1,1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_78,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ2,T2,S),
	not_holds_at(btoS_ACK2,T2,S).

%guarantee -- unnamed_guarantee_79
%	GF(((stoB_REQ3=true&btoS_ACK3=true)|(!(stoB_REQ3=true)&!(btoS_ACK3=true))))

guarantee(unnamed_guarantee_79).

antecedent_holds(unnamed_guarantee_79,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_79,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_guarantee_79,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_79,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_79,1,0,T2,S).

root_consequent_holds(OP,unnamed_guarantee_79,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ3,T2,S),
	holds_at(btoS_ACK3,T2,S).

root_consequent_holds(OP,unnamed_guarantee_79,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_79,1,1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_79,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ3,T2,S),
	not_holds_at(btoS_ACK3,T2,S).

%guarantee -- unnamed_guarantee_80
%	GF(((stoB_REQ4=true&btoS_ACK4=true)|(!(stoB_REQ4=true)&!(btoS_ACK4=true))))

guarantee(unnamed_guarantee_80).

antecedent_holds(unnamed_guarantee_80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_guarantee_80,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_80,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_80,1,0,T2,S).

root_consequent_holds(OP,unnamed_guarantee_80,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(stoB_REQ4,T2,S),
	holds_at(btoS_ACK4,T2,S).

root_consequent_holds(OP,unnamed_guarantee_80,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_80,1,1,T2,S).

root_consequent_holds(OP,unnamed_guarantee_80,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stoB_REQ4,T2,S),
	not_holds_at(btoS_ACK4,T2,S).

%guarantee -- unnamed_guarantee_81
%	GF(stateG12=false)

guarantee(unnamed_guarantee_81).

antecedent_holds(unnamed_guarantee_81,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(unnamed_guarantee_81,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,unnamed_guarantee_81,0,0,T,S).

root_consequent_holds(OP,unnamed_guarantee_81,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,unnamed_guarantee_81,1,0,T2,S).

root_consequent_holds(OP,unnamed_guarantee_81,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(stateG12,T2,S).

%---*** Signature  ***---

atom(btoR_REQ0).
atom(btoR_REQ1).
atom(btoS_ACK0).
atom(btoS_ACK1).
atom(btoS_ACK2).
atom(btoS_ACK3).
atom(btoS_ACK4).
atom(dEQ).
atom(eMPTY).
atom(eNQ).
atom(fULL).
atom(rtoB_ACK0).
atom(rtoB_ACK1).
atom(sLC0).
atom(sLC1).
atom(sLC2).
atom(stateG12).
atom(stateG7_0).
atom(stateG7_1).
atom(stoB_REQ0).
atom(stoB_REQ1).
atom(stoB_REQ2).
atom(stoB_REQ3).
atom(stoB_REQ4).


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
not_holds_at(btoR_REQ0,0,trace_name_0).
not_holds_at(btoR_REQ1,0,trace_name_0).
not_holds_at(btoS_ACK0,0,trace_name_0).
not_holds_at(btoS_ACK1,0,trace_name_0).
not_holds_at(btoS_ACK2,0,trace_name_0).
not_holds_at(btoS_ACK3,0,trace_name_0).
not_holds_at(btoS_ACK4,0,trace_name_0).
not_holds_at(dEQ,0,trace_name_0).
not_holds_at(eMPTY,0,trace_name_0).
not_holds_at(eNQ,0,trace_name_0).
not_holds_at(fULL,0,trace_name_0).
not_holds_at(rtoB_ACK0,0,trace_name_0).
not_holds_at(rtoB_ACK1,0,trace_name_0).
not_holds_at(sLC0,0,trace_name_0).
not_holds_at(sLC1,0,trace_name_0).
not_holds_at(sLC2,0,trace_name_0).
not_holds_at(stateG12,0,trace_name_0).
not_holds_at(stateG7_0,0,trace_name_0).
not_holds_at(stateG7_1,0,trace_name_0).
not_holds_at(stoB_REQ0,0,trace_name_0).
not_holds_at(stoB_REQ1,0,trace_name_0).
not_holds_at(stoB_REQ2,0,trace_name_0).
not_holds_at(stoB_REQ3,0,trace_name_0).
not_holds_at(stoB_REQ4,0,trace_name_0).

to_violate(unnamed_assumption_10).

is_guarantee(unnamed_guarantee_1).
is_guarantee(unnamed_guarantee_10).
is_guarantee(unnamed_guarantee_11).
is_guarantee(unnamed_guarantee_12).
is_guarantee(unnamed_guarantee_13).
is_guarantee(unnamed_guarantee_14).
is_guarantee(unnamed_guarantee_15).
is_guarantee(unnamed_guarantee_16).
is_guarantee(unnamed_guarantee_17).
is_guarantee(unnamed_guarantee_18).
is_guarantee(unnamed_guarantee_19).
is_guarantee(unnamed_guarantee_2).
is_guarantee(unnamed_guarantee_20).
is_guarantee(unnamed_guarantee_21).
is_guarantee(unnamed_guarantee_22).
is_guarantee(unnamed_guarantee_23).
is_guarantee(unnamed_guarantee_24).
is_guarantee(unnamed_guarantee_25).
is_guarantee(unnamed_guarantee_26).
is_guarantee(unnamed_guarantee_27).
is_guarantee(unnamed_guarantee_28).
is_guarantee(unnamed_guarantee_29).
is_guarantee(unnamed_guarantee_3).
is_guarantee(unnamed_guarantee_30).
is_guarantee(unnamed_guarantee_31).
is_guarantee(unnamed_guarantee_32).
is_guarantee(unnamed_guarantee_33).
is_guarantee(unnamed_guarantee_34).
is_guarantee(unnamed_guarantee_35).
is_guarantee(unnamed_guarantee_36).
is_guarantee(unnamed_guarantee_37).
is_guarantee(unnamed_guarantee_38).
is_guarantee(unnamed_guarantee_39).
is_guarantee(unnamed_guarantee_4).
is_guarantee(unnamed_guarantee_40).
is_guarantee(unnamed_guarantee_41).
is_guarantee(unnamed_guarantee_42).
is_guarantee(unnamed_guarantee_43).
is_guarantee(unnamed_guarantee_44).
is_guarantee(unnamed_guarantee_45).
is_guarantee(unnamed_guarantee_46).
is_guarantee(unnamed_guarantee_47).
is_guarantee(unnamed_guarantee_48).
is_guarantee(unnamed_guarantee_49).
is_guarantee(unnamed_guarantee_5).
is_guarantee(unnamed_guarantee_50).
is_guarantee(unnamed_guarantee_51).
is_guarantee(unnamed_guarantee_52).
is_guarantee(unnamed_guarantee_53).
is_guarantee(unnamed_guarantee_54).
is_guarantee(unnamed_guarantee_55).
is_guarantee(unnamed_guarantee_56).
is_guarantee(unnamed_guarantee_57).
is_guarantee(unnamed_guarantee_58).
is_guarantee(unnamed_guarantee_59).
is_guarantee(unnamed_guarantee_6).
is_guarantee(unnamed_guarantee_60).
is_guarantee(unnamed_guarantee_61).
is_guarantee(unnamed_guarantee_62).
is_guarantee(unnamed_guarantee_63).
is_guarantee(unnamed_guarantee_64).
is_guarantee(unnamed_guarantee_65).
is_guarantee(unnamed_guarantee_66).
is_guarantee(unnamed_guarantee_67).
is_guarantee(unnamed_guarantee_68).
is_guarantee(unnamed_guarantee_69).
is_guarantee(unnamed_guarantee_7).
is_guarantee(unnamed_guarantee_70).
is_guarantee(unnamed_guarantee_71).
is_guarantee(unnamed_guarantee_72).
is_guarantee(unnamed_guarantee_73).
is_guarantee(unnamed_guarantee_74).
is_guarantee(unnamed_guarantee_75).
is_guarantee(unnamed_guarantee_76).
is_guarantee(unnamed_guarantee_77).
is_guarantee(unnamed_guarantee_78).
is_guarantee(unnamed_guarantee_79).
is_guarantee(unnamed_guarantee_8).
is_guarantee(unnamed_guarantee_80).
is_guarantee(unnamed_guarantee_81).
is_guarantee(unnamed_guarantee_9).

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
