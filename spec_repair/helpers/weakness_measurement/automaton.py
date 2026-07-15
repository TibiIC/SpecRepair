import itertools
import re
import subprocess
import timeit

import dd
import numpy as np
import tarjan

class Automaton:
    """Defines the Buchi automaton corresponding to an LTL formula"""

    def __init__(self,sourceType,**kwargs):
        """- sourceType can be 'ltl' or 'smv' or 'buchi_hoa'
           - If sourceType=='ltl' kwargs contains
                - an ltlFormula field with the LTL formula
                - a var_set field with the variables in the model
           - If sourceType=='smv' kwargs contains
                a file field with the .smv file containing the Kripke structure file
           - If sourceType=='buchi_hoa' kwargs contains
                - a hoa_file field with the HOA description of a Buchi automaton
                - a var_set field with the variables in the model
           - If sourceType=='manual', then the fields must be included manually"""

        # Init graph structure
        self.numstates = 0  # Total number of states. States are numbered from 0 to numstates-1
        self.edges = []  # Each edge is a quadruple [id_src, label, id_dest, multiplicity].
        # An edge may correspond to more than one transition, according to the logical expression in label.
        # multiplicity is the number of transitions it corresponds. It is redundant information
        self.init_states = []  # Ids of initial states
        self.accepting_states = []  # Ids of accepting states
        self.edge_vars = []  # List of variables occurring in edge label formulae (subset of var_set)

        self.sccs = [] # List of SCCs. Used to buffer the results of getSCCs()
        self.accepting_sccs_indices = [] # List of accepting SCCs. Used to buffer the results of getAcceptingSCCs()
        self.coreachable_sccs_indices = [] # List of co-reachable SCCs. Used to buffer the results of getCoReachableSCCs
        self.sccs_entropies = [] # List of entropies of each SCC. Used to buffer the results of getEntropy()
        self.is_strongly_connected = None # getHausdorffDimension decides whether the automaton is strongly connected
        self.sccs_maxentropy = [] # List of accepting SCCs with max entropy. Used to buffer the results of getHausdorffDimension()

        # TIME PROBE: Check time to generate automaton
        start = timeit.default_timer()

        # If the source is an LTL formula, read it and convert it to a Buchi automaton
        if sourceType == "ltl":
            self.ltlFormula = kwargs["ltlFormula"]
            self.var_set = kwargs["var_set"]  # Full set of variables of the model (includes unconstrained vars not appearing in ltlFormula)

            #self._getVarsFromFormula()
            self.reduced = True  # When reduced is true, use overflow avoidance trick
            self._LTL2Buchi(self.ltlFormula)

        elif sourceType == "buchi_hoa":
            self.hoa_file = kwargs["hoa_file"]

            #self._getVarsFromHOA()
            self.reduced = True

            if "var_set" in kwargs.keys():
                self.var_set = kwargs["var_set"]
            else:
                self.var_set = self._getVarsFromHOA()

            hoa_stream = open(self.hoa_file,"r")
            self._convertHOA2Automaton(hoa_stream)
            hoa_stream.close()

        # TIME PROBE STOP
        self.automaton_compute_time = timeit.default_timer() - start


    def _getVarsFromHOA(self):
        hoa_stream = open(self.hoa_file,"r")

        for line in hoa_stream.readlines():
            if line.startswith("AP:"):
                # Variables are listed in this line in quotes and separated by blanks
                # s[index("\"")+1:-2] deletes first and last quotes along with the prefix "AP: <n>", split takes care of the middle ones
                hoa_var_set = line[line.index("\"")+1:-2].split("\" \"")
                break

        hoa_stream.close()
        return hoa_var_set


    def _getVarsFromFormula(self):
        """Get the set of variables appearing in the LTL formula. Used in overflow avoidance tricks"""

        # candidateVars contains all alphanumeric substrings in formula.
        # Turned to set to eliminate duplicates
        candidateVars = list(set(re.findall(r"\w+", self.ltlFormula)))
        # Delete X operator from variables
        candidateVars = map(lambda x: x[1:] if x.startswith("X") else x,candidateVars)

        # Temporal operators must be removed
        if 'G' in candidateVars: candidateVars.remove('G')
        if 'X' in candidateVars: candidateVars.remove('X')
        if 'F' in candidateVars: candidateVars.remove('F')

        self.constrained_var_set = candidateVars


    def _LTL2Buchi(self,ltlFormula):
        """Calls the external tool Spot to compute the automaton corresponding to the LTL formula"""

        # shlex.split splits the string according to shell format
        # subprocess.PIPE is needed to pipe the standard output of ltl2tgba to the standard input of this Python script
        cmd = ["ltl2tgba", "-B", "-S", "-D", "-f", ltlFormula]
        with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
            self._convertHOA2Automaton(p.stdout)
            p.wait()


    def _convertHOA2Automaton(self, hoa_stream):
        """Robust parsing of Spot's HOA format without relying on strict ordering."""

        # ---- Read and normalize entire HOA text ----
        text = hoa_stream.read().decode('utf-8', errors='replace')
        lines = [line.strip() for line in text.splitlines()]

        # ---- helpers ----
        def find_line(prefix):
            for line in lines:
                if line.startswith(prefix):
                    return line
            return None

        # -------------------------
        # 1. Parse number of states
        # -------------------------
        m = re.search(r"States:\s*(\d+)", text)
        if not m:
            raise ValueError("Could not find 'States:' entry in HOA.")
        self.numstates = int(m.group(1))

        # -------------------------
        # 2. Parse initial states
        # -------------------------
        m = re.search(r"Start:\s*([0-9 ]+)", text)
        if not m:
            raise ValueError("Could not find 'Start:' entry in HOA.")

        init_list = [int(s) for s in m.group(1).split()]
        if not init_list:
            raise ValueError("HOA reports no initial states.")

        self.init_states = init_list[:1]  # take first (Spot only uses one)

        # -------------------------
        # 3. Parse atomic propositions (AP section)
        # -------------------------
        ap_line = find_line("AP:")
        if ap_line is None:
            raise ValueError("Could not find AP: entry in HOA.")

        # Example: AP: 3 "p" "q" "r"
        m = re.match(r'AP:\s*(\d+)(.*)', ap_line)
        ap_count = int(m.group(1))

        if ap_count == 0:
            # TRUE/FALSE case
            self.constrained_var_set = self.var_set
        else:
            # Extract strings inside quotes
            props = re.findall(r'"([^"]+)"', ap_line)
            self.constrained_var_set = props

        # -------------------------
        # 4. Parse all states and transitions
        # -------------------------
        self.accepting_states = []
        self.edges = []

        # Regex patterns
        state_header_re = re.compile(r"State:\s*(\d+)(?:\s*\{([^}]*)\})?")
        edge_re = re.compile(r'\[(.*?)\]\s*([0-9]+)')

        current_state = None

        for line in lines:
            # Match state headers
            st = state_header_re.match(line)
            if st:
                current_state = int(st.group(1))
                if st.group(2) is not None:
                    # Accepting state
                    self.accepting_states.append(current_state)
                continue

            # Match transitions
            ed = edge_re.match(line)
            if ed and current_state is not None:
                raw_formula = ed.group(1)
                dst = int(ed.group(2))

                # Replace AP index numbers with actual variable names
                def repl(m):
                    idx = int(m.group())
                    return self.constrained_var_set[idx]

                formula = re.sub(r'\b[0-9]+\b', repl, raw_formula)
                formula = formula.replace("!", "~")
                formula = re.sub(r"\bt\b", "TRUE", formula)

                if self.reduced:
                    multiplicity = self._getEdgeReducedMultiplicity(formula)
                else:
                    multiplicity = self._getEdgeMultiplicity(formula)

                self.edges.append([current_state, formula, dst, multiplicity])

    def _getEdgeMultiplicity(self,formula):
        """Returns the number of variable assignments satisfying the label formula in edge"""

        # Extract all variables in the formula. Take distinct entries only.
        # Do not list constants as variables
        vars = list(set(re.findall(r"\b(?!TRUE|FALSE)\w+",formula)))
        # Reformat constants in dd syntax
        formula = formula.replace("TRUE","True").replace("FALSE","False")

        # Build a BDD object
        bdd = dd.BDD()
        [bdd.add_var(var) for var in vars]
        node = bdd.add_expr(formula)

        # BDD.count gets the number of satisfying assignments for the BDD
        # The number is multiplied by a factor accounting for the unconstrained variables in the formula
        # ** is exponentiation
        return node.count(nvars=len(vars))*2**(len(self.var_set)-len(vars))

    def _getEdgeReducedMultiplicity(self, formula):
        """Computes the multiplicity of an edge by neglecting variables not appearing in the formula"""

        # Extract all variables in the formula. Take distinct entries only.
        # Do not list constants as variables
        vars = list(set(re.findall(r"\b(?!TRUE|FALSE)\w+",formula)))
        # Reformat constants in dd syntax
        formula = formula.replace("TRUE","True").replace("FALSE","False")

        # Build a BDD object
        bdd = dd.BDD()
        [bdd.add_var(var) for var in vars]
        node = bdd.add_expr(formula)

        # BDD.count gets the number of satisfying assignments for the BDD
        # The number is multiplied by a factor accounting for the unconstrained variables in the formula
        # ** is exponentiation
        return node.count(nvars=len(vars)) * 2 ** (len(self.constrained_var_set) - len(vars))

    def getAdjacencyMatrix(self):
        """Returns the adjacency matrix of the automaton"""
        mat = np.zeros([self.numstates,self.numstates],np.int32)
        for edge in self.edges:
            # Assign edge multiplicity to the (id_src,id_dst) matrix element
            mat[edge[0]][edge[2]] = edge[3]
        return mat

    def reachable(self, graph, node, reached):
        """Returns the set of all reachable states from the initial one (return type: set)"""

        reached.update([node])
        adjacent = graph.get(node)

        if adjacent is not None:
            for subnode in adjacent:
                if subnode not in reached:
                    reached.update(self.reachable(graph, subnode, reached))
        return reached

    def getCoReachableSCCs(self):
        if self.coreachable_sccs_indices == []:
            sccs = self.getSCCs()
            coreach_list = self.getCoReachabilityList()
            accepting_sccs = self.getAcceptingSCCs()

            coreachable_states = set([])
            for accepting_scc in accepting_sccs:
                coreachable_states.update(self.reachable(coreach_list, self.sccs[accepting_scc][0], coreachable_states))

            self.coreachable_sccs_indices = [self.sccs.index(scc) for scc in sccs if scc[0] in coreachable_states]
        return self.coreachable_sccs_indices

    def getSCCs(self):
        """Returns all SCCs of the automaton reachable from the initial state."""
        if self.sccs == []:
            adjList = self.getAdjacencyList()
            reachable_states = self.reachable(adjList, self.init_states[0], set([]))

            self.sccs = [x for x in tarjan.tarjan(adjList) if not not set(x).intersection(reachable_states)]

            if len(self.sccs) == 1:
                self.is_strongly_connected = True
            else:
                self.is_strongly_connected = False
            return self.sccs
        else:
            return self.sccs

    def getAcceptingSCCs(self):
        if self.accepting_sccs_indices == [] and self.accepting_states != []:
            accepting_sccs = self.getSCCs()
            # Different behavior for Buchi and Generalized Buchi
            if type(self.accepting_states[0]) == int:
                self.accepting_sccs_indices = [self.sccs.index(x) for x in self.sccs if not not set(x).intersection(set(self.accepting_states))]
            else:
                for accepting_set in self.accepting_states:
                    # Remove the sccs that have no intersection with accepting_set
                    accepting_sccs = [x for x in accepting_sccs if not not set(x).intersection(set(accepting_set))]
                self.accepting_sccs_indices = [self.sccs.index(x) for x in accepting_sccs]
        return self.accepting_sccs_indices

    def turnIntoClosure(self):
        """Transforms self into the automaton of its closure. In the closure, every state is an accepting state"""
        self.accepting_states = range(self.numstates)
        self.accepting_sccs_indices = self.sccs
        self.coreachable_sccs_indices = self.sccs
        self.sccs_entropies = []

    def getEntropiesSCCs(self):
        if self.sccs_entropies == []:
            self.getSCCs()
            self.sccs_entropies = [None] * len(self.sccs)
            sccs_indices = self.getCoReachableSCCs()
            adjMatrix = self.getAdjacencyMatrix()
            for scc in sccs_indices:
                submatrix = adjMatrix[np.ix_(self.sccs[scc], self.sccs[scc])]
                maxeig = np.max(np.absolute(np.linalg.eig(submatrix)[0]))
                if self.reduced:
                    # Overflow avoidance (see Notebook 2 pag. 6)
                    if maxeig == 0:
                        entropy = 0
                    else:
                        entropy = (len(self.var_set) - len(self.constrained_var_set) + np.log2(maxeig)) / len(self.var_set)

                    self.sccs_entropies[scc] = entropy
                else:
                    self.sccs_entropies[scc] = (np.log2(maxeig) / len(self.var_set))
        return self.sccs_entropies


    def getEntropy(self):
        return max(self.getEntropiesSCCs() or [0])


    def getHausdorffDimension(self):
        """Computes the Hausdorff Dimension of the automaton's accepted language."""

        accepting_sccs = self.getAcceptingSCCs()
        hausdim = max([self.getEntropiesSCCs()[i] for i in accepting_sccs] or [0])
        self.sccs_maxentropy = [
            scc for scc, ent in zip(self.sccs, self.sccs_entropies)
            if ent == hausdim
        ]
        return hausdim


    def getAdjacencyList(self):
        """Returns the adjacency list of the automaton (without multiplicities)"""
        list = dict()
        for i in range(0,self.numstates):
            list[i] = []
            for edge in self.edges:
                # If edge source is i
                if edge[0] == i:
                    # Add edge dest to adjacent nodes of i
                    list[i].append(edge[2])
        return list

    def getCoReachabilityList(self):
        """Returns the adjacency list after inverting the direction of all arcs"""
        list = dict()
        for i in range(0,self.numstates):
            list[i] = []
            for edge in self.edges:
                # If edge source is i
                if edge[2] == i:
                    # Add edge dest to adjacent nodes of i
                    list[i].append(edge[0])
        return list

    def getSubgraph(self, state_list):
        """Returns the subgraph induced by the state_list in input. Edges are only included if both the nodes they insist
        onto are in state_list"""

        subgraph = Automaton("manual")
        subgraph.var_set = self.var_set
        subgraph.constrained_var_set = self.constrained_var_set
        subgraph.reduced = self.reduced

        subgraph.numstates = len(state_list)

        # state_list contains the ids of the states as they are identified in the original automaton
        # self.
        # Also self.edges uses those ids. But in the subgraph we need to identify them progressively
        # to keep consistency. So subgraph.edges first reads the edges and then those are transformed
        # to use the new ids for the states
        subgraph.edges = [x for x in self.edges if x[0] in state_list and x[2] in state_list]
        for edge in subgraph.edges:
            edge[0] = state_list.index(edge[0])
            edge[2] = state_list.index(edge[2])

        # Any initial state will not change the Hausdorff dimension. Set it to state 0
        subgraph.init_states = [0]


        # Same applies to state ids in accepting states
        # In a Buchi automaton accepting_states is just a list of states, while in a GBA it is
        # a collection of lists of states
        if self.accepting_states != [] and type(self.accepting_states[0]) == int:
            subgraph.accepting_states = [state_list.index(x) for x in state_list if x in self.accepting_states]
        else:
            subgraph.accepting_states = []
            for accepting_set in self.accepting_states:
                subgraph.accepting_states.append([state_list.index(x) for x in state_list if x in accepting_set])

        return subgraph

