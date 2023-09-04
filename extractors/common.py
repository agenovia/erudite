"""Base extractor class for all extractors to inherit from"""

from abc import ABC, abstractmethod


class Extractor(ABC):
    """Base extractor class for all extractors to inherit from"""

    @abstractmethod
    def extract(self, output):
        """
        Implement a method to write a dictionary to a JSON file either in the output directory
        or to the specified output file
        """
