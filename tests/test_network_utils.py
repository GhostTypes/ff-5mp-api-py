"""
Tests for NetworkUtils class.

These tests validate the utility methods used for handling network responses.
"""

import pytest

from flashforge.api.network.utils import NetworkUtils
from flashforge.models.responses import GenericResponse


class TestNetworkUtilsIsOk:
    """Test cases for NetworkUtils.is_ok() method."""

    def test_returns_true_for_code_zero(self):
        """Test that code 0 indicates success."""
        response = GenericResponse(code=0, message="OK")
        assert NetworkUtils.is_ok(response) is True

    def test_returns_true_for_code_200(self):
        """Test that code 200 indicates success."""
        response = GenericResponse(code=200, message="OK")
        assert NetworkUtils.is_ok(response) is True

    def test_returns_false_for_error_codes(self):
        """Test that error codes return False."""
        for error_code in [-1, 1, 400, 401, 404, 500]:
            response = GenericResponse(code=error_code, message="Error")
            assert NetworkUtils.is_ok(response) is False, f"Code {error_code} should return False"

    def test_returns_false_for_none(self):
        """Test that None response returns False."""
        assert NetworkUtils.is_ok(None) is False

    def test_handles_dict_response_with_code_zero(self):
        """Test that dict responses with code 0 return True."""
        response = {"code": 0, "message": "OK"}
        assert NetworkUtils.is_ok(response) is True

    def test_handles_dict_response_with_code_200(self):
        """Test that dict responses with code 200 return True."""
        response = {"code": 200, "message": "OK"}
        assert NetworkUtils.is_ok(response) is True

    def test_handles_dict_response_with_error_code(self):
        """Test that dict responses with error codes return False."""
        response = {"code": 1, "message": "Error"}
        assert NetworkUtils.is_ok(response) is False

    def test_handles_dict_response_missing_code(self):
        """Test that dict responses without code field default to -1."""
        response = {"message": "No code field"}
        assert NetworkUtils.is_ok(response) is False

    def test_handles_object_without_code_attribute(self):
        """Test objects without code attribute default to False."""
        class MockResponse:
            def __init__(self):
                self.message = "No code attribute"

        response = MockResponse()
        assert NetworkUtils.is_ok(response) is False


class TestNetworkUtilsGetErrorMessage:
    """Test cases for NetworkUtils.get_error_message() method."""

    def test_returns_message_from_object(self):
        """Test extracting message from GenericResponse object."""
        response = GenericResponse(code=1, message="Connection failed")
        assert NetworkUtils.get_error_message(response) == "Connection failed"

    def test_returns_message_from_dict(self):
        """Test extracting message from dict response."""
        response = {"code": 1, "message": "File not found"}
        assert NetworkUtils.get_error_message(response) == "File not found"

    def test_returns_unknown_error_for_dict_without_message(self):
        """Test that dict without message returns 'Unknown error'."""
        response = {"code": 1}
        assert NetworkUtils.get_error_message(response) == "Unknown error"

    def test_returns_unknown_error_for_object_without_message(self):
        """Test that object without message attribute returns 'Unknown error'."""
        class MockResponse:
            def __init__(self):
                self.code = 1

        response = MockResponse()
        assert NetworkUtils.get_error_message(response) == "Unknown error"

    def test_returns_no_response_for_none(self):
        """Test that None returns 'No response received'."""
        assert NetworkUtils.get_error_message(None) == "No response received"

    def test_converts_message_to_string(self):
        """Test that message is converted to string."""
        response = {"message": 12345}
        assert NetworkUtils.get_error_message(response) == "12345"
