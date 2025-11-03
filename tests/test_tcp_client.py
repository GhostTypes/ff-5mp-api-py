"""
Unit tests for the FlashForge TCP client.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from flashforge.tcp import GCodes
from flashforge.tcp.tcp_client import FlashForgeTcpClient

from tests.fixtures.printer_responses import (
    FILE_LIST_TCP_EMPTY,
    FILE_LIST_TCP_PRO,
    FILE_LIST_TCP_REGULAR,
)


class DummyWriter:
    """Minimal writer stub for send_command tests."""

    def __init__(self):
        self.write_calls = []
        self.is_closing = MagicMock(return_value=False)
        self.drain = AsyncMock()

    def write(self, data: bytes):
        self.write_calls.append(data)


@pytest.mark.asyncio
async def test_parse_file_list_response_pro_format():
    """Pro format responses retain the storage prefix."""
    client = FlashForgeTcpClient("127.0.0.1")
    result = client._parse_file_list_response(FILE_LIST_TCP_PRO)
    assert result == ["[FLASH]/file1.gcode", "[FLASH]/file2.gcode"]


@pytest.mark.asyncio
async def test_parse_file_list_response_regular_format():
    """Regular format responses parse correctly."""
    client = FlashForgeTcpClient("127.0.0.1")
    result = client._parse_file_list_response(FILE_LIST_TCP_REGULAR)
    assert "file a.gcode" in result
    assert "My File(1).gcode" in result


@pytest.mark.asyncio
async def test_parse_file_list_response_with_spaces():
    """Filenames containing spaces are preserved."""
    client = FlashForgeTcpClient("127.0.0.1")
    result = client._parse_file_list_response(FILE_LIST_TCP_REGULAR)
    assert any(" " in name for name in result)


@pytest.mark.asyncio
async def test_parse_file_list_response_with_special_chars():
    """Unicode and special characters are retained."""
    client = FlashForgeTcpClient("127.0.0.1")
    result = client._parse_file_list_response("/data/Résumé_Test.gcode::/data/文件.gcode")
    assert "Résumé_Test.gcode" in result
    assert "文件.gcode" in result


@pytest.mark.asyncio
async def test_parse_file_list_response_empty():
    """Empty string returns empty list."""
    client = FlashForgeTcpClient("127.0.0.1")
    assert client._parse_file_list_response(FILE_LIST_TCP_EMPTY) == []


@pytest.mark.asyncio
async def test_send_command_async_success():
    """send_command_async writes command and returns reply."""
    client = FlashForgeTcpClient("127.0.0.1")
    client._check_socket = AsyncMock()
    client._receive_multi_line_replay_async = AsyncMock(return_value="ok\n")
    client._writer = DummyWriter()
    client._reader = AsyncMock()

    reply = await client.send_command_async("~M119")

    assert reply == "ok\n"
    assert client._writer.write_calls == [b"~M119\n"]
    client._receive_multi_line_replay_async.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_command_async_timeout():
    """Timeout resets socket and returns None."""
    client = FlashForgeTcpClient("127.0.0.1")
    client._check_socket = AsyncMock()
    client._receive_multi_line_replay_async = AsyncMock(return_value=None)
    client._reset_socket = AsyncMock()
    client._writer = DummyWriter()
    client._reader = AsyncMock()

    reply = await client.send_command_async("~M119")

    assert reply is None
    client._reset_socket.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_command_async_connection_lost():
    """Connection errors are handled gracefully."""
    client = FlashForgeTcpClient("127.0.0.1")
    client._check_socket = AsyncMock(side_effect=Exception("lost"))
    client._writer = DummyWriter()
    client._reader = AsyncMock()

    reply = await client.send_command_async("~M119")

    assert reply is None


@pytest.mark.asyncio
async def test_start_keep_alive():
    """start_keep_alive schedules periodic heartbeat."""
    client = FlashForgeTcpClient("127.0.0.1")
    client.send_command_async = AsyncMock(side_effect=["ok", "ok"])

    await client.start_keep_alive()
    await asyncio.sleep(0.05)  # allow keep-alive task to run at least once
    await client.stop_keep_alive()

    assert client.send_command_async.await_count >= 1


@pytest.mark.asyncio
async def test_stop_keep_alive():
    """stop_keep_alive cancels keep alive and optionally logs out."""
    client = FlashForgeTcpClient("127.0.0.1")
    client.send_command_async = AsyncMock(return_value="ok")

    await client.start_keep_alive()
    await asyncio.sleep(0.05)
    await client.stop_keep_alive(logout=True)

    client.send_command_async.assert_any_await(GCodes.CMD_LOGOUT)
    assert client._keep_alive_task is None or client._keep_alive_task.done()


@pytest.mark.asyncio
async def test_keep_alive_handles_disconnection():
    """Keep-alive exits when connection lost."""
    client = FlashForgeTcpClient("127.0.0.1")
    client.send_command_async = AsyncMock(return_value=None)

    await client.start_keep_alive()
    await asyncio.sleep(0.05)

    assert client._keep_alive_errors == 1
    assert client._keep_alive_task is not None
    assert client._keep_alive_task.done()
    await client.stop_keep_alive()
