"""
FlashForge Python API - Job Control Module
"""

import base64
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp

from ...models.responses import (
    AD5XLocalJobParams,
    AD5XMaterialMapping,
    AD5XSingleColorJobParams,
    AD5XUploadParams,
    Creator5JobParams,
    Creator5UploadParams,
)
from ..constants.endpoints import Endpoints
from ..network.utils import NetworkUtils, json_from_response

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
        self._control: Control | None = None

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
        # The 3.1.3 threshold only applies to the 5M family. The AD5X and Creator 5
        # series always use the new payload/header format, and their firmware
        # versioning isn't comparable to the 5M's 3.x line (e.g. the C5 reports
        # 1.9.2, which the numeric check below would wrongly read as "old"), so
        # short-circuit to the new format for them.
        if self.client.is_ad5x or self.client.is_creator5 or self.client.is_creator5_pro:
            return True
        try:
            current_version = self.client.firmware_ver.split(".")
            min_version = [3, 1, 3]

            for i in range(3):
                current = int(current_version[i] if i < len(current_version) else "0")
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
        args = {"action": "setClearPlatform"}

        return await self.control.send_control_command("stateCtrl_cmd", args)

    async def upload_file(
        self, file_path: str, start_print: bool, level_before_print: bool
    ) -> bool:
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

        print(
            f"Starting upload for {file_name}, Size: {file_size}, Start: {start_print}, Level: {level_before_print}"
        )

        try:
            # Prepare the custom HTTP headers with metadata
            custom_headers = {
                "serialNumber": self.client.serial_number,
                "checkCode": self.client.check_code,
                "fileSize": str(file_size),
                "printNow": str(start_print).lower(),
                "levelingBeforePrint": str(level_before_print).lower(),
                "Expect": "100-continue",
            }

            # Add additional headers for new firmware
            if self._is_new_firmware_version():
                print("Using new firmware headers for upload.")
                custom_headers["flowCalibration"] = "false"
                custom_headers["useMatlStation"] = "false"
                custom_headers["gcodeToolCnt"] = "0"
                # Base64 encode "[]" which is "W10="
                custom_headers["materialMappings"] = "W10="
            else:
                print("Using old firmware headers for upload.")

            print("Upload Request Headers:", custom_headers)

            # Create multipart form data
            async with aiohttp.ClientSession() as session:
                with open(file_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "gcodeFile", f, filename=file_name, content_type="application/octet-stream"
                    )

                    async with session.post(
                        self.client.get_endpoint(Endpoints.UPLOAD_FILE),
                        data=data,
                        headers=custom_headers,
                    ) as response:
                        print(f"Upload Response Status: {response.status}")

                        if response.status != 200:
                            print(f"Upload failed: Printer responded with status {response.status}")
                            return False

                        result = await json_from_response(response)
                        print("Upload Response Data:", result)

                        if NetworkUtils.is_ok(result):
                            print("Upload successful according to printer response.")
                            return True
                        else:
                            print(
                                f"Upload failed: Printer response code={result.get('code')}, message={result.get('message')}"
                            )
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
                "materialMappings": [],  # Empty array for materialMappings
            }
        else:
            # Old format for firmware < 3.1.3
            payload = {
                "serialNumber": self.client.serial_number,
                "checkCode": self.client.check_code,
                "fileName": file_name,
                "levelingBeforePrint": leveling_before_print,
            }

        try:
            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.GCODE_PRINT),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    return False

                result = await json_from_response(response)
                return NetworkUtils.is_ok(result)

        except Exception as error:
            print(f"PrintLocalFile error: {error}")
            raise error

    async def upload_file_ad5x(self, params: AD5XUploadParams) -> bool:
        """
        Uploads a G-code or 3MF file to AD5X printer with material station support.
        Handles material mappings, flow calibration, and other AD5X-specific features.
        Material mappings are base64-encoded in HTTP headers according to AD5X API requirements.

        Args:
            params: AD5X upload parameters including file path, print options, and material mappings

        Returns:
            True if the file upload is successful, False otherwise
        """
        # Validate that this is an AD5X printer
        if not self._validate_ad5x_printer():
            return False

        # Validate material mappings
        if not self._validate_material_mappings(params.material_mappings):
            return False

        # Validate file exists
        file_path_obj = Path(params.file_path)
        if not file_path_obj.exists():
            print(f"UploadFileAD5X error: File not found at {params.file_path}")
            return False

        file_size = file_path_obj.stat().st_size
        file_name = file_path_obj.name

        print(
            f"Starting AD5X upload for {file_name}, Size: {file_size}, Start: {params.start_print}, Level: {params.leveling_before_print}, Tools: {len(params.material_mappings)}"
        )

        try:
            # Encode material mappings to base64
            material_mappings_base64 = self._encode_material_mappings_to_base64(
                params.material_mappings
            )

            # Prepare AD5X-specific HTTP headers
            custom_headers = {
                "serialNumber": self.client.serial_number,
                "checkCode": self.client.check_code,
                "fileSize": str(file_size),
                "printNow": str(params.start_print).lower(),
                "levelingBeforePrint": str(params.leveling_before_print).lower(),
                "flowCalibration": str(params.flow_calibration).lower(),
                "firstLayerInspection": str(params.first_layer_inspection).lower(),
                "timeLapseVideo": str(params.time_lapse_video).lower(),
                "useMatlStation": "true",  # Always true for AD5X uploads with material mappings
                "gcodeToolCnt": str(len(params.material_mappings)),
                "materialMappings": material_mappings_base64,
                "Expect": "100-continue",
            }

            print("AD5X Upload Request Headers:", custom_headers)

            # Create multipart form data
            async with aiohttp.ClientSession() as session:
                with open(params.file_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "gcodeFile", f, filename=file_name, content_type="application/octet-stream"
                    )

                    async with session.post(
                        self.client.get_endpoint(Endpoints.UPLOAD_FILE),
                        data=data,
                        headers=custom_headers,
                    ) as response:
                        print(f"AD5X Upload Response Status: {response.status}")

                        if response.status != 200:
                            print(
                                f"AD5X Upload failed: Printer responded with status {response.status}"
                            )
                            return False

                        result = await json_from_response(response)
                        print("AD5X Upload Response Data:", result)

                        if NetworkUtils.is_ok(result):
                            print("AD5X Upload successful according to printer response.")
                            return True
                        else:
                            print(
                                f"AD5X Upload failed: Printer response code={result.get('code')}, message={result.get('message')}"
                            )
                            return False

        except Exception as e:
            print(f"UploadFileAD5X error: {e}")
            return False

    async def start_ad5x_multi_color_job(self, params: AD5XLocalJobParams) -> bool:
        """
        Starts a multi-color local print job on AD5X printers with material mappings.
        This method automatically configures the material station settings and validates
        all parameters before sending the print command.

        Args:
            params: Job parameters including file name, leveling option, and material mappings

        Returns:
            True if successful, False if validation fails or printer rejects
        """
        # Validate that this is an AD5X printer
        if not self._validate_ad5x_printer():
            return False

        # Validate material mappings
        if not self._validate_material_mappings(params.material_mappings):
            return False

        # Validate file name
        if not params.file_name or params.file_name.strip() == "":
            print("AD5X Multi-Color Job error: fileName cannot be empty")
            return False

        # Create payload with AD5X-specific parameters
        payload = {
            "serialNumber": self.client.serial_number,
            "checkCode": self.client.check_code,
            "fileName": params.file_name,
            "levelingBeforePrint": params.leveling_before_print,
            "firstLayerInspection": False,
            "flowCalibration": False,
            "timeLapseVideo": False,
            "useMatlStation": True,  # Automatically set to true for multi-color jobs
            "gcodeToolCnt": len(params.material_mappings),  # Set based on material mappings count
            "materialMappings": [
                {
                    "toolId": m.tool_id,
                    "slotId": m.slot_id,
                    "materialName": m.material_name,
                    "toolMaterialColor": m.tool_material_color,
                    "slotMaterialColor": m.slot_material_color,
                }
                for m in params.material_mappings
            ],
        }

        try:
            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.GCODE_PRINT),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    return False

                result = await json_from_response(response)
                return NetworkUtils.is_ok(result)

        except Exception as error:
            print(f"AD5X Multi-Color Job error: {error}")
            raise error

    async def start_ad5x_single_color_job(self, params: AD5XSingleColorJobParams) -> bool:
        """
        Starts a single-color local print job on AD5X printers.
        This method automatically configures the printer for single-color printing
        without using the material station.

        Args:
            params: Job parameters including file name and leveling option

        Returns:
            True if successful, False if validation fails or printer rejects
        """
        # Validate that this is an AD5X printer
        if not self._validate_ad5x_printer():
            return False

        # Validate file name
        if not params.file_name or params.file_name.strip() == "":
            print("AD5X Single-Color Job error: fileName cannot be empty")
            return False

        # Create payload with AD5X-specific parameters for single-color printing
        payload = {
            "serialNumber": self.client.serial_number,
            "checkCode": self.client.check_code,
            "fileName": params.file_name,
            "levelingBeforePrint": params.leveling_before_print,
            "firstLayerInspection": False,
            "flowCalibration": False,
            "timeLapseVideo": False,
            "useMatlStation": False,  # Set to false for single-color jobs
            "gcodeToolCnt": 0,  # Set to 0 for single-color jobs
            "materialMappings": [],  # Empty array for single-color jobs
        }

        try:
            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.GCODE_PRINT),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    return False

                result = await json_from_response(response)
                return NetworkUtils.is_ok(result)

        except Exception as error:
            print(f"AD5X Single-Color Job error: {error}")
            raise error

    # --- Creator 5 / Creator 5 Pro ---
    # The Creator 5 splits the material-station workflow across two requests,
    # unlike the AD5X (which maps materials at upload time). On the C5:
    #   1. Upload the file (POST /uploadGcode). The firmware reads `useMatlStation`
    #      and `gcodeToolCnt` here to register the file as a multi-tool job. There
    #      is NO `firstLayerInspection` header (the field doesn't exist on the
    #      C5), and the booleans are checked as the string "true"/"false".
    #   2. Start the print (POST /printGcode) with the per-tool
    #      `materialMappings`. See start_creator5_job.

    async def upload_file_creator5(self, params: Creator5UploadParams) -> bool:
        """
        Uploads a file (.gcode or .3mf) to a Creator 5 / Creator 5 Pro via
        ``POST /uploadGcode``, with the C5-specific material-station headers.

        Unlike :meth:`upload_file_ad5x` this sends no ``firstLayerInspection``
        header (the C5 has no such field) and no ``materialMappings`` header (the
        C5 maps materials at print-start, not upload). Booleans are sent as the
        string "true"/"false".

        Args:
            params: Creator 5 upload parameters.

        Returns:
            True on success, False otherwise.
        """
        file_path_obj = Path(params.file_path)

        if not file_path_obj.exists():
            print(f"upload_file_creator5 error: File not found at {params.file_path}")
            return False

        file_size = file_path_obj.stat().st_size
        file_name = file_path_obj.name

        print(
            f"Starting Creator 5 upload for {file_name}, Size: {file_size}, "
            f"Start: {params.start_print}, Level: {params.leveling_before_print}, "
            f"MatlStation: {params.use_matl_station}, Tools: {params.gcode_tool_cnt}"
        )

        try:
            # C5 upload headers. No firstLayerInspection (absent on the C5);
            # booleans sent as "true"/"false" (firmware checks for "true"); no
            # materialMappings header (C5 maps at print-start, not upload).
            custom_headers = {
                "serialNumber": self.client.serial_number,
                "checkCode": self.client.check_code,
                "fileSize": str(file_size),
                "printNow": str(params.start_print).lower(),
                "levelingBeforePrint": str(params.leveling_before_print).lower(),
                "flowCalibration": str(params.flow_calibration).lower(),
                "timeLapseVideo": str(params.time_lapse_video).lower(),
                "useMatlStation": str(params.use_matl_station).lower(),
                "gcodeToolCnt": str(params.gcode_tool_cnt),
                "Expect": "100-continue",
            }

            print("Creator 5 Upload Request Headers:", custom_headers)

            # Create multipart form data
            async with aiohttp.ClientSession() as session:
                with open(params.file_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "gcodeFile", f, filename=file_name, content_type="application/octet-stream"
                    )

                    async with session.post(
                        self.client.get_endpoint(Endpoints.UPLOAD_FILE),
                        data=data,
                        headers=custom_headers,
                    ) as response:
                        print(f"Creator 5 Upload Response Status: {response.status}")

                        if response.status != 200:
                            print(
                                f"Creator 5 Upload failed: Printer responded with "
                                f"status {response.status}"
                            )
                            return False

                        result = await json_from_response(response)
                        print("Creator 5 Upload Response Data:", result)

                        if NetworkUtils.is_ok(result):
                            print("Creator 5 Upload successful according to printer response.")
                            return True

                        print(
                            "Creator 5 Upload failed: Printer response code="
                            f"{result.get('code')}, message={result.get('message')}"
                        )
                        return False

        except Exception as e:
            print(f"upload_file_creator5 error: {e}")
            return False

    async def start_creator5_job(self, params: Creator5JobParams) -> bool:
        """
        Starts a local print on a Creator 5 / Creator 5 Pro via ``POST /printGcode``.

        This is the Creator 5's print-start material-matching command (distinct
        from the AD5X, which maps materials at upload time). The file must already
        be on the printer. Provide ``material_mappings`` for a multi-tool print, or
        omit them for a single-tool print. Sends only the fields the Creator 5
        firmware reads: NO ``useMatlStation`` / ``gcodeToolCnt`` (those live on the
        upload) and NO ``firstLayerInspection`` (doesn't exist on the C5).
        ``flowCalibration`` and ``timeLapseVideo`` are always present (default False).

        Args:
            params: File name, leveling flag, and optional flags / material mappings.

        Returns:
            True if the printer accepts the print command, False if validation
            fails or the printer rejects it.

        Raises:
            Exception: On a network failure sending the command.
        """
        if not self._validate_material_station_printer():
            return False

        if not params.file_name or params.file_name.strip() == "":
            print("Creator 5 Job error: fileName cannot be empty")
            return False

        has_mappings = params.material_mappings is not None and len(params.material_mappings) > 0
        if has_mappings and not self._validate_creator5_material_mappings(
            params.material_mappings or []
        ):
            return False

        payload: dict[str, Any] = {
            "serialNumber": self.client.serial_number,
            "checkCode": self.client.check_code,
            "fileName": params.file_name,
            "levelingBeforePrint": params.leveling_before_print,
            "flowCalibration": params.flow_calibration,
            "timeLapseVideo": params.time_lapse_video,
        }
        if has_mappings:
            payload["materialMappings"] = [
                {
                    "toolId": m.tool_id,
                    "slotId": m.slot_id,
                    "materialName": m.material_name,
                    "toolMaterialColor": m.tool_material_color,
                    "slotMaterialColor": m.slot_material_color,
                }
                for m in params.material_mappings or []
            ]

        try:
            session = await self.client.get_http_session()
            async with session.post(
                self.client.get_endpoint(Endpoints.GCODE_PRINT),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    return False

                result = await json_from_response(response)
                return NetworkUtils.is_ok(result)

        except Exception as error:
            print(f"Creator 5 Job error: {error}")
            raise error

    def _validate_material_station_printer(self) -> bool:
        """
        Validates that the current printer has a material station and therefore
        supports material-mapping uploads/jobs. Covers AD5X and the Creator 5
        series, which share the same material-mapping print flow (Creator 5 =
        "AD5X + more").

        Returns:
            True if the printer supports material mappings, False otherwise.
        """
        if not self.client.is_ad5x and not self.client.is_creator5:
            print(
                "Material-station job error: this method requires an AD5X or "
                "Creator 5 series printer"
            )
            return False
        return True

    def _validate_creator5_material_mappings(
        self, material_mappings: list[AD5XMaterialMapping]
    ) -> bool:
        """
        Validates Creator 5 material mappings. Delegates to the shared validator
        with ``allow_empty=True`` (the C5 uses an empty array for the
        single-tool print start).

        Args:
            material_mappings: Array of Creator 5 mappings to validate.

        Returns:
            True if all mappings are valid, False otherwise.
        """
        return self._validate_mappings(
            material_mappings, allow_empty=True, label="Creator 5 material mappings"
        )

    def _validate_mappings(
        self,
        material_mappings: list[AD5XMaterialMapping],
        *,
        allow_empty: bool,
        label: str,
    ) -> bool:
        """
        Shared material-mapping validator used by both the AD5X and Creator 5
        flows. Checks toolId 0-3, slotId 1-4, non-empty materialName, and
        ``#RRGGBB`` tool/slot colors.

        Args:
            material_mappings: Array of mappings to validate.
            allow_empty: If True, an empty array is accepted (Creator 5
                single-tool start). If False, an empty array is rejected
                (AD5X multi-color jobs require at least one mapping).
            label: Prefix for the printed validation-error messages.

        Returns:
            True if all mappings are valid, False otherwise.
        """
        if not material_mappings or len(material_mappings) == 0:
            if allow_empty:
                return True
            print(
                f"{label} error: materialMappings array cannot be empty for multi-color jobs"
            )
            return False

        if len(material_mappings) > 4:
            print(f"{label} error: Maximum 4 material mappings allowed")
            return False

        hex_color_regex = re.compile(r"^#[0-9A-Fa-f]{6}$")

        for i, mapping in enumerate(material_mappings):
            if mapping.tool_id < 0 or mapping.tool_id > 3:
                print(
                    f"{label} error: toolId must be between 0-3, "
                    f"got {mapping.tool_id} at index {i}"
                )
                return False

            if mapping.slot_id < 1 or mapping.slot_id > 4:
                print(
                    f"{label} error: slotId must be between 1-4, "
                    f"got {mapping.slot_id} at index {i}"
                )
                return False

            if not mapping.material_name or mapping.material_name.strip() == "":
                print(f"{label} error: materialName cannot be empty at index {i}")
                return False

            if not hex_color_regex.match(mapping.tool_material_color):
                print(
                    f"{label} error: toolMaterialColor must be in "
                    f"#RRGGBB format, got {mapping.tool_material_color} at index {i}"
                )
                return False

            if not hex_color_regex.match(mapping.slot_material_color):
                print(
                    f"{label} error: slotMaterialColor must be in "
                    f"#RRGGBB format, got {mapping.slot_material_color} at index {i}"
                )
                return False

        return True

    def _validate_ad5x_printer(self) -> bool:
        """
        Validates that the current printer is an AD5X model.

        Returns:
            True if the printer is AD5X, false otherwise
        """
        if not self.client.is_ad5x:
            print("AD5X Job error: This method can only be used with AD5X printers")
            return False
        return True

    def _encode_material_mappings_to_base64(
        self, material_mappings: list[AD5XMaterialMapping]
    ) -> str:
        """
        Encodes material mappings array to base64 string for HTTP headers.
        Converts AD5XMaterialMapping array to JSON and then to base64 encoding.

        Args:
            material_mappings: Array of material mappings to encode

        Returns:
            Base64-encoded JSON string
        """
        try:
            json_array = [
                {
                    "toolId": m.tool_id,
                    "slotId": m.slot_id,
                    "materialName": m.material_name,
                    "toolMaterialColor": m.tool_material_color,
                    "slotMaterialColor": m.slot_material_color,
                }
                for m in material_mappings
            ]
            json_string = json.dumps(json_array)
            return base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
        except Exception as error:
            print("Failed to encode material mappings to base64:", error)
            raise Exception("Failed to encode material mappings for upload") from error  # noqa: B904

    def _validate_material_mappings(self, material_mappings: list[AD5XMaterialMapping]) -> bool:
        """
        Validates material mappings for AD5X multi-color jobs. Delegates to the
        shared validator with ``allow_empty=False`` (AD5X multi-color jobs
        require at least one mapping).

        Args:
            material_mappings: Array of material mappings to validate

        Returns:
            True if all mappings are valid, false otherwise
        """
        return self._validate_mappings(
            material_mappings, allow_empty=False, label="Material mappings validation"
        )
