"""Implement abstract classes for building entries and references to import to Weaviate."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, List, Union

from weaviate.util import generate_uuid5


class InvalidReferenceError(Exception):
    """Raised when a reference is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class Entry(ABC):
    """An abstract class for a data entry.

    Args:
        data (dict):
            The data to insert.
        class_name (str):
            The name of the class to insert into Weaviate and must already exist in the schema.
    """

    def __init__(self, data: dict, class_name: str):
        self.data = data
        self.class_name = class_name if class_name else self.__class__.__name__
        self.__references: List[Reference] = []

    def __repr__(self):
        return (
            f"{self.class_name}(data={str(self.data)[:40]}...<truncated, call .data>,"
            f"class_name={self.class_name})"
        )

    @property
    def uuid(self) -> str:
        """Returns a UUID5 based on the data passed to the class."""
        # this must generate a deterministic UUID using the data passed to the class
        return generate_uuid5(identifier=self.data, namespace=self.class_name)

    def add_references(
        self,
        references: List[Reference]
    ) -> None:
        """Adds a reference to the entry.

        Args:
            references (List[Reference]):
                A list of references to add to the entry.

        Raises:
            InvalidReferenceError:
                Raised when the reference does not include self as either a parent or child.
        """
        for ref in references:
            if ref not in self.__references:
                is_child, is_parent = self == ref.child, self == ref.parent
                if not is_child | is_parent:
                    raise InvalidReferenceError(
                        "Reference must include self as either a parent or child"
                    )
                self.__references.append(ref)

    def get_references(self) -> List[Reference]:
        """Retrieve all references to this Entry"""
        return self.__references

    @property
    def has_references(self) -> bool:
        """Convenience property for checking if the entry has any references attached."""
        return any(self.get_references())

    @property
    @abstractmethod
    def entry(self) -> dict:
        """Implement a property that returns a dictionary to be inserted into Weaviate."""


@dataclass(frozen=True)
class Reference(ABC):
    """Reference defines the relationship between two entries.

    Behind the scenes, this reference is used to link Weaviate objects together.
    When a reference is present in an entry, a call to the Weaviate client's
    `add_reference` function is made.
    >>> client.add_reference(
            from_object_class_name=<Reference.parent.class_name>,
            from_object_uuid=<Reference.parent.uuid>,
            from_property_name=<Reference.on_property>,
            to_object_class_name=<Reference.child.class_name>,
            to_object_uuid=<Reference.child.uuid>,
        )
    A reference can be added to the child, the parent, or both, but the
    entry object containing the reference must itself be either a parent
    or a child.

    Args:
        parent (Entry):
            The parent entry object.
        child (Entry):
            The child entry object.
        on_parent_property (str):
            The property on the parent that references the child.
        on_child_property (str):
            The property on the child that references the parent.
            This should only be specified if a two-way reference is desired.
            The child must have a property referencing the parent in the schema.
    """

    parent: Entry
    child: Entry
    on_parent_property: str
    on_child_property: Union[str, None] = None


class Collection(ABC):
    """
    Collection takes in a list of entries and provides a method
    for yielding a single entry in the list
    """

    @abstractmethod
    def get_entries(self) -> Generator[Entry, None, None]:
        """Implement a generator that yields Entry objects"""
