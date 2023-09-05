"""Base extractor class for all extractors to inherit from"""

import re
import unicodedata
from abc import ABC, abstractmethod


class Extractor(ABC):
    """Base extractor class for all extractors to inherit from"""

    format: str

    @abstractmethod
    def compile(self) -> dict:
        """
        Implement a method to compile the text of a book into a dictionary, ready for writing to a JSON file
        """

    @abstractmethod
    def extract(self, output):
        """
        Implement a method to write a dictionary to a JSON file either in the output directory
        or to the specified output file
        """

    @classmethod
    def clean_soup(cls, text):
        """Cleans text from a Gutenberg HTML file"""
        quotation_substitution = re.compile("[“”]")
        ret = text
        # perform quotation substitution
        ret = quotation_substitution.sub('"', ret)
        # ret = ret.replace("\n", " ")
        ret = unicodedata.normalize("NFKD", ret)
        ret = ret.strip()
        return ret
