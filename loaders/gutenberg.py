"""Gutenberg JSON importer"""
from __future__ import annotations

from functools import reduce
from operator import concat
from typing import Generator

from weaviate import Client

from loaders.common.types import Reference

from .common.types import Batch, Entry, Reference
from .common.util import WeaviateImporter


class Book(Entry):
    """A book entry.

    A book is deeply nested. It contains the chapters, which in turn contain the paragraphs.
    As of the current Weaviate version, it is not possible to create a nested object in a single
    request. Therefore, the book must be unnested into individual entries
    (i.e Book, Meta, Chapter, Paragraph) before insertion.

    Properties:
        entry: Returns the title and author of the book.

    Methods:
        get_chapters: Returns a generator that yields each chapter `Entry`.
        get_meta: Returns the meta `Entry`.
    """

    @property
    def entry(self) -> dict:
        """Get the title and author of the book."""
        return {
            "title": self.data["title"],
            "author": self.data["author"],
        }

    def get_chapters(self) -> Generator[Chapter, None, None]:
        """Get the chapters of the book."""
        for child in self.data["chapters"]:
            chap = Chapter(child, class_name="Chapter")
            contains = Reference(parent=self, child=chap, on_parent_property="chapters")
            container = Reference(
                parent=chap, child=self, on_parent_property="containedIn"
            )
            self.add_references([contains])
            chap.add_references([container])
            yield chap

    def get_meta(self):
        """Get the metainfo of the book."""
        meta = Meta(self.data, class_name="Meta")
        contains = Reference(parent=self, child=meta, on_parent_property="meta")
        container = Reference(parent=meta, child=self, on_parent_property="containedIn")
        self.add_references([contains])
        meta.add_references([container])
        return meta


class Meta(Entry):
    """A meta entry.

    Properties:
        entry: Returns the meta details (language, subject and citation) of the book.
    """

    @property
    def entry(self) -> dict:
        """Get the meta details (language, subject and citation) of the book."""
        return {
            "language": self.data["meta"]["language"],
            "subject": self.data["meta"]["subject"],
            "citation": self.data["meta"]["citation"],
        }


class Chapter(Entry):
    """A chapter entry.

    Properties:
        entry: Returns the chapter's title, sequence id and text.

    Methods:
        get_paragraphs: Returns a generator that yields each paragraph `Entry`.
    """

    @property
    def entry(self) -> dict:
        """Get the chapter details of the book."""
        return {
            "title": self.data["title"],
            "seq": self.data["seq"],
            "text": self.data["text"],
        }

    def get_paragraphs(self) -> Generator[Paragraph, None, None]:
        """Get the chapter's paragraphs."""
        for child in self.data["paragraphs"]:
            para = Paragraph(child, class_name="Paragraph")
            contains = Reference(
                parent=self, child=para, on_parent_property="paragraphs"
            )
            container = Reference(
                parent=para, child=self, on_parent_property="containedIn"
            )
            self.add_references([contains])
            para.add_references([container])
            yield para


class Paragraph(Entry):
    """A paragraph entry.

    Properties:
        entry: Returns the paragraph's text and sequence id.
    """

    @property
    def entry(self) -> dict:
        """Get the paragraph's text and sequence id."""
        return {
            "seq": self.data["seq"],
            "text": self.data["text"],
        }


class BookCompilation(Batch):
    """Unnests a book into individual entries.

    Attributes:
        book (Book): The book to unnest.

    Methods:
        get_entries: Returns a generator that yields each `Entry` in the book (i.e Book, Meta, Chapter, Paragraph).
    """

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
    book_collection = BookCompilation(book)
    importer = WeaviateImporter(client, book_collection)
    importer.run()
