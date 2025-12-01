import pyparsing as pp
import re
import random

# To make the parsing "incredibly faster"
pp.ParserElement.enablePackrat()
# initialList = []
# invariantsList = []
# fairnessList = []

## GR(1) grammar

# --- Put these near the top (replaces your operator declarations slightly) ---

# Use Literal for single-char tokens (avoid Keyword which can match inside identifiers)
un_op = pp.Literal("!") | pp.Literal("X")
always_op = pp.Literal("G")
eventually_op = pp.Literal("F")
until_op = pp.Literal("/U/")

# variables: allow letters + underscore, then digits/letters/underscore
variable = pp.Word(pp.alphas + "_", pp.alphanums + "_")

# whitespace handling: ensure parentheses and operators are tokenized cleanly
LPAREN = pp.Literal("(").suppress()
RPAREN = pp.Literal(")").suppress()

and_op = pp.Literal("&")
or_op = pp.Literal("|")
implies_op = pp.Literal("->")
dimplies_op = pp.Literal("<->")

# boolean constants
const_true = pp.CaselessLiteral("true")
const_false = pp.CaselessLiteral("false")

bool_operand = const_true | const_false | variable

# --- small helper to normalise input before parsing ---
def _pretokenize_phi(s: str) -> str:
    """
    Insert spaces around parentheses and common operators to help pyparsing tokenization.
    This avoids catastrophic backtracking for dense inputs (e.g. G(...)&G(...))
    """
    # Put spaces around parentheses
    s = s.replace("(", " ( ").replace(")", " ) ")
    # Ensure spacing around common operator symbols (->, & , | , ! , /U/ , G F X)
    s = s.replace("->", " -> ").replace("<->", " <-> ")
    s = s.replace("&", " & ").replace("|", " | ").replace("!", " ! ")
    s = s.replace("/U/", " /U/ ")
    # For unary letters ensure spaces: turn 'G(' or 'G (' both handled by parentheses above,
    # also ensure we separate e.g. 'GF(' into 'G F ('
    s = re.sub(r'\bG(?=\s*\w|\s*\()', 'G ', s)
    s = re.sub(r'\bF(?=\s*\w|\s*\()', 'F ', s)
    s = re.sub(r'\bX(?=\s*\w|\s*\()', 'X ', s)
    # collapse multi-spaces
    s = re.sub(r'\s+', ' ', s).strip()
    return s

class BoolOperand(object):
    def __init__(self, t):
        self.operand = t[0]

    def __str__(self):
        return self.operand

    def __eq__(self, other):
        return self.operand == other.operand

    def __ne__(self, other):
        return not self == other
    # Redefine hash to allow uniqueness check in set operations
    def __hash__(self):
        return hash(self.operand)

bool_operand.setParseAction(BoolOperand)

class BoolUnary(object):
    def __init__(self, t):
        self.operator = t[0][0]
        self.operand = t[0][1]
        # If the operand is a ! there is no need of parentheses
        # If it is a temporal operator like X, G, F, it needs parentheses to divide the operator from the first
        # letter of the operand
        self.expression = self.operator+"("+str(self.operand)+")" if self.operator != "!" \
            else self.operator+str(self.operand)

    def __str__(self):
        return self.expression

    def __eq__(self,other):
        return self.expression == other.expression

    def __ne__(self,other):
        return not self == other

    # Redefine hash to allow uniqueness check in set operations
    def __hash__(self):
        return hash(self.expression)

class BoolBinary(object):
    def __init__(self, t):
        self.operator = t[0][1]
        self.args = t[0][0::2]
        self.expression = "(" + str(self.args[0])
        for arg in self.args[1:]:
            self.expression = self.expression + \
                              " " + self.reprsymbol + " " + \
                              str(arg)
        self.expression = self.expression + ")"

    def __str__(self):
        return self.expression

    def __eq__(self,other):
        return self.expression == other.expression
    def __ne__(self,other):
        return not self == other

    # Redefine __hash__ to allow uniqueness check in set operations
    def __hash__(self):
        return hash(self.expression)

