class AdaptationLearned:
    """
    Represents an adaptation learned from a violation of a specification.
    It is a decoding of the output that is produced by ILASP during learning,
    and is used to structure and extract the learned adaptation.
    """

    def __init__(self, type, name_expression, disjunction_index, atom_temporal_operators):
        """
        :param type: The type of the adaptation learned (i.e. antecedent_exception, consequent_exception, etc).
        :param name_expression: The name of the invariant/justice goal that will be adapted.
        :param disjunction_index: The index of the disjunction that will be adapted within the expression.
        :param atom_temporal_operators: The atoms and their respective temporal operators used in the adaptation.
        """
        self.type = type
        self.name_expression = name_expression
        self.disjunction_index = disjunction_index
        self.atom_temporal_operators = atom_temporal_operators


