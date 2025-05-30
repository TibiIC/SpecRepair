#ilasp_script

max_solutions = 100

ilasp.cdilp.initialise()
solve_result = ilasp.cdilp.solve()

c_egs = None
if solve_result is not None:
  c_egs = ilasp.find_all_counterexamples(solve_result)

conflict_analysis_strategy = {
  'positive-strategy': 'all-ufs',
  'negative-strategy': 'single-as',
  'brave-strategy':    'all-ufs',
  'cautious-strategy': 'single-as-pair'
}

solution_count = 0

while solution_count < max_solutions and solve_result is not None:
  if c_egs:
    ce = ilasp.get_example(c_egs[0]['id'])
    constraint = ilasp.cdilp.analyse_conflict(solve_result['hypothesis'], ce['id'], conflict_analysis_strategy)
  
    # An example with recorded penalty of 0 is in reality an example with an
    # infinite penalty, meaning that it must be covered. Constraint propagation is,
    # therefore, unnecessary.
    if ce['penalty'] != -1:
      c_eg_ids = list(map(lambda x: x['id'], c_egs))
      prop_egs = []
      if ce['type'] == 'positive':
        prop_egs = ilasp.cdilp.propagate_constraint(constraint, c_eg_ids, {'select-examples': ['positive'], 'strategy': 'cdpi-implies-constraint'})
      elif ce['type'] == 'negative':
        prop_egs = ilasp.cdilp.propagate_constraint(constraint, c_eg_ids, {'select-examples': ['negative'], 'strategy': 'neg-constraint-implies-cdpi'})
      elif ce['type'] == 'brave-order':
        prop_egs = ilasp.cdilp.propagate_constraint(constraint, c_eg_ids, {'select-examples': ['brave-order'],    'strategy': 'cdoe-implies-constraint'})
      else:
        prop_egs = [ce['id']]
  
      ilasp.cdilp.add_coverage_constraint(constraint, prop_egs)
  
    else:
      ilasp.cdilp.add_coverage_constraint(constraint, [ce['id']])

  solve_result = ilasp.cdilp.solve()

  if solve_result is not None:
    c_egs = ilasp.find_all_counterexamples(solve_result)
    if not c_egs:
      solution_count+=1
      debug_print(f'Solution {solution_count} (score {solve_result["expected_score"]})')
      print(ilasp.hypothesis_to_string(solve_result['hypothesis']))
      new_constraint_body = map(lambda x: f'nge_HYP({x})', solve_result["hypothesis"])
      # if you want to rule allow non-subset-minimal solutions uncomment this line and comment the one below.
      # new_constraint = f':- {",".join(new_constraint_body)}, #count' + "{ H : nge_HYP(H) }" + f' = {len(solve_result["hypothesis"])}.\n'
      new_constraint = f':- {",".join(new_constraint_body)}.\n'
      ilasp.cdilp.add_to_meta_program(new_constraint)


if solution_count == 0:
  print('UNSATISFIABLE')

ilasp.stats.print_timings()

#end.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Mode Declaration
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#modeh(consequent_exception(const(expression_v), var(time), var(trace))).
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
#constant(expression_v, initial_guarantee).
#constant(expression_v, guarantee1_1).
#constant(expression_v, guarantee2_1).
#bias("
:- constraint.
:- head(consequent_exception(_,V1,V2)), body(timepoint_of_op(_,V3,_,V4)), (V1, V2) != (V3, V4).
:- head(consequent_exception(_,_,V1)), body(holds_at(_,_,V2)), V1 != V2.
:- head(consequent_exception(_,_,V1)), body(not_holds_at(_,_,V2)), V1 != V2.
:- body(timepoint_of_op(_,_,V1,_)), body(holds_at(_,V2,_)), V1 != V2.
:- body(timepoint_of_op(_,_,V1,_)), body(not_holds_at(_,V2,_)), V1 != V2.
:- body(timepoint_of_op(_,_,_,_)), not body(not_holds_at(_,_,_)), not body(holds_at(_,_,_)).
:- body(timepoint_of_op(current,V1,V2,_)), V1 != V2.
:- body(timepoint_of_op(next,V1,V2,_)), V1 == V2.
:- body(timepoint_of_op(prev,V1,V2,_)), V1 == V2.
:- body(timepoint_of_op(eventually,V1,V2,_)), V1 == V2.
:- body(holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).
:- body(not_holds_at(_,V1,V2)), not body(timepoint_of_op(_,_,V1,V2)).
:- head(consequent_exception(_,_,_)), body(timepoint_of_op(next,_,_,_)).
:- head(consequent_exception(_,_,_)), body(timepoint_of_op(prev,_,_,_)).
:- head(consequent_exception(_,_,_)), body(timepoint_of_op(eventually,_,_,_)).
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
%guarantee -- initial_guarantee
%	pump=false;
guarantee(initial_guarantee).
antecedent_holds(initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S).
consequent_holds(initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S),
	root_consequent_holds(current,initial_guarantee,0,0,S).
consequent_holds(initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S),
	root_consequent_holds(eventually,initial_guarantee,0,0,S),
	ev_temp_op(initial_guarantee).
root_consequent_holds(OP,initial_guarantee,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(pump,T2,S).
consequent_holds(initial_guarantee,0,S):-
	trace(S),
	timepoint(0,S),
	consequent_exception(initial_guarantee,0,S),
	not ev_temp_op(initial_guarantee).
%guarantee -- guarantee1_1
%	G(highwater=true->next(pump=true));
guarantee(guarantee1_1).
antecedent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,guarantee1_1,0,T,S).
root_antecedent_holds(OP,guarantee1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(highwater,T2,S).
consequent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,guarantee1_1,0,T,S),
	not ev_temp_op(guarantee1_1).
consequent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,guarantee1_1,0,T,S),
	ev_temp_op(guarantee1_1).
root_consequent_holds(OP,guarantee1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(pump,T2,S).
consequent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	consequent_exception(guarantee1_1,T,S),
	not ev_temp_op(guarantee1_1).
%guarantee -- guarantee2_1
%	G(methane=true->next(pump=false));
guarantee(guarantee2_1).
antecedent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_antecedent_holds(current,guarantee2_1,0,T,S).
root_antecedent_holds(OP,guarantee2_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(methane,T2,S).
consequent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(next,guarantee2_1,0,T,S),
	not ev_temp_op(guarantee2_1).
consequent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	root_consequent_holds(eventually,guarantee2_1,0,T,S),
	ev_temp_op(guarantee2_1).
root_consequent_holds(OP,guarantee2_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	not weak_timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(pump,T2,S).
consequent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	consequent_exception(guarantee2_1,T,S),
	not ev_temp_op(guarantee2_1).
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
%---*** Violation Trace ***---

#pos({entailed(counter_strat_0_0)},{},{

% CS_Path: ini_S0_DEAD

trace(counter_strat_0_0).
timepoint(0,counter_strat_0_0).
timepoint(1,counter_strat_0_0).
timepoint(2,counter_strat_0_0).
next(1,0,counter_strat_0_0).
next(2,1,counter_strat_0_0).
not_holds_at(highwater,0,counter_strat_0_0).
not_holds_at(methane,0,counter_strat_0_0).
not_holds_at(pump,0,counter_strat_0_0).
holds_at(highwater,1,counter_strat_0_0).
holds_at(methane,1,counter_strat_0_0).
holds_at(pump,1,counter_strat_0_0).
not_holds_at(highwater,2,counter_strat_0_0).
not_holds_at(methane,2,counter_strat_0_0).
not_holds_at(pump,2,counter_strat_0_0).
}).
