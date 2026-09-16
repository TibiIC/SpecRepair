%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Antecedent exception
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% Narrow the antecedent so the rule stops firing on the violating trace.
%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Solution Enumeration
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% The pylasp driver the GR(1) tasks use, verbatim. Without it ILASP prints one
% hypothesis; with it, up to `max_solutions`, each excluded from the next round
% by a constraint over nge_HYP so the search moves on rather than repeating
% itself.
%
% Raising max_solutions costs a full CDILP round per extra solution. 10 matches
% MAX_ASP_HYPOTHESES in spec_repair/config.py, so a repair found here is
% directly comparable with one from the GR(1) pipeline.
%
% The commented-out line inside the loop is ILASP's own: uncomment it to allow
% non-subset-minimal solutions, which surfaces repairs that a strictly minimal
% search discards.

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
% The antecedent is a disjunction of conjunctions. Adding a CONJUNCT to one of
% those conjunctions makes that disjunct harder to satisfy, so the implication
% holds vacuously more often and the formula is WEAKER.
%
%     G( a -> b )   becomes   G( (a & <new>) -> b )
%
% <new> is whatever subtree the learner builds out of the spare nodes: a bare
% atom, a negated atom, or an atom under any temporal operator ltl/ defines -
% including since, release and the weak variants, none of which the original
% antecedent_exception could express.
%
% Run:  ILASP --version=4 files/until_semantics/antecedent_exception.las

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Mode Declaration
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% The heads are the AST predicates themselves - no repair-specific vocabulary.
% A repair IS a set of tree facts, so the learner speaks the same language the
% formula is written in. Nothing here mentions time or trace: the temporal
% behaviour comes from ltl/ evaluating whatever tree it is handed, which is the
% main simplification over the GR(1) encoding where every exception had to
% thread var(time) and var(trace) through itself.

#modeh(conjunction(const(ante_conjunct), const(spare))).
#modeh(atomic(const(spare), const(atom))).
#modeh(negate(const(spare), const(spare))).
#modeh(previous(const(spare), const(spare))).   % strong previous - Spectra's PREV is Y, false at instant 0
#modeh(w_next(const(spare), const(spare))).   % weak next - true at the last instant, so a repair cannot be refuted merely by the trace running out

#constant(atom,a).
#constant(atom,b).
#constant(atom,c).

% A small pool of spare node names for the learner to build with. Widen this to
% let it build deeper subtrees; each extra name multiplies the search space, so
% two is a deliberate starting point rather than a limit.
#constant(spare,x0).
#constant(spare,x1).

% The attachment point. Declared as a constant so the head above can ground -
% without this the modeh is unusable and the whole task silently learns nothing.
#constant(ante_conjunct,f_antecedent_conjunct_0).

#bias("
% #bias is checked PER RULE, so only properties of a single rule belong here.
% Every head below is a ground fact, so what is expressible is exactly: this
% head is never worth proposing. A node that is its own child is the clearest
% case - it makes the tree cyclic and `holds` can never be derived for it.
:- head(conjunction(N,N)).
:- head(negate(N,N)).
:- head(previous(N,N)).
:- head(w_next(N,N)).
% The attachment point is already pinned by const(ante_conjunct) above, which
% declares exactly one value, so no bias constraint is needed for it.
").

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Background Knowledge
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% The evaluator, copied verbatim from ltl/. ILASP needs the task to be
% self-contained, so this is a snapshot: regenerate if ltl/ changes.

