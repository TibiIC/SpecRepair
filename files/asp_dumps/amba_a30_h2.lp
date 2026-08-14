% amba (case_study_2)
% environment variables : hburst_burst4, hburst_single, hbusreq_0, hbusreq_1, hbusreq_2, hlock_0, hlock_1, hlock_2, hready
% system variables      : btq_state_1_s0, btq_state_1_s1, btq_state_2_s0, btq_state_2_s1, btq_state_3_s0, btq_state_3_s1, btq_state_4_s0, btq_state_4_s1, btq_state_5_s0, btq_state_5_s1, btq_state_6_s0, btq_state_6_s1, decide, hgrant_0, hgrant_1, hgrant_2, hmaster_val0, hmaster_val1, hmastlock, hready_counter_val0, hready_counter_val1, hready_counter_val2, hready_counter_val3, locked, start
% target                : a30
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

%assumption -- a10_0
%	G((((hmastlock=true&(hburst_single=false&hburst_burst4=false))&hmaster_val0=true)->F(next(hbusreq_0=false))))

assumption(a10_0).

antecedent_holds(a10_0,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,a10_0,0,T,S).

root_antecedent_holds(OP,a10_0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(a10_0,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,a10_0,0,0,T,S).

root_consequent_holds(OP,a10_0,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(next,a10_0,1,0,T2,S).

root_consequent_holds(OP,a10_0,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hbusreq_0,T2,S).

%assumption -- a10_1
%	G((((hmastlock=true&(hburst_single=false&hburst_burst4=false))&hmaster_val1=true)->F(next(hbusreq_1=false))))

assumption(a10_1).

antecedent_holds(a10_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,a10_1,0,T,S).

root_antecedent_holds(OP,a10_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(a10_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,a10_1,0,0,T,S).

root_consequent_holds(OP,a10_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(next,a10_1,1,0,T2,S).

root_consequent_holds(OP,a10_1,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hbusreq_1,T2,S).

%assumption -- a10_2
%	G((((hmastlock=true&(hburst_single=false&hburst_burst4=false))&(hmaster_val0=false&hmaster_val1=false))->F(next(hbusreq_2=false))))

assumption(a10_2).

antecedent_holds(a10_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,a10_2,0,T,S).

root_antecedent_holds(OP,a10_2,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(a10_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,a10_2,0,0,T,S).

root_consequent_holds(OP,a10_2,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(next,a10_2,1,0,T2,S).

root_consequent_holds(OP,a10_2,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hbusreq_2,T2,S).

%assumption -- a20
%	GF(hready=true)

assumption(a20).

antecedent_holds(a20,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(a20,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,a20,0,0,T,S).

root_consequent_holds(OP,a20,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,a20,1,0,T2,S).

root_consequent_holds(OP,a20,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready,T2,S).

%assumption -- a30
%	G((((((((((!(hlock_0=true)&!(hlock_1=true))&!(hlock_2=true))|((!(hlock_0=true)&!(hlock_1=true))&hbusreq_2=true))|((!(hlock_0=true)&hbusreq_1=true)&!(hlock_2=true)))|((!(hlock_0=true)&hbusreq_1=true)&hbusreq_2=true))|((hbusreq_0=true&!(hlock_1=true))&!(hlock_2=true)))|((hbusreq_0=true&!(hlock_1=true))&hbusreq_2=true))|((hbusreq_0=true&hbusreq_1=true)&!(hlock_2=true)))|((hbusreq_0=true&hbusreq_1=true)&hbusreq_2=true)))

assumption(a30).

antecedent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,0,T,S).

root_consequent_holds(OP,a30,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,1,T,S).

root_consequent_holds(OP,a30,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	holds_at(hbusreq_2,T2,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,2,T,S).

root_consequent_holds(OP,a30,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	holds_at(hbusreq_1,T2,S),
	not_holds_at(hlock_2,T2,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,3,T,S).

root_consequent_holds(OP,a30,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	holds_at(hbusreq_1,T2,S),
	holds_at(hbusreq_2,T2,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,4,T,S).

root_consequent_holds(OP,a30,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hbusreq_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,5,T,S).

root_consequent_holds(OP,a30,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hbusreq_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	holds_at(hbusreq_2,T2,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,6,T,S).

root_consequent_holds(OP,a30,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hbusreq_0,T2,S),
	holds_at(hbusreq_1,T2,S),
	not_holds_at(hlock_2,T2,S).

consequent_holds(a30,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,a30,0,7,T,S).

root_consequent_holds(OP,a30,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hbusreq_0,T2,S),
	holds_at(hbusreq_1,T2,S),
	holds_at(hbusreq_2,T2,S).

%guarantee -- g10
%	G((hready=false->next(start=false)))

guarantee(g10).

antecedent_holds(g10,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,g10,0,T,S).

root_antecedent_holds(OP,g10,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S).

consequent_holds(g10,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,g10,0,0,T,S).

root_consequent_holds(OP,g10,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S).

%guarantee -- g20_0_monitor_init
%	btq_state_1_s0=true

guarantee(g20_0_monitor_init).

antecedent_holds(g20_0_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(g20_0_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,g20_0_monitor_init,0,0,0,S).

root_consequent_holds(OP,g20_0_monitor_init,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S).

%guarantee -- g20_0_monitor_safety
%	G((((((((((((((((((((btq_state_1_s0=true&!(hmastlock=true))&!(hbusreq_0=false))&next(btq_state_1_s0=true))|(((btq_state_1_s0=true&!(hburst_single=false))&!(hbusreq_0=false))&next(btq_state_1_s0=true)))|(((btq_state_1_s0=true&!(hburst_burst4=false))&!(hbusreq_0=false))&next(btq_state_1_s0=true)))|(((btq_state_1_s0=true&!(hmaster_val0=true))&!(hbusreq_0=false))&next(btq_state_1_s0=true)))|(((btq_state_1_s0=true&!(start=true))&!(hbusreq_0=false))&next(btq_state_1_s0=true)))|((((((btq_state_1_s0=true&hmastlock=true)&hburst_single=false)&hburst_burst4=false)&hmaster_val0=true)&start=true)&next((start=true&btq_state_1_s0=true))))|((btq_state_1_s0=true&hbusreq_0=false)&next((!(start=true)&btq_state_1_s0=true))))|(((btq_state_1_s0=true&!(hmastlock=true))&hbusreq_0=false)&next((start=true&btq_state_1_s0=true))))|(((btq_state_1_s0=true&!(hburst_single=false))&hbusreq_0=false)&next((start=true&btq_state_1_s0=true))))|(((btq_state_1_s0=true&!(hburst_burst4=false))&hbusreq_0=false)&next((start=true&btq_state_1_s0=true))))|(((btq_state_1_s0=true&!(hmaster_val0=true))&hbusreq_0=false)&next((start=true&btq_state_1_s0=true))))|(((btq_state_1_s0=true&!(start=true))&hbusreq_0=false)&next((start=true&btq_state_1_s0=true))))|(((((((btq_state_1_s0=true&hmastlock=true)&hburst_single=false)&hburst_burst4=false)&hmaster_val0=true)&start=true)&!(hbusreq_0=false))&next((!(start=true)&btq_state_1_s1=true))))|((btq_state_1_s1=true&hbusreq_0=false)&next((!(start=true)&btq_state_1_s0=true))))|((btq_state_1_s1=true&!(hbusreq_0=false))&next((!(start=true)&btq_state_1_s1=true))))|(btq_state_1_s1=true&next((start=true&(btq_state_1_s0=false&btq_state_1_s1=false)))))|((btq_state_1_s0=false&btq_state_1_s1=false)&next((btq_state_1_s0=false&btq_state_1_s1=false)))))

guarantee(g20_0_monitor_safety).

antecedent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,0,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,1,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,2,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,3,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	holds_at(hburst_single,T2,S),
	holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,4,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,5,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,6,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,7,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,8,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,9,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,10,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,11,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,12,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,13,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,14,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,15,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	not_holds_at(hmastlock,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,16,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,17,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	holds_at(hburst_single,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,18,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,19,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	holds_at(hburst_burst4,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,20,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,21,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,22,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,23,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	not_holds_at(start,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,24,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,25,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_1_s1,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,26,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,27,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s1,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_1_s0,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,28,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,29,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s1,T2,S),
	holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_1_s1,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,30,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,31,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s1,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(btq_state_1_s0,T2,S),
	not_holds_at(btq_state_1_s1,T2,S).

consequent_holds(g20_0_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_0_monitor_safety,0,32,T,S),
	root_consequent_holds(next,g20_0_monitor_safety,0,33,T,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_1_s0,T2,S),
	not_holds_at(btq_state_1_s1,T2,S).

root_consequent_holds(OP,g20_0_monitor_safety,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_1_s0,T2,S),
	not_holds_at(btq_state_1_s1,T2,S).

%guarantee -- g20_0_monitor_justice
%	GF((btq_state_1_s0=true|btq_state_1_s1=true))

guarantee(g20_0_monitor_justice).

antecedent_holds(g20_0_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g20_0_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g20_0_monitor_justice,0,0,T,S).

root_consequent_holds(OP,g20_0_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g20_0_monitor_justice,1,0,T2,S).

root_consequent_holds(OP,g20_0_monitor_justice,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s0,T2,S).

root_consequent_holds(OP,g20_0_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g20_0_monitor_justice,1,1,T2,S).

root_consequent_holds(OP,g20_0_monitor_justice,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_1_s1,T2,S).

%guarantee -- g20_1_monitor_init
%	btq_state_2_s0=true

guarantee(g20_1_monitor_init).

antecedent_holds(g20_1_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(g20_1_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,g20_1_monitor_init,0,0,0,S).

root_consequent_holds(OP,g20_1_monitor_init,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S).

%guarantee -- g20_1_monitor_safety
%	G((((((((((((((((((((btq_state_2_s0=true&!(hmastlock=true))&!(hbusreq_1=false))&next(btq_state_2_s0=true))|(((btq_state_2_s0=true&!(hburst_single=false))&!(hbusreq_1=false))&next(btq_state_2_s0=true)))|(((btq_state_2_s0=true&!(hburst_burst4=false))&!(hbusreq_1=false))&next(btq_state_2_s0=true)))|(((btq_state_2_s0=true&!(hmaster_val1=true))&!(hbusreq_1=false))&next(btq_state_2_s0=true)))|(((btq_state_2_s0=true&!(start=true))&!(hbusreq_1=false))&next(btq_state_2_s0=true)))|((((((btq_state_2_s0=true&hmastlock=true)&hburst_single=false)&hburst_burst4=false)&hmaster_val1=true)&start=true)&next((start=true&btq_state_2_s0=true))))|((btq_state_2_s0=true&hbusreq_1=false)&next((!(start=true)&btq_state_2_s0=true))))|(((btq_state_2_s0=true&!(hmastlock=true))&hbusreq_1=false)&next((start=true&btq_state_2_s0=true))))|(((btq_state_2_s0=true&!(hburst_single=false))&hbusreq_1=false)&next((start=true&btq_state_2_s0=true))))|(((btq_state_2_s0=true&!(hburst_burst4=false))&hbusreq_1=false)&next((start=true&btq_state_2_s0=true))))|(((btq_state_2_s0=true&!(hmaster_val1=true))&hbusreq_1=false)&next((start=true&btq_state_2_s0=true))))|(((btq_state_2_s0=true&!(start=true))&hbusreq_1=false)&next((start=true&btq_state_2_s0=true))))|(((((((btq_state_2_s0=true&hmastlock=true)&hburst_single=false)&hburst_burst4=false)&hmaster_val1=true)&start=true)&!(hbusreq_1=false))&next((!(start=true)&btq_state_2_s1=true))))|((btq_state_2_s1=true&hbusreq_1=false)&next((!(start=true)&btq_state_2_s0=true))))|((btq_state_2_s1=true&!(hbusreq_1=false))&next((!(start=true)&btq_state_2_s1=true))))|(btq_state_2_s1=true&next((start=true&(btq_state_2_s0=false&btq_state_2_s1=false)))))|((btq_state_2_s0=false&btq_state_2_s1=false)&next((btq_state_2_s0=false&btq_state_2_s1=false)))))

guarantee(g20_1_monitor_safety).

antecedent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,0,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,1,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,2,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,3,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	holds_at(hburst_single,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,4,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,5,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,6,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,7,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,8,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,9,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,10,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,11,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,12,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,13,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,14,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,15,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	not_holds_at(hmastlock,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,16,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,17,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	holds_at(hburst_single,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,18,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,19,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	holds_at(hburst_burst4,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,20,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,21,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,22,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,23,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	not_holds_at(start,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,24,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,25,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_2_s1,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,26,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,27,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s1,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_2_s0,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,28,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,29,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s1,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_2_s1,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,30,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,31,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(btq_state_2_s0,T2,S),
	not_holds_at(btq_state_2_s1,T2,S).

consequent_holds(g20_1_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_1_monitor_safety,0,32,T,S),
	root_consequent_holds(next,g20_1_monitor_safety,0,33,T,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_2_s0,T2,S),
	not_holds_at(btq_state_2_s1,T2,S).

root_consequent_holds(OP,g20_1_monitor_safety,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_2_s0,T2,S),
	not_holds_at(btq_state_2_s1,T2,S).

%guarantee -- g20_1_monitor_justice
%	GF((btq_state_2_s0=true|btq_state_2_s1=true))

guarantee(g20_1_monitor_justice).

antecedent_holds(g20_1_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g20_1_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g20_1_monitor_justice,0,0,T,S).

root_consequent_holds(OP,g20_1_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g20_1_monitor_justice,1,0,T2,S).

root_consequent_holds(OP,g20_1_monitor_justice,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s0,T2,S).

root_consequent_holds(OP,g20_1_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g20_1_monitor_justice,1,1,T2,S).

root_consequent_holds(OP,g20_1_monitor_justice,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_2_s1,T2,S).

%guarantee -- g20_2_monitor_init
%	btq_state_3_s0=true

guarantee(g20_2_monitor_init).

antecedent_holds(g20_2_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(g20_2_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,g20_2_monitor_init,0,0,0,S).

root_consequent_holds(OP,g20_2_monitor_init,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

%guarantee -- g20_2_monitor_safety
%	G((((((((((((((((((((((btq_state_3_s0=true&!(hmastlock=true))&!(hbusreq_2=false))&next(btq_state_3_s0=true))|(((btq_state_3_s0=true&!(hburst_single=false))&!(hbusreq_2=false))&next(btq_state_3_s0=true)))|(((btq_state_3_s0=true&!(hburst_burst4=false))&!(hbusreq_2=false))&next(btq_state_3_s0=true)))|(((btq_state_3_s0=true&!(hmaster_val0=false))&!(hbusreq_2=false))&next(btq_state_3_s0=true)))|(((btq_state_3_s0=true&!(hmaster_val1=false))&!(hbusreq_2=false))&next(btq_state_3_s0=true)))|(((btq_state_3_s0=true&!(start=true))&!(hbusreq_2=false))&next(btq_state_3_s0=true)))|(((((((btq_state_3_s0=true&hmastlock=true)&hburst_single=false)&hburst_burst4=false)&hmaster_val0=false)&hmaster_val1=false)&start=true)&next((start=true&btq_state_3_s0=true))))|((btq_state_3_s0=true&hbusreq_2=false)&next((!(start=true)&btq_state_3_s0=true))))|(((btq_state_3_s0=true&!(hmastlock=true))&hbusreq_2=false)&next((start=true&btq_state_3_s0=true))))|(((btq_state_3_s0=true&!(hburst_single=false))&hbusreq_2=false)&next((start=true&btq_state_3_s0=true))))|(((btq_state_3_s0=true&!(hburst_burst4=false))&hbusreq_2=false)&next((start=true&btq_state_3_s0=true))))|(((btq_state_3_s0=true&!(hmaster_val0=false))&hbusreq_2=false)&next((start=true&btq_state_3_s0=true))))|(((btq_state_3_s0=true&!(hmaster_val1=false))&hbusreq_2=false)&next((start=true&btq_state_3_s0=true))))|(((btq_state_3_s0=true&!(start=true))&hbusreq_2=false)&next((start=true&btq_state_3_s0=true))))|((((((((btq_state_3_s0=true&hmastlock=true)&hburst_single=false)&hburst_burst4=false)&hmaster_val0=false)&hmaster_val1=false)&start=true)&!(hbusreq_2=false))&next((!(start=true)&btq_state_3_s1=true))))|((btq_state_3_s1=true&hbusreq_2=false)&next((!(start=true)&btq_state_3_s0=true))))|((btq_state_3_s1=true&!(hbusreq_2=false))&next((!(start=true)&btq_state_3_s1=true))))|(btq_state_3_s1=true&next((start=true&(btq_state_3_s0=false&btq_state_3_s1=false)))))|((btq_state_3_s0=false&btq_state_3_s1=false)&next((btq_state_3_s0=false&btq_state_3_s1=false)))))

guarantee(g20_2_monitor_safety).

antecedent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,0,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,1,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,2,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,3,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hburst_single,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,4,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,5,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,6,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,7,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,8,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,9,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,10,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,11,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,12,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,13,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,14,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,15,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,16,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,17,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	not_holds_at(hmastlock,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,18,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,19,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hburst_single,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,20,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,21,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hburst_burst4,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,22,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,23,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,24,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,25,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,26,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,27,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	not_holds_at(start,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,28,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,29,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S),
	holds_at(hmastlock,T2,S),
	not_holds_at(hburst_single,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_3_s1,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,30,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,31,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s1,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_3_s0,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,32,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,33,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s1,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(btq_state_3_s1,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,34,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,35,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,34,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s1,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,35,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(btq_state_3_s0,T2,S),
	not_holds_at(btq_state_3_s1,T2,S).

consequent_holds(g20_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g20_2_monitor_safety,0,36,T,S),
	root_consequent_holds(next,g20_2_monitor_safety,0,37,T,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,36,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_3_s0,T2,S),
	not_holds_at(btq_state_3_s1,T2,S).

root_consequent_holds(OP,g20_2_monitor_safety,0,37,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_3_s0,T2,S),
	not_holds_at(btq_state_3_s1,T2,S).

%guarantee -- g20_2_monitor_justice
%	GF((btq_state_3_s0=true|btq_state_3_s1=true))

guarantee(g20_2_monitor_justice).

antecedent_holds(g20_2_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g20_2_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g20_2_monitor_justice,0,0,T,S).

root_consequent_holds(OP,g20_2_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g20_2_monitor_justice,1,0,T2,S).

root_consequent_holds(OP,g20_2_monitor_justice,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s0,T2,S).

root_consequent_holds(OP,g20_2_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g20_2_monitor_justice,1,1,T2,S).

root_consequent_holds(OP,g20_2_monitor_justice,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_3_s1,T2,S).

%guarantee -- g30_monitor_init
%	btq_state_4_s0=true

guarantee(g30_monitor_init).

antecedent_holds(g30_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(g30_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,g30_monitor_init,0,0,0,S).

root_consequent_holds(OP,g30_monitor_init,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S).

%guarantee -- g30_monitor_safety
%	G((((((((((((((((((((((((((((((btq_state_4_s0=true&!(hmastlock=true))&next((!(hready_counter_val0=false)&btq_state_4_s0=true)))|((btq_state_4_s0=true&!(hmastlock=true))&next((!(hready_counter_val1=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hmastlock=true))&next((!(hready_counter_val2=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hmastlock=true))&next((!(hready_counter_val3=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hburst_burst4=true))&next((!(hready_counter_val0=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hburst_burst4=true))&next((!(hready_counter_val1=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hburst_burst4=true))&next((!(hready_counter_val2=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hburst_burst4=true))&next((!(hready_counter_val3=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(start=true))&next((!(hready_counter_val0=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(start=true))&next((!(hready_counter_val1=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(start=true))&next((!(hready_counter_val2=false)&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(start=true))&next((!(hready_counter_val3=false)&btq_state_4_s0=true))))|((((btq_state_4_s0=true&hmastlock=true)&hburst_burst4=true)&start=true)&next((start=true&btq_state_4_s0=true))))|(btq_state_4_s0=true&next(((!(start=true)&(((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hmastlock=true))&next(((start=true&(((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(hburst_burst4=true))&next(((start=true&(((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))&btq_state_4_s0=true))))|((btq_state_4_s0=true&!(start=true))&next(((start=true&(((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))&btq_state_4_s0=true))))|((((btq_state_4_s0=true&hmastlock=true)&hburst_burst4=true)&start=true)&next(((!(start=true)&!(hready_counter_val0=false))&btq_state_4_s1=true))))|((((btq_state_4_s0=true&hmastlock=true)&hburst_burst4=true)&start=true)&next(((!(start=true)&!(hready_counter_val1=false))&btq_state_4_s1=true))))|((((btq_state_4_s0=true&hmastlock=true)&hburst_burst4=true)&start=true)&next(((!(start=true)&!(hready_counter_val2=false))&btq_state_4_s1=true))))|((((btq_state_4_s0=true&hmastlock=true)&hburst_burst4=true)&start=true)&next(((!(start=true)&!(hready_counter_val3=false))&btq_state_4_s1=true))))|(btq_state_4_s1=true&next(((!(start=true)&(((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))&btq_state_4_s0=true))))|(btq_state_4_s1=true&next(((!(start=true)&!(hready_counter_val0=false))&btq_state_4_s1=true))))|(btq_state_4_s1=true&next(((!(start=true)&!(hready_counter_val1=false))&btq_state_4_s1=true))))|(btq_state_4_s1=true&next(((!(start=true)&!(hready_counter_val2=false))&btq_state_4_s1=true))))|(btq_state_4_s1=true&next(((!(start=true)&!(hready_counter_val3=false))&btq_state_4_s1=true))))|(btq_state_4_s1=true&next((start=true&(btq_state_4_s0=false&btq_state_4_s1=false)))))|((btq_state_4_s0=false&btq_state_4_s1=false)&next((btq_state_4_s0=false&btq_state_4_s1=false)))))

guarantee(g30_monitor_safety).

antecedent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,0,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,1,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hmastlock,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,2,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,3,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hmastlock,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,4,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,5,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hmastlock,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val2,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,6,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,7,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hmastlock,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,8,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,9,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hburst_burst4,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,10,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,11,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hburst_burst4,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,12,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,13,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hburst_burst4,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val2,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,14,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,15,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hburst_burst4,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,16,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,17,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,18,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,19,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,20,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,21,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val2,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,22,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,23,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,24,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,25,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	holds_at(hmastlock,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,26,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,27,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,28,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,29,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hmastlock,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,30,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,31,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(hburst_burst4,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,32,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,33,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	not_holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,34,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,35,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,34,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	holds_at(hmastlock,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,35,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val0,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,36,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,37,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,36,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	holds_at(hmastlock,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,37,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,38,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,39,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,38,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	holds_at(hmastlock,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,39,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val2,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,40,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,41,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,40,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S),
	holds_at(hmastlock,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(start,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,41,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,42,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,43,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,42,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,43,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s0,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,44,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,45,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,44,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,45,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val0,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,46,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,47,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,46,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,47,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,48,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,49,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,48,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,49,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val2,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,50,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,51,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,50,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,51,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready_counter_val3,T2,S),
	holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,52,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,53,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,52,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,53,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(btq_state_4_s0,T2,S),
	not_holds_at(btq_state_4_s1,T2,S).

consequent_holds(g30_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g30_monitor_safety,0,54,T,S),
	root_consequent_holds(next,g30_monitor_safety,0,55,T,S).

root_consequent_holds(OP,g30_monitor_safety,0,54,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_4_s0,T2,S),
	not_holds_at(btq_state_4_s1,T2,S).

root_consequent_holds(OP,g30_monitor_safety,0,55,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_4_s0,T2,S),
	not_holds_at(btq_state_4_s1,T2,S).

%guarantee -- g30_monitor_justice
%	GF((btq_state_4_s0=true|btq_state_4_s1=true))

guarantee(g30_monitor_justice).

antecedent_holds(g30_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g30_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g30_monitor_justice,0,0,T,S).

root_consequent_holds(OP,g30_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g30_monitor_justice,1,0,T2,S).

root_consequent_holds(OP,g30_monitor_justice,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s0,T2,S).

root_consequent_holds(OP,g30_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g30_monitor_justice,1,1,T2,S).

root_consequent_holds(OP,g30_monitor_justice,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_4_s1,T2,S).

%guarantee -- g40
%	G((((((((((((((((((((((((((((((((((((((!(hready=true)&!(hready=true))&!(hready=true))|(((!(hready=true)&!(hready=true))&hgrant_2=true)&next((hmaster_val0=false&hmaster_val1=false))))|(((!(hready=true)&!(hready=true))&!(hgrant_2=true))&next(!(hmaster_val0=false))))|(((!(hready=true)&!(hready=true))&!(hgrant_2=true))&next(!(hmaster_val1=false))))|(((!(hready=true)&hgrant_1=true)&!(hready=true))&next(hmaster_val1=true)))|(((!(hready=true)&hgrant_1=true)&hgrant_2=true)&next((hmaster_val1=true&(hmaster_val0=false&hmaster_val1=false)))))|(((!(hready=true)&hgrant_1=true)&!(hgrant_2=true))&next((hmaster_val1=true&!(hmaster_val0=false)))))|(((!(hready=true)&hgrant_1=true)&!(hgrant_2=true))&next((hmaster_val1=true&!(hmaster_val1=false)))))|(((!(hready=true)&!(hgrant_1=true))&!(hready=true))&next(!(hmaster_val1=true))))|(((!(hready=true)&!(hgrant_1=true))&hgrant_2=true)&next((!(hmaster_val1=true)&(hmaster_val0=false&hmaster_val1=false)))))|(((!(hready=true)&!(hgrant_1=true))&!(hgrant_2=true))&next((!(hmaster_val1=true)&!(hmaster_val0=false)))))|(((!(hready=true)&!(hgrant_1=true))&!(hgrant_2=true))&next((!(hmaster_val1=true)&!(hmaster_val1=false)))))|(((hgrant_0=true&!(hready=true))&!(hready=true))&next(hmaster_val0=true)))|(((hgrant_0=true&!(hready=true))&hgrant_2=true)&next((hmaster_val0=true&(hmaster_val0=false&hmaster_val1=false)))))|(((hgrant_0=true&!(hready=true))&!(hgrant_2=true))&next((hmaster_val0=true&!(hmaster_val0=false)))))|(((hgrant_0=true&!(hready=true))&!(hgrant_2=true))&next((hmaster_val0=true&!(hmaster_val1=false)))))|(((hgrant_0=true&hgrant_1=true)&!(hready=true))&next((hmaster_val0=true&hmaster_val1=true))))|(((hgrant_0=true&hgrant_1=true)&hgrant_2=true)&next(((hmaster_val0=true&hmaster_val1=true)&(hmaster_val0=false&hmaster_val1=false)))))|(((hgrant_0=true&hgrant_1=true)&!(hgrant_2=true))&next(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val0=false)))))|(((hgrant_0=true&hgrant_1=true)&!(hgrant_2=true))&next(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val1=false)))))|(((hgrant_0=true&!(hgrant_1=true))&!(hready=true))&next((hmaster_val0=true&!(hmaster_val1=true)))))|(((hgrant_0=true&!(hgrant_1=true))&hgrant_2=true)&next(((hmaster_val0=true&!(hmaster_val1=true))&(hmaster_val0=false&hmaster_val1=false)))))|(((hgrant_0=true&!(hgrant_1=true))&!(hgrant_2=true))&next(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val0=false)))))|(((hgrant_0=true&!(hgrant_1=true))&!(hgrant_2=true))&next(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val1=false)))))|(((!(hgrant_0=true)&!(hready=true))&!(hready=true))&next(!(hmaster_val0=true))))|(((!(hgrant_0=true)&!(hready=true))&hgrant_2=true)&next((!(hmaster_val0=true)&(hmaster_val0=false&hmaster_val1=false)))))|(((!(hgrant_0=true)&!(hready=true))&!(hgrant_2=true))&next((!(hmaster_val0=true)&!(hmaster_val0=false)))))|(((!(hgrant_0=true)&!(hready=true))&!(hgrant_2=true))&next((!(hmaster_val0=true)&!(hmaster_val1=false)))))|(((!(hgrant_0=true)&hgrant_1=true)&!(hready=true))&next((!(hmaster_val0=true)&hmaster_val1=true))))|(((!(hgrant_0=true)&hgrant_1=true)&hgrant_2=true)&next(((!(hmaster_val0=true)&hmaster_val1=true)&(hmaster_val0=false&hmaster_val1=false)))))|(((!(hgrant_0=true)&hgrant_1=true)&!(hgrant_2=true))&next(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val0=false)))))|(((!(hgrant_0=true)&hgrant_1=true)&!(hgrant_2=true))&next(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val1=false)))))|(((!(hgrant_0=true)&!(hgrant_1=true))&!(hready=true))&next((!(hmaster_val0=true)&!(hmaster_val1=true)))))|(((!(hgrant_0=true)&!(hgrant_1=true))&hgrant_2=true)&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&(hmaster_val0=false&hmaster_val1=false)))))|(((!(hgrant_0=true)&!(hgrant_1=true))&!(hgrant_2=true))&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val0=false)))))|(((!(hgrant_0=true)&!(hgrant_1=true))&!(hgrant_2=true))&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val1=false))))))

guarantee(g40).

antecedent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,0,T,S).

root_consequent_holds(OP,g40,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hready,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,1,T,S),
	root_consequent_holds(next,g40,0,2,T,S).

root_consequent_holds(OP,g40,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hready,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,3,T,S),
	root_consequent_holds(next,g40,0,4,T,S).

root_consequent_holds(OP,g40,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,5,T,S),
	root_consequent_holds(next,g40,0,6,T,S).

root_consequent_holds(OP,g40,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,7,T,S),
	root_consequent_holds(next,g40,0,8,T,S).

root_consequent_holds(OP,g40,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,9,T,S),
	root_consequent_holds(next,g40,0,10,T,S).

root_consequent_holds(OP,g40,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,11,T,S),
	root_consequent_holds(next,g40,0,12,T,S).

root_consequent_holds(OP,g40,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,13,T,S),
	root_consequent_holds(next,g40,0,14,T,S).

root_consequent_holds(OP,g40,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,15,T,S),
	root_consequent_holds(next,g40,0,16,T,S).

root_consequent_holds(OP,g40,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,17,T,S),
	root_consequent_holds(next,g40,0,18,T,S).

root_consequent_holds(OP,g40,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,19,T,S),
	root_consequent_holds(next,g40,0,20,T,S).

root_consequent_holds(OP,g40,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,21,T,S),
	root_consequent_holds(next,g40,0,22,T,S).

root_consequent_holds(OP,g40,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,23,T,S),
	root_consequent_holds(next,g40,0,24,T,S).

root_consequent_holds(OP,g40,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,25,T,S),
	root_consequent_holds(next,g40,0,26,T,S).

root_consequent_holds(OP,g40,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,27,T,S),
	root_consequent_holds(next,g40,0,28,T,S).

root_consequent_holds(OP,g40,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,29,T,S),
	root_consequent_holds(next,g40,0,30,T,S).

root_consequent_holds(OP,g40,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,31,T,S),
	root_consequent_holds(next,g40,0,32,T,S).

root_consequent_holds(OP,g40,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,33,T,S),
	root_consequent_holds(next,g40,0,34,T,S).

root_consequent_holds(OP,g40,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,34,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,35,T,S),
	root_consequent_holds(next,g40,0,36,T,S).

root_consequent_holds(OP,g40,0,35,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,36,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,37,T,S),
	root_consequent_holds(next,g40,0,38,T,S).

root_consequent_holds(OP,g40,0,37,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,38,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,39,T,S),
	root_consequent_holds(next,g40,0,40,T,S).

root_consequent_holds(OP,g40,0,39,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,40,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,41,T,S),
	root_consequent_holds(next,g40,0,42,T,S).

root_consequent_holds(OP,g40,0,41,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,42,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,43,T,S),
	root_consequent_holds(next,g40,0,44,T,S).

root_consequent_holds(OP,g40,0,43,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,44,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,45,T,S),
	root_consequent_holds(next,g40,0,46,T,S).

root_consequent_holds(OP,g40,0,45,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,46,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,47,T,S),
	root_consequent_holds(next,g40,0,48,T,S).

root_consequent_holds(OP,g40,0,47,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,48,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,49,T,S),
	root_consequent_holds(next,g40,0,50,T,S).

root_consequent_holds(OP,g40,0,49,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,50,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,51,T,S),
	root_consequent_holds(next,g40,0,52,T,S).

root_consequent_holds(OP,g40,0,51,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,52,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,53,T,S),
	root_consequent_holds(next,g40,0,54,T,S).

root_consequent_holds(OP,g40,0,53,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hready,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,54,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,55,T,S),
	root_consequent_holds(next,g40,0,56,T,S).

root_consequent_holds(OP,g40,0,55,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,56,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,57,T,S),
	root_consequent_holds(next,g40,0,58,T,S).

root_consequent_holds(OP,g40,0,57,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,58,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,59,T,S),
	root_consequent_holds(next,g40,0,60,T,S).

root_consequent_holds(OP,g40,0,59,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,60,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,61,T,S),
	root_consequent_holds(next,g40,0,62,T,S).

root_consequent_holds(OP,g40,0,61,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,62,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,63,T,S),
	root_consequent_holds(next,g40,0,64,T,S).

root_consequent_holds(OP,g40,0,63,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hready,T2,S).

root_consequent_holds(OP,g40,0,64,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,65,T,S),
	root_consequent_holds(next,g40,0,66,T,S).

root_consequent_holds(OP,g40,0,65,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,66,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,67,T,S),
	root_consequent_holds(next,g40,0,68,T,S).

root_consequent_holds(OP,g40,0,67,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,68,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g40,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g40,0,69,T,S),
	root_consequent_holds(next,g40,0,70,T,S).

root_consequent_holds(OP,g40,0,69,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g40,0,70,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

%guarantee -- g50
%	G((hready=true->((locked=true&next(hmastlock=true))|(!(locked=true)&next(!(hmastlock=true))))))

guarantee(g50).

antecedent_holds(g50,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,g50,0,T,S).

root_antecedent_holds(OP,g50,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready,T2,S).

consequent_holds(g50,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g50,0,0,T,S),
	root_consequent_holds(next,g50,0,1,T,S).

root_consequent_holds(OP,g50,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S).

root_consequent_holds(OP,g50,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S).

consequent_holds(g50,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g50,0,2,T,S),
	root_consequent_holds(next,g50,0,3,T,S).

root_consequent_holds(OP,g50,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S).

root_consequent_holds(OP,g50,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S).

%guarantee -- g60
%	G((((((((((((((((((((((((((((((((((((((((((((((((((((((next(((!(start=false)&!(start=false))&!(start=false)))|((hmaster_val0=false&hmaster_val1=false)&next(((!(start=false)&!(start=false))&(hmaster_val0=false&hmaster_val1=false)))))|(!(hmaster_val0=false)&next(((!(start=false)&!(start=false))&!(hmaster_val0=false)))))|(!(hmaster_val0=false)&next(((!(start=false)&!(start=false))&!(hmaster_val1=false)))))|(!(hmaster_val1=false)&next(((!(start=false)&!(start=false))&!(hmaster_val0=false)))))|(!(hmaster_val1=false)&next(((!(start=false)&!(start=false))&!(hmaster_val1=false)))))|(hmaster_val1=true&next(((!(start=false)&hmaster_val1=true)&!(start=false)))))|(((hmaster_val1=true&hmaster_val0=false)&hmaster_val1=false)&next(((!(start=false)&hmaster_val1=true)&(hmaster_val0=false&hmaster_val1=false)))))|((hmaster_val1=true&!(hmaster_val0=false))&next(((!(start=false)&hmaster_val1=true)&!(hmaster_val0=false)))))|((hmaster_val1=true&!(hmaster_val0=false))&next(((!(start=false)&hmaster_val1=true)&!(hmaster_val1=false)))))|((hmaster_val1=true&!(hmaster_val1=false))&next(((!(start=false)&hmaster_val1=true)&!(hmaster_val0=false)))))|((hmaster_val1=true&!(hmaster_val1=false))&next(((!(start=false)&hmaster_val1=true)&!(hmaster_val1=false)))))|(!(hmaster_val1=true)&next(((!(start=false)&!(hmaster_val1=true))&!(start=false)))))|(((!(hmaster_val1=true)&hmaster_val0=false)&hmaster_val1=false)&next(((!(start=false)&!(hmaster_val1=true))&(hmaster_val0=false&hmaster_val1=false)))))|((!(hmaster_val1=true)&!(hmaster_val0=false))&next(((!(start=false)&!(hmaster_val1=true))&!(hmaster_val0=false)))))|((!(hmaster_val1=true)&!(hmaster_val0=false))&next(((!(start=false)&!(hmaster_val1=true))&!(hmaster_val1=false)))))|((!(hmaster_val1=true)&!(hmaster_val1=false))&next(((!(start=false)&!(hmaster_val1=true))&!(hmaster_val0=false)))))|((!(hmaster_val1=true)&!(hmaster_val1=false))&next(((!(start=false)&!(hmaster_val1=true))&!(hmaster_val1=false)))))|(hmaster_val0=true&next(((hmaster_val0=true&!(start=false))&!(start=false)))))|(((hmaster_val0=true&hmaster_val0=false)&hmaster_val1=false)&next(((hmaster_val0=true&!(start=false))&(hmaster_val0=false&hmaster_val1=false)))))|((hmaster_val0=true&!(hmaster_val0=false))&next(((hmaster_val0=true&!(start=false))&!(hmaster_val0=false)))))|((hmaster_val0=true&!(hmaster_val0=false))&next(((hmaster_val0=true&!(start=false))&!(hmaster_val1=false)))))|((hmaster_val0=true&!(hmaster_val1=false))&next(((hmaster_val0=true&!(start=false))&!(hmaster_val0=false)))))|((hmaster_val0=true&!(hmaster_val1=false))&next(((hmaster_val0=true&!(start=false))&!(hmaster_val1=false)))))|((hmaster_val0=true&hmaster_val1=true)&next(((hmaster_val0=true&hmaster_val1=true)&!(start=false)))))|((((hmaster_val0=true&hmaster_val1=true)&hmaster_val0=false)&hmaster_val1=false)&next(((hmaster_val0=true&hmaster_val1=true)&(hmaster_val0=false&hmaster_val1=false)))))|(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val0=false))&next(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val0=false)))))|(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val0=false))&next(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val1=false)))))|(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val1=false))&next(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val0=false)))))|(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val1=false))&next(((hmaster_val0=true&hmaster_val1=true)&!(hmaster_val1=false)))))|((hmaster_val0=true&!(hmaster_val1=true))&next(((hmaster_val0=true&!(hmaster_val1=true))&!(start=false)))))|((((hmaster_val0=true&!(hmaster_val1=true))&hmaster_val0=false)&hmaster_val1=false)&next(((hmaster_val0=true&!(hmaster_val1=true))&(hmaster_val0=false&hmaster_val1=false)))))|(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val0=false))&next(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val0=false)))))|(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val0=false))&next(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val1=false)))))|(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val1=false))&next(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val0=false)))))|(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val1=false))&next(((hmaster_val0=true&!(hmaster_val1=true))&!(hmaster_val1=false)))))|(!(hmaster_val0=true)&next(((!(hmaster_val0=true)&!(start=false))&!(start=false)))))|(((!(hmaster_val0=true)&hmaster_val0=false)&hmaster_val1=false)&next(((!(hmaster_val0=true)&!(start=false))&(hmaster_val0=false&hmaster_val1=false)))))|((!(hmaster_val0=true)&!(hmaster_val0=false))&next(((!(hmaster_val0=true)&!(start=false))&!(hmaster_val0=false)))))|((!(hmaster_val0=true)&!(hmaster_val0=false))&next(((!(hmaster_val0=true)&!(start=false))&!(hmaster_val1=false)))))|((!(hmaster_val0=true)&!(hmaster_val1=false))&next(((!(hmaster_val0=true)&!(start=false))&!(hmaster_val0=false)))))|((!(hmaster_val0=true)&!(hmaster_val1=false))&next(((!(hmaster_val0=true)&!(start=false))&!(hmaster_val1=false)))))|((!(hmaster_val0=true)&hmaster_val1=true)&next(((!(hmaster_val0=true)&hmaster_val1=true)&!(start=false)))))|((((!(hmaster_val0=true)&hmaster_val1=true)&hmaster_val0=false)&hmaster_val1=false)&next(((!(hmaster_val0=true)&hmaster_val1=true)&(hmaster_val0=false&hmaster_val1=false)))))|(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val0=false))&next(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val0=false)))))|(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val0=false))&next(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val1=false)))))|(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val1=false))&next(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val0=false)))))|(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val1=false))&next(((!(hmaster_val0=true)&hmaster_val1=true)&!(hmaster_val1=false)))))|((!(hmaster_val0=true)&!(hmaster_val1=true))&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(start=false)))))|((((!(hmaster_val0=true)&!(hmaster_val1=true))&hmaster_val0=false)&hmaster_val1=false)&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&(hmaster_val0=false&hmaster_val1=false)))))|(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val0=false))&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val0=false)))))|(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val0=false))&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val1=false)))))|(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val1=false))&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val0=false)))))|(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val1=false))&next(((!(hmaster_val0=true)&!(hmaster_val1=true))&!(hmaster_val1=false))))))

