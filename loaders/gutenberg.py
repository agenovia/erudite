"""Gutenberg JSON importer"""
from __future__ import annotations

from functools import reduce
from operator import concat
from weaviate import Client
from typing import Generator

from .common.types import Collection, Entry, Reference
from .common.util import WeaviateImporter


class Book(Entry):
    """A book entry."""

    @property
    def entry(self) -> dict:
        """Get the title and author of the book."""
        return {
            "title": self.data["title"],
            "author": self.data["author"],
        }

    def get_chapters(self) -> Generator[Chapter, None, None]:
        """Get the chapters of the book."""
        for chap in self.data["chapters"]:
            # TODO(agenovia) change the way we add references
            # every time chapters is called, a new chapter object is created
            # we don't want that
            _chap = Chapter(chap, class_name="Chapter")
            _contains = Reference(
                parent=self, child=_chap, on_parent_property="chapters"
            )
            _container = Reference(
                parent=_chap, child=self, on_parent_property="containedIn"
            )
            self.add_references([_contains])
            _chap.add_references([_container])
            yield _chap

    def get_meta(self):
        """Get the metainfo of the book."""
        _meta = Meta(self.data, class_name="Meta")
        _contains = Reference(parent=self, child=_meta, on_parent_property="meta")
        _container = Reference(
            parent=_meta, child=self, on_parent_property="containedIn"
        )
        self.add_references([_contains])
        _meta.add_references([_container])
        return _meta


class Meta(Entry):
    """A meta entry."""

    @property
    def entry(self) -> dict:
        """Get the meta details of the book."""
        return {
            "language": self.data["meta"]["language"],
            "subject": self.data["meta"]["subject"],
            "citation": self.data["meta"]["citation"],
        }


class Chapter(Entry):
    """A chapter entry."""

    @property
    def entry(self) -> dict:
        """Get the chapter details of the book."""
        return {
            "title": self.data["title"],
            "seq": self.data["seq"],
            "text": self.data["text"],
        }

    def get_paragraphs(self) -> Generator[Paragraph, None, None]:
        for para in self.data["paragraphs"]:
            _para = Paragraph(para, class_name="Paragraph")
            _reference = Reference(
                parent=self, child=_para, on_parent_property="paragraphs"
            )
            _contained_in = Reference(
                parent=_para, child=self, on_parent_property="containedIn"
            )
            self.add_references([_reference])
            _para.add_references([_contained_in])
            yield _para


class Paragraph(Entry):
    """A paragraph entry."""

    @property
    def entry(self) -> dict:
        """Get the chapter details of the book."""
        return {
            "seq": self.data["seq"],
            "text": self.data["text"],
        }


class BookCollection(Collection):
    """Book contains at least one chapter, and each chapter contains at least on paragraph.
    This collection is used to iterate over the book and yield each entry."""

    def __init__(self, book: Book):
        self.book = book

    def get_entries(self):
        """Generator that yields a single entry from the book object."""
        _chapters = list(self.book.get_chapters())
        _paragraphs = reduce(
            concat, map(lambda chap: list(chap.get_paragraphs()), _chapters)
        )
        entries = [self.book, self.book.get_meta(), *_chapters, *_paragraphs]
        for entry in entries:
            yield entry


def main(json_obj: dict, client: Client, class_name="Book"):
    """Main function."""
    book = Book(json_obj, class_name=class_name)
    book_collection = BookCollection(book)
    importer = WeaviateImporter(client, book_collection)
    importer.run()
