"""ETL for Gutenberg HTML files."""

import json
import re
import unicodedata
from datetime import datetime
from typing import List, Union

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

from .common import Extractor


class TextCleaner:
    """Contains methods for cleaning text"""

    @classmethod
    def clean(cls, paragraph):
        """Cleans a paragraph entry from a Gutenberg HTML file"""
        quotation_substitution = re.compile("[“”]")
        ret = paragraph
        # perform quotation substitution
        ret = quotation_substitution.sub('"', ret)
        ret = ret.replace("\n", " ")
        ret = unicodedata.normalize("NFKD", ret)
        ret = ret.strip()
        return ret


class GutenbergExtractor(Extractor):
    """HTML extractor for Project Gutenberg HTML files."""

    def __init__(self, input_file: str):
        """Extract the relevant book elements of the HTML file provided.

        Args:
            input_file (str): Path to an HTML file.

        Usage:
            >>> ex = GutenbergExtractor("file.html")
            # convert the HTML file into a json file and write to
            # the path specified
            >>> ex.extract(path_to_file)
        """
        self.file = input_file

    def extract(self, output):
        """Writes the extracted book to a JSON file"""
        book = Book(self.file).get()
        with open(output, "w", encoding="utf-8") as f:
            json.dump(book, f, indent=4)  # type: ignore


class Book:
    """Contains the title, author, and chapters of a book"""

    def __init__(self, input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            self.soup = BeautifulSoup(f.read(), "html.parser")

    def get_meta(self, name):
        """Get the content of a meta tag"""
        try:
            return self.soup.find("meta", {"name": name}).get("content")  # type: ignore
        except AttributeError:
            return None

    @property
    def title(self) -> Union[str, None]:
        """Return the title of the book"""

        def title(element):
            return element.name == "h1" and (element.find_parents()[0].name == "body")

        try:
            ret = self.soup.find(title)
            return ret.get_text()  # type: ignore
        except AttributeError:
            return None

    @property
    def author(self) -> Union[List[str], None]:
        """Retun the author of the book"""

        def author(element):
            return element.name == "h2" and (element.find_parents()[0].name == "body")

        try:
            ret = self.soup.find(author)
            reg = re.compile(r"(?:[A-Z][a-z\-']+\s?){1,}", re.MULTILINE)
            return reg.findall(ret.get_text()) # type: ignore
        except AttributeError:
            return None

    @property
    def chapters(self) -> ResultSet:
        """Return a ResultSet of chapters"""
        return self.soup.find_all("div", "chapter")

    @staticmethod
    def convert_date(date_string):
        """Utility for converting a date string into a different format"""
        try:
            return datetime.strptime(date_string[:10], "%Y-%m-%d").strftime("%b %d, %Y")
        except (ValueError, TypeError, AttributeError):
            return None

    def get(self):
        """Return a dictionary containing the title, author, and chapters of a book"""
        title, author, language, subject, source, retrieved, rights = (
            self.get_meta("dc.title"),
            self.get_meta("dc.creator"),
            self.get_meta("dc.language"),
            self.get_meta("dc.subject"),
            self.get_meta("dcterms.source"),
            self.convert_date(self.get_meta("dcterms.modified")),
            self.get_meta("dc.rights"),
        )
        citation = (
            f"{rights} {author}. {title}. Urbana, Illinois: Project Gutenberg. "
            f"Retrieved {retrieved} from {source}"
        )

        return {
            "title": title if title is not None else self.title,
            "author": author if author is not None else self.author,
            "meta": {
                "language": language,
                "subject": subject,
                "citation": citation,
            },
            "chapters": [
                Chapter(chapter, idx).get()
                for idx, chapter in enumerate(self.chapters, start=1)
            ],
        }


class Chapter:
    """Contains the chapter title and a list of paragraphs"""

    def __init__(self, chapter: Tag, seq: int):
        self.chapter = chapter
        self.seq = seq

    @property
    def title(self):
        """Returns the title of the chapter"""
        tag = self.chapter.find("h2")
        try:
            regex = re.compile("(?:.*?)(?:\\n|\n)(.*)")
            match = regex.match(tag.get_text())  # type: ignore
            return match.group(1) if match is not None else None
        except AttributeError:
            return None

    @property
    def whole_chapter(self) -> str:
        """Returns the entire cleaned text of the chapter"""
        text = "\n".join([paragraph.get_text() for paragraph in self.paragraphs])
        return TextCleaner.clean(text)

    @property
    def paragraphs(self) -> ResultSet:
        """Returns a ResultSet of all the paragraphs in the chapter"""
        return self.chapter.find_all("p")

    def get(self):
        """Returns a dictionary containing the chapter title and a list of paragraphs"""
        return {
            "title": self.title,
            "seq": self.seq,
            "text": self.whole_chapter,
            "paragraphs": [
                Paragraph(paragraph, idx).get()
                for idx, paragraph in enumerate(self.paragraphs, start=1)
            ],
        }


class Paragraph:
    """Returns a dictionary containing the text of the paragraph"""

    def __init__(self, paragraph, seq):
        self.paragraph = paragraph
        self.seq = seq

    @property
    def whole_paragraph(self) -> str:
        """Returns the entire cleaned text of the paragraph"""
        return TextCleaner.clean(self.paragraph.get_text())

    def get(self):
        """Format into a dictionary and return"""
        return {"seq": self.seq, "text": self.whole_paragraph}
