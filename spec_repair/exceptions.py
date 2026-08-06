class NoViolationException(Exception):
    pass


class NoWeakeningException(Exception):
    pass


class NoAssumptionWeakeningException(NoWeakeningException):
    pass


class NoGuaranteeWeakeningException(NoWeakeningException):
    pass


class DeadlockRequiredException(Exception):
    pass


class LearningException(Exception):
    pass


class NameClashException(Exception):
    pass

class InvalidCaseStudyException(Exception):
    """
    The inputs to a repair run do not satisfy its preconditions.

    A repair run assumes two things about its case study:

    1. the input specification is **realisable**, and
    2. the violation trace violates at least one **non-initial** assumption.

    Neither is something the repair can establish for itself, and a case study
    that breaks either is not a hard repair problem - it is a malformed one.
    Raised up front rather than allowed to surface later as a confusing
    downstream failure: a trace that violates nothing sends the search into
    guarantee weakening on an already-realisable specification, where the
    unrealisable core is empty, no guarantee is marked learnable, and the
    learning task comes back UNSAT with the misleading message "No guarantee
    weakening produces realizable spec".
    """


class SpecificationNotVerifiableException(Exception):
    """
    Spectra's CLI cannot check this specification at all.

    Distinct from "unrealisable": the CLI never gave a verdict, because the
    specification breaks one of its structural rules - an initial condition
    referring to a primed (next) variable, or an initial assumption referring to
    a system variable. `violations_in_initial_conditions` detects those up front
    because the CLI reports them inconsistently, and the synthesis wrappers
    return None rather than output.

    A repair candidate that trips this is malformed rather than merely wrong, so
    it is not a solution and must not be recorded as one.
    """
