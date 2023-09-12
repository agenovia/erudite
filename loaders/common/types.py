"""Base classes for building entries, references and batches to import to Weaviate."""
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

    Each object inserted into Weaviate must be of this type. If multiple Entries are to be
    inserted, then a Batch object must be used that implements the `get_entries` method to
    yield each Entry.

    Args:
        data (dict): The data to insert.
        class_name (str):
            The name of the class to insert into Weaviate. Must already exist in the schema.
            Will default to self.__class__.__name__ if not provided.

    Properties:
        uuid: A UUID5 id generated from the data and class_name.
        entry: A dictionary to be inserted into Weaviate.
        has_references: A boolean indicating if the entry has any references attached.

    Methods:
        add_references: Adds a reference to the entry.
        get_references: Retrieve all references to this Entry
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
        """Generates a UUID for the entry.

        This method calls weaviate.util.generate_uuid5 using the data as the identifier
        and self.class_name as the namespace. This ensures uniqueness within the given
        Weaviate class.

        Returns:
            str: A UUID5 id.
        """
        # this must generate a deterministic UUID using the data passed to the class
        return generate_uuid5(identifier=self.data, namespace=self.class_name)

    def add_references(self, references: List[Reference]) -> None:
        """Adds a reference to the entry.

        Args:
            references (List[Reference]): A list of references to add to the entry.

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
        """Retrieve all references to this Entry

        Returns:
            List[Reference]: A list of references to this Entry
        """
        return self.__references

    @property
    def has_references(self) -> bool:
        """Convenience property for checking if the entry has any references attached.

        Returns:
            bool: True if the entry has references, False otherwise.
        """
        return any(self.get_references())

    @property
    @abstractmethod
    def entry(self) -> dict:
        """Implement a property that returns a dictionary to be inserted into Weaviate.

        Returns:
            dict: A dictionary object to be inserted into Weaviate.
        """


@dataclass(frozen=True)
class Reference:
    """Defines the relationship between two entries.

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

    A reference can be added to the child or the parent, but the
    entry object containing the reference must itself be either a parent
    or a child.

    While the same reference can be added to both the child and the parent to
    establish a two-way reference, it is preferable to specify the `on_child_property`
    argument instead. WeaviateImporter will ensure that the reference is added
    properly to the parent and its child.

    Args:
        parent (Entry):
            The parent entry object.
        child (Entry):
            The child entry object.
        on_parent_property (str):
            The property on the parent that references the child.
        on_child_property (str):
            The property on the child that references the parent; used when
            a two-way reference is desired.

            When adding a two-way reference, first ensure that the child has
            the necessary property within the Weaviate database schema to
            reference the parent. Then, specify the property name here.
    """

    parent: Entry
    child: Entry
    on_parent_property: str
    on_child_property: Union[str, None] = None


class Batch(ABC):
    """
    This class is implemented to handle entries with nested sub-entries that must be
    inserted to Weaviate individually. For example, a book may have multiple chapters,
    each a separate `Entry` that has a title, a sequence id and a reference to an array of
    paragraphs, itself containing multiple `Entry` objects with a reference to its parent
    chapter.

    This class is used to iterate over each sub-entry and yield a single entry.

    The importer will then check if the data is a single entry or a collection of entries
    and call the appropriate method.

    Methods:
        get_entries: A generator that yields Entry objects.
    """

    @abstractmethod
    def get_entries(self) -> Generator[Entry, None, None]:
        """Implement a generator that yields Entry objects"""