% ---- ltl/time.asp ----
succ(T+1,T,S) :- time(T,S), time(T+1,S).
has_succ(T,S) :- succ(_,T,S).
has_pred(T,S) :- succ(T,_,S).
reach(T,T,S) :- time(T,S).
reach(T,T2,S) :- reach(T,T1,S), succ(T2,T1,S).
% ---- ltl/propositional.asp ----
holds(T,X,S) :- trace(T,A,S), atomic(X,A).
holds(T,X,S) :- time(T,S), true(X).
holds(T,X,S) :- negate(X,F), time(T,S), not holds(T,F,S).
holds(T,X,S) :- conjunction(X,_), time(T,S), holds(T,F,S): conjunction(X,F).
holds(T,X,S) :- disjunction(X,F), time(T,S), holds(T,F,S).
holds(T,X,S) :- implies(X,F,G), time(T,S), not holds(T,F,S).
holds(T,X,S) :- implies(X,F,G), time(T,S), holds(T,F,S), holds(T,G,S).
% ---- ltl/future.asp ----
holds(T,X,S) :- next(X,F), time(T,S), holds(T2,F,S), succ(T2,T,S).
holds(T,X,S) :- w_next(X,F), time(T,S), holds(T2,F,S), succ(T2,T,S).
holds(T,X,S) :- w_next(X,F), time(T,S), not has_succ(T,S).
holds(T,X,S) :- until(X,F,G), holds(T,G,S).
holds(T,X,S) :- until(X,F,G), holds(T,F,S), holds(T2,X,S), succ(T2,T,S).
holds(T,X,S) :- w_until(X,F,G), holds(T,G,S).
holds(T,X,S) :- w_until(X,F,G), holds(T,F,S), holds(T2,X,S), succ(T2,T,S).
holds(T,X,S) :- w_until(X,F,G), holds(T,F,S), time(T,S), not has_succ(T,S).
holds(T,X,S) :- release(X,F,G), time(T,S), holds(T2,G,S) : reach(T,T2,S).
holds(T,X,S) :- release(X,F,G), reach(T,T2,S), holds(T2,F,S),
                holds(T3,G,S) : reach(T,T3,S), reach(T3,T2,S).
holds(T,X,S) :- s_release(X,F,G), reach(T,T2,S), holds(T2,F,S),
                holds(T3,G,S) : reach(T,T3,S), reach(T3,T2,S).
holds(T,X,S) :- eventually(X,F), holds(T,F,S).
holds(T,X,S) :- eventually(X,F), holds(T2,X,S), succ(T2,T,S).
holds(T,X,S) :- w_eventually(X,F), holds(T,F,S).
holds(T,X,S) :- w_eventually(X,F), holds(T2,X,S), succ(T2,T,S).
holds(T,X,S) :- w_eventually(X,F), time(T,S), not has_succ(T,S).
holds(T,X,S) :- always(X,F), time(T,S), holds(T2,F,S) : reach(T,T2,S).
% ---- ltl/past.asp ----
holds(T,X,S) :- previous(X,F), succ(T,T1,S), holds(T1,F,S).
holds(T,X,S) :- w_previous(X,F), succ(T,T1,S), holds(T1,F,S).
holds(T,X,S) :- w_previous(X,F), time(T,S), not has_pred(T,S).
holds(T,X,S) :- since(X,F,G), holds(T,G,S).
holds(T,X,S) :- since(X,F,G), holds(T,F,S), holds(T1,X,S), succ(T,T1,S).
holds(T,X,S) :- w_since(X,F,G), holds(T,G,S).
holds(T,X,S) :- w_since(X,F,G), holds(T,F,S), holds(T1,X,S), succ(T,T1,S).
holds(T,X,S) :- w_since(X,F,G), holds(T,F,S), time(T,S), not has_pred(T,S).
holds(T,X,S) :- once(X,F), holds(T,F,S).
holds(T,X,S) :- once(X,F), holds(T1,X,S), succ(T,T1,S).
holds(T,X,S) :- historically(X,F), time(T,S), holds(T1,F,S) : reach(T1,T,S).
% ---- ltl/satisfiability.asp ----
sat(S) :- holds(0,X,S), root(X).

% ---- the specification under repair, from ltl/example.asp ----

