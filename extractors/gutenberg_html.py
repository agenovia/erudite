"""ETL for Gutenberg HTML files."""

import json
import re
from datetime import datetime
from typing import List, Union

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

from .common import Extractor


class GutenbergExtractor(Extractor):
    """HTML extractor for Project Gutenberg HTML files."""

    format = "gutenberg_html"

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
        super().__init__()
        self.file = input_file

    def compile(self):
        """Compile the book into a dictionary"""
        return Book(self.file).get()

    def extract(self, output):
        """Writes the extracted book to a JSON file"""
        book = self.compile()
        with open(output, "w", encoding="utf-8") as f:
            json.dump(book, f, indent=4)  # type: ignore

    @classmethod
    def clean_chapter(cls, text):
        super().clean_soup(text)

    @classmethod
    def clean_paragraph(cls, text):
        ret = super().clean_soup(text)
        ret = ret.replace("\n", " ")
        return ret


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
            return reg.findall(ret.get_text())  # type: ignore
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
            "chapters": Chapters(self.chapters).get(),
        }


class Chapters:
    def __init__(self, chapters: ResultSet):
        self.chapters = chapters

    def get_title(self, tag: Tag):
        """Returns the title of the chapter"""
        ret = tag.find("h2")
        try:
            regex = re.compile("(?:.*?)?(?:\\n|\n)?(.*)")
            match = regex.match(ret.get_text())  # type: ignore
            return match.group(1) if match is not None else None
        except AttributeError:
            return None

    @property
    def clean_chapters(self):
        """Returns a list of chapters that are not empty"""

        def is_empty(paragraph):
            return len(paragraph) in [0, 1, 2]

        chapters = []
        for chap in self.chapters:
            paragraphs = chap.find_all("p")
            chapter_text = GutenbergExtractor.clean_paragraph(
                " ".join([tag.get_text() for tag in paragraphs])
            )
            if not is_empty(chapter_text):
                chapters.append(
                    {
                        "title": self.get_title(chap),
                        "text": chapter_text,
                        "paragraphs": paragraphs,
                    }
                )
        return chapters

    def get(self):
        """Build a list of dictionaries containing the chapter title and a list of paragraphs"""
        ret = []
        for seq, chapter in enumerate(self.clean_chapters, start=1):
            details = {
                "title": chapter["title"],
                "seq": seq,
                "text": chapter["text"],
                "paragraphs": Paragraphs(chapter["paragraphs"]).get(),
            }
            ret.append(details)
        return ret


# class Chapter:
#     """Contains the chapter title and a list of paragraphs"""

#     """
#     For each chapter, if the whole paragraph is empty, then it is not a true chapter
#     """

#     def __init__(self, chapter: Tag, seq: int):
#         self.chapter = chapter
#         self.seq = seq

#     @property
#     def title(self):
#         """Returns the title of the chapter"""
#         tag = self.chapter.find("h2")
#         try:
#             regex = re.compile("(?:.*?)(?:\\n|\n)(.*)")
#             match = regex.match(tag.get_text())  # type: ignore
#             return match.group(1) if match is not None else None
#         except AttributeError:
#             return None

#     @property
#     def whole_chapter(self) -> str:
#         """Returns the entire cleaned text of the chapter"""
#         text = "\n".join([paragraph.get_text() for paragraph in self.paragraphs])
#         return GutenbergExtractor.clean_soup(text)

#     @property
#     def paragraphs(self) -> ResultSet:
#         """Returns a ResultSet of all the paragraphs in the chapter"""
#         return self.chapter.find_all("p")

#     def get(self):
#         """Returns a dictionary containing the chapter title and a list of paragraphs"""
#         return {
#             "title": self.title,
#             "seq": self.seq,
#             "text": self.whole_chapter,
#             # "paragraphs": [
#             #     Paragraph(paragraph, idx).get()
#             #     for idx, paragraph in enumerate(self.paragraphs, start=1)
#             # ],
#             "paragraphs": Paragraphs(self.paragraphs).get,
#         }


class Paragraphs:
    """Returns a dictionary containing the text of the paragraph"""

    def __init__(self, paragraphs: ResultSet):
        self.paragraphs = paragraphs

    def build_paragraph_set(self):
        """Return a list of dictionaries containing the text of the paragraph and its sequence number"""
        paragraphs = []
        seq = 1
        for para in self.paragraphs:
            para = GutenbergExtractor.clean_paragraph(para.get_text())
            if len(para) in [0,1,2]:
                continue
            paragraphs.append({"seq": seq, "text": para})
            seq += 1
        return paragraphs

    def get(self):
        """Format into a dictionary and return"""
        return self.build_paragraph_set()
