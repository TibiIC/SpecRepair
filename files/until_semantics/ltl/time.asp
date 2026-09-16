% Time definitions & easy fills

succ(T+1,T,S) :- time(T,S), time(T+1,S).
has_succ(T,S) :- succ(_,T,S).
has_pred(T,S) :- succ(T,_,S).

reach(T,T,S) :- time(T,S).
reach(T,T2,S) :- reach(T,T1,S), succ(T2,T1,S).