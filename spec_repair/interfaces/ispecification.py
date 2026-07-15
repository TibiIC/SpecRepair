from abc import ABC, abstractmethod


class ISpecification(ABC):
    @abstractmethod
    def to_str(self) -> str:
        """
        Convert the specification to a string representation.
        """
        pass

    @abstractmethod
    def to_asp(self, for_clingo):
        """
        Generate ASP representation of the specification.
        """
        pass