"""
FlashForge Python API - Files Module
"""
import base64
from typing import TYPE_CHECKING, List, Optional

import aiohttp

from ...models.machine_info import FFGcodeFileEntry
from ...models.responses import GenericResponse, GCodeListResponse, ThumbnailResponse
from ..constants.endpoints import Endpoints
from ..network.utils import NetworkUtils
from pydantic import ValidationError

if TYPE_CHECKING:
    from ...client import FlashForgeClient


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

    async def get_file_list(self) -> List[str]:
        """
        Retrieves a list of files stored locally on the printer.
        
        Returns:
            A list of file names, or empty list if retrieval fails.
        """
        # This method uses the TCP client to get file list
        if hasattr(self.client, 'tcp_client') and self.client.tcp_client:
            return await self.client.tcp_client.get_file_list_async()
        return []

    async def get_local_file_list(self) -> List[str]:
        """
        Retrieves a list of files stored locally on the printer.
        
        Returns:
            A list of file names, or empty list if retrieval fails.
        """
        return await self.get_file_list()

    async def get_recent_file_list(self) -> List[FFGcodeFileEntry]:
        """
        Retrieves a list of the 10 most recently printed files from the printer's API.
        For AD5X and newer printers, returns detailed file entries with material info.
        For older printers, returns basic file entries with normalized data.

        Returns:
            A list of FFGcodeFileEntry objects. Returns an empty list if the request fails or an error occurs.
        """
        payload = {
            "serialNumber": self.client.serial_number,
            "checkCode": self.client.check_code
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.client.get_endpoint(Endpoints.GCODE_LIST),
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        return []

                    # Fix for FlashForge printer's malformed Content-Type header
                    # Some printers return "appliation/json" instead of "application/json"
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        # Fallback: manually parse as JSON if Content-Type is malformed
                        text = await response.text()
                        import json
                        data = json.loads(text)

                    if not NetworkUtils.is_ok(data):
                        print(f"Error retrieving file list: {NetworkUtils.get_error_message(data)}")
                        return []

                    # Parse the response using GCodeListResponse
                    try:
                        result = GCodeListResponse(**data)
                    except ValidationError:
                        raw_list = data.get("gcodeList", [])
                        if isinstance(raw_list, list):
                            entries: List[FFGcodeFileEntry] = []
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
                                FFGcodeFileEntry(
                                    gcodeFileName=file_name,
                                    printingTime=0
                                )
                                for file_name in result.gcode_list
                            ]
                        else:
                            # Already FFGcodeFileEntry objects
                            return result.gcode_list

                    return []

        except Exception as err:
            print(f"GetRecentFileList error: {err}")
            return []

    async def get_gcode_thumbnail(self, file_name: str) -> Optional[bytes]:
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
            "fileName": file_name
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.client.get_endpoint(Endpoints.GCODE_THUMB),
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        return None

                    # Fix for FlashForge printer's malformed Content-Type header
                    # Some printers return "appliation/json" instead of "application/json"
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        # Fallback: manually parse as JSON if Content-Type is malformed
                        text = await response.text()
                        import json
                        data = json.loads(text)

                    if NetworkUtils.is_ok(data):
                        # Parse response and return decoded image bytes
                        result = ThumbnailResponse(**data)
                        return base64.b64decode(result.image_data)
                    else:
                        print(f"Error retrieving thumbnail: {NetworkUtils.get_error_message(data)}")
                        return None

        except Exception as err:
            print(f"GetGcodeThumbnail error: {err}")
            return None
