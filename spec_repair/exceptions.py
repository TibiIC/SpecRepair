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