class BoolAnd(BoolBinary):
    reprsymbol = '&'

class BoolOr(BoolBinary):
    reprsymbol = '|'

class BoolImplies(BoolBinary):
    reprsymbol = '->'

class BoolDImplies(BoolBinary):
    reprsymbol = '<->'

class Always(BoolUnary):
    reprsymbol = 'G'

class Eventually(BoolUnary):
    reprsymbol = 'F'

class Until(BoolBinary):
    reprsymbol = '/U/'

# --- Build the infixNotation grammars again (unchanged classes reuse) ---
bool_expr = pp.infixNotation(bool_operand,
                             [(un_op, 1, pp.opAssoc.RIGHT, BoolUnary),
                              (and_op, 2, pp.opAssoc.LEFT, BoolAnd),
                              (or_op, 2, pp.opAssoc.LEFT, BoolOr),
                              (implies_op, 2, pp.opAssoc.LEFT, BoolImplies),
                              (dimplies_op, 2, pp.opAssoc.LEFT, BoolDImplies)])

ltl_expr = pp.infixNotation(bool_operand,
                             [(un_op, 1, pp.opAssoc.RIGHT, BoolUnary),
                              (always_op, 1, pp.opAssoc.RIGHT, Always),
                              (eventually_op, 1, pp.opAssoc.RIGHT, Eventually),
                              (and_op, 2, pp.opAssoc.LEFT, BoolAnd),
                              (or_op, 2, pp.opAssoc.LEFT, BoolOr),
                              (implies_op, 2, pp.opAssoc.LEFT, BoolImplies),
                              (dimplies_op, 2, pp.opAssoc.LEFT, BoolDImplies),
                              (until_op, 2, pp.opAssoc.LEFT, Until)])

# class Invariant(object):
#     def __init__(self,t):
#         self.expression = "("+str(t)+")"
#
#     def __str__(self):
#         return self.expression
#
# class Fairness(object):
#     def __init__(self,t):
#         self.expression = "("+str(t)+")"
#
#     def __str__(self):
#         return self.expression
#
# class Initial(object):
#     def __init__(self,t):
#         self.expression = "("+str(t)+")"
#
#     def __str__(self):
#         return self.expression

pars = None

def parserInit():
    """Resets the global parser cache (kept for backward compatibility)."""
    global pars
    pars = None


def _safe_parse(phi: str, grammar):
    """
    Parse phi with given grammar in a safe, local way.
    Returns the parsed tokens or raises a parsing exception.
    """
    if phi == "" or phi is None:
        return None
    phi_norm = _pretokenize_phi(phi)
    # Use parseAll=True to detect trailing junk (helps debugging)
    return grammar.parseString(phi_norm, parseAll=True)


def parseInitials(phi):
    if not phi:
        return []
    try:
        parsed = _safe_parse(phi, ltl_expr)
    except pp.ParseException as e:
        raise ValueError(f"Failed to parse initials: {e}\nInput snippet: {phi[:200]}") from e

    initials = []
    root = parsed[0]
    # When root is not a unary/operand, we expect a BoolBinary with .args
    if not isinstance(root, BoolUnary) and not isinstance(root, BoolOperand):
        for gr1_unit in root.args:
            if not isinstance(gr1_unit, Always):
                initials.append("(" + str(gr1_unit) + ")")
    elif not isinstance(root, Always):
        initials.append("(" + str(root) + ")")

    return initials


def parseInvariants(phi):
    if not phi:
        return []
    try:
        parsed = _safe_parse(phi, ltl_expr)
    except pp.ParseException as e:
        raise ValueError(f"Failed to parse invariants: {e}\nInput snippet: {phi[:200]}") from e

    invariants = []
    root = parsed[0]
    if not isinstance(root, BoolUnary) and not isinstance(root, BoolOperand):
        for gr1_unit in root.args:
            if isinstance(gr1_unit, Always):
                if not isinstance(gr1_unit.operand, Eventually):
                    invariants.append("(" + str(gr1_unit.operand) + ")")
    elif isinstance(root, Always):
        if not isinstance(root.operand, Eventually):
            invariants.append("(" + str(root.operand) + ")")
    return invariants