guarantee(g60).

antecedent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,g60,0,0,T,S).

root_consequent_holds(OP,g60,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,1,T,S),
	root_consequent_holds(next,g60,0,2,T,S).

root_consequent_holds(OP,g60,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,3,T,S),
	root_consequent_holds(next,g60,0,4,T,S).

root_consequent_holds(OP,g60,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,5,T,S),
	root_consequent_holds(next,g60,0,6,T,S).

root_consequent_holds(OP,g60,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,7,T,S),
	root_consequent_holds(next,g60,0,8,T,S).

root_consequent_holds(OP,g60,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,9,T,S),
	root_consequent_holds(next,g60,0,10,T,S).

root_consequent_holds(OP,g60,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,11,T,S),
	root_consequent_holds(next,g60,0,12,T,S).

root_consequent_holds(OP,g60,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,13,T,S),
	root_consequent_holds(next,g60,0,14,T,S).

root_consequent_holds(OP,g60,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,15,T,S),
	root_consequent_holds(next,g60,0,16,T,S).

root_consequent_holds(OP,g60,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,17,T,S),
	root_consequent_holds(next,g60,0,18,T,S).

root_consequent_holds(OP,g60,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,19,T,S),
	root_consequent_holds(next,g60,0,20,T,S).

root_consequent_holds(OP,g60,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,21,T,S),
	root_consequent_holds(next,g60,0,22,T,S).

