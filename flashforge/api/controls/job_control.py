"""
FlashForge Python API - Job Control Module
"""
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiohttp

from ..constants.endpoints import Endpoints
from ..network.utils import NetworkUtils

if TYPE_CHECKING:
    from ...client import FlashForgeClient
    from .control import Control


class JobControl:
    """
    Provides methods for managing print jobs on the FlashForge 3D printer.
    This includes pausing, resuming, canceling prints, uploading files for printing,
    and starting prints from local files.
    """

    def __init__(self, client: "FlashForgeClient"):
        """
        Creates an instance of the JobControl class.
        
        Args:
            client: The FlashForgeClient instance used for communication with the printer.
        """
        self.client = client
        self._control: Optional[Control] = None

    @property
    def control(self) -> "Control":
        """Get the control instance."""
        if self._control is None:
            self._control = self.client.control
        return self._control

    async def pause_print_job(self) -> bool:
        """
        Pauses the current print job.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.control.send_job_control_cmd("pause")

    async def resume_print_job(self) -> bool:
        """
        Resumes a paused print job.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.control.send_job_control_cmd("continue")

    async def cancel_print_job(self) -> bool:
        """
        Cancels the current print job.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        return await self.control.send_job_control_cmd("cancel")

    def _is_new_firmware_version(self) -> bool:
        """
        Checks if the printer's firmware version is 3.1.3 or newer.
        This is used to determine which API payload format to use for certain commands.
        
        Returns:
            True if the firmware is new (>= 3.1.3), False otherwise or if version cannot be determined.
        """
        try:
            current_version = self.client.firmware_ver.split('.')
            min_version = [3, 1, 3]

            for i in range(3):
                current = int(current_version[i] if i < len(current_version) else '0')
                if current > min_version[i]:
                    return True
                if current < min_version[i]:
                    return False

            return True  # Equal versions
        except Exception:
            return False

    async def clear_platform(self) -> bool:
        """
        Sends a command to clear the printer's build platform.
        
        Returns:
            True if the command is successful, False otherwise.
        """
        args = {
            "action": "setClearPlatform"
        }

        return await self.control.send_control_command("stateCtrl_cmd", args)

    async def upload_file(self, file_path: str, start_print: bool, level_before_print: bool) -> bool:
        """
        Uploads a G-code or 3MF file to the printer and optionally starts printing.
        It handles different API requirements based on the printer's firmware version.
        
        Args:
            file_path: The local path to the G-code or 3MF file to upload.
            start_print: If True, the printer will start printing the file immediately after upload.
            level_before_print: If True, the printer will perform bed leveling before starting the print.
            
        Returns:
            True if the file upload (and optional print start) is successful, False otherwise.
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            print(f"UploadFile error: File not found at {file_path}")
            return False

        file_size = file_path_obj.stat().st_size
        file_name = file_path_obj.name

        print(f"Starting upload for {file_name}, Size: {file_size}, Start: {start_print}, Level: {level_before_print}")

        try:
            # Prepare the custom HTTP headers with metadata
            custom_headers = {
                'serialNumber': self.client.serial_number,
                'checkCode': self.client.check_code,
                'fileSize': str(file_size),
                'printNow': str(start_print).lower(),
                'levelingBeforePrint': str(level_before_print).lower(),
                'Expect': '100-continue'
            }

            # Add additional headers for new firmware
            if self._is_new_firmware_version():
                print("Using new firmware headers for upload.")
                custom_headers['flowCalibration'] = 'false'
                custom_headers['useMatlStation'] = 'false'
                custom_headers['gcodeToolCnt'] = '0'
                # Base64 encode "[]" which is "W10="
                custom_headers['materialMappings'] = 'W10='
            else:
                print("Using old firmware headers for upload.")

            print("Upload Request Headers:", custom_headers)

            # Create multipart form data
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('gcodeFile', f, filename=file_name, content_type='application/octet-stream')

                    async with session.post(
                        self.client.get_endpoint(Endpoints.UPLOAD_FILE),
                        data=data,
                        headers=custom_headers
                    ) as response:
                        print(f"Upload Response Status: {response.status}")

                        if response.status != 200:
                            print(f"Upload failed: Printer responded with status {response.status}")
                            return False

                        # Fix for FlashForge printer's malformed Content-Type header
                        # Some printers return "appliation/json" instead of "application/json"
                        try:
                            result = await response.json()
                        except aiohttp.ContentTypeError:
                            # Fallback: manually parse as JSON if Content-Type is malformed
                            text = await response.text()
                            import json
                            result = json.loads(text)
                            
                        print("Upload Response Data:", result)

                        if NetworkUtils.is_ok(result):
                            print("Upload successful according to printer response.")
                            return True
                        else:
                            print(f"Upload failed: Printer response code={result.get('code')}, message={result.get('message')}")
                            return False

        except Exception as e:
            print(f"UploadFile error: {e}")
            return False

    async def print_local_file(self, file_name: str, leveling_before_print: bool) -> bool:
        """
        Starts printing a file that is already stored locally on the printer.
        It handles different API payload formats based on the printer's firmware version.
        
        Args:
            file_name: The name of the file on the printer (e.g., "my_model.gcode") to print.
            leveling_before_print: If True, the printer will perform bed leveling before starting the print.
            
        Returns:
            True if the print command is successfully sent and acknowledged, False otherwise.
        """
        if self._is_new_firmware_version():
            # New format for firmware >= 3.1.3
            payload = {
                "serialNumber": self.client.serial_number,
                "checkCode": self.client.check_code,
                "fileName": file_name,
                "levelingBeforePrint": leveling_before_print,
                "flowCalibration": False,
                "useMatlStation": False,
                "gcodeToolCnt": 0,
                "materialMappings": []  # Empty array for materialMappings
            }
        else:
            # Old format for firmware < 3.1.3
            payload = {
                "serialNumber": self.client.serial_number,
                "checkCode": self.client.check_code,
                "fileName": file_name,
                "levelingBeforePrint": leveling_before_print
            }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.client.get_endpoint(Endpoints.GCODE_PRINT),
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        return False

                    # Fix for FlashForge printer's malformed Content-Type header
                    # Some printers return "appliation/json" instead of "application/json"
                    try:
                        result = await response.json()
                    except aiohttp.ContentTypeError:
                        # Fallback: manually parse as JSON if Content-Type is malformed
                        text = await response.text()
                        import json
                        result = json.loads(text)
                        
                    return NetworkUtils.is_ok(result)

        except Exception as error:
            print(f"PrintLocalFile error: {error}")
            raise error