root(0).
always(0,f_implication).
implies(f_implication,f_antecedent,f_consequent).
disjunction(f_antecedent,f_antecedent_conjunct_0).

conjunction(f_antecedent_conjunct_0,f_antecedent_conjunct_formula_0).
atomic(f_antecedent_conjunct_formula_0,a).

% conjunction(f_antecedent_conjunct_0,x0).
% atomic(x0,c).

disjunction(f_consequent, f_consequent_conjunct_0).
conjunction(f_consequent_conjunct_0, f_consequent_atom_b).
atomic(f_consequent_atom_b, b).


% ---- well-formedness of whatever the learner builds ----
%
% These constrain the HYPOTHESIS AS A WHOLE - "this node was given two kinds"
% relates two learned facts - so they cannot live in #bias, which is checked one
% rule at a time. As background constraints they reject the ill-formed candidate
% outright, which is the effect wanted.
%
% Scoped to `spare/1` so they never touch the hand-written formula above.

spare(x0).
spare(x1).

kind_of(N,atomic) :- spare(N), atomic(N,_).
kind_of(N,negate) :- spare(N), negate(N,_).
kind_of(N,previous) :- spare(N), previous(N,_).
kind_of(N,w_next) :- spare(N), w_next(N,_).

% One kind per node, or the tree means two things at once.
:- spare(N), #count{ K : kind_of(N,K) } > 1.

% One kind is not enough: `atomic/2` repeated on a node is an OR, so a single
% spare could come back as `a | c` where only a literal was wanted. The disjunct
% layer already expresses that, so allowing it here just gives the solver two
% encodings of one formula to search through.
:- spare(N), #count{ A : atomic(N,A) } > 1.

% A node that is attached but never given a kind can derive no `holds`, so the
% subtree above it is dead and the repair degenerates into deleting whatever it
% was attached to. Cheaper to forbid than to let the negative example catch it.
% A node is `referenced` when something points at it as a child. A referenced
% spare with no kind derives no `holds`, so the subtree above it is dead and the
% repair degenerates into deleting whatever it was attached to. Listing every
% pointing predicate catches a dangle at any depth, not only at the attachment.

referenced(N) :- conjunction(_,N), spare(N).
referenced(N) :- negate(_,N), spare(N).
referenced(N) :- previous(_,N), spare(N).
referenced(N) :- w_next(_,N), spare(N).

:- spare(N), referenced(N), not kind_of(N,_).


% ---- the learned subtree must be a tree, and must be connected ----
%
% Two things the mode declaration can still propose that are simply waste, and
% neither is expressible in #bias because both relate SEVERAL learned facts:
%
%   a cycle       negate(x0,x1), negate(x1,x0). No `holds` is ever derivable
%                 for either node, so the conjunct above them is dead.
%                 Self-loops are caught in #bias, being one rule; a two-node
%                 cycle needs two rules and has to be caught here.
%
%   an orphan     atomic(x1,a) with nothing pointing at x1. Contributes
%                 nothing, but doubles the space it sits in.

points(N,M) :- negate(N,M), spare(N), spare(M).
points(N,M) :- previous(N,M), spare(N), spare(M).
points(N,M) :- w_next(N,M), spare(N), spare(M).

reaches(N,M) :- points(N,M).
reaches(N,M) :- reaches(N,K), points(K,M).
:- spare(N), reaches(N,N).

attached(N) :- ante_conjunct(D), conjunction(D,N), spare(N).
attached(M) :- attached(N), points(N,M).
:- spare(N), kind_of(N,_), not attached(N).

% Attachment points referred to by name above.
ante_conjunct(f_antecedent_conjunct_0).
cons_node(f_consequent).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Examples
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% g1 is the violating trace: a holds at instant 1 and b does not, so
% G(a -> b) fails. The repair has to admit it.

#pos({sat(g1)}, {}, {
  trace_name(g1).
  time(0..1,g1).
  trace(1,a,g1).
}).