root_consequent_holds(OP,g60,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,23,T,S),
	root_consequent_holds(next,g60,0,24,T,S).

root_consequent_holds(OP,g60,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,25,T,S),
	root_consequent_holds(next,g60,0,26,T,S).

root_consequent_holds(OP,g60,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,27,T,S),
	root_consequent_holds(next,g60,0,28,T,S).

root_consequent_holds(OP,g60,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,29,T,S),
	root_consequent_holds(next,g60,0,30,T,S).

root_consequent_holds(OP,g60,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,31,T,S),
	root_consequent_holds(next,g60,0,32,T,S).

root_consequent_holds(OP,g60,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,33,T,S),
	root_consequent_holds(next,g60,0,34,T,S).

root_consequent_holds(OP,g60,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,34,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,35,T,S),
	root_consequent_holds(next,g60,0,36,T,S).

root_consequent_holds(OP,g60,0,35,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,36,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,37,T,S),
	root_consequent_holds(next,g60,0,38,T,S).

root_consequent_holds(OP,g60,0,37,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,38,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,39,T,S),
	root_consequent_holds(next,g60,0,40,T,S).

root_consequent_holds(OP,g60,0,39,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,40,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,41,T,S),
	root_consequent_holds(next,g60,0,42,T,S).

root_consequent_holds(OP,g60,0,41,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,42,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,43,T,S),
	root_consequent_holds(next,g60,0,44,T,S).

