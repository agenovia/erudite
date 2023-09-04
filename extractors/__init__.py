from dataclasses import dataclass
from . import gutenberg

@dataclass
class Extractors:
    gutenberg = gutenberg.GutenbergExtractor