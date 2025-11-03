"""
Unit tests for the Files module.
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flashforge.client import FlashForgeClient

from tests.fixtures.printer_responses import (
    FILE_LIST_5M_PRO_RESPONSE,
    FILE_LIST_AD5X_RESPONSE,
    THUMBNAIL_RESPONSE,
)


def _mock_session(response_payload: dict, status: int = 200):
    """Build a mocked aiohttp ClientSession."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=response_payload)
    mock_response.text = AsyncMock(return_value=json.dumps(response_payload))

    mock_post_ctx = MagicMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=mock_post_ctx)

    return mock_session


def _build_client() -> FlashForgeClient:
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client.tcp_client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_get_recent_file_list_ad5x_format():
    """AD5X file list returns detailed entries."""
    client = _build_client()
    mock_session = _mock_session(FILE_LIST_AD5X_RESPONSE)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.files.NetworkUtils.is_ok", return_value=True):
            result = await client.files.get_recent_file_list()

    assert len(result) == 1
    entry = result[0]
    assert entry.gcode_file_name == "multi_color_test.3mf"
    assert entry.gcode_tool_cnt == 2
    assert entry.use_matl_station is True


@pytest.mark.asyncio
async def test_get_recent_file_list_old_printer_format():
    """Legacy printers fallback to simple string list."""
    client = _build_client()
    mock_session = _mock_session(FILE_LIST_5M_PRO_RESPONSE)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.files.NetworkUtils.is_ok", return_value=True):
            result = await client.files.get_recent_file_list()

    assert len(result) == 2
    assert result[0].gcode_file_name == "benchy.gcode"
    assert result[1].gcode_file_name == "calibration_cube.gcode"


@pytest.mark.asyncio
async def test_get_recent_file_list_empty():
    """Empty responses return empty list."""
    client = _build_client()
    mock_session = _mock_session({"code": 0, "gcodeList": []})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.files.NetworkUtils.is_ok", return_value=True):
            result = await client.files.get_recent_file_list()

    assert result == []


@pytest.mark.asyncio
async def test_get_recent_file_list_http_error():
    """HTTP errors return empty list."""
    client = _build_client()
    mock_session = _mock_session({}, status=500)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await client.files.get_recent_file_list()

    assert result == []


@pytest.mark.asyncio
async def test_get_recent_file_list_malformed_json():
    """Malformed JSON is handled gracefully."""
    client = _build_client()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(side_effect=ValueError("invalid json"))
    mock_response.text = AsyncMock(return_value="not json")

    mock_post_ctx = MagicMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=mock_post_ctx)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await client.files.get_recent_file_list()

    assert result == []


@pytest.mark.asyncio
async def test_get_recent_file_list_network_timeout():
    """Timeout retrieving file list returns empty list."""
    client = _build_client()

    class FailingSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            raise asyncio.TimeoutError()

    failing_session = FailingSession()

    with patch("aiohttp.ClientSession", return_value=failing_session):
        result = await client.files.get_recent_file_list()

    assert result == []


@pytest.mark.asyncio
async def test_get_recent_file_list_connection_reset():
    """Connection reset returns empty list."""
    client = _build_client()

    class ResetSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            raise ConnectionResetError()

    reset_session = ResetSession()

    with patch("aiohttp.ClientSession", return_value=reset_session):
        result = await client.files.get_recent_file_list()

    assert result == []


@pytest.mark.asyncio
async def test_get_local_file_list_with_files():
    """Local file list returns TCP entries."""
    client = _build_client()
    client.tcp_client.get_file_list_async = AsyncMock(return_value=["file1.gcode", "file2.gcode"])

    result = await client.files.get_local_file_list()

    assert result == ["file1.gcode", "file2.gcode"]
    client.tcp_client.get_file_list_async.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_local_file_list_empty():
    """Empty list when TCP client returns nothing."""
    client = _build_client()
    client.tcp_client.get_file_list_async = AsyncMock(return_value=[])

    result = await client.files.get_local_file_list()

    assert result == []


@pytest.mark.asyncio
async def test_get_gcode_thumbnail_success():
    """Thumbnail retrieval returns decoded bytes."""
    client = _build_client()
    mock_session = _mock_session(THUMBNAIL_RESPONSE)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with patch("flashforge.api.controls.files.NetworkUtils.is_ok", return_value=True):
            data = await client.files.get_gcode_thumbnail("cube.gcode")

    assert isinstance(data, bytes)
    assert data.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_get_gcode_thumbnail_not_found():
    """Missing thumbnail returns None."""
    client = _build_client()
    mock_session = _mock_session({}, status=404)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        data = await client.files.get_gcode_thumbnail("missing.gcode")

    assert data is None
