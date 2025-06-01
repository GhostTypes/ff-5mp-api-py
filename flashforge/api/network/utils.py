"""
FlashForge Python API - Network Utilities
"""
from typing import Optional, Union

from ...models.responses import GenericResponse


class NetworkUtils:
    """Utility class for handling network responses and status codes."""

    @staticmethod
    def is_ok(response: Optional[Union[GenericResponse, dict]]) -> bool:
        """
        Checks if a response indicates success.
        
        Args:
            response: The response object to check
            
        Returns:
            True if the response indicates success, False otherwise
        """
        if response is None:
            return False

        # Handle dictionary responses
        if isinstance(response, dict):
            code = response.get("code", -1)
        else:
            # Handle GenericResponse objects
            code = getattr(response, "code", -1)

        # Success codes: 0 or 200
        return code in (0, 200)

    @staticmethod
    def get_error_message(response: Optional[Union[GenericResponse, dict]]) -> str:
        """
        Extracts error message from a response.
        
        Args:
            response: The response object to extract message from
            
        Returns:
            Error message string, or empty string if none found
        """
        if response is None:
            return "No response received"

        # Handle dictionary responses
        if isinstance(response, dict):
            return response.get("message", "Unknown error")
        else:
            # Handle GenericResponse objects
            return getattr(response, "message", "Unknown error")
