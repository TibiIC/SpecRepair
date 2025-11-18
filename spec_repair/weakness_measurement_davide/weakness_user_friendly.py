import numpy as np

from spec_repair.weakness_measurement_davide import automaton as a
from spec_repair.weakness_measurement_davide import syntax_utils as su


class Weakness:
    """Weakness measurement for a single GR(1) formula"""
    def __init__(self, d1, d2, nummaxentropysccs=None, d3=None):
        self.d1 = d1 or -np.inf
        self.d2 = d2
        self.nummaxentropysccs = nummaxentropysccs
        self.d3 = d3

    def __str__(self):
        return str((self.d1, self.d2, self.nummaxentropysccs, self.d3))

def computeWeakness(formula, var_set):
    """Compute the weakness of a single complete formula (no base/refinement)."""
    # Initialize parser
    su.parserInit()

    # Build full automaton
    automaton = a.Automaton("ltl", ltlFormula=formula, var_set=var_set)
    d1 = automaton.getEntropy()
    d2 = automaton.getHausdorffDimension()

    # SCC-based d3 calculation
    cfairness = su.getCFairness(formula)
    sccs_maxentropy = automaton.sccs_maxentropy
    num_max_entropy_sccs = len(sccs_maxentropy)

    if cfairness and sccs_maxentropy:
        sccs_automata = []
        for scc in sccs_maxentropy:
            scc_closure = automaton.getSubgraph(scc)
            scc_closure.turnIntoClosure()
            sccs_automata.append(scc_closure)

        cfairness_automata = [a.Automaton("ltl", ltlFormula=f"G({cf})", var_set=var_set)
                              for cf in cfairness]

        max_entropy_deleted_language = -np.inf
        for scc_automaton in sccs_automata:
            for cfair_automaton in cfairness_automata:
                intersection = a.IntersectionAutomaton(scc_automaton, cfair_automaton)
                entropy = intersection.getHausdorffDimension()
                if entropy > max_entropy_deleted_language:
                    max_entropy_deleted_language = entropy
    else:
        max_entropy_deleted_language = -np.inf

    return Weakness(d1, d2, num_max_entropy_sccs, max_entropy_deleted_language)