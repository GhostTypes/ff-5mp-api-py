"""
FlashForge Python API - Files Module
"""

import base64
import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError

from ...models.machine_info import FFGcodeFileEntry
from ...models.responses import GCodeListResponse, ThumbnailResponse
from ..constants.endpoints import Endpoints
from ..network.utils import NetworkUtils, json_from_response

if TYPE_CHECKING:
    from ...client import FlashForgeClient

logger = logging.getLogger(__name__)


class Files:
    """
    Provides methods for managing files on the FlashForge 3D printer.
    This includes retrieving file lists and thumbnails.
    """

    def __init__(self, client: "FlashForgeClient"):
        """
        Creates an instance of the Files class.

        Args:
            client: The FlashForgeClient instance used for communication with the printer.
        """
        self.client = client

    async def get_file_list(self) -> list[str]:
        """
        Retrieves a list of files stored locally on the printer.

        HTTP-only printers (Creator 5 / 5 Pro) have no TCP/8899 file-listing
        channel, so this falls back to the HTTP ``/gcodeList`` recent-file list
        (mirroring ``Files.ts``) instead of hanging on a dead TCP socket.

        Returns:
            A list of file names, or empty list if retrieval fails.
        """
        if self.client.http_only:
            entries = await self.get_recent_file_list()
            return [e.gcode_file_name for e in entries if e.gcode_file_name]

        # Legacy / 5M-family printers expose the file list over TCP.
        if hasattr(self.client, "tcp_client") and self.client.tcp_client:
            return await self.client.tcp_client.get_file_list_async()
        return []

    async def get_local_file_list(self) -> list[str]:
        """
        Retrieves a list of files stored locally on the printer.

        HTTP-only printers (Creator 5 / 5 Pro) have no TCP/8899 file-listing
        channel; see :meth:`get_file_list` for the HTTP fallback.

        Returns:
            A list of file names, or empty list if retrieval fails.
        """
        return await self.get_file_list()

    async def get_recent_file_list(self) -> list[FFGcodeFileEntry]:
        """
        Retrieves a list of the 10 most recently printed files from the printer's API.
        For AD5X and newer printers, returns detailed file entries with material info.
        For older printers, returns basic file entries with normalized data.

        Returns:
            A list of FFGcodeFileEntry objects. Returns an empty list if the request fails or an error occurs.
        """
        payload = {"serialNumber": self.client.serial_number, "checkCode": self.client.check_code}

        try:
            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.GCODE_LIST),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    return []

                data = await json_from_response(response)

                if not NetworkUtils.is_ok(data):
                    logger.warning(
                        "Error retrieving the file list: %s",
                        NetworkUtils.get_error_message(data),
                    )
                    return []

                # Parse the response using GCodeListResponse
                try:
                    result = GCodeListResponse(**data)
                except ValidationError as err:
                    # The names-only fallback below silently costs the caller
                    # every per-file field, which is indistinguishable from a
                    # printer that only reports names. Say so, loudly enough to
                    # reach an integration's log, or the next model that changes
                    # this payload looks like it reports no metadata at all.
                    logger.warning(
                        "Could not parse the /gcodeList response; falling back to file "
                        "names only, so print time, filament weight, and per-tool "
                        "material data are unavailable for every file. %s",
                        err,
                    )
                    raw_list = data.get("gcodeList", [])
                    if isinstance(raw_list, list):
                        entries: list[FFGcodeFileEntry] = []
                        for file_name in raw_list:
                            if isinstance(file_name, str):
                                entries.append(
                                    FFGcodeFileEntry(
                                        gcodeFileName=file_name,
                                        printingTime=0,
                                    )
                                )
                        return entries
                    return []

                # AD5X and newer printers provide detailed info in gcodeListDetail
                if result.gcode_list_detail and len(result.gcode_list_detail) > 0:
                    return result.gcode_list_detail

                # Fallback for older printers using gcodeList
                if result.gcode_list and len(result.gcode_list) > 0:
                    # Check if it's a list of strings or already FFGcodeFileEntry objects
                    first_item = result.gcode_list[0]

                    if isinstance(first_item, str):
                        # Convert string array to FFGcodeFileEntry objects
                        return [
                            FFGcodeFileEntry(gcodeFileName=file_name, printingTime=0)
                            for file_name in result.gcode_list
                            if isinstance(file_name, str)
                        ]
                    elif isinstance(first_item, FFGcodeFileEntry):
                        # Already FFGcodeFileEntry objects - need explicit type narrowing
                        return [
                            item for item in result.gcode_list if isinstance(item, FFGcodeFileEntry)
                        ]

                return []

        except Exception as err:
            logger.warning("get_recent_file_list error: %s", err)
            return []

    async def get_gcode_thumbnail(self, file_name: str) -> bytes | None:
        """
        Retrieves the thumbnail image for a specified G-code file.
        The image data is returned as bytes.

        Args:
            file_name: The name of the G-code file (e.g., "my_print.gcode") for which to retrieve the thumbnail.

        Returns:
            Bytes containing the thumbnail image data (decoded from base64),
            or None if the request fails, the file has no thumbnail, or an error occurs.
        """
        payload = {
            "serialNumber": self.client.serial_number,
            "checkCode": self.client.check_code,
            "fileName": file_name,
        }

        try:
            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.GCODE_THUMB),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    return None

                data = await json_from_response(response)

                if NetworkUtils.is_ok(data):
                    # Parse response and return decoded image bytes
                    result = ThumbnailResponse(**data)
                    return base64.b64decode(result.image_data)
                else:
                    logger.warning(
                        "Error retrieving the thumbnail: %s",
                        NetworkUtils.get_error_message(data),
                    )
                    return None

        except Exception as err:
            logger.warning("get_gcode_thumbnail error: %s", err)
            return None
