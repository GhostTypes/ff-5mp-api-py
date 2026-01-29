"""
Shared utility functions for mypy documentation processing.
"""

import re


def clean_mypy_markdown(content: str) -> str:
    """
    Clean mypy documentation markdown content.

    Removes:
    - Navigation header (everything before first H1 heading)
    - Footer navigation (Next/Previous links)
    - Copyright notice
    - "On this page" table of contents
    - Permalink anchors (¶) in headings

    Args:
        content: Raw markdown content from mypy documentation

    Returns:
        Cleaned markdown content with navigation and footer removed
    """
    lines = content.split("\n")

    # Find the start of actual content (first H1 heading)
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("# ") and "[¶]" in line:
            start_idx = i
            break

    # Find the end of actual content
    # Look for ALL footer markers and use the earliest one
    footer_markers = []

    for i in range(len(lines) - 1, start_idx, -1):
        line = lines[i].strip()

        # Look for standalone navigation markers
        if line in ["[Next", "[Previous"]:
            footer_markers.append(("nav", i))

        # Look for copyright
        if "Copyright ©" in line:
            footer_markers.append(("copyright", i))

        # Look for "On this page" table of contents
        if line == "On this page":
            footer_markers.append(("toc", i))

    # Use the earliest footer marker found
    if footer_markers:
        # Sort by line number and take the first (earliest)
        footer_markers.sort(key=lambda x: x[1])
        marker_type, end_idx = footer_markers[0]

        # Remove trailing blank lines before the footer marker
        while end_idx > start_idx and lines[end_idx - 1].strip() == "":
            end_idx -= 1
    else:
        end_idx = len(lines)

    # Extract the main content
    cleaned_lines = lines[start_idx:end_idx]

    # Remove permalink anchors from headings
    # Pattern: [¶](#some-anchor "Link to this heading")
    permalink_pattern = r'\[¶\]\(#[^)]+\s+"[^"]+"\)'

    cleaned_lines = [re.sub(permalink_pattern, "", line) for line in cleaned_lines]

    # Join back together
    cleaned_content = "\n".join(cleaned_lines)

    # Clean up excessive blank lines (more than 2 consecutive)
    cleaned_content = re.sub(r"\n{3,}", "\n\n", cleaned_content)

    # Strip leading/trailing whitespace
    cleaned_content = cleaned_content.strip()

    return cleaned_content
