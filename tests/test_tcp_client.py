"""Unit and parity tests for the low-level FlashForge TCP client."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from flashforge.tcp import GCodes
from flashforge.tcp.tcp_client import FlashForgeTcpClient, FlashForgeTcpClientOptions
from tests.fixtures.printer_responses import (
    FILE_LIST_TCP_EMPTY,
    FILE_LIST_TCP_PRO,
    FILE_LIST_TCP_REGULAR,
)


class DummyWriter:
    """Minimal writer stub for command and upload tests."""

    def __init__(self) -> None:
        self.write_calls: list[bytes] = []
        self.is_closing = MagicMock(return_value=False)
        self.drain = AsyncMock()
        self.close = MagicMock()
        self.wait_closed = AsyncMock()

    def write(self, data: bytes) -> None:
        self.write_calls.append(data)


def _create_upload_client(response_map: dict[str, str | None]) -> FlashForgeTcpClient:
    client = FlashForgeTcpClient("127.0.0.1")
    client._check_socket = AsyncMock()
    client._writer = DummyWriter()
    client._reader = AsyncMock()
    client._receive_multi_line_replay_async = AsyncMock(side_effect=response_map.get)
    return client


def test_constructor_supports_port_overrides():
    """The low-level client uses default or overridden TCP ports."""
    default_client = FlashForgeTcpClient("127.0.0.1")
    custom_client = FlashForgeTcpClient(
        "127.0.0.1",
        FlashForgeTcpClientOptions(port=19099),
    )

    assert default_client.port == 8899
    assert custom_client.port == 19099


def test_parse_file_list_response_pro_format():
    """Pro format responses retain the storage prefix."""
    client = FlashForgeTcpClient("127.0.0.1")

    assert client._parse_file_list_response(FILE_LIST_TCP_PRO) == [
        "[FLASH]/file1.gcode",
        "[FLASH]/file2.gcode",
    ]


def test_parse_file_list_response_regular_format():
    """Regular format responses preserve spaces and printable characters."""
    client = FlashForgeTcpClient("127.0.0.1")
    result = client._parse_file_list_response(FILE_LIST_TCP_REGULAR)

    assert "file a.gcode" in result
    assert "My File(1).gcode" in result


def test_parse_file_list_response_empty():
    """Empty list responses return an empty array."""
    client = FlashForgeTcpClient("127.0.0.1")

    assert client._parse_file_list_response(FILE_LIST_TCP_EMPTY) == []


@pytest.mark.asyncio
async def test_send_command_async_success():
    """send_command_async writes the command and returns the parsed reply."""
    client = FlashForgeTcpClient("127.0.0.1")
    client._check_socket = AsyncMock()
    client._receive_multi_line_replay_async = AsyncMock(return_value="ok\n")
    client._writer = DummyWriter()
    client._reader = AsyncMock()

    reply = await client.send_command_async("~M119")

    assert reply == "ok\n"
    assert client._writer.write_calls == [b"~M119\n"]
    client._receive_multi_line_replay_async.assert_awaited_once_with("~M119")


@pytest.mark.asyncio
async def test_send_command_async_timeout_resets_socket():
    """Timeouts should trigger a socket reset and return None."""
    client = FlashForgeTcpClient("127.0.0.1")
    client._check_socket = AsyncMock()
    client._receive_multi_line_replay_async = AsyncMock(return_value=None)
    client._reset_socket = AsyncMock()
    client._writer = DummyWriter()
    client._reader = AsyncMock()

    reply = await client.send_command_async("~M119")

    assert reply is None
    client._reset_socket.assert_awaited_once()


def test_m661_uses_widened_completion_delay():
    """M661 file listings keep the wider settle window from the TS client."""
    client = FlashForgeTcpClient("127.0.0.1")

    assert client.get_response_completion_delay_ms(GCodes.CMD_LIST_LOCAL_FILES, False) == 1200


@pytest.mark.asyncio
async def test_upload_file_success(tmp_path: Path):
    """Legacy uploads use M28, raw binary data, and M29 in sequence."""
    local_file = tmp_path / "test-upload.gcode"
    file_data = b"G28\nG1 X10 Y10\nM104 S200\n"
    local_file.write_bytes(file_data)

    start_command = (
        GCodes.CMD_PREP_FILE_UPLOAD.replace("%%size%%", str(len(file_data)))
        .replace("%%filename%%", "test-upload.gcode")
    )
    client = _create_upload_client(
        {
            start_command: "CMD M28 Received.\n/data/test-upload.gcode\n",
            GCodes.CMD_COMPLETE_FILE_UPLOAD: "CMD M29 Received.\n",
        }
    )

    result = await client.upload_file(str(local_file))

    assert result is True
    assert client._writer.write_calls[0] == f"{start_command}\n".encode("ascii")
    assert client._writer.write_calls[-1] == f"{GCodes.CMD_COMPLETE_FILE_UPLOAD}\n".encode("ascii")
    assert client._writer.write_calls[1:-1] == [
        file_data,
    ]
    assert client._writer.write_calls[0:1] == [
        f"{start_command}\n".encode("ascii"),
    ]


@pytest.mark.asyncio
async def test_upload_file_normalizes_legacy_remote_paths(tmp_path: Path):
    """Legacy upload file names should normalize /data and 0:/user prefixes."""
    local_file = tmp_path / "local-name.gcode"
    file_data = b"M105\n"
    local_file.write_bytes(file_data)

    start_command = (
        GCodes.CMD_PREP_FILE_UPLOAD.replace("%%size%%", str(len(file_data)))
        .replace("%%filename%%", "renamed.gx")
    )
    client = _create_upload_client(
        {
            start_command: "CMD M28 Received.\n/data/renamed.gx\n",
            GCodes.CMD_COMPLETE_FILE_UPLOAD: "CMD M29 Received.\n",
        }
    )

    result = await client.upload_file(str(local_file), "/data/renamed.gx")

    assert result is True
    assert client._writer.write_calls[0] == f"{start_command}\n".encode("ascii")


@pytest.mark.asyncio
async def test_upload_file_fails_on_m29_error(tmp_path: Path):
    """M29 error responses should fail the upload cleanly."""
    local_file = tmp_path / "broken-upload.gcode"
    file_data = b"G1 X5 Y5\n"
    local_file.write_bytes(file_data)

    start_command = (
        GCodes.CMD_PREP_FILE_UPLOAD.replace("%%size%%", str(len(file_data)))
        .replace("%%filename%%", "broken-upload.gcode")
    )
    client = _create_upload_client(
        {
            start_command: "CMD M28 Received.\n/data/broken-upload.gcode\n",
            GCodes.CMD_COMPLETE_FILE_UPLOAD: "CMD M29 Received.\nFile Is Not Available\n",
        }
    )

    result = await client.upload_file(str(local_file))

    assert result is False


@pytest.mark.asyncio
async def test_upload_file_missing_local_path_returns_false(tmp_path: Path):
    """Missing local files should fail before any socket work begins."""
    client = _create_upload_client({})

    result = await client.upload_file(str(tmp_path / "missing.gcode"))

    assert result is False
    client._check_socket.assert_not_awaited()


@pytest.mark.asyncio
async def test_start_keep_alive():
    """start_keep_alive schedules periodic heartbeats."""
    client = FlashForgeTcpClient("127.0.0.1")
    client.send_command_async = AsyncMock(side_effect=["ok", "ok"])

    await client.start_keep_alive()
    await asyncio.sleep(0.05)
    await client.stop_keep_alive()

    assert client.send_command_async.await_count >= 1


@pytest.mark.asyncio
async def test_stop_keep_alive_logs_out():
    """Stopping keep-alive with logout sends the logout command."""
    client = FlashForgeTcpClient("127.0.0.1")
    client.send_command_async = AsyncMock(return_value="ok")

    await client.start_keep_alive()
    await asyncio.sleep(0.05)
    await client.stop_keep_alive(logout=True)

    client.send_command_async.assert_any_await(GCodes.CMD_LOGOUT)
    assert client._keep_alive_task is None or client._keep_alive_task.done()


@pytest.mark.asyncio
async def test_keep_alive_handles_disconnection():
    """Keep-alive exits when the printer stops responding."""
    client = FlashForgeTcpClient("127.0.0.1")
    client.send_command_async = AsyncMock(return_value=None)

    await client.start_keep_alive()
    await asyncio.sleep(0.05)

    assert client._keep_alive_errors == 1
    assert client._keep_alive_task is not None
    assert client._keep_alive_task.done()
    await client.stop_keep_alive()
