"""
FlashForge Python API - Main Unified Client

This module provides the main FlashForgeClient class that orchestrates both HTTP and TCP
communication layers for controlling FlashForge 3D printers.
"""
import asyncio
from typing import Optional

import aiohttp

from .api.constants.endpoints import Endpoints
from .api.controls import Control, Files, Info, JobControl, TempControl
from .api.controls.info import MachineInfoParser
from .api.network.utils import NetworkUtils
from .models import FFMachineInfo, ProductResponse
from .tcp import FlashForgeClient as TcpClient
from .tcp import PrinterInfo


class FlashForgeClient:
    """
    Main client for interacting with a FlashForge 3D printer.
    
    This class provides methods for controlling the printer, managing print jobs,
    retrieving information, and handling file operations. It orchestrates both
    HTTP and TCP communication layers to provide a unified interface.
    """

    def __init__(self, ip_address: str, serial_number: str, check_code: str):
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
        self._PORT = 8898
        self._HTTP_TIMEOUT = 5.0

        # HTTP client state
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._http_client_busy = False

        # TCP client setup
        self.tcp_client = TcpClient(ip_address)

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
        self.firmware_version: str = ""
        self.firmware_ver: str = ""
        self.mac_address: str = ""
        self.flash_cloud_code: str = ""
        self.polar_cloud_code: str = ""
        self.lifetime_print_time: str = ""
        self.lifetime_filament_meters: str = ""

        # Control states
        self.led_control: bool = False
        self.filtration_control: bool = False

    @property
    def is_ad5x(self) -> bool:
        """
        Indicates if the printer is an AD5X model.

        Returns:
            True if the printer is AD5X, False otherwise
        """
        return self._is_ad5x

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_http_session()
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
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
            self._http_session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"Accept": "*/*"}
            )
        return self._http_session

    async def initialize(self) -> bool:
        """
        Initializes the FlashForgeClient and verifies the connection to the printer.
        
        Returns:
            True if initialization is successful, False otherwise
        """
        connected = await self.verify_connection()
        if connected:
            return True
        print("Failed to connect to printer")
        return False

    async def is_http_client_busy(self) -> bool:
        """
        Checks if the HTTP client is currently busy.
        
        Returns:
            True if the HTTP client is busy, False otherwise
        """
        # Wait a bit if busy to prevent tight loops
        while self._http_client_busy:
            await asyncio.sleep(0.01)
        return self._http_client_busy

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
        print("New API control failed!")
        return False

    async def dispose(self) -> None:
        """
        Disposes of the FlashForgeClient instance, stopping keep-alive messages 
        and cleaning up resources.
        """
        # Stop TCP keep-alive and dispose
        if hasattr(self.tcp_client, 'stop_keep_alive'):
            await self.tcp_client.stop_keep_alive(True)
        if hasattr(self.tcp_client, 'dispose'):
            await self.tcp_client.dispose()

        # Close HTTP session
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

    def cache_details(self, info: Optional[FFMachineInfo]) -> bool:
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
        self.firmware_version = info.firmware_version or ""
        self.firmware_ver = info.firmware_version.split('-')[0] if info.firmware_version else ""
        self.mac_address = info.mac_address or ""
        self.flash_cloud_code = info.flash_cloud_register_code or ""
        self.polar_cloud_code = info.polar_cloud_register_code or ""
        self.lifetime_print_time = info.formatted_total_run_time or ""
        self._is_ad5x = info.is_ad5x

        # Format filament usage
        if info.cumulative_filament is not None:
            self.lifetime_filament_meters = f"{info.cumulative_filament:.2f}m"
        else:
            self.lifetime_filament_meters = "0.00m"

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
                print("Failed to get valid response from printer API")
                return False

            # Parse machine info from detail response
            machine_info = MachineInfoParser.from_detail(response.detail)
            if not machine_info:
                print("Failed to parse machine info from detail response")
                return False

            # Get TCP printer information to check for Pro model
            tcp_info: Optional[PrinterInfo] = await self.tcp_client.get_printer_info()
            if tcp_info:
                if "Pro" in tcp_info.type_name:
                    self.is_pro = True
            else:
                print("Warning: Unable to get PrinterInfo from TCP API, some features might not work")

            # Cache the details
            return self.cache_details(machine_info)

        except Exception as error:
            print(f"Error in verify_connection: {error}")
            return False

    async def send_product_command(self) -> bool:
        """
        Sends a product command to the printer to retrieve control states.
        
        This method sets the http_client_busy flag while the request is in progress.
        
        Returns:
            True if the product command is sent successfully and valid data is received, 
            False otherwise
        """
        self._http_client_busy = True

        payload = {
            "serialNumber": self.serial_number,
            "checkCode": self.check_code
        }

        try:
            session = await self._ensure_http_session()
            async with session.post(
                self.get_endpoint(Endpoints.PRODUCT),
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status != 200:
                    return False

                # Fix for FlashForge printer's malformed Content-Type header
                # Some printers return "appliation/json" instead of "application/json"
                try:
                    data = await response.json()
                except aiohttp.ContentTypeError:
                    # Fallback: manually parse as JSON if Content-Type is malformed
                    text = await response.text()
                    import json
                    data = json.loads(text)

                # Validate response structure
                if not NetworkUtils.is_ok(data):
                    return False

                # Parse product response and set control states
                product_response = ProductResponse(**data)
                if product_response and product_response.product:
                    product = product_response.product
                    self.led_control = product.lightCtrlState != 0
                    self.filtration_control = not (
                        product.internalFanCtrlState == 0 or
                        product.externalFanCtrlState == 0
                    )
                    return True

        except Exception as error:
            print(f"Error in send_product_command: {error}")
            return False
        finally:
            self._http_client_busy = False

        return False

    async def get_http_session(self) -> aiohttp.ClientSession:
        """
        Gets the HTTP session for making requests.
        
        Returns:
            The HTTP session instance
        """
        return await self._ensure_http_session()

    # Additional convenience methods for direct access to common operations

    async def get_printer_status(self) -> Optional[FFMachineInfo]:
        """
        Gets the current printer status and information.
        
        Returns:
            FFMachineInfo object with current printer status, or None if failed
        """
        return await self.info.get()

    async def get_temperatures(self):
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

    def __repr__(self) -> str:
        """String representation of the client."""
        return (
            f"FlashForgeClient(ip={self.ip_address}, "
            f"printer='{self.printer_name}', "
            f"pro={self.is_pro}, "
            f"firmware='{self.firmware_ver}')"
        )
