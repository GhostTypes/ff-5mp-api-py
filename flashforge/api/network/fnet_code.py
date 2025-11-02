"""
FlashForge Python API - Network Operation Codes
"""

from enum import Enum


class FNetCode(Enum):
    """
    Represents network operation codes, typically used in API responses
    to indicate the success or failure of a requested operation.
    """

    OK = 0  # Indicates that the network operation was successful
    ERROR = 1  # Indicates that an error occurred during the network operation
