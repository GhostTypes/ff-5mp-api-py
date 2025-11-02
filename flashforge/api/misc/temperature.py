"""
FlashForge Python API - Temperature Utility Class
"""


class Temperature:
    """
    Represents a temperature value.
    This class is a simple wrapper around a numeric temperature value,
    providing methods to get the value and its string representation.
    It's a general temperature representation that can be used for various purposes.
    """

    def __init__(self, value: float):
        """
        Creates an instance of the Temperature class.

        Args:
            value: The numeric temperature value, typically in Celsius.
        """
        self._value = value

    def get_value(self) -> float:
        """
        Gets the numeric temperature value.

        Returns:
            The temperature value.
        """
        return self._value

    def __str__(self) -> str:
        """
        Gets the string representation of the temperature value.

        Returns:
            The temperature value as a string.
        """
        return str(self._value)

    def __repr__(self) -> str:
        return f"Temperature({self._value})"
