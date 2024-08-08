from typing import Generic, Optional, List

from spec_repair.heuristics import T


class Recorder(Generic[T]):
    def __init__(self):
        self._set: set[T] = set()
        self._value_to_id: dict[T, int] = {}
        self._next_id: int = 0

    def add(self, value: T) -> int:
        """
        Adds an element to the set if it's not already present and assigns it a unique ID.
        Returns the ID of the element.
        :param value: The element to add.
        :return: The ID of the element.
        """
        if value not in self._set:
            self._set.add(value)
            self._value_to_id[value] = self._next_id
            self._next_id += 1
        return self._value_to_id[value]

    def get_id(self, value: T) -> Optional[int]:
        """
        Returns the ID associated with the element, or None if the element is not present.
        :param value: The element to get the ID for.
        :return: The ID of the element, or None if the element is not present.
        """
        return self._value_to_id.get(value)

    def get_element_by_id(self, id_: int) -> Optional[T]:
        """
        Returns the element associated with the given ID, or None if no such element exists.
        :param id_: The ID to get the element for.
        :return: The element associated with the ID, or None if no such element exists.
        """
        for elem, elem_id in self._value_to_id.items():
            if elem_id == id_:
                return elem
        return None

    def get_all_values(self) -> List[T]:
        """
        Returns a list of all unique elements stored in the set.
        :return: A list of all unique elements stored in the set.
        """
        return list(self._set)

    def get_all_ids(self) -> List[int]:
        """
        Returns a list of all unique IDs currently in use.
        :return: A list of all unique IDs currently in use.
        """
        return list(self._value_to_id.values())

    def __contains__(self, element: T) -> bool:
        """
        Checks if an element is in the ElementManager.
        Returns True if the element is present, otherwise False.
        :param element: The element to check for.
        :return: True if the element is present, otherwise False.
        """
        return element in self._set
