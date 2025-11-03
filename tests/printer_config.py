"""
Centralized Printer Configuration for Live Tests

This file contains the configuration for connecting to a real FlashForge printer
during live integration tests. Edit the values below to match your printer setup.

IMPORTANT:
- Unit tests do NOT require a real printer and will run regardless of these settings
- Live/integration tests that require a printer will check SKIP_LIVE_TESTS flag
- Set SKIP_LIVE_TESTS=True to skip tests that need actual printer hardware
"""

import pytest

# =============================================================================
# PRINTER CONNECTION SETTINGS - EDIT THESE FOR YOUR PRINTER
# =============================================================================

# Set to True to skip tests that require a real printer connection
SKIP_LIVE_TESTS = True

# Your printer's IP address on the local network
PRINTER_IP = "192.168.1.120"

# Your printer's serial number (found in printer settings or on the device)
SERIAL_NUMBER = "SNMQRE9400951"

# Your printer's check code (authentication code for API access)
CHECK_CODE = "0e35a229"

# Optional: Printer name for display in test output
PRINTER_NAME = "FlashForge AD5X"

# 5M Pro Configuration
PRINTER_5M_PRO_IP = "192.168.1.140"
PRINTER_5M_PRO_SERIAL = "SNMOMC9900728"
PRINTER_5M_PRO_CHECK_CODE = "your_check_code_here"
PRINTER_5M_PRO_NAME = "Adventurer 5M Pro"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_test_printer_config() -> dict:
    """
    Returns the printer configuration as a dictionary.

    Returns:
        dict: Configuration with keys 'ip', 'serial_number', 'check_code'
    """
    return {
        "ip": PRINTER_IP,
        "serial_number": SERIAL_NUMBER,
        "check_code": CHECK_CODE,
        "name": PRINTER_NAME,
    }


def get_5m_pro_config() -> dict:
    """
    Returns the 5M Pro printer configuration.

    Returns:
        dict: Configuration with keys 'ip', 'serial_number', 'check_code', 'name'
    """
    return {
        "ip": PRINTER_5M_PRO_IP,
        "serial_number": PRINTER_5M_PRO_SERIAL,
        "check_code": PRINTER_5M_PRO_CHECK_CODE,
        "name": PRINTER_5M_PRO_NAME,
    }


def skip_if_no_printer(reason: str = "Requires live printer connection"):
    """
    Pytest decorator to skip tests when SKIP_LIVE_TESTS is True.

    Usage:
        @skip_if_no_printer()
        async def test_upload_file():
            # This test only runs if SKIP_LIVE_TESTS=False
            pass

    Args:
        reason: Custom reason message for skipping

    Returns:
        pytest.mark.skipif decorator
    """
    return pytest.mark.skipif(
        SKIP_LIVE_TESTS,
        reason=f"{reason} (SKIP_LIVE_TESTS=True in printer_config.py)"
    )


# =============================================================================
# VALIDATION
# =============================================================================

def validate_config() -> bool:
    """
    Validates that the printer configuration has been properly set.

    Returns:
        bool: True if config appears valid, False if using default/placeholder values
    """
    if SKIP_LIVE_TESTS:
        return True  # No validation needed if skipping live tests

    has_defaults = (
        PRINTER_IP == "192.168.1.100" or
        SERIAL_NUMBER == "your_serial_number_here" or
        CHECK_CODE == "your_check_code_here"
    )

    if has_defaults:
        print("\n" + "=" * 70)
        print("WARNING: Using default printer configuration!")
        print("=" * 70)
        print("Please edit tests/printer_config.py with your actual printer settings:")
        print(f"  - PRINTER_IP: {PRINTER_IP}")
        print(f"  - SERIAL_NUMBER: {SERIAL_NUMBER}")
        print(f"  - CHECK_CODE: {CHECK_CODE}")
        print("\nOr set SKIP_LIVE_TESTS=True to skip tests requiring a printer.")
        print("=" * 70 + "\n")
        return False

    return True
