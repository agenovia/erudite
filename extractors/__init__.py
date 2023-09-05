from dataclasses import dataclass

from . import common, gutenberg_html


@dataclass(frozen=True)
class Extractors:
    """
    Extractors interrogates the common.Extractor class for all subclasses and builds a dictionary.
    The keys are all the viable formats passed using the --format flag.
    """

    extractors = {
        k: v for (k, v) in [(c.format, c) for c in common.Extractor.__subclasses__()]
    }
