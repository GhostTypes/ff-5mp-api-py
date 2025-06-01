"""
FlashForge Python API - Files Module
"""
from typing import TYPE_CHECKING, List, Optional

import aiohttp

from ...models.responses import GenericResponse
from ..constants.endpoints import Endpoints
from ..network.utils import NetworkUtils

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

    async def get_recent_file_list(self) -> Optional[GenericResponse]:
        """
        Retrieves a list of recently printed files from the printer.
        
        Returns:
            A GenericResponse containing the recent file list, or None if retrieval fails.
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
                        return GenericResponse(**data)
                    else:
                        print(f"GetRecentFileList error: {NetworkUtils.get_error_message(data)}")
                        return None

        except Exception as err:
            print(f"GetRecentFileList request error: {err}")
            return None

    async def get_gcode_thumbnail(self, file_name: str) -> Optional[GenericResponse]:
        """
        Retrieves the thumbnail image for a G-code file.
        
        Args:
            file_name: The name of the G-code file to get the thumbnail for.
            
        Returns:
            A GenericResponse containing the thumbnail data, or None if retrieval fails.
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
                        return GenericResponse(**data)
                    else:
                        print(f"GetGCodeThumbnail error: {NetworkUtils.get_error_message(data)}")
                        return None

        except Exception as err:
            print(f"GetGCodeThumbnail request error: {err}")
            return None
