"""
FlashForge Python API - Scientific Notation Formatter
"""


def format_scientific_notation(value: float) -> str:
    """
    Formats a number into a string, using scientific notation if the number is
    very small (absolute value < 0.001) or very large (absolute value >= 10000).
    Otherwise, it returns the standard string representation of the number.

    Args:
        value: The number to format.

    Returns:
        A string representation of the number, potentially in scientific notation.

    Examples:
        >>> format_scientific_notation(0.000123)
        '1.23e-04'
        >>> format_scientific_notation(12345)
        '1.2345e+04'
        >>> format_scientific_notation(12.34)
        '12.34'
    """
    if abs(value) < 0.001 or abs(value) >= 10000:
        return f"{value:e}"
    return str(value)