def _find_balanced(s: str, start_idx: int):
    """
    Given string s and index start_idx pointing at a '(' character,
    return (content, end_idx) where content is the substring inside
    the matching parentheses (without the outer parentheses),
    and end_idx is the index of the closing ')' + 1.
    If parentheses are unbalanced, raises ValueError.
    """
    assert s[start_idx] == '('
    depth = 0
    i = start_idx
    n = len(s)
    i += 1
    depth = 1
    start_content = i
    while i < n:
        ch = s[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return s[start_content:i], i + 1
        i += 1
    raise ValueError("Unbalanced parentheses starting at index {}".format(start_idx))

def parseFairness(phi: str):
    """
    Robust extractor for fairness atoms: finds all boolean subexpressions 'p'
    such that the formula contains G(F(p)) (allowing whitespace and parentheses).
    Returns list of strings like '(p)' or 'p' depending on original form.
    This avoids parsing the entire LTL with pyparsing.
    """
    if not phi:
        return []

    s = phi
    fairness_atoms = []

    i = 0
    n = len(s)
    while i < n:
        # find 'G' character (must not be part of an identifier name)
        # we accept both 'G' and 'G ' and 'G(' forms
        idx = s.find('G', i)
        if idx == -1:
            break
        j = idx + 1
        # skip whitespace
        while j < n and s[j].isspace():
            j += 1
        # accept either '(' directly or something like 'G(' or 'G ('
        if j < n and s[j] == '(':
            try:
                # extract content of G(...)
                g_content, g_end = _find_balanced(s, j)
            except ValueError:
                # malformed G( ... ) - skip this occurrence
                i = idx + 1
                continue

            # now look inside g_content for leading F(...)
            # skip whitespace
            k = 0
            while k < len(g_content) and g_content[k].isspace():
                k += 1
            # Accept forms: F(...), or maybe parentheses around it (e.g., (F(...)))
            if k < len(g_content) and g_content[k] == 'F':
                kk = k + 1
                while kk < len(g_content) and g_content[kk].isspace():
                    kk += 1
                if kk < len(g_content) and g_content[kk] == '(':
                    try:
                        inner, inner_end = _find_balanced(g_content, kk)
                    except ValueError:
                        i = idx + 1
                        continue
                    # inner is the content inside F(...)
                    # Normalize whitespace and parentheses a bit
                    atom = inner.strip()
                    # If the atom is wrapped in parentheses like '(a|b)', keep them consistent:
                    # return with surrounding parentheses if present in original inner
                    atom = atom
                    fairness_atoms.append(
                        "(" + atom + ")" if not (atom.startswith("(") and atom.endswith(")")) else atom)
            # else: maybe there is an F(...) somewhere deeper; do a simple search for 'F(' in g_content
            else:
                fpos = g_content.find('F(')
                if fpos != -1:
                    try:
                        inner, inner_end = _find_balanced(g_content,
                                                          fpos + 1)  # fpos points to 'F', so '(' at fpos+1
                        atom = inner.strip()
                        fairness_atoms.append(
                            "(" + atom + ")" if not (atom.startswith("(") and atom.endswith(")")) else atom)
                    except ValueError:
                        pass
            i = j + (g_end if isinstance(g_end, int) else 0)  # move past this G(...)
        else:
            # If not followed by '(' then skip this 'G' and continue search
            i = j

    return fairness_atoms

def getCFairness(phi: str):
    """Return list of negated fairness atoms: for each G(F(p)) return '!(p)' as string"""
    fairness = parseFairness(phi)
    return ["!(" + x + ")" for x in fairness]

def getInvariant(phi):
    """Given phi, returns a single invariant containing the conjunction of the invariants in phi"""
    if phi == "":
        return []
    invariants = parseInvariants(phi)
    return "G(" + " & ".join(invariants)+")"

def getParseTreeFromBoolean(phi):
    phi = removeUnnecessaryParentheses(phi)
    return bool_expr.parseString(phi)[0]

def removeUnnecessaryParentheses(phi):
    """Given a string containing a Boolean logic expression, removes unnecessary parentheses from it.
    This is to avoid errors when parsing the string due to excessive recursion depth"""

    # Remove parentheses around single literals
    var_pattern = re.compile(r"\((\w+)\)")
    while re.findall(var_pattern,phi) != []:
        phi = re.sub(var_pattern,r"\1",phi)

    # Remove double negations
    idx_double_neg = phi.find("!(!")
    while idx_double_neg != -1:
        # Current recursion depth (the first negation symbol is at depth 0)
        j = 1
        # Current scanned character
        i = idx_double_neg + 3
        no_double_neg = False
        # No double negation if after !(! there is not a parenthesized expression or a literal:
        # !(!var) is a double negation
        # !(!(a & b)) is
        # !(!a & b) is not
        while i < len(phi) and j != 0 and not no_double_neg:
            if phi[i] == "(":
                j = j + 1
            elif phi[i] == ")":
                j = j - 1
            elif j == 1 and (phi[i]=="&" or phi[i]=="|" or phi[i]=="-"):
                no_double_neg = True
            i = i + 1
        if j == 0:
            end_double_neg = i - 1
            phi = phi[0:idx_double_neg]+phi[idx_double_neg+3:end_double_neg]+phi[end_double_neg+1:]
            # Look up for another candidate double negation in the changed string
            idx_double_neg = phi.find("!(!")
        # If going into this branch, the current candidate double
        # negation was not a double negation. phi did not change, so we need to look for the next index containing
        # !(!
        elif idx_double_neg+3 < len(phi):
            offset_double_neg = phi[idx_double_neg+3:].find("!(!")
            if offset_double_neg != -1:
                idx_double_neg = offset_double_neg + idx_double_neg + 3
            else:
                idx_double_neg = -1
        else:
            # No more to check
            idx_double_neg = -1

    return phi


def main():
    print(parseInitials("a"))
    parserInit()
    print(parseInvariants("a & b & G(a) & G(F(c))"))
    parserInit()
    print(getInvariant("G(a & b -> c | d & X(e)) & G(f | g) & G(F(h & !i))"))
    parserInit()
    print(getCFairness("G(a & b -> c | d & X(e)) & G(f | g) & G(F(h & !i))"))
    parserInit()
    print(parseInitials("!b1 & !b2 & !b3 & G((b1 & f1) -> X(!b1)) & G((b2 & f2) -> X(!b2)) & G((b3 & f3) -> X(!b3)) & G((b1 & !f1) -> X(b1)) & G((b2 & !f2) -> X(b2)) & G((b3 & !f3) -> X(b3)) & G((!b1 & !b2 & !b3) -> X(b1 | b2 | b3))"))
    print(getInvariant("!b1 & !b2 & !b3 & G((b1 & f1) -> X(!b1)) & G((b2 & f2) -> X(!b2)) & G((b3 & f3) -> X(!b3)) & G((b1 & !f1) -> X(b1)) & G((b2 & !f2) -> X(b2)) & G((b3 & !f3) -> X(b3)) & G((!b1 & !b2 & !b3) -> X(b1 | b2 | b3))"))
    print(getCFairness("!b1 & !b2 & !b3 & G((b1 & f1) -> X(!b1)) & G((b2 & f2) -> X(!b2)) & G((b3 & f3) -> X(!b3)) & G((b1 & !f1) -> X(b1)) & G((b2 & !f2) -> X(b2)) & G((b3 & !f3) -> X(b3)) & G((!b1 & !b2 & !b3) -> X(b1 | b2 | b3))"))

    parserInit()
    print(str(getParseTreeFromBoolean("a | !b & c & d | e & (!f | !(g & h) | i) | (j)")))

    print("Parentheses cleanup: " + removeUnnecessaryParentheses("(a & !(!(b))) & !(!(b & (c) & !d)) & ((((d)))) & !(!e)"))


if(__name__=="__main__"):
    main()