root_consequent_holds(OP,g60,0,43,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,44,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,45,T,S),
	root_consequent_holds(next,g60,0,46,T,S).

root_consequent_holds(OP,g60,0,45,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,46,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,47,T,S),
	root_consequent_holds(next,g60,0,48,T,S).

root_consequent_holds(OP,g60,0,47,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,48,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,49,T,S),
	root_consequent_holds(next,g60,0,50,T,S).

root_consequent_holds(OP,g60,0,49,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,50,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,51,T,S),
	root_consequent_holds(next,g60,0,52,T,S).

root_consequent_holds(OP,g60,0,51,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,52,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,53,T,S),
	root_consequent_holds(next,g60,0,54,T,S).

root_consequent_holds(OP,g60,0,53,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,54,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,55,T,S),
	root_consequent_holds(next,g60,0,56,T,S).

root_consequent_holds(OP,g60,0,55,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,56,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,57,T,S),
	root_consequent_holds(next,g60,0,58,T,S).

root_consequent_holds(OP,g60,0,57,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,58,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,59,T,S),
	root_consequent_holds(next,g60,0,60,T,S).

root_consequent_holds(OP,g60,0,59,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,60,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,61,T,S),
	root_consequent_holds(next,g60,0,62,T,S).

root_consequent_holds(OP,g60,0,61,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,62,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,63,T,S),
	root_consequent_holds(next,g60,0,64,T,S).

root_consequent_holds(OP,g60,0,63,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,64,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,65,T,S),
	root_consequent_holds(next,g60,0,66,T,S).

root_consequent_holds(OP,g60,0,65,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,66,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,67,T,S),
	root_consequent_holds(next,g60,0,68,T,S).

root_consequent_holds(OP,g60,0,67,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,68,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,69,T,S),
	root_consequent_holds(next,g60,0,70,T,S).

root_consequent_holds(OP,g60,0,69,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,70,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,71,T,S),
	root_consequent_holds(next,g60,0,72,T,S).

root_consequent_holds(OP,g60,0,71,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,72,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,73,T,S),
	root_consequent_holds(next,g60,0,74,T,S).

root_consequent_holds(OP,g60,0,73,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,74,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,75,T,S),
	root_consequent_holds(next,g60,0,76,T,S).

root_consequent_holds(OP,g60,0,75,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,76,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,77,T,S),
	root_consequent_holds(next,g60,0,78,T,S).

root_consequent_holds(OP,g60,0,77,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,78,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,79,T,S),
	root_consequent_holds(next,g60,0,80,T,S).

root_consequent_holds(OP,g60,0,79,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,80,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,81,T,S),
	root_consequent_holds(next,g60,0,82,T,S).

root_consequent_holds(OP,g60,0,81,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,82,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(start,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,83,T,S),
	root_consequent_holds(next,g60,0,84,T,S).

root_consequent_holds(OP,g60,0,83,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,84,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,85,T,S),
	root_consequent_holds(next,g60,0,86,T,S).

root_consequent_holds(OP,g60,0,85,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,86,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,87,T,S),
	root_consequent_holds(next,g60,0,88,T,S).

root_consequent_holds(OP,g60,0,87,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,88,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,89,T,S),
	root_consequent_holds(next,g60,0,90,T,S).

root_consequent_holds(OP,g60,0,89,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,90,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,91,T,S),
	root_consequent_holds(next,g60,0,92,T,S).

root_consequent_holds(OP,g60,0,91,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,92,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,93,T,S),
	root_consequent_holds(next,g60,0,94,T,S).

root_consequent_holds(OP,g60,0,93,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,94,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,95,T,S),
	root_consequent_holds(next,g60,0,96,T,S).

root_consequent_holds(OP,g60,0,95,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,96,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(start,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,97,T,S),
	root_consequent_holds(next,g60,0,98,T,S).

root_consequent_holds(OP,g60,0,97,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,98,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,99,T,S),
	root_consequent_holds(next,g60,0,100,T,S).

root_consequent_holds(OP,g60,0,99,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,100,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,101,T,S),
	root_consequent_holds(next,g60,0,102,T,S).

root_consequent_holds(OP,g60,0,101,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

root_consequent_holds(OP,g60,0,102,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,103,T,S),
	root_consequent_holds(next,g60,0,104,T,S).

root_consequent_holds(OP,g60,0,103,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,104,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val0,T2,S).

consequent_holds(g60,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g60,0,105,T,S),
	root_consequent_holds(next,g60,0,106,T,S).

root_consequent_holds(OP,g60,0,105,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

root_consequent_holds(OP,g60,0,106,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S),
	holds_at(hmaster_val1,T2,S).

%guarantee -- g64
%	G((next(start=false)->((hmastlock=true&next(hmastlock=true))|(!(hmastlock=true)&next(!(hmastlock=true))))))

guarantee(g64).

antecedent_holds(g64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(next,g64,0,T,S).

root_antecedent_holds(OP,g64,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S).

consequent_holds(g64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g64,0,0,T,S),
	root_consequent_holds(next,g64,0,1,T,S).

root_consequent_holds(OP,g64,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S).

root_consequent_holds(OP,g64,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S).

consequent_holds(g64,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g64,0,2,T,S),
	root_consequent_holds(next,g64,0,3,T,S).

root_consequent_holds(OP,g64,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S).

root_consequent_holds(OP,g64,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S).

%guarantee -- g70
%	G((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((!(decide=true)&!(decide=true))&!(decide=true))|((!(decide=true)&!(decide=true))&next(!(hgrant_2=true))))|(((!(decide=true)&!(decide=true))&hlock_2=true)&next(locked=true)))|(((!(decide=true)&!(decide=true))&!(hlock_2=true))&next(!(locked=true))))|((!(decide=true)&!(decide=true))&next(!(hgrant_1=true))))|(!(decide=true)&next((!(hgrant_1=true)&!(hgrant_2=true)))))|((!(decide=true)&hlock_2=true)&next((!(hgrant_1=true)&locked=true))))|((!(decide=true)&!(hlock_2=true))&next((!(hgrant_1=true)&!(locked=true)))))|(((!(decide=true)&hlock_1=true)&!(decide=true))&next(locked=true)))|((!(decide=true)&hlock_1=true)&next((locked=true&!(hgrant_2=true)))))|(((!(decide=true)&hlock_1=true)&hlock_2=true)&next((locked=true&locked=true))))|(((!(decide=true)&hlock_1=true)&!(hlock_2=true))&next((locked=true&!(locked=true)))))|(((!(decide=true)&!(hlock_1=true))&!(decide=true))&next(!(locked=true))))|((!(decide=true)&!(hlock_1=true))&next((!(locked=true)&!(hgrant_2=true)))))|(((!(decide=true)&!(hlock_1=true))&hlock_2=true)&next((!(locked=true)&locked=true))))|(((!(decide=true)&!(hlock_1=true))&!(hlock_2=true))&next((!(locked=true)&!(locked=true)))))|((!(decide=true)&!(decide=true))&next(!(hgrant_0=true))))|(!(decide=true)&next((!(hgrant_0=true)&!(hgrant_2=true)))))|((!(decide=true)&hlock_2=true)&next((!(hgrant_0=true)&locked=true))))|((!(decide=true)&!(hlock_2=true))&next((!(hgrant_0=true)&!(locked=true)))))|(!(decide=true)&next((!(hgrant_0=true)&!(hgrant_1=true)))))|next(((!(hgrant_0=true)&!(hgrant_1=true))&!(hgrant_2=true))))|(hlock_2=true&next(((!(hgrant_0=true)&!(hgrant_1=true))&locked=true))))|(!(hlock_2=true)&next(((!(hgrant_0=true)&!(hgrant_1=true))&!(locked=true)))))|((hlock_1=true&!(decide=true))&next((!(hgrant_0=true)&locked=true))))|(hlock_1=true&next(((!(hgrant_0=true)&locked=true)&!(hgrant_2=true)))))|((hlock_1=true&hlock_2=true)&next(((!(hgrant_0=true)&locked=true)&locked=true))))|((hlock_1=true&!(hlock_2=true))&next(((!(hgrant_0=true)&locked=true)&!(locked=true)))))|((!(hlock_1=true)&!(decide=true))&next((!(hgrant_0=true)&!(locked=true)))))|(!(hlock_1=true)&next(((!(hgrant_0=true)&!(locked=true))&!(hgrant_2=true)))))|((!(hlock_1=true)&hlock_2=true)&next(((!(hgrant_0=true)&!(locked=true))&locked=true))))|((!(hlock_1=true)&!(hlock_2=true))&next(((!(hgrant_0=true)&!(locked=true))&!(locked=true)))))|(((hlock_0=true&!(decide=true))&!(decide=true))&next(locked=true)))|((hlock_0=true&!(decide=true))&next((locked=true&!(hgrant_2=true)))))|(((hlock_0=true&!(decide=true))&hlock_2=true)&next((locked=true&locked=true))))|(((hlock_0=true&!(decide=true))&!(hlock_2=true))&next((locked=true&!(locked=true)))))|((hlock_0=true&!(decide=true))&next((locked=true&!(hgrant_1=true)))))|(hlock_0=true&next(((locked=true&!(hgrant_1=true))&!(hgrant_2=true)))))|((hlock_0=true&hlock_2=true)&next(((locked=true&!(hgrant_1=true))&locked=true))))|((hlock_0=true&!(hlock_2=true))&next(((locked=true&!(hgrant_1=true))&!(locked=true)))))|(((hlock_0=true&hlock_1=true)&!(decide=true))&next((locked=true&locked=true))))|((hlock_0=true&hlock_1=true)&next(((locked=true&locked=true)&!(hgrant_2=true)))))|(((hlock_0=true&hlock_1=true)&hlock_2=true)&next(((locked=true&locked=true)&locked=true))))|(((hlock_0=true&hlock_1=true)&!(hlock_2=true))&next(((locked=true&locked=true)&!(locked=true)))))|(((hlock_0=true&!(hlock_1=true))&!(decide=true))&next((locked=true&!(locked=true)))))|((hlock_0=true&!(hlock_1=true))&next(((locked=true&!(locked=true))&!(hgrant_2=true)))))|(((hlock_0=true&!(hlock_1=true))&hlock_2=true)&next(((locked=true&!(locked=true))&locked=true))))|(((hlock_0=true&!(hlock_1=true))&!(hlock_2=true))&next(((locked=true&!(locked=true))&!(locked=true)))))|(((!(hlock_0=true)&!(decide=true))&!(decide=true))&next(!(locked=true))))|((!(hlock_0=true)&!(decide=true))&next((!(locked=true)&!(hgrant_2=true)))))|(((!(hlock_0=true)&!(decide=true))&hlock_2=true)&next((!(locked=true)&locked=true))))|(((!(hlock_0=true)&!(decide=true))&!(hlock_2=true))&next((!(locked=true)&!(locked=true)))))|((!(hlock_0=true)&!(decide=true))&next((!(locked=true)&!(hgrant_1=true)))))|(!(hlock_0=true)&next(((!(locked=true)&!(hgrant_1=true))&!(hgrant_2=true)))))|((!(hlock_0=true)&hlock_2=true)&next(((!(locked=true)&!(hgrant_1=true))&locked=true))))|((!(hlock_0=true)&!(hlock_2=true))&next(((!(locked=true)&!(hgrant_1=true))&!(locked=true)))))|(((!(hlock_0=true)&hlock_1=true)&!(decide=true))&next((!(locked=true)&locked=true))))|((!(hlock_0=true)&hlock_1=true)&next(((!(locked=true)&locked=true)&!(hgrant_2=true)))))|(((!(hlock_0=true)&hlock_1=true)&hlock_2=true)&next(((!(locked=true)&locked=true)&locked=true))))|(((!(hlock_0=true)&hlock_1=true)&!(hlock_2=true))&next(((!(locked=true)&locked=true)&!(locked=true)))))|(((!(hlock_0=true)&!(hlock_1=true))&!(decide=true))&next((!(locked=true)&!(locked=true)))))|((!(hlock_0=true)&!(hlock_1=true))&next(((!(locked=true)&!(locked=true))&!(hgrant_2=true)))))|(((!(hlock_0=true)&!(hlock_1=true))&hlock_2=true)&next(((!(locked=true)&!(locked=true))&locked=true))))|(((!(hlock_0=true)&!(hlock_1=true))&!(hlock_2=true))&next(((!(locked=true)&!(locked=true))&!(locked=true))))))

