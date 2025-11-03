"""
Live integration tests for the FlashForge Adventurer 5M Pro printer.

These tests verify connectivity and core functionality against real hardware.
They are skipped when SKIP_LIVE_TESTS=True in tests/printer_config.py.
"""
import pytest

from flashforge import FlashForgeClient
from tests.printer_config import get_5m_pro_config, skip_if_no_printer


@pytest.mark.asyncio
@skip_if_no_printer("Requires 5M Pro printer")
class Test5MProLiveIntegration:
    """Live integration tests requiring a connected 5M Pro printer."""

    async def test_connect_and_get_status_5m_pro(self):
        """Connect to 5M Pro and verify status information."""
        config = get_5m_pro_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize(), "Failed to initialize client"
            assert client.printer_name == config["name"]
            assert client.is_ad5x is False

            info = await client.info.get()
            assert info is not None
            assert info.is_ad5x is False
            assert info.name == config["name"]

    async def test_get_file_list_5m_pro(self):
        """Validate file list parsing for non-AD5X printers."""
        config = get_5m_pro_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            files = await client.files.get_recent_file_list()
            assert isinstance(files, list)
            for entry in files:
                assert hasattr(entry, "gcode_file_name")
                assert entry.gcode_file_name is not None
                # 5M Pro entries should not include AD5X-only metadata
                assert getattr(entry, "gcode_tool_datas", None) in (None, [])

    async def test_led_control_5m_pro(self):
        """Ensure LED control commands execute without error."""
        config = get_5m_pro_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            # Toggle LEDs; ignore return value but ensure calls do not raise.
            await client.control.set_led_on()
            await client.control.set_led_off()

    async def test_filtration_control_5m_pro(self):
        """Verify filtration control commands execute successfully."""
        config = get_5m_pro_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            await client.control.set_external_filtration_on()
            await client.control.set_filtration_off()

    async def test_job_control_validation_5m_pro(self):
        """Ensure job control responds gracefully when printer is idle."""
        config = get_5m_pro_config()

        async with FlashForgeClient(config["ip"], config["serial_number"], config["check_code"]) as client:
            assert await client.initialize()

            info = await client.info.get()
            assert info is not None

            if info.status != "printing":
                result = await client.job_control.pause_print_job()
                assert result is False
