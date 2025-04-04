from py_ltl.parser import ILTLParser
from py_ltl.formula import AtomicProposition, Not, And, Implies, Or, Until, Next, Globally, Eventually
from pyparsing import Word, alphas, opAssoc, infixNotation, alphanums, Literal, oneOf


class SpectraFormulaParser(ILTLParser):
    """Parser for LTL formulas from strings in Spectra encoding using pyparsing."""
    def __init__(self):
        # Define atomic propositions (letters and optional values)
        identifier = Word(alphas, alphanums + "_")
        equals = Literal("=")
        value = Word(alphas) | Word("0123456789")

        # Ensure assignments are matched as a single unit FIRST
        atomic_with_value = (identifier + equals + value).setParseAction(self._parse_atomic)
        atomic_alone = identifier.setParseAction(lambda t: AtomicProposition(str(t[0]), True))

        self.operand = atomic_with_value | atomic_alone

        NOT = oneOf(["!"])
        AND = oneOf(["&"])
        OR = oneOf(["|"])
        IMPLIES = oneOf(["->"])
        UNTIL = oneOf(["U"])
        NEXT = oneOf(["X", "next"])
        GLOBALLY = oneOf(["G", "alw"])
        EVENTUALLY = oneOf(["F"])

        # Define operators
        self.operators = [
            (NOT, 1, opAssoc.RIGHT, self._parse_not),
            (NEXT, 1, opAssoc.RIGHT, self._parse_next),
            (GLOBALLY, 1, opAssoc.RIGHT, self._parse_globally),
            (EVENTUALLY, 1, opAssoc.RIGHT, self._parse_eventually),
            (AND, 2, opAssoc.LEFT, self._parse_and),
            (OR, 2, opAssoc.LEFT, self._parse_or),
            (IMPLIES, 2, opAssoc.RIGHT, self._parse_implies),
            (UNTIL, 2, opAssoc.LEFT, self._parse_until),
        ]

        # Define the grammar using infix notation
        self.expression = infixNotation(
            self.operand,
            [(op, num, assoc, fn) for op, num, assoc, fn in self.operators]
        )

    def _parse_atomic(self, tokens) -> AtomicProposition:
        if len(tokens) == 1:
            return AtomicProposition(tokens[0], True)  # Default value is True
        elif len(tokens) == 3 and tokens[1] == "=":
            if isinstance(tokens[0], AtomicProposition):
                atom_name = tokens[0].name
            else:
                atom_name = tokens[0]
            value = tokens[2].lower()
            if value == "true":
                value = True
            elif value == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            else:
                raise ValueError(f"Invalid value for atomic proposition: {value}")
            return AtomicProposition(atom_name, value)

        else:
            raise ValueError(f"Unexpected atomic format: {tokens}")

    def _parse_not(self, tokens):
        return Not(tokens[0][1])

    def _parse_and(self, tokens):
        return And(tokens[0][0], tokens[0][2])

    def _parse_implies(self, tokens):
        return Implies(tokens[0][0], tokens[0][2])

    def _parse_or(self, tokens):
        return Or(tokens[0][0], tokens[0][2])

    def _parse_until(self, tokens):
        raise NotImplementedError("Until operator does not make sense in this context")

    def _parse_next(self, tokens):
        return Next(tokens[0][1])

    def _parse_globally(self, tokens):
        return Globally(tokens[0][1])

    def _parse_eventually(self, tokens):
        return Eventually(tokens[0][1])

    def parse(self, expression: str):
        """Parse a string into an LTL formula object."""
        return self.expression.parseString(expression, parseAll=True)[0]
