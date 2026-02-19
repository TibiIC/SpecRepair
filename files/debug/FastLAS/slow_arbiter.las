#ilasp_script

max_solutions = 10

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

#modeh(antecedent_exception(const(expression_v), const(index), var(time), var(trace))).
#modeb(2,timepoint_of_op(const(temp_op_v), var(time), var(time), var(trace)), (positive)).
#modeb(2,holds_at(const(usable_atom), var(time), var(trace)), (positive)).
#modeb(2,not_holds_at(const(usable_atom), var(time), var(trace)), (positive)).
#constant(usable_atom,a).
#constant(usable_atom,g1).
#constant(usable_atom,g2).
#constant(usable_atom,r1).
#constant(usable_atom,r2).
#constant(index,0..0).
#constant(temp_op_v,current).
#constant(temp_op_v,next).
#constant(temp_op_v,prev).
#constant(temp_op_v,eventually).
#constant(expression_v, guarantee1_1).
#constant(expression_v, guarantee3_1).
#constant(expression_v, guarantee2_1).
#constant(expression_v, guarantee4).
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
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(next,_,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(prev,_,_,_)).
:- head(antecedent_exception(_,_,_,_)), body(timepoint_of_op(eventually,_,_,_)).
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

%guarantee -- guarantee1_1
%	G((r1=true->F(g1=true)))

guarantee(guarantee1_1).

antecedent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,guarantee1_1,0,T,S),
	not antecedent_exception(guarantee1_1,0,T,S).

root_antecedent_holds(OP,guarantee1_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(r1,T2,S).

consequent_holds(guarantee1_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,guarantee1_1,0,0,T,S).

root_consequent_holds(OP,guarantee1_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,guarantee1_1,1,0,T2,S).

root_consequent_holds(OP,guarantee1_1,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(g1,T2,S).

%guarantee -- guarantee2_1
%	G((r2=true->F((g2=true|g1=false))))

guarantee(guarantee2_1).

antecedent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,guarantee2_1,0,T,S),
	not antecedent_exception(guarantee2_1,0,T,S).

root_antecedent_holds(OP,guarantee2_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(r2,T2,S).

consequent_holds(guarantee2_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(eventually,guarantee2_1,0,0,T,S).

root_consequent_holds(OP,guarantee2_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,guarantee2_1,1,0,T2,S).

root_consequent_holds(OP,guarantee2_1,1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	holds_at(g2,T2,S).

root_consequent_holds(OP,guarantee2_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	root_consequent_holds(current,guarantee2_1,1,1,T2,S).

root_consequent_holds(OP,guarantee2_1,1,1,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(g1,T2,S).

%guarantee -- guarantee3_1
%	G(((a=false&r2=false)->(g1=false&g2=false)))

guarantee(guarantee3_1).

antecedent_holds(guarantee3_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_antecedent_holds(current,guarantee3_1,0,T,S),
	not antecedent_exception(guarantee3_1,0,T,S).

root_antecedent_holds(OP,guarantee3_1,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(a,T2,S),
	not_holds_at(r2,T2,S).

consequent_holds(guarantee3_1,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,guarantee3_1,0,0,T,S).

root_consequent_holds(OP,guarantee3_1,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(g1,T2,S),
	not_holds_at(g2,T2,S).

%guarantee -- guarantee4
%	G((g1=false|g2=false))

guarantee(guarantee4).

antecedent_holds(guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	not antecedent_exception(guarantee4,0,T,S).

consequent_holds(guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,guarantee4,0,0,T,S).

root_consequent_holds(OP,guarantee4,0,0,T1,S):-
	trace(S),
	timepoint(T1,S),
	timepoint(T2,S),
	temporal_operator(OP),
	timepoint_of_op(OP,T1,T2,S),
	not_holds_at(g1,T2,S).

consequent_holds(guarantee4,T,S):-
	trace(S),
	timepoint(T,S),
	not weak_timepoint(T,S),
	root_consequent_holds(current,guarantee4,0,1,T,S).

root_consequent_holds(OP,guarantee4,0,1,T1,S):-
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

#pos({entailed(trace_name_0)},{},{

trace(trace_name_0).
timepoint(0,trace_name_0).
weak_timepoint(weak_t,trace_name_0).
next(weak_t,0,trace_name_0).
next(weak_t,weak_t,trace_name_0).
not_holds_at(a,0,trace_name_0).
not_holds_at(g1,0,trace_name_0).
not_holds_at(g2,0,trace_name_0).
not_holds_at(r1,0,trace_name_0).
not_holds_at(r2,0,trace_name_0).
}).
%---*** Violation Trace ***---

#pos({entailed(counter_strat_0_1)},{},{

% CS_Path: ini_DEAD

trace(counter_strat_0_1).
timepoint(0,counter_strat_0_1).
weak_timepoint(weak_t,counter_strat_0_1).
next(weak_t,0,counter_strat_0_1).
next(weak_t,weak_t,counter_strat_0_1).
not_holds_at(a,0,counter_strat_0_1).
not_holds_at(r1,0,counter_strat_0_1).
holds_at(r2,0,counter_strat_0_1).
holds_at(g1,0,counter_strat_0_1).
not_holds_at(g2,0,counter_strat_0_1).
}).
%---*** Violation Trace ***---

#pos({entailed(counter_strat_43_10)},{},{

% CS_Path: ini_S0_S0

trace(counter_strat_43_10).
timepoint(0,counter_strat_43_10).
timepoint(1,counter_strat_43_10).
next(1,0,counter_strat_43_10).
next(1,1,counter_strat_43_10).
holds_at(a,0,counter_strat_43_10).
holds_at(r1,0,counter_strat_43_10).
holds_at(r2,0,counter_strat_43_10).
holds_at(g1,0,counter_strat_43_10).
not_holds_at(g2,0,counter_strat_43_10).
not_holds_at(a,1,counter_strat_43_10).
not_holds_at(r1,1,counter_strat_43_10).
not_holds_at(r2,1,counter_strat_43_10).
not_holds_at(g1,1,counter_strat_43_10).
not_holds_at(g2,1,counter_strat_43_10).
}).
%---*** Violation Trace ***---

#pos({entailed(counter_strat_101_15)},{},{

% CS_Path: ini_S1_DEAD

trace(counter_strat_101_15).
timepoint(0,counter_strat_101_15).
timepoint(1,counter_strat_101_15).
weak_timepoint(weak_t,counter_strat_101_15).
next(1,0,counter_strat_101_15).
next(weak_t,1,counter_strat_101_15).
next(weak_t,weak_t,counter_strat_101_15).
holds_at(a,0,counter_strat_101_15).
holds_at(r1,0,counter_strat_101_15).
holds_at(r2,0,counter_strat_101_15).
not_holds_at(g1,0,counter_strat_101_15).
not_holds_at(g2,0,counter_strat_101_15).
not_holds_at(a,1,counter_strat_101_15).
not_holds_at(r1,1,counter_strat_101_15).
not_holds_at(r2,1,counter_strat_101_15).
holds_at(g1,1,counter_strat_101_15).
not_holds_at(g2,1,counter_strat_101_15).
}).
