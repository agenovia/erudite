"""Maps the extractors to the format provided.""" ""
import os

from extractors import Extractors


class FileExists(Exception):
    """Exception raised when the output file already exists."""

    def __init__(self, message):
        super().__init__(message)


class FileUnsupported(Exception):
    """Exception raised when the input file is unsupported."""

    def __init__(self, message):
        super().__init__(message)


class ExtractorUnsupported(Exception):
    """Exception raised for unsupported extractor formats."""

    def __init__(self, message):
        super().__init__(message)


class InvalidExtractor(Exception):
    """Exception raised for invalid extractor formats."""

    def __init__(self, message):
        super().__init__(message)


class Extract:
    """Handles extraction using the format provided"""

    def __init__(self, input_path, output_path, file_format, overwrite=False):
        self.input = input_path
        self.output = output_path
        self.extractor = self.get_extractor(file_format)
        self.overwrite = overwrite

    def get_extractor(self, name):
        """Get an extractor by name."""
        extractors = {"gutenberg": Extractors.gutenberg}

        try:
            extractor = extractors[name]
            return extractor
        except KeyError as exc:
            raise ExtractorUnsupported(
                f"'{name}' is not supported format. Please choose from {list(extractors.keys())}"
            ) from exc

    def output_filepath(self, file):
        """Determine new filename"""
        if os.path.isdir(self.output):
            input_filename = os.path.split(file)[-1]
            output_filename = input_filename.replace(".html", ".json")
            return os.path.join(self.output, output_filename)
        else:
            return self.output

    def run(self):
        """Extract file using the extractor provided."""
        if os.path.isdir(self.input):
            for file in os.scandir(self.input):
                if file.name.endswith(".html"):
                    out = self.output_filepath(file)
                    if os.path.exists(out) and not self.overwrite:
                        raise FileExists(
                            f"{out} already exists and --overwrite flag is not set."
                        )
                    self.extractor(file.path).extract(out)
        else:
            if self.input.endswith(".html"):
                out = self.output_filepath(self.input)
                if os.path.exists(out) and not self.overwrite:
                    raise FileExists(
                        f"{out} already exists and --overwrite flag is not set."
                    )
                self.extractor(self.input).extract(out)
            else:
                raise FileUnsupported(f"{self.input} is not a supported file type.")