guarantee(g70).

antecedent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,0,T,S).

root_consequent_holds(OP,g70,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,1,T,S),
	root_consequent_holds(next,g70,0,2,T,S).

root_consequent_holds(OP,g70,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,3,T,S),
	root_consequent_holds(next,g70,0,4,T,S).

root_consequent_holds(OP,g70,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,5,T,S),
	root_consequent_holds(next,g70,0,6,T,S).

root_consequent_holds(OP,g70,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,7,T,S),
	root_consequent_holds(next,g70,0,8,T,S).

root_consequent_holds(OP,g70,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,9,T,S),
	root_consequent_holds(next,g70,0,10,T,S).

root_consequent_holds(OP,g70,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,11,T,S),
	root_consequent_holds(next,g70,0,12,T,S).

root_consequent_holds(OP,g70,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,13,T,S),
	root_consequent_holds(next,g70,0,14,T,S).

root_consequent_holds(OP,g70,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,15,T,S),
	root_consequent_holds(next,g70,0,16,T,S).

root_consequent_holds(OP,g70,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,17,T,S),
	root_consequent_holds(next,g70,0,18,T,S).

root_consequent_holds(OP,g70,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,19,T,S),
	root_consequent_holds(next,g70,0,20,T,S).

root_consequent_holds(OP,g70,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,21,T,S),
	root_consequent_holds(next,g70,0,22,T,S).

root_consequent_holds(OP,g70,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,23,T,S),
	root_consequent_holds(next,g70,0,24,T,S).

root_consequent_holds(OP,g70,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,25,T,S),
	root_consequent_holds(next,g70,0,26,T,S).

root_consequent_holds(OP,g70,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,27,T,S),
	root_consequent_holds(next,g70,0,28,T,S).

root_consequent_holds(OP,g70,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,29,T,S),
	root_consequent_holds(next,g70,0,30,T,S).

root_consequent_holds(OP,g70,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,31,T,S),
	root_consequent_holds(next,g70,0,32,T,S).

root_consequent_holds(OP,g70,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,33,T,S),
	root_consequent_holds(next,g70,0,34,T,S).

root_consequent_holds(OP,g70,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,34,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,35,T,S),
	root_consequent_holds(next,g70,0,36,T,S).

root_consequent_holds(OP,g70,0,35,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,36,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,37,T,S),
	root_consequent_holds(next,g70,0,38,T,S).

root_consequent_holds(OP,g70,0,37,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,38,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,39,T,S),
	root_consequent_holds(next,g70,0,40,T,S).

root_consequent_holds(OP,g70,0,39,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,40,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,g70,0,41,T,S).

root_consequent_holds(OP,g70,0,41,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,42,T,S),
	root_consequent_holds(next,g70,0,43,T,S).

root_consequent_holds(OP,g70,0,42,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,43,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,44,T,S),
	root_consequent_holds(next,g70,0,45,T,S).

root_consequent_holds(OP,g70,0,44,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,45,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,46,T,S),
	root_consequent_holds(next,g70,0,47,T,S).

root_consequent_holds(OP,g70,0,46,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,47,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,48,T,S),
	root_consequent_holds(next,g70,0,49,T,S).

root_consequent_holds(OP,g70,0,48,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,49,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,50,T,S),
	root_consequent_holds(next,g70,0,51,T,S).

root_consequent_holds(OP,g70,0,50,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,51,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,52,T,S),
	root_consequent_holds(next,g70,0,53,T,S).

root_consequent_holds(OP,g70,0,52,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,53,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,54,T,S),
	root_consequent_holds(next,g70,0,55,T,S).

root_consequent_holds(OP,g70,0,54,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,55,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,56,T,S),
	root_consequent_holds(next,g70,0,57,T,S).

root_consequent_holds(OP,g70,0,56,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,57,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,58,T,S),
	root_consequent_holds(next,g70,0,59,T,S).

root_consequent_holds(OP,g70,0,58,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,59,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,60,T,S),
	root_consequent_holds(next,g70,0,61,T,S).

root_consequent_holds(OP,g70,0,60,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,61,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,62,T,S),
	root_consequent_holds(next,g70,0,63,T,S).

root_consequent_holds(OP,g70,0,62,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,63,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,64,T,S),
	root_consequent_holds(next,g70,0,65,T,S).

root_consequent_holds(OP,g70,0,64,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,65,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,66,T,S),
	root_consequent_holds(next,g70,0,67,T,S).

root_consequent_holds(OP,g70,0,66,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,67,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,68,T,S),
	root_consequent_holds(next,g70,0,69,T,S).

root_consequent_holds(OP,g70,0,68,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,69,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,70,T,S),
	root_consequent_holds(next,g70,0,71,T,S).

root_consequent_holds(OP,g70,0,70,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,71,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,72,T,S),
	root_consequent_holds(next,g70,0,73,T,S).

root_consequent_holds(OP,g70,0,72,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S).

root_consequent_holds(OP,g70,0,73,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,74,T,S),
	root_consequent_holds(next,g70,0,75,T,S).

root_consequent_holds(OP,g70,0,74,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,75,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,76,T,S),
	root_consequent_holds(next,g70,0,77,T,S).

root_consequent_holds(OP,g70,0,76,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,77,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,78,T,S),
	root_consequent_holds(next,g70,0,79,T,S).

root_consequent_holds(OP,g70,0,78,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,79,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,80,T,S),
	root_consequent_holds(next,g70,0,81,T,S).

root_consequent_holds(OP,g70,0,80,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,81,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,82,T,S),
	root_consequent_holds(next,g70,0,83,T,S).

root_consequent_holds(OP,g70,0,82,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,83,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,84,T,S),
	root_consequent_holds(next,g70,0,85,T,S).

root_consequent_holds(OP,g70,0,84,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,85,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,86,T,S),
	root_consequent_holds(next,g70,0,87,T,S).

root_consequent_holds(OP,g70,0,86,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,87,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,88,T,S),
	root_consequent_holds(next,g70,0,89,T,S).

root_consequent_holds(OP,g70,0,88,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,89,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,90,T,S),
	root_consequent_holds(next,g70,0,91,T,S).

root_consequent_holds(OP,g70,0,90,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,91,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,92,T,S),
	root_consequent_holds(next,g70,0,93,T,S).

root_consequent_holds(OP,g70,0,92,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,93,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,94,T,S),
	root_consequent_holds(next,g70,0,95,T,S).

root_consequent_holds(OP,g70,0,94,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,95,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,96,T,S),
	root_consequent_holds(next,g70,0,97,T,S).

root_consequent_holds(OP,g70,0,96,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,97,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,98,T,S),
	root_consequent_holds(next,g70,0,99,T,S).

root_consequent_holds(OP,g70,0,98,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,99,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,100,T,S),
	root_consequent_holds(next,g70,0,101,T,S).

root_consequent_holds(OP,g70,0,100,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,101,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,102,T,S),
	root_consequent_holds(next,g70,0,103,T,S).

root_consequent_holds(OP,g70,0,102,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,103,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,104,T,S),
	root_consequent_holds(next,g70,0,105,T,S).

root_consequent_holds(OP,g70,0,104,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S).

root_consequent_holds(OP,g70,0,105,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,106,T,S),
	root_consequent_holds(next,g70,0,107,T,S).

root_consequent_holds(OP,g70,0,106,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,107,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,108,T,S),
	root_consequent_holds(next,g70,0,109,T,S).

root_consequent_holds(OP,g70,0,108,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,109,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,110,T,S),
	root_consequent_holds(next,g70,0,111,T,S).

root_consequent_holds(OP,g70,0,110,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,111,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,112,T,S),
	root_consequent_holds(next,g70,0,113,T,S).

root_consequent_holds(OP,g70,0,112,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,113,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,114,T,S),
	root_consequent_holds(next,g70,0,115,T,S).

root_consequent_holds(OP,g70,0,114,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,115,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,116,T,S),
	root_consequent_holds(next,g70,0,117,T,S).

root_consequent_holds(OP,g70,0,116,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,117,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,118,T,S),
	root_consequent_holds(next,g70,0,119,T,S).

