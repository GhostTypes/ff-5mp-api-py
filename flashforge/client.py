"""
FlashForge Python API - Main Unified Client

This module provides the main FlashForgeClient class that orchestrates both HTTP and TCP
communication layers for controlling FlashForge 3D printers.
"""

import asyncio
import logging
from dataclasses import dataclass

import aiohttp
from pydantic import ValidationError

from .api.constants.endpoints import CAMERA_STREAM_PORT, Endpoints
from .api.controls import Control, Files, Info, JobControl, TempControl
from .api.controls.info import MachineInfoParser
from .api.network.utils import NetworkUtils, json_from_response
from .models import FFMachineInfo, Product, ProductResponse
from .tcp import FlashForgeClient as TcpClient
from .tcp import FlashForgeTcpClientOptions, PrinterInfo
from .tcp.parsers.temp_info import TempInfo

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FiveMClientConnectionOptions:
    """Optional connection and feature overrides for FiveMClient-compatible clients."""

    http_port: int | None = None
    tcp_port: int | None = None
    led_control_override: bool | None = None
    # Force HTTP-only transport (skip the TCP/8899 handshake). Set this for a
    # Creator 5 / Creator 5 Pro, which exposes no TCP service; otherwise it is
    # auto-detected from the firmware-reported model after `verify_connection`.
    http_only: bool | None = None


