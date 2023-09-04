#! /usr/bin/env python3
import sys
from argparse import ArgumentParser

from utils.extractor import Extract


class Parser(ArgumentParser):
    """Custom parser that always prints help when an error occurs."""

    def error(self, message):
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        sys.exit(2)


def parse_args():
    """Parse command line arguments."""
    parser = Parser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser(
        "extract", help="Extract data from HTML and output to JSON."
    )
    extract.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to .html file or directory containing .html files.",
    )
    extract.add_argument(
        "-o", "--output_dir", help="Directory to write the JSON files."
    )
    extract.add_argument(
        "--format",
        required=True,
        help="Extractor format must be present in the extractors directory.",
    )
    extract.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="If specified, allows the overwriting of existing files.",
    )
    load = subparsers.add_parser(
        "load", help="Load JSON files into a Weaviate instance."
    )
    load.add_argument("-s", "--schema", help="Weaviate schema to load into.")
    load.add_argument(
        "-t", "--target", required=True, help="Full address of weaviate instance."
    )
    load.add_argument("--key", help="Weaviate API key.")
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    if args.command == "extract":
        Extract(args.input, args.output_dir, args.format, args.overwrite).run()
    elif args.command == "load":
        # TODO(agenovia) implement Weaviate loader
        pass


if __name__ == "__main__":
    main()
