from dataclasses import dataclass

from . import gutenberg, gutenberg_modified


@dataclass(frozen=True)
class Extractors:
    extractors = {
        "gutenberg": gutenberg.GutenbergExtractor,
        "gutenberg_modified": gutenberg_modified.GutenbergExtractor,
    }