class FlashForgeClient:
    """
    Main client for interacting with a FlashForge 3D printer.

    This class provides methods for controlling the printer, managing print jobs,
    retrieving information, and handling file operations. It orchestrates both
    HTTP and TCP communication layers to provide a unified interface.
    """

    def __init__(
        self,
        ip_address: str,
        serial_number: str,
        check_code: str,
        options: FiveMClientConnectionOptions | None = None,
    ):
        """
        Creates an instance of FlashForgeClient.

        Args:
            ip_address: The IP address of the printer
            serial_number: The serial number of the printer
            check_code: The check code for the printer
        """
        # Connection parameters
        self.ip_address = ip_address
        self.serial_number = serial_number
        self.check_code = check_code

        # Constants
        self._PORT = options.http_port if options and options.http_port is not None else 8898
        self._HTTP_TIMEOUT = 15.0

        # HTTP client state
        self._http_session: aiohttp.ClientSession | None = None
        self._http_client_event = asyncio.Event()
        self._http_client_event.set()  # Not busy initially

        # FIFO mutex for command submission. asyncio.Lock hands the lock to
        # waiters in the order they asked for it. So command POSTs run one at
        # a time, in submission order. Scope: command POSTs only (/control,
        # /product, /printGcode). File uploads (/uploadGcode) and read/poll
        # POSTs (/detail, /gcodeList, /gcodeThumb) stay outside the lock. An
        # upload can run for minutes; pause and stop must never queue behind
        # one.
        self._command_lock = asyncio.Lock()

        # TCP client setup
        tcp_options = None
        if options and options.tcp_port is not None:
            tcp_options = FlashForgeTcpClientOptions(port=options.tcp_port)
        self.tcp_client = TcpClient(ip_address, tcp_options)

        # Control instances
        self.control = Control(self)
        self.job_control = JobControl(self)
        self.info = Info(self)
        self.files = Files(self)
        self.temp_control = TempControl(self)

        # Printer information cache
        self.printer_name: str = ""
        self.is_pro: bool = False
        self._is_ad5x: bool = False
        self.is_creator5: bool = False
        self.is_creator5_pro: bool = False
        self.firmware_version: str = ""
        self.firmware_ver: str = ""
        self.mac_address: str = ""
        self.flash_cloud_code: str = ""
        self.polar_cloud_code: str = ""
        self.camera_stream_url: str = ""
        self.lifetime_print_time: str = ""
        self.lifetime_filament_meters: str = ""
        self.product_info: Product | None = None

        # Control states
        self.led_control: bool = False
        self.filtration_control: bool = False
        self._detected_led_control: bool = False
        self._detected_filtration_control: bool = False
        self._led_control_override = (
            options.led_control_override
            if options and options.led_control_override is not None
            else None
        )
        self._apply_feature_overrides()

        # Transport selection. Creator 5 / Creator 5 Pro have no TCP/8899
        # service, so they must run HTTP-only. An explicit override wins;
        # otherwise http_only is auto-set from the detected model in
        # `verify_connection` / `cache_details`.
        self._http_only_override: bool | None = (
            options.http_only if options and options.http_only is not None else None
        )
        self._http_only: bool = bool(self._http_only_override)

    @property
    def is_ad5x(self) -> bool:
        """
        Indicates if the printer is an AD5X model.

        Returns:
            True if the printer is AD5X, False otherwise
        """
        return self._is_ad5x

    @property
    def http_only(self) -> bool:
        """
        Indicates whether the client should avoid the TCP transport.

        True for Creator 5 / Creator 5 Pro (no TCP/8899 service) or when an
        explicit ``http_only`` override was supplied at construction. When True,
        TCP-only operations are unavailable (see :meth:`can_use_tcp`).

        Returns:
            True if the client must operate over HTTP only
        """
        return self._http_only

    def can_use_tcp(self, op: str = "") -> bool:
        """
        Report whether a TCP-backed operation may be attempted.

        Returns False whenever this client is HTTP-only (e.g. a Creator 5 with
        no TCP/8899 service). TCP-delegating control/temperature methods check
        this and no-op (return False) instead of hanging on a dead socket.

        Args:
            op: Optional operation name, included in the warning log.

        Returns:
            True if TCP operations are permitted, False otherwise
        """
        if self._http_only:
            logger.debug("%s() unavailable: printer has no TCP control channel (HTTP-only).", op)
            return False
        return True

    def _update_http_only_from_model(self) -> None:
        """Recompute ``http_only`` from the detected model unless overridden."""
        if self._http_only_override is not None:
            self._http_only = bool(self._http_only_override)
        else:
            self._http_only = self.is_creator5 or self.is_creator5_pro

    async def __aenter__(self) -> "FlashForgeClient":
        """Async context manager entry."""
        await self._ensure_http_session()
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.dispose()

    async def _ensure_http_session(self) -> aiohttp.ClientSession:
        """
        Ensures that an HTTP session is available.

        Returns:
            The HTTP session instance
        """
        if self._http_session is None or self._http_session.closed:
            timeout = aiohttp.ClientTimeout(total=self._HTTP_TIMEOUT)
            self._http_session = aiohttp.ClientSession(timeout=timeout, headers={"Accept": "*/*"})
        return self._http_session

    @property
    def command_lock(self) -> asyncio.Lock:
        """
        The FIFO lock that serializes command-submission HTTP POSTs.

        Command POSTs (/control, /product, /printGcode) hold this lock while
        the request is in flight. asyncio.Lock serves waiters in arrival order,
        so concurrent commands run one at a time, first come first served.
        Uploads and read/poll requests never take this lock. So a long upload
        cannot delay a pause or stop command.
        """
        return self._command_lock

    async def initialize(self) -> bool:
        """
        Initializes the FlashForgeClient and verifies the connection to the printer.

        Returns:
            True if initialization is successful, False otherwise
        """
        connected = await self.verify_connection()
        if connected:
            return True
        logger.warning("Failed to connect to the printer.")
        return False

    @property
    def _http_client_busy(self) -> bool:
        """
        Legacy property to maintain internal API compatibility.
        Returns True if the client is busy (event is not set), False otherwise.
        """
        return not self._http_client_event.is_set()

    @_http_client_busy.setter
    def _http_client_busy(self, value: bool) -> None:
        """
        Sets the busy state using the event.
        True means busy (clear event), False means not busy (set event).
        """
        if value:
            self._http_client_event.clear()
        else:
            self._http_client_event.set()

    async def is_http_client_busy(self) -> bool:
        """
        Checks if the HTTP client is currently busy.
        Waits until the client is not busy before returning.

        Returns:
            False (always returns False after waiting, for compatibility)
        """
        await self._http_client_event.wait()
        return False

    def release_http_client(self) -> None:
        """Releases the HTTP client, allowing it to be used for new requests."""
        self._http_client_busy = False

    async def init_control(self) -> bool:
        """
        Initializes the control interface with the printer.

        This involves sending a product command and initializing TCP control.

        Returns:
            True if control initialization is successful, False otherwise
        """
        if await self.send_product_command():
            return await self.tcp_client.init_control()
        logger.warning("New API control failed; the product command was rejected.")
        return False

    async def dispose(self) -> None:
        """
        Disposes of the FlashForgeClient instance, stopping keep-alive messages
        and cleaning up resources.
        """
        # Stop TCP keep-alive and dispose. An HTTP-only client (e.g. Creator 5,
        # which has no TCP/8899 service) never opened a TCP socket, so skip the
        # cleanup handshake -- otherwise the logout send would attempt (and time
        # out on) a connection that was never established.
        if not self._http_only:
            if hasattr(self.tcp_client, "stop_keep_alive"):
                await self.tcp_client.stop_keep_alive(True)
            if hasattr(self.tcp_client, "dispose"):
                await self.tcp_client.dispose()

        # Close HTTP session
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

        self.camera_stream_url = ""

    async def detect_camera_stream(self, timeout_ms: int = 3000) -> str:
        """
        Probes the printer's known OEM camera endpoint.

        Falls back to a short GET when HEAD is unsupported so MJPEG servers
        that reject HEAD requests are still detected.

        Args:
            timeout_ms: Timeout for each probe attempt in milliseconds.

        Returns:
            The working camera stream URL, or an empty string if not detected.
        """
        probe_url = f"http://{self.ip_address}:{CAMERA_STREAM_PORT}/?action=stream"
        timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000)

        if await self._probe_camera_stream_with_method("head", probe_url, timeout):
            return probe_url

        if await self._probe_camera_stream_with_method("get", probe_url, timeout):
            return probe_url

        return ""

    async def _probe_camera_stream_with_method(
        self,
        method: str,
        probe_url: str,
        timeout: aiohttp.ClientTimeout,
    ) -> bool:
        try:
            session = await self._ensure_http_session()
            request = session.head if method == "head" else session.get

            async with request(probe_url, timeout=timeout) as response:
                return self._is_valid_camera_probe_response(
                    response.status, response.headers.get("Content-Type", "")
                )
        except Exception:
            return False

    @staticmethod
    def _is_valid_camera_probe_response(status: int, content_type: str | None) -> bool:
        if status != 200:
            return False

        normalized_content_type = (content_type or "").lower()
        return (
            normalized_content_type == ""
            or "multipart" in normalized_content_type
            or "video/x-mjpeg" in normalized_content_type
        )

    def cache_details(self, info: FFMachineInfo | None) -> bool:
        """
        Caches machine details from the provided FFMachineInfo object.

        Args:
            info: The FFMachineInfo object containing printer details

        Returns:
            True if caching is successful, False otherwise
        """
        if not info:
            return False

        # Cache all printer information
        self.printer_name = info.name or ""
        self.is_pro = info.is_pro
        self.firmware_version = info.firmware_version or ""
        self.firmware_ver = info.firmware_version.split("-")[0] if info.firmware_version else ""
        self.mac_address = info.mac_address or ""
        self.flash_cloud_code = info.flash_cloud_register_code or ""
        self.polar_cloud_code = info.polar_cloud_register_code or ""
        self.camera_stream_url = info.camera_stream_url or ""
        self.lifetime_print_time = info.formatted_total_run_time or ""
        self._is_ad5x = info.is_ad5x
        self.is_creator5 = info.is_creator5
        self.is_creator5_pro = info.is_creator5_pro
        # Refresh transport selection now that the model flags are cached.
        self._update_http_only_from_model()

        # Format filament usage
        filament_value = info.cumulative_filament if info.cumulative_filament is not None else 0.0
        self.lifetime_filament_meters = f"{filament_value:.2f}m"
        self._apply_feature_overrides()

        return True

    def get_endpoint(self, endpoint: str) -> str:
        """
        Constructs the full API endpoint URL.

        Args:
            endpoint: The specific API endpoint path

        Returns:
            The full URL for the API endpoint
        """
        return f"http://{self.ip_address}:{self._PORT}{endpoint}"

    async def verify_connection(self) -> bool:
        """
        Verifies the connection to the printer by retrieving machine details and TCP information.

        Returns:
            True if the connection is verified, False otherwise
        """
        try:
            # Get HTTP API response
            response = await self.info.get_detail_response()
            if not response or not NetworkUtils.is_ok(response):
                logger.warning("Failed to get a valid response from the printer API.")
                return False

            # Parse machine info from detail response
            machine_info = MachineInfoParser.from_detail(response.detail)
            if not machine_info:
                logger.warning("Failed to parse machine info from the /detail response.")
                return False

            # Detect http_only from the parsed model BEFORE touching TCP. The
            # Creator 5 / Creator 5 Pro expose no TCP/8899 service, so the M115
            # handshake would hang until the connect timeout. An explicit
            # override always wins.
            if self._http_only_override is not None:
                self._http_only = bool(self._http_only_override)
            else:
                self._http_only = machine_info.is_creator5

            # Get TCP printer information to check for Pro model
            tcp_info: PrinterInfo | None = None
            if not self._http_only:
                tcp_info = await self.tcp_client.get_printer_info()
                if tcp_info:
                    if (
                        "Pro" in tcp_info.type_name
                        and not machine_info.is_pro
                        and not machine_info.is_ad5x
                    ):
                        self.is_pro = True
                else:
                    logger.warning(
                        "Unable to get PrinterInfo from the TCP API; some features might "
                        "not work."
                    )

            # Cache the details
            return self.cache_details(machine_info)

        except Exception as error:
            logger.warning("Error in verify_connection: %s", error)
            return False

    async def send_product_command(self) -> bool:
        """
        Sends a product command to the printer to retrieve control states.

        This method holds the command lock while the request is in progress.

        Returns:
            True if the product command is sent successfully and valid data is received,
            False otherwise
        """
        payload = {"serialNumber": self.serial_number, "checkCode": self.check_code}

        try:
            session = await self._ensure_http_session()
            async with self._command_lock:
                async with session.post(
                    self.get_endpoint(Endpoints.PRODUCT),
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        return False

                    data = await json_from_response(response)

                    # Validate response structure
                    if not NetworkUtils.is_ok(data):
                        return False

                    # Parse product response and set control states
                    product_response = ProductResponse(**data)
                    if product_response and product_response.product:
                        product = product_response.product
                        self.product_info = product
                        self._detected_led_control = product.lightCtrlState != 0
                        self._detected_filtration_control = not (
                            product.internalFanCtrlState == 0 or product.externalFanCtrlState == 0
                        )
                        self._apply_feature_overrides()
                        return True

        except ValidationError as error:
            # Distinct from a rejected check code, and it must not read as one:
            # the printer answered 200 with code 0, we simply could not parse
            # what it said. Callers treat a False return as bad credentials
            # (ff-5mp-hass surfaces it as "check code incorrect"), so the log
            # line is the only place the real cause can surface.
            logger.warning(
                "Could not parse the /product response; reporting the printer as "
                "unavailable rather than the credentials as rejected. This usually "
                "means the firmware added a field this library has not seen. %s",
                error,
            )
            return False
        except Exception as error:
            logger.warning("Error in send_product_command: %s", error)
            return False

        return False

    async def get_http_session(self) -> aiohttp.ClientSession:
        """
        Gets the HTTP session for making requests.

        Returns:
            The HTTP session instance
        """
        return await self._ensure_http_session()

    # Additional convenience methods for direct access to common operations

    async def get_printer_status(self) -> FFMachineInfo | None:
        """
        Gets the current printer status and information.

        Returns:
            FFMachineInfo object with current printer status, or None if failed
        """
        return await self.info.get()

    async def get_temperatures(self) -> TempInfo | None:
        """
        Gets current temperature readings from the printer.

        Returns:
            Temperature information from the TCP client
        """
        return await self.tcp_client.get_temp_info()

    async def home_all_axes(self) -> bool:
        """
        Homes all axes (X, Y, Z) of the printer.

        Returns:
            True if successful, False otherwise
        """
        return await self.control.home_axes()

    async def emergency_stop(self) -> bool:
        """
        Performs an emergency stop of the printer.

        Returns:
            True if successful, False otherwise
        """
        return await self.job_control.cancel_print_job()

    async def pause_print(self) -> bool:
        """
        Pauses the current print job.

        Returns:
            True if successful, False otherwise
        """
        return await self.job_control.pause_print_job()

    async def resume_print(self) -> bool:
        """
        Resumes a paused print job.

        Returns:
            True if successful, False otherwise
        """
        return await self.job_control.resume_print_job()

    def set_feature_overrides(self, *, led_control: bool | None = None) -> None:
        """Apply manual feature overrides for integrations that need UI-level capability control."""
        self._led_control_override = led_control
        self._apply_feature_overrides()

    def _apply_feature_overrides(self) -> None:
        """Apply any configured manual capability overrides to the cached client state."""
        self.led_control = (
            self._led_control_override
            if self._led_control_override is not None
            else self._detected_led_control
        )
        self.filtration_control = self._detected_filtration_control

    def __repr__(self) -> str:
        """String representation of the client."""
        return (
            f"FlashForgeClient(ip={self.ip_address}, "
            f"printer='{self.printer_name}', "
            f"pro={self.is_pro}, "
            f"firmware='{self.firmware_ver}')"
        )