#######################################################################################################################

class IntersectionAutomaton(Automaton):

    def __init__(self,a1,a2):

        # TIME PROBE: Check time to generate automaton
        start = timeit.default_timer()

        # The states of the intersection automaton are all combinations of a state of a1 and a state of a2
        self.states = list(itertools.product(range(0,a1.numstates),range(0,a2.numstates)))
        self.numstates1 = a1.numstates
        self.numstates2 = a2.numstates
        self.numstates = len(self.states)
        self.reduced = True # For overflow avoidance in Hausdim computation
        # A non-deadlocking edge in the intersection automaton is a combination of an edge in a1 and one in a2
        self.edges = [] # Each edge is a 4-element list [id_src formula id_dest multiplicity]
        self.var_set = list(set(a1.var_set + a2.var_set))
        self.constrained_var_set = list(set(a1.constrained_var_set + a2.constrained_var_set))
        self.init_states =[self._linearizedStateID(a,b) for a in a1.init_states for b in a2.init_states]
        self.accepting_states = [a1.accepting_states,a2.accepting_states]

        self.sccs = [] # List of SCCs. Used to buffer the results of getSCCs()
        self.accepting_sccs_indices = [] # List of accepting SCCs. Used to buffer the results of getAcceptingSCCs()
        self.coreachable_sccs_indices = [] # List of co-reachable SCCs. Used to buffer the results of getCoReachableSCCs
        self.sccs_entropies = [] # List of entropies of each SCC. Used to buffer the results of getEntropy()
        self.is_strongly_connected = None # getHausdorffDimension decides whether the automaton is strongly connected
        self.sccs_maxentropy = [] # List of accepting SCCs with max entropy. Used to buffer the results of getHausdorffDimension()

        for edge1 in a1.edges:
            for edge2 in a2.edges:
                # The formula of the edge is the 'and' between the formula of edge1 and the formula of edge2
                formula = "("+ edge1[1] + ") & (" + edge2[1] + ")"
                multiplicity = self._getEdgeReducedMultiplicity(formula) if self.reduced else self._getEdgeMultiplicity(formula)
                # If the multiplicity of this formula is 0, then do not add the edge
                if multiplicity > 0:
                    self.edges.append([self._linearizedStateID(edge1[0],edge2[0]),formula,self._linearizedStateID(edge1[2],edge2[2]),multiplicity])

        # TIME PROBE STOP
        self.automaton_compute_time = timeit.default_timer() - start

    def _linearizedStateID(self,i,j):
        """In the intersection automaton states are denoted by pairs of state IDs from two automata. Return a linearized index
        for the given state (i,j), linearized by sorting the pairs by increasing i's and then by increasing j's"""

        return i*self.numstates2+j

    def _stateIDAsPair(self,lin_id):
        return (int(lin_id/self.numstates2),lin_id%self.numstates2)

    def getAcceptingSCCs(self):
        """If the automaton comes from an intersection, it has two accepting sets. The first one has indices from the
        first automaton and the second one from the second automaton"""
        if self.accepting_sccs_indices == []:
            sccs = self.getSCCs()
            for i,scc in enumerate(sccs):
                accepting_aut_1 = False
                accepting_aut_2 = False
                scc_pairs = [self._stateIDAsPair(x) for x in scc]
                s = 0
                while s < len(scc_pairs) and not (accepting_aut_1 and accepting_aut_2):
                    if scc_pairs[s][0] in self.accepting_states[0]:
                        accepting_aut_1 = True
                    if scc_pairs[s][1] in self.accepting_states[1]:
                        accepting_aut_2 = True
                    s += 1
                if accepting_aut_1 and accepting_aut_2:
                    self.accepting_sccs_indices.append(i)
        return self.accepting_sccs_indices
