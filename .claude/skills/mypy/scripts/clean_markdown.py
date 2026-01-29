#!/usr/bin/env python3
"""
Clean mypy documentation markdown by removing navigation and footer content.
Keeps only the main documentation content.
"""

import sys

from .utils import clean_mypy_markdown


def main():
    if len(sys.argv) < 2:
        print("Usage: clean_markdown.py <input_file> [output_file]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Read input
    with open(input_file, encoding="utf-8") as f:
        content = f.read()

    # Clean the content
    cleaned = clean_mypy_markdown(content)

    # Output
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"Cleaned content saved to: {output_file}", file=sys.stderr)
    else:
        print(cleaned)


if __name__ == "__main__":
    main()
