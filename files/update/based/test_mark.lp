#pos({p(a)}, {}).

#constant(domain, a).
#constant(domain, b).

#modeh(p(const(domain))).
#modeh(used(const(domain))).
#bias("
  attribute(in_head(X)) :- head(X).
").
#inject("
  all_active.
  attribute(X) :- active(R), attribute(R, X).
  :- attribute(in_head(p(X))), not attribute(in_head(used(X))).
").