root_consequent_holds(OP,g70,0,118,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(decide,T2,S).

root_consequent_holds(OP,g70,0,119,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,120,T,S),
	root_consequent_holds(next,g70,0,121,T,S).

root_consequent_holds(OP,g70,0,120,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S).

root_consequent_holds(OP,g70,0,121,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,122,T,S),
	root_consequent_holds(next,g70,0,123,T,S).

root_consequent_holds(OP,g70,0,122,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,123,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g70,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g70,0,124,T,S),
	root_consequent_holds(next,g70,0,125,T,S).

root_consequent_holds(OP,g70,0,124,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(hlock_2,T2,S).

root_consequent_holds(OP,g70,0,125,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S),
	not_holds_at(locked,T2,S).

%guarantee -- g80
%	G(((((((((((((((((((((((((((((!(decide=false)&!(decide=false))&!(decide=false))|(((!(decide=false)&!(decide=false))&hgrant_2=true)&next(hgrant_2=true)))|(((!(decide=false)&!(decide=false))&!(hgrant_2=true))&next(!(hgrant_2=true))))|(((!(decide=false)&hgrant_1=true)&!(decide=false))&next(hgrant_1=true)))|(((!(decide=false)&hgrant_1=true)&hgrant_2=true)&next((hgrant_1=true&hgrant_2=true))))|(((!(decide=false)&hgrant_1=true)&!(hgrant_2=true))&next((hgrant_1=true&!(hgrant_2=true)))))|(((!(decide=false)&!(hgrant_1=true))&!(decide=false))&next(!(hgrant_1=true))))|(((!(decide=false)&!(hgrant_1=true))&hgrant_2=true)&next((!(hgrant_1=true)&hgrant_2=true))))|(((!(decide=false)&!(hgrant_1=true))&!(hgrant_2=true))&next((!(hgrant_1=true)&!(hgrant_2=true)))))|(((hgrant_0=true&!(decide=false))&!(decide=false))&next(hgrant_0=true)))|(((hgrant_0=true&!(decide=false))&hgrant_2=true)&next((hgrant_0=true&hgrant_2=true))))|(((hgrant_0=true&!(decide=false))&!(hgrant_2=true))&next((hgrant_0=true&!(hgrant_2=true)))))|(((hgrant_0=true&hgrant_1=true)&!(decide=false))&next((hgrant_0=true&hgrant_1=true))))|(((hgrant_0=true&hgrant_1=true)&hgrant_2=true)&next(((hgrant_0=true&hgrant_1=true)&hgrant_2=true))))|(((hgrant_0=true&hgrant_1=true)&!(hgrant_2=true))&next(((hgrant_0=true&hgrant_1=true)&!(hgrant_2=true)))))|(((hgrant_0=true&!(hgrant_1=true))&!(decide=false))&next((hgrant_0=true&!(hgrant_1=true)))))|(((hgrant_0=true&!(hgrant_1=true))&hgrant_2=true)&next(((hgrant_0=true&!(hgrant_1=true))&hgrant_2=true))))|(((hgrant_0=true&!(hgrant_1=true))&!(hgrant_2=true))&next(((hgrant_0=true&!(hgrant_1=true))&!(hgrant_2=true)))))|(((!(hgrant_0=true)&!(decide=false))&!(decide=false))&next(!(hgrant_0=true))))|(((!(hgrant_0=true)&!(decide=false))&hgrant_2=true)&next((!(hgrant_0=true)&hgrant_2=true))))|(((!(hgrant_0=true)&!(decide=false))&!(hgrant_2=true))&next((!(hgrant_0=true)&!(hgrant_2=true)))))|(((!(hgrant_0=true)&hgrant_1=true)&!(decide=false))&next((!(hgrant_0=true)&hgrant_1=true))))|(((!(hgrant_0=true)&hgrant_1=true)&hgrant_2=true)&next(((!(hgrant_0=true)&hgrant_1=true)&hgrant_2=true))))|(((!(hgrant_0=true)&hgrant_1=true)&!(hgrant_2=true))&next(((!(hgrant_0=true)&hgrant_1=true)&!(hgrant_2=true)))))|(((!(hgrant_0=true)&!(hgrant_1=true))&!(decide=false))&next((!(hgrant_0=true)&!(hgrant_1=true)))))|(((!(hgrant_0=true)&!(hgrant_1=true))&hgrant_2=true)&next(((!(hgrant_0=true)&!(hgrant_1=true))&hgrant_2=true))))|(((!(hgrant_0=true)&!(hgrant_1=true))&!(hgrant_2=true))&next(((!(hgrant_0=true)&!(hgrant_1=true))&!(hgrant_2=true))))))

guarantee(g80).

antecedent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,0,T,S).

root_consequent_holds(OP,g80,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	holds_at(decide,T2,S),
	holds_at(decide,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,1,T,S),
	root_consequent_holds(next,g80,0,2,T,S).

root_consequent_holds(OP,g80,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	holds_at(decide,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,3,T,S),
	root_consequent_holds(next,g80,0,4,T,S).

root_consequent_holds(OP,g80,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	holds_at(decide,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,5,T,S),
	root_consequent_holds(next,g80,0,6,T,S).

root_consequent_holds(OP,g80,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_1,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,7,T,S),
	root_consequent_holds(next,g80,0,8,T,S).

root_consequent_holds(OP,g80,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,9,T,S),
	root_consequent_holds(next,g80,0,10,T,S).

root_consequent_holds(OP,g80,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,11,T,S),
	root_consequent_holds(next,g80,0,12,T,S).

root_consequent_holds(OP,g80,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,13,T,S),
	root_consequent_holds(next,g80,0,14,T,S).

root_consequent_holds(OP,g80,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,15,T,S),
	root_consequent_holds(next,g80,0,16,T,S).

root_consequent_holds(OP,g80,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,17,T,S),
	root_consequent_holds(next,g80,0,18,T,S).

root_consequent_holds(OP,g80,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(decide,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,18,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,19,T,S),
	root_consequent_holds(next,g80,0,20,T,S).

root_consequent_holds(OP,g80,0,19,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(decide,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,20,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,21,T,S),
	root_consequent_holds(next,g80,0,22,T,S).

root_consequent_holds(OP,g80,0,21,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(decide,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,22,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,23,T,S),
	root_consequent_holds(next,g80,0,24,T,S).

root_consequent_holds(OP,g80,0,23,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,24,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,25,T,S),
	root_consequent_holds(next,g80,0,26,T,S).

root_consequent_holds(OP,g80,0,25,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,26,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,27,T,S),
	root_consequent_holds(next,g80,0,28,T,S).

root_consequent_holds(OP,g80,0,27,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,28,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,29,T,S),
	root_consequent_holds(next,g80,0,30,T,S).

root_consequent_holds(OP,g80,0,29,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,30,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,31,T,S),
	root_consequent_holds(next,g80,0,32,T,S).

root_consequent_holds(OP,g80,0,31,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,32,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,33,T,S),
	root_consequent_holds(next,g80,0,34,T,S).

root_consequent_holds(OP,g80,0,33,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,34,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,35,T,S),
	root_consequent_holds(next,g80,0,36,T,S).

root_consequent_holds(OP,g80,0,35,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(decide,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,36,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,37,T,S),
	root_consequent_holds(next,g80,0,38,T,S).

root_consequent_holds(OP,g80,0,37,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(decide,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,38,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,39,T,S),
	root_consequent_holds(next,g80,0,40,T,S).

root_consequent_holds(OP,g80,0,39,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(decide,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,40,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,41,T,S),
	root_consequent_holds(next,g80,0,42,T,S).

root_consequent_holds(OP,g80,0,41,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,42,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,43,T,S),
	root_consequent_holds(next,g80,0,44,T,S).

root_consequent_holds(OP,g80,0,43,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,44,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,45,T,S),
	root_consequent_holds(next,g80,0,46,T,S).

root_consequent_holds(OP,g80,0,45,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,46,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,47,T,S),
	root_consequent_holds(next,g80,0,48,T,S).

root_consequent_holds(OP,g80,0,47,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(decide,T2,S).

root_consequent_holds(OP,g80,0,48,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,49,T,S),
	root_consequent_holds(next,g80,0,50,T,S).

root_consequent_holds(OP,g80,0,49,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,50,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_2,T2,S).

consequent_holds(g80,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g80,0,51,T,S),
	root_consequent_holds(next,g80,0,52,T,S).

root_consequent_holds(OP,g80,0,51,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g80,0,52,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

%guarantee -- g84
%	G((decide=false->((locked=true&next(locked=true))|(!(locked=true)&next(!(locked=true))))))

guarantee(g84).

antecedent_holds(g84,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,g84,0,T,S).

root_antecedent_holds(OP,g84,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(decide,T2,S).

consequent_holds(g84,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g84,0,0,T,S),
	root_consequent_holds(next,g84,0,1,T,S).

root_consequent_holds(OP,g84,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S).

root_consequent_holds(OP,g84,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(locked,T2,S).

consequent_holds(g84,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g84,0,2,T,S),
	root_consequent_holds(next,g84,0,3,T,S).

root_consequent_holds(OP,g84,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S).

root_consequent_holds(OP,g84,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S).

%guarantee -- g90_0
%	G((hbusreq_0=true->F((hbusreq_0=false|hmaster_val0=true))))

guarantee(g90_0).

antecedent_holds(g90_0,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,g90_0,0,T,S).

root_antecedent_holds(OP,g90_0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hbusreq_0,T2,S).

consequent_holds(g90_0,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g90_0,0,0,T,S).

root_consequent_holds(OP,g90_0,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_0,1,0,T2,S).

root_consequent_holds(OP,g90_0,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hbusreq_0,T2,S).

root_consequent_holds(OP,g90_0,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_0,1,1,T2,S).

root_consequent_holds(OP,g90_0,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S).

%guarantee -- g90_1
%	G((hbusreq_1=true->F((hbusreq_1=false|hmaster_val1=true))))

guarantee(g90_1).

antecedent_holds(g90_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,g90_1,0,T,S).

root_antecedent_holds(OP,g90_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hbusreq_1,T2,S).

consequent_holds(g90_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g90_1,0,0,T,S).

root_consequent_holds(OP,g90_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_1,1,0,T2,S).

root_consequent_holds(OP,g90_1,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g90_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_1,1,1,T2,S).

root_consequent_holds(OP,g90_1,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val1,T2,S).

%guarantee -- g90_2_monitor_init
%	btq_state_5_s0=true

guarantee(g90_2_monitor_init).

antecedent_holds(g90_2_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(g90_2_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,g90_2_monitor_init,0,0,0,S).

root_consequent_holds(OP,g90_2_monitor_init,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S).

%guarantee -- g90_2_monitor_safety
%	G((((((((((((btq_state_5_s0=true&!(hgrant_1=false))&!(hbusreq_1=true))&next(btq_state_5_s0=true))|(((btq_state_5_s0=true&hgrant_1=false)&hgrant_1=true)&next(btq_state_5_s0=true)))|(((btq_state_5_s0=true&!(hgrant_1=true))&hbusreq_1=true)&next(btq_state_5_s0=true)))|((((btq_state_5_s0=true&!(hgrant_1=false))&hgrant_1=true)&hbusreq_1=true)&next(btq_state_5_s0=true)))|((((btq_state_5_s0=true&hgrant_1=false)&!(hgrant_1=true))&!(hbusreq_1=true))&next(btq_state_5_s1=true)))|(((btq_state_5_s1=true&!(hgrant_1=true))&hbusreq_1=true)&next(btq_state_5_s0=true)))|(((btq_state_5_s1=true&!(hgrant_1=true))&!(hbusreq_1=true))&next(btq_state_5_s1=true)))|((btq_state_5_s1=true&hgrant_1=true)&next((btq_state_5_s0=false&btq_state_5_s1=false))))|((btq_state_5_s0=false&btq_state_5_s1=false)&next((btq_state_5_s0=false&btq_state_5_s1=false)))))

guarantee(g90_2_monitor_safety).

antecedent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,0,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,1,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S),
	holds_at(hgrant_1,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,2,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,3,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hgrant_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,4,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,5,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,6,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,7,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hgrant_1,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,8,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,9,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s1,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,10,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,11,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,12,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,13,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hbusreq_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s1,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,14,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,15,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s1,T2,S),
	holds_at(hgrant_1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_5_s0,T2,S),
	not_holds_at(btq_state_5_s1,T2,S).

consequent_holds(g90_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g90_2_monitor_safety,0,16,T,S),
	root_consequent_holds(next,g90_2_monitor_safety,0,17,T,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_5_s0,T2,S),
	not_holds_at(btq_state_5_s1,T2,S).

root_consequent_holds(OP,g90_2_monitor_safety,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_5_s0,T2,S),
	not_holds_at(btq_state_5_s1,T2,S).

%guarantee -- g90_2_monitor_justice
%	GF((btq_state_5_s0=true|btq_state_5_s1=true))

guarantee(g90_2_monitor_justice).

antecedent_holds(g90_2_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g90_2_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g90_2_monitor_justice,0,0,T,S).

root_consequent_holds(OP,g90_2_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_2_monitor_justice,1,0,T2,S).

root_consequent_holds(OP,g90_2_monitor_justice,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s0,T2,S).

root_consequent_holds(OP,g90_2_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_2_monitor_justice,1,1,T2,S).

root_consequent_holds(OP,g90_2_monitor_justice,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_5_s1,T2,S).

%guarantee -- g90_2
%	G((hbusreq_2=true->F((hbusreq_2=false|(hmaster_val0=false&hmaster_val1=false)))))

guarantee(g90_2).

antecedent_holds(g90_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,g90_2,0,T,S).

root_antecedent_holds(OP,g90_2,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hbusreq_2,T2,S).

consequent_holds(g90_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g90_2,0,0,T,S).

root_consequent_holds(OP,g90_2,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_2,1,0,T2,S).

root_consequent_holds(OP,g90_2,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g90_2,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g90_2,1,1,T2,S).

root_consequent_holds(OP,g90_2,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S),
	not_holds_at(hmaster_val1,T2,S).

%guarantee -- g100_2_monitor_init
%	btq_state_6_s0=true

guarantee(g100_2_monitor_init).

antecedent_holds(g100_2_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(g100_2_monitor_init,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,g100_2_monitor_init,0,0,0,S).

root_consequent_holds(OP,g100_2_monitor_init,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S).

%guarantee -- g100_2_monitor_safety
%	G((((((((((((btq_state_6_s0=true&!(hgrant_2=false))&!(hbusreq_2=true))&next(btq_state_6_s0=true))|(((btq_state_6_s0=true&hgrant_2=false)&hgrant_2=true)&next(btq_state_6_s0=true)))|(((btq_state_6_s0=true&!(hgrant_2=true))&hbusreq_2=true)&next(btq_state_6_s0=true)))|((((btq_state_6_s0=true&!(hgrant_2=false))&hgrant_2=true)&hbusreq_2=true)&next(btq_state_6_s0=true)))|((((btq_state_6_s0=true&hgrant_2=false)&!(hgrant_2=true))&!(hbusreq_2=true))&next(btq_state_6_s1=true)))|(((btq_state_6_s1=true&!(hgrant_2=true))&hbusreq_2=true)&next(btq_state_6_s0=true)))|(((btq_state_6_s1=true&!(hgrant_2=true))&!(hbusreq_2=true))&next(btq_state_6_s1=true)))|((btq_state_6_s1=true&hgrant_2=true)&next((btq_state_6_s0=false&btq_state_6_s1=false))))|((btq_state_6_s0=false&btq_state_6_s1=false)&next((btq_state_6_s0=false&btq_state_6_s1=false)))))

guarantee(g100_2_monitor_safety).

antecedent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,0,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,1,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S),
	holds_at(hgrant_2,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,2,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,3,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S),
	not_holds_at(hgrant_2,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,4,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,5,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S),
	not_holds_at(hgrant_2,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,6,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,7,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S),
	holds_at(hgrant_2,T2,S),
	holds_at(hgrant_2,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,8,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,9,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S),
	not_holds_at(hgrant_2,T2,S),
	not_holds_at(hgrant_2,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s1,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,10,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,11,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s1,T2,S),
	not_holds_at(hgrant_2,T2,S),
	holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,12,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,13,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,12,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s1,T2,S),
	not_holds_at(hgrant_2,T2,S),
	not_holds_at(hbusreq_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,13,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s1,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,14,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,15,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,14,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s1,T2,S),
	holds_at(hgrant_2,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,15,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_6_s0,T2,S),
	not_holds_at(btq_state_6_s1,T2,S).

consequent_holds(g100_2_monitor_safety,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,g100_2_monitor_safety,0,16,T,S),
	root_consequent_holds(next,g100_2_monitor_safety,0,17,T,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,16,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_6_s0,T2,S),
	not_holds_at(btq_state_6_s1,T2,S).

root_consequent_holds(OP,g100_2_monitor_safety,0,17,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_6_s0,T2,S),
	not_holds_at(btq_state_6_s1,T2,S).

%guarantee -- g100_2_monitor_justice
%	GF((btq_state_6_s0=true|btq_state_6_s1=true))

guarantee(g100_2_monitor_justice).

antecedent_holds(g100_2_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(g100_2_monitor_justice,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,g100_2_monitor_justice,0,0,T,S).

root_consequent_holds(OP,g100_2_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g100_2_monitor_justice,1,0,T2,S).

root_consequent_holds(OP,g100_2_monitor_justice,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s0,T2,S).

root_consequent_holds(OP,g100_2_monitor_justice,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,g100_2_monitor_justice,1,1,T2,S).

root_consequent_holds(OP,g100_2_monitor_justice,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(btq_state_6_s1,T2,S).

%guarantee -- g110
%	(hgrant_1=false&hgrant_2=false)

guarantee(g110).

antecedent_holds(g110,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(g110,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,g110,0,0,0,S).

root_consequent_holds(OP,g110,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hgrant_1,T2,S),
	not_holds_at(hgrant_2,T2,S).

%assumption -- a40
%	(((hbusreq_0=false&hlock_0=false)&(hbusreq_1=false&hlock_1=false))&(hbusreq_2=false&hlock_2=false))

assumption(a40).

antecedent_holds(a40,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(a40,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,a40,0,0,0,S).

root_consequent_holds(OP,a40,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hbusreq_0,T2,S),
	not_holds_at(hlock_0,T2,S),
	not_holds_at(hbusreq_1,T2,S),
	not_holds_at(hlock_1,T2,S),
	not_holds_at(hbusreq_2,T2,S),
	not_holds_at(hlock_2,T2,S).

%guarantee -- gar_anon_1
%	hready_counter_val0=true

guarantee(gar_anon_1).

antecedent_holds(gar_anon_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(gar_anon_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,gar_anon_1,0,0,0,S).

root_consequent_holds(OP,gar_anon_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S).

%guarantee -- gar_anon_2
%	G(((((hmastlock=true&hburst_burst4=true)&start=true)&hready=false)->next(hready_counter_val0=true)))

guarantee(gar_anon_2).

antecedent_holds(gar_anon_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_2,0,T,S).

root_antecedent_holds(OP,gar_anon_2,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(start,T2,S),
	not_holds_at(hready,T2,S).

consequent_holds(gar_anon_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,gar_anon_2,0,0,T,S).

root_consequent_holds(OP,gar_anon_2,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S).

%guarantee -- gar_anon_3
%	G(((((hmastlock=true&hburst_burst4=true)&start=true)&hready=true)->next(hready_counter_val1=true)))

guarantee(gar_anon_3).

antecedent_holds(gar_anon_3,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_3,0,T,S).

root_antecedent_holds(OP,gar_anon_3,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmastlock,T2,S),
	holds_at(hburst_burst4,T2,S),
	holds_at(start,T2,S),
	holds_at(hready,T2,S).

consequent_holds(gar_anon_3,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,gar_anon_3,0,0,T,S).

root_consequent_holds(OP,gar_anon_3,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S).

%guarantee -- gar_anon_4
%	G(((((((((((((((!(hmastlock=true)&hready=true)&hready_counter_val0=true)|((!(hmastlock=true)&hready=true)&hready_counter_val1=true))|((!(hmastlock=true)&hready=true)&hready_counter_val2=true))|((!(hmastlock=true)&hready=true)&hready_counter_val3=true))|((!(hburst_burst4=true)&hready=true)&hready_counter_val0=true))|((!(hburst_burst4=true)&hready=true)&hready_counter_val1=true))|((!(hburst_burst4=true)&hready=true)&hready_counter_val2=true))|((!(hburst_burst4=true)&hready=true)&hready_counter_val3=true))|((!(start=true)&hready=true)&hready_counter_val0=true))|((!(start=true)&hready=true)&hready_counter_val1=true))|((!(start=true)&hready=true)&hready_counter_val2=true))|((!(start=true)&hready=true)&hready_counter_val3=true))->((((hready_counter_val0=true&next(hready_counter_val1=true))|(hready_counter_val1=true&next(hready_counter_val2=true)))|(hready_counter_val2=true&next(hready_counter_val3=true)))|(hready_counter_val3=true&next((((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))))))

guarantee(gar_anon_4).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,0,T,S).

root_antecedent_holds(OP,gar_anon_4,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val0,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,1,T,S).

root_antecedent_holds(OP,gar_anon_4,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val1,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,2,T,S).

root_antecedent_holds(OP,gar_anon_4,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val2,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,3,T,S).

root_antecedent_holds(OP,gar_anon_4,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val3,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,4,T,S).

root_antecedent_holds(OP,gar_anon_4,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val0,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,5,T,S).

root_antecedent_holds(OP,gar_anon_4,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val1,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,6,T,S).

root_antecedent_holds(OP,gar_anon_4,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val2,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,7,T,S).

root_antecedent_holds(OP,gar_anon_4,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val3,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,8,T,S).

root_antecedent_holds(OP,gar_anon_4,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val0,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,9,T,S).

root_antecedent_holds(OP,gar_anon_4,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val1,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,10,T,S).

root_antecedent_holds(OP,gar_anon_4,10,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val2,T2,S).

antecedent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_4,11,T,S).

root_antecedent_holds(OP,gar_anon_4,11,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready,T2,S),
	holds_at(hready_counter_val3,T2,S).

consequent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_4,0,0,T,S),
	root_consequent_holds(next,gar_anon_4,0,1,T,S).

root_consequent_holds(OP,gar_anon_4,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S).

root_consequent_holds(OP,gar_anon_4,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S).

consequent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_4,0,2,T,S),
	root_consequent_holds(next,gar_anon_4,0,3,T,S).

root_consequent_holds(OP,gar_anon_4,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S).

root_consequent_holds(OP,gar_anon_4,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val2,T2,S).

consequent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_4,0,4,T,S),
	root_consequent_holds(next,gar_anon_4,0,5,T,S).

root_consequent_holds(OP,gar_anon_4,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val2,T2,S).

root_consequent_holds(OP,gar_anon_4,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val3,T2,S).

consequent_holds(gar_anon_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_4,0,6,T,S),
	root_consequent_holds(next,gar_anon_4,0,7,T,S).

root_consequent_holds(OP,gar_anon_4,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val3,T2,S).

root_consequent_holds(OP,gar_anon_4,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

%guarantee -- gar_anon_5
%	G(((((((((!(hmastlock=true)&hready=true)&hready_counter_val0=false)&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false)|(((((!(hburst_burst4=true)&hready=true)&hready_counter_val0=false)&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))|(((((!(start=true)&hready=true)&hready_counter_val0=false)&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))->next((((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))))

guarantee(gar_anon_5).

antecedent_holds(gar_anon_5,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_5,0,T,S).

root_antecedent_holds(OP,gar_anon_5,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S),
	holds_at(hready,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

antecedent_holds(gar_anon_5,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_5,1,T,S).

root_antecedent_holds(OP,gar_anon_5,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	holds_at(hready,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

antecedent_holds(gar_anon_5,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_5,2,T,S).

root_antecedent_holds(OP,gar_anon_5,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	holds_at(hready,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

consequent_holds(gar_anon_5,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(next,gar_anon_5,0,0,T,S).

root_consequent_holds(OP,gar_anon_5,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

%guarantee -- gar_anon_6
%	G(((((!(hmastlock=true)&hready=false)|(!(hburst_burst4=true)&hready=false))|(!(start=true)&hready=false))->(((((hready_counter_val0=true&next(hready_counter_val0=true))|(hready_counter_val1=true&next(hready_counter_val1=true)))|(hready_counter_val2=true&next(hready_counter_val2=true)))|(hready_counter_val3=true&next(hready_counter_val3=true)))|((((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false)&next((((hready_counter_val0=false&hready_counter_val1=false)&hready_counter_val2=false)&hready_counter_val3=false))))))

guarantee(gar_anon_6).

antecedent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_6,0,T,S).

root_antecedent_holds(OP,gar_anon_6,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S),
	not_holds_at(hready,T2,S).

antecedent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_6,1,T,S).

root_antecedent_holds(OP,gar_anon_6,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_burst4,T2,S),
	not_holds_at(hready,T2,S).

antecedent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,gar_anon_6,2,T,S).

root_antecedent_holds(OP,gar_anon_6,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	not weak_timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(start,T2,S),
	not_holds_at(hready,T2,S).

consequent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_6,0,0,T,S),
	root_consequent_holds(next,gar_anon_6,0,1,T,S).

root_consequent_holds(OP,gar_anon_6,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S).

root_consequent_holds(OP,gar_anon_6,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val0,T2,S).

consequent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_6,0,2,T,S),
	root_consequent_holds(next,gar_anon_6,0,3,T,S).

root_consequent_holds(OP,gar_anon_6,0,2,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S).

root_consequent_holds(OP,gar_anon_6,0,3,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val1,T2,S).

consequent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_6,0,4,T,S),
	root_consequent_holds(next,gar_anon_6,0,5,T,S).

root_consequent_holds(OP,gar_anon_6,0,4,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val2,T2,S).

root_consequent_holds(OP,gar_anon_6,0,5,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val2,T2,S).

consequent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_6,0,6,T,S),
	root_consequent_holds(next,gar_anon_6,0,7,T,S).

root_consequent_holds(OP,gar_anon_6,0,6,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val3,T2,S).

root_consequent_holds(OP,gar_anon_6,0,7,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hready_counter_val3,T2,S).

consequent_holds(gar_anon_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,gar_anon_6,0,8,T,S),
	root_consequent_holds(next,gar_anon_6,0,9,T,S).

root_consequent_holds(OP,gar_anon_6,0,8,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

root_consequent_holds(OP,gar_anon_6,0,9,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val0,T2,S),
	not_holds_at(hready_counter_val1,T2,S),
	not_holds_at(hready_counter_val2,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

%guarantee -- gar_anon_7
%	decide=true

guarantee(gar_anon_7).

antecedent_holds(gar_anon_7,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(gar_anon_7,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,gar_anon_7,0,0,0,S).

root_consequent_holds(OP,gar_anon_7,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(decide,T2,S).

%guarantee -- gar_anon_8
%	start=true

guarantee(gar_anon_8).

antecedent_holds(gar_anon_8,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(gar_anon_8,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,gar_anon_8,0,0,0,S).

root_consequent_holds(OP,gar_anon_8,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(start,T2,S).

%guarantee -- gar_anon_9
%	locked=false

guarantee(gar_anon_9).

antecedent_holds(gar_anon_9,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(gar_anon_9,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,gar_anon_9,0,0,0,S).

root_consequent_holds(OP,gar_anon_9,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(locked,T2,S).

%guarantee -- gar_anon_10
%	hmaster_val0=true

guarantee(gar_anon_10).

antecedent_holds(gar_anon_10,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(gar_anon_10,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,gar_anon_10,0,0,0,S).

root_consequent_holds(OP,gar_anon_10,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hmaster_val0,T2,S).

%guarantee -- gar_anon_11
%	hmastlock=false

guarantee(gar_anon_11).

antecedent_holds(gar_anon_11,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(gar_anon_11,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,gar_anon_11,0,0,0,S).

root_consequent_holds(OP,gar_anon_11,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmastlock,T2,S).

%guarantee -- gar_anon_12
%	hgrant_0=true

guarantee(gar_anon_12).

antecedent_holds(gar_anon_12,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(gar_anon_12,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,gar_anon_12,0,0,0,S).

root_consequent_holds(OP,gar_anon_12,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(hgrant_0,T2,S).

%assumption -- asm_anon_1
%	hready=false

assumption(asm_anon_1).

antecedent_holds(asm_anon_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S).

consequent_holds(asm_anon_1,0,S):-
	trace(S),
	timepoint(0,S),
	not weak_timepoint(0,S),
	root_consequent_holds(current,asm_anon_1,0,0,0,S).

root_consequent_holds(OP,asm_anon_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready,T2,S).

%assumption -- hburst_mutual_exclusion
%	G((!(hburst_single=true)|!(hburst_burst4=true)))

assumption(hburst_mutual_exclusion).

antecedent_holds(hburst_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hburst_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hburst_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,hburst_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_single,T2,S).

consequent_holds(hburst_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hburst_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,hburst_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hburst_burst4,T2,S).

%guarantee -- hmaster_mutual_exclusion
%	G((!(hmaster_val0=true)|!(hmaster_val1=true)))

guarantee(hmaster_mutual_exclusion).

antecedent_holds(hmaster_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hmaster_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hmaster_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,hmaster_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val0,T2,S).

consequent_holds(hmaster_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hmaster_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,hmaster_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hmaster_val1,T2,S).

%guarantee -- hready_counter_mutual_exclusion_1
%	G((!(hready_counter_val0=true)|!(hready_counter_val1=true)))

guarantee(hready_counter_mutual_exclusion_1).

antecedent_holds(hready_counter_mutual_exclusion_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hready_counter_mutual_exclusion_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_1,0,0,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val0,T2,S).

consequent_holds(hready_counter_mutual_exclusion_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_1,0,1,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_1,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val1,T2,S).

%guarantee -- hready_counter_mutual_exclusion_2
%	G((!(hready_counter_val0=true)|!(hready_counter_val2=true)))

guarantee(hready_counter_mutual_exclusion_2).

antecedent_holds(hready_counter_mutual_exclusion_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hready_counter_mutual_exclusion_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_2,0,0,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_2,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val0,T2,S).

consequent_holds(hready_counter_mutual_exclusion_2,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_2,0,1,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_2,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val2,T2,S).

%guarantee -- hready_counter_mutual_exclusion_3
%	G((!(hready_counter_val0=true)|!(hready_counter_val3=true)))

guarantee(hready_counter_mutual_exclusion_3).

antecedent_holds(hready_counter_mutual_exclusion_3,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hready_counter_mutual_exclusion_3,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_3,0,0,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_3,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val0,T2,S).

consequent_holds(hready_counter_mutual_exclusion_3,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_3,0,1,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_3,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

%guarantee -- hready_counter_mutual_exclusion_4
%	G((!(hready_counter_val1=true)|!(hready_counter_val2=true)))

guarantee(hready_counter_mutual_exclusion_4).

antecedent_holds(hready_counter_mutual_exclusion_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hready_counter_mutual_exclusion_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_4,0,0,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_4,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val1,T2,S).

consequent_holds(hready_counter_mutual_exclusion_4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_4,0,1,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_4,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val2,T2,S).

%guarantee -- hready_counter_mutual_exclusion_5
%	G((!(hready_counter_val1=true)|!(hready_counter_val3=true)))

guarantee(hready_counter_mutual_exclusion_5).

antecedent_holds(hready_counter_mutual_exclusion_5,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hready_counter_mutual_exclusion_5,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_5,0,0,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_5,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val1,T2,S).

consequent_holds(hready_counter_mutual_exclusion_5,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_5,0,1,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_5,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

%guarantee -- hready_counter_mutual_exclusion_6
%	G((!(hready_counter_val2=true)|!(hready_counter_val3=true)))

guarantee(hready_counter_mutual_exclusion_6).

antecedent_holds(hready_counter_mutual_exclusion_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(hready_counter_mutual_exclusion_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_6,0,0,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_6,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val2,T2,S).

consequent_holds(hready_counter_mutual_exclusion_6,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,hready_counter_mutual_exclusion_6,0,1,T,S).

root_consequent_holds(OP,hready_counter_mutual_exclusion_6,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(hready_counter_val3,T2,S).

%guarantee -- btq_state_1_mutual_exclusion
%	G((!(btq_state_1_s0=true)|!(btq_state_1_s1=true)))

guarantee(btq_state_1_mutual_exclusion).

antecedent_holds(btq_state_1_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(btq_state_1_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_1_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,btq_state_1_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_1_s0,T2,S).

consequent_holds(btq_state_1_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_1_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,btq_state_1_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_1_s1,T2,S).

%guarantee -- btq_state_2_mutual_exclusion
%	G((!(btq_state_2_s0=true)|!(btq_state_2_s1=true)))

guarantee(btq_state_2_mutual_exclusion).

antecedent_holds(btq_state_2_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(btq_state_2_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_2_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,btq_state_2_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_2_s0,T2,S).

consequent_holds(btq_state_2_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_2_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,btq_state_2_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_2_s1,T2,S).

%guarantee -- btq_state_3_mutual_exclusion
%	G((!(btq_state_3_s0=true)|!(btq_state_3_s1=true)))

guarantee(btq_state_3_mutual_exclusion).

antecedent_holds(btq_state_3_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(btq_state_3_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_3_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,btq_state_3_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_3_s0,T2,S).

consequent_holds(btq_state_3_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_3_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,btq_state_3_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_3_s1,T2,S).

%guarantee -- btq_state_4_mutual_exclusion
%	G((!(btq_state_4_s0=true)|!(btq_state_4_s1=true)))

guarantee(btq_state_4_mutual_exclusion).

antecedent_holds(btq_state_4_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(btq_state_4_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_4_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,btq_state_4_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_4_s0,T2,S).

consequent_holds(btq_state_4_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_4_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,btq_state_4_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_4_s1,T2,S).

%guarantee -- btq_state_5_mutual_exclusion
%	G((!(btq_state_5_s0=true)|!(btq_state_5_s1=true)))

guarantee(btq_state_5_mutual_exclusion).

antecedent_holds(btq_state_5_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(btq_state_5_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_5_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,btq_state_5_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_5_s0,T2,S).

consequent_holds(btq_state_5_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_5_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,btq_state_5_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_5_s1,T2,S).

%guarantee -- btq_state_6_mutual_exclusion
%	G((!(btq_state_6_s0=true)|!(btq_state_6_s1=true)))

guarantee(btq_state_6_mutual_exclusion).

antecedent_holds(btq_state_6_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S).

consequent_holds(btq_state_6_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_6_mutual_exclusion,0,0,T,S).

root_consequent_holds(OP,btq_state_6_mutual_exclusion,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_6_s0,T2,S).

consequent_holds(btq_state_6_mutual_exclusion,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,btq_state_6_mutual_exclusion,0,1,T,S).

root_consequent_holds(OP,btq_state_6_mutual_exclusion,0,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(btq_state_6_s1,T2,S).

%---*** Signature  ***---

atom(btq_state_1_s0).
atom(btq_state_1_s1).
atom(btq_state_2_s0).
atom(btq_state_2_s1).
atom(btq_state_3_s0).
atom(btq_state_3_s1).
atom(btq_state_4_s0).
atom(btq_state_4_s1).
atom(btq_state_5_s0).
atom(btq_state_5_s1).
atom(btq_state_6_s0).
atom(btq_state_6_s1).
atom(decide).
atom(hburst_burst4).
atom(hburst_single).
atom(hbusreq_0).
atom(hbusreq_1).
atom(hbusreq_2).
atom(hgrant_0).
atom(hgrant_1).
atom(hgrant_2).
atom(hlock_0).
atom(hlock_1).
atom(hlock_2).
atom(hmaster_val0).
atom(hmaster_val1).
atom(hmastlock).
atom(hready).
atom(hready_counter_val0).
atom(hready_counter_val1).
atom(hready_counter_val2).
atom(hready_counter_val3).
atom(locked).
atom(start).


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
not_holds_at(btq_state_1_s0,0,trace_name_0).
not_holds_at(btq_state_1_s1,0,trace_name_0).
not_holds_at(btq_state_2_s0,0,trace_name_0).
not_holds_at(btq_state_2_s1,0,trace_name_0).
not_holds_at(btq_state_3_s0,0,trace_name_0).
not_holds_at(btq_state_3_s1,0,trace_name_0).
not_holds_at(btq_state_4_s0,0,trace_name_0).
not_holds_at(btq_state_4_s1,0,trace_name_0).
not_holds_at(btq_state_5_s0,0,trace_name_0).
not_holds_at(btq_state_5_s1,0,trace_name_0).
not_holds_at(btq_state_6_s0,0,trace_name_0).
not_holds_at(btq_state_6_s1,0,trace_name_0).
not_holds_at(decide,0,trace_name_0).
not_holds_at(hburst_burst4,0,trace_name_0).
not_holds_at(hburst_single,0,trace_name_0).
not_holds_at(hbusreq_0,0,trace_name_0).
not_holds_at(hbusreq_1,0,trace_name_0).
not_holds_at(hbusreq_2,0,trace_name_0).
not_holds_at(hgrant_0,0,trace_name_0).
not_holds_at(hgrant_1,0,trace_name_0).
not_holds_at(hgrant_2,0,trace_name_0).
not_holds_at(hlock_0,0,trace_name_0).
not_holds_at(hlock_1,0,trace_name_0).
not_holds_at(hlock_2,0,trace_name_0).
not_holds_at(hmaster_val0,0,trace_name_0).
not_holds_at(hmaster_val1,0,trace_name_0).
not_holds_at(hmastlock,0,trace_name_0).
not_holds_at(hready,0,trace_name_0).
not_holds_at(hready_counter_val0,0,trace_name_0).
not_holds_at(hready_counter_val1,0,trace_name_0).
not_holds_at(hready_counter_val2,0,trace_name_0).
not_holds_at(hready_counter_val3,0,trace_name_0).
not_holds_at(locked,0,trace_name_0).
not_holds_at(start,0,trace_name_0).

to_violate(a30).

is_guarantee(btq_state_1_mutual_exclusion).
is_guarantee(btq_state_2_mutual_exclusion).
is_guarantee(btq_state_3_mutual_exclusion).
is_guarantee(btq_state_4_mutual_exclusion).
is_guarantee(btq_state_5_mutual_exclusion).
is_guarantee(btq_state_6_mutual_exclusion).
is_guarantee(g10).
is_guarantee(g100_2_monitor_init).
is_guarantee(g100_2_monitor_justice).
is_guarantee(g100_2_monitor_safety).
is_guarantee(g110).
is_guarantee(g20_0_monitor_init).
is_guarantee(g20_0_monitor_justice).
is_guarantee(g20_0_monitor_safety).
is_guarantee(g20_1_monitor_init).
is_guarantee(g20_1_monitor_justice).
is_guarantee(g20_1_monitor_safety).
is_guarantee(g20_2_monitor_init).
is_guarantee(g20_2_monitor_justice).
is_guarantee(g20_2_monitor_safety).
is_guarantee(g30_monitor_init).
is_guarantee(g30_monitor_justice).
is_guarantee(g30_monitor_safety).
is_guarantee(g40).
is_guarantee(g50).
is_guarantee(g60).
is_guarantee(g64).
is_guarantee(g70).
is_guarantee(g80).
is_guarantee(g84).
is_guarantee(g90_0).
is_guarantee(g90_1).
is_guarantee(g90_2).
is_guarantee(g90_2_monitor_init).
is_guarantee(g90_2_monitor_justice).
is_guarantee(g90_2_monitor_safety).
is_guarantee(gar_anon_1).
is_guarantee(gar_anon_10).
is_guarantee(gar_anon_11).
is_guarantee(gar_anon_12).
is_guarantee(gar_anon_2).
is_guarantee(gar_anon_3).
is_guarantee(gar_anon_4).
is_guarantee(gar_anon_5).
is_guarantee(gar_anon_6).
is_guarantee(gar_anon_7).
is_guarantee(gar_anon_8).
is_guarantee(gar_anon_9).
is_guarantee(hmaster_mutual_exclusion).
is_guarantee(hready_counter_mutual_exclusion_1).
is_guarantee(hready_counter_mutual_exclusion_2).
is_guarantee(hready_counter_mutual_exclusion_3).
is_guarantee(hready_counter_mutual_exclusion_4).
is_guarantee(hready_counter_mutual_exclusion_5).
is_guarantee(hready_counter_mutual_exclusion_6).

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
