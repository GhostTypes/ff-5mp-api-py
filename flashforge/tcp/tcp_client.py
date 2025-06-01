"""
Low-level TCP client for communicating with FlashForge 3D printers.

This module provides the foundational TCP communication layer, managing socket connections,
sending raw commands, handling responses, and maintaining keep-alive connections.
"""

import asyncio
import logging
from typing import List, Optional

from .gcode.gcodes import GCodes

logger = logging.getLogger(__name__)


class FlashForgeTcpClient:
    """
    Foundational TCP client for communicating with FlashForge 3D printers.
    
    This class manages the socket connection, sending raw commands, handling responses,
    and maintaining a keep-alive connection. It serves as the base class for
    FlashForgeClient, which implements more specific G-code command logic.
    
    The communication protocol typically involves sending ASCII G-code/M-code commands
    terminated by a newline character ('\\n') and receiving text-based responses,
    often ending with "ok" to indicate success.
    """

    def __init__(self, hostname: str) -> None:
        """
        Create an instance of FlashForgeTcpClient.
        
        Initializes the hostname and attempts to connect to the printer.
        
        Args:
            hostname: The IP address or hostname of the FlashForge printer
        """
        self.hostname = hostname
        self.port = 8899
        """The default TCP port used for connecting to FlashForge printers."""

        self.timeout = 5.0
        """The default timeout (in seconds) for socket operations."""

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        """The underlying network streams for TCP communication."""

        self._keep_alive_task: Optional[asyncio.Task] = None
        """Task for the keep-alive mechanism."""

        self._keep_alive_cancellation_token = False
        """Token to signal cancellation of the keep-alive loop."""

        self._keep_alive_errors = 0
        """Counter for consecutive keep-alive errors."""

        self._socket_busy = False
        """Flag indicating if the socket is currently busy sending a command and awaiting a response."""

        self._socket_lock = asyncio.Lock()
        """Lock to ensure only one command is sent at a time."""

        try:
            logger.info("TcpPrinterClient creation")
            # Note: We don't connect immediately in Python - connection is established on first use
            logger.info("Initialized (connection will be established on first command)")
        except Exception:
            logger.error("TcpPrinterClient failed to init!")
            raise

    async def start_keep_alive(self) -> None:
        """
        Start a keep-alive mechanism to maintain the TCP connection with the printer.
        
        Periodically sends a status command (GCodes.CMD_PRINT_STATUS) to the printer.
        Adjusts the keep-alive interval based on error counts.
        This method runs asynchronously and will continue until stop_keep_alive is called
        or too many consecutive errors occur.
        """
        if self._keep_alive_task and not self._keep_alive_task.done():
            return  # Already running

        self._keep_alive_cancellation_token = False

        async def run_keep_alive():
            try:
                while not self._keep_alive_cancellation_token:
                    # logger.debug("KeepAlive")
                    result = await self.send_command_async(GCodes.CMD_PRINT_STATUS)
                    if result is None:
                        # Keep alive failed, connection error/timeout etc
                        self._keep_alive_errors += 1  # Keep track of errors
                        # logger.debug(f"Current keep alive failure: {self._keep_alive_errors}")
                        break

                    if self._keep_alive_errors > 0:
                        self._keep_alive_errors -= 1  # Move back to 0 errors with each "good" keep-alive

                    # Increase keep alive timeout based on error count
                    await asyncio.sleep(5.0 + self._keep_alive_errors * 1.0)

            except Exception as error:
                logger.error(f"KeepAlive encountered an exception: {error}")

        self._keep_alive_task = asyncio.create_task(run_keep_alive())

    async def stop_keep_alive(self, logout: bool = False) -> None:
        """
        Stop the keep-alive mechanism.
        
        Args:
            logout: If True, sends a logout command to the printer before stopping
        """
        if logout:
            try:
                await self.send_command_async(GCodes.CMD_LOGOUT)  # Release control
            except Exception:
                pass  # Ignore errors during logout

        self._keep_alive_cancellation_token = True

        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass

        logger.info("Keep-alive stopped.")

    async def is_socket_busy(self) -> bool:
        """
        Check if the socket is currently busy processing a command.
        
        Returns:
            True if the socket is busy, False otherwise
        """
        return self._socket_busy

    async def send_command_async(self, cmd: str) -> Optional[str]:
        """
        Send a command string to the printer asynchronously via the TCP socket.
        
        It ensures the socket is available, writes the command (appending a newline),
        and then waits to receive a multi-line reply.
        Handles socket busy state and various connection errors.
        
        Args:
            cmd: The command string to send (e.g., "~M115")
            
        Returns:
            The printer's string reply, or None if an error occurs,
            the reply is invalid, or the connection needs to be reset
        """
        async with self._socket_lock:
            self._socket_busy = True

            logger.debug(f"sendCommand: {cmd}")
            try:
                await self._check_socket()

                # Write command
                self._writer.write((cmd + '\n').encode('ascii'))
                await self._writer.drain()

                # Receive response
                reply = await self._receive_multi_line_replay_async(cmd)

                if reply is not None:
                    # logger.debug(f"Received reply for command: {reply}")
                    return reply
                else:
                    logger.warning("Invalid or no reply received, resetting connection to printer.")
                    await self._reset_socket()
                    await self._check_socket()
                    return None

            except Exception as error:
                logger.error(f"Error while sending command: {error}")
                return None
            finally:
                self._socket_busy = False

    async def _wait_until_socket_available(self) -> None:
        """
        Wait until the socket is no longer busy or a timeout is reached.
        
        This is used to serialize commands sent over the socket.
        
        Raises:
            TimeoutError: If the socket remains busy for too long (10 seconds)
        """
        max_wait_time = 10.0  # 10 seconds
        start_time = asyncio.get_event_loop().time()

        while self._socket_busy and (asyncio.get_event_loop().time() - start_time < max_wait_time):
            await asyncio.sleep(0.1)

        if self._socket_busy:
            raise TimeoutError("Socket remained busy for too long, timing out")

    async def _check_socket(self) -> None:
        """
        Check the status of the socket connection and attempt to reconnect if needed.
        
        If reconnection occurs, it also restarts the keep-alive mechanism.
        """
        logger.debug("CheckSocket()")
        fix = False

        if self._writer is None or self._reader is None:
            fix = True
            # logger.debug("TcpPrinterClient socket is null")
        elif self._writer.is_closing():
            fix = True
            # logger.debug("TcpPrinterClient socket is closed")

        if not fix:
            return

        logger.warning("Reconnecting to TCP socket...")
        await self._connect()
        await self.start_keep_alive()  # Start this here rather than in Connect()

    async def _connect(self) -> None:
        """
        Establish a TCP connection to the printer.
        
        Initializes the reader and writer streams and sets up error handling.
        """
        # logger.debug("Connect()")
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.hostname, self.port),
                timeout=self.timeout
            )
        except Exception as error:
            logger.error(f"Failed to connect to {self.hostname}:{self.port}: {error}")
            raise

    async def _reset_socket(self) -> None:
        """
        Reset the current socket connection.
        
        Stops the keep-alive mechanism and closes the connection.
        """
        # logger.debug("ResetSocket()")
        await self.stop_keep_alive()
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    async def _receive_multi_line_replay_async(self, cmd: str) -> Optional[str]:
        """
        Asynchronously receive a multi-line reply from the printer for a given command.
        
        It listens for data from the reader, concatenates incoming data,
        and determines when the full reply has been received based on command-specific delimiters
        (usually "ok" for text commands, or specific logic for binary data like thumbnails).
        Handles timeouts and errors during reception.
        
        Args:
            cmd: The command string for which the reply is expected. This influences how completion is detected.
            
        Returns:
            The complete string reply from the printer, or None if an error occurs,
            the reply is incomplete, or a timeout happens.
            For thumbnail commands (M662), the response is a binary string.
        """
        # logger.debug("ReceiveMultiLineReplayAsync()")

        if not self._reader:
            # logger.error("Reader is null, cannot receive reply.")
            return None

        answer = bytearray()

        # Set timeout based on command type
        timeout_duration = 5.0  # default timeout
        if cmd == GCodes.CMD_LIST_LOCAL_FILES or cmd.startswith(GCodes.CMD_GET_THUMBNAIL):
            timeout_duration = 10.0  # increase command timeout

        try:
            while True:
                # Read data with timeout
                try:
                    data = await asyncio.wait_for(self._reader.read(4096), timeout=1.0)
                except asyncio.TimeoutError:
                    # Check if we have a complete response so far
                    if self._is_response_complete(cmd, answer):
                        break
                    continue

                if not data:
                    logger.error("Connection closed by remote host")
                    return None

                answer.extend(data)

                # Check for completion
                if self._is_response_complete(cmd, answer):
                    # For file list command, wait a bit more for all data
                    if cmd == GCodes.CMD_LIST_LOCAL_FILES:
                        await asyncio.sleep(0.5)
                        # Try to read any remaining data
                        try:
                            additional_data = await asyncio.wait_for(self._reader.read(4096), timeout=0.1)
                            if additional_data:
                                answer.extend(additional_data)
                        except asyncio.TimeoutError:
                            pass
                    # For thumbnail requests, wait longer for binary data
                    elif cmd.startswith(GCodes.CMD_GET_THUMBNAIL):
                        await asyncio.sleep(1.5)
                        # Try to read any remaining binary data
                        try:
                            additional_data = await asyncio.wait_for(self._reader.read(8192), timeout=0.5)
                            if additional_data:
                                answer.extend(additional_data)
                        except asyncio.TimeoutError:
                            pass
                    break

        except Exception as e:
            logger.error(f"Error receiving multi-line command reply: {e}")
            return None

        # Convert response based on command type
        if cmd.startswith(GCodes.CMD_GET_THUMBNAIL):
            # For binary responses (M662), return as binary string
            result = answer.decode('latin1')  # Preserve binary data
            if not result:
                logger.error("Received empty thumbnail response.")
                return None
            return result
        else:
            # For text responses, convert to UTF-8
            try:
                result = answer.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to latin1 if UTF-8 fails
                result = answer.decode('latin1')

            if not result:
                logger.error("ReceiveMultiLineReplayAsync received an empty response.")
                return None
            return result

    def _is_response_complete(self, cmd: str, data: bytearray) -> bool:
        """
        Check if the response is complete based on the command type.
        
        Args:
            cmd: The command that was sent
            data: The data received so far
            
        Returns:
            True if the response appears complete, False otherwise
        """
        try:
            if cmd.startswith(GCodes.CMD_GET_THUMBNAIL):
                # For binary responses, check for "ok" in the header only
                header = data[:100].decode('ascii', errors='ignore')
                return "ok" in header
            else:
                # For text commands, check for "ok" in the full response
                text = data.decode('utf-8', errors='ignore')
                return "ok" in text
        except Exception:
            return False

    async def get_file_list_async(self) -> List[str]:
        """
        Retrieve a list of G-code files stored on the printer's local storage.
        
        Sends the CMD_LIST_LOCAL_FILES (M661) command and parses the response.
        
        Returns:
            An array of file names (strings, without '/data/' prefix).
            Returns an empty array if the command fails or no files are found.
        """
        response = await self.send_command_async(GCodes.CMD_LIST_LOCAL_FILES)
        if response:
            return self._parse_file_list_response(response)
        return []

    def _parse_file_list_response(self, response: str) -> List[str]:
        """
        Parse the raw string response from the M661 (list files) command.
        
        The response format typically includes segments separated by "::", with file paths
        prefixed by "/data/". This method extracts and cleans these file names.
        
        Args:
            response: The raw string response from the M661 command
            
        Returns:
            An array of file names, with the "/data/" prefix removed and any trailing invalid characters trimmed
        """
        segments = response.split('::')

        # Extract file paths
        file_paths = []
        for segment in segments:
            data_index = segment.find('/data/')
            if data_index != -1:
                full_path = segment[data_index:]
                if full_path.startswith('/data/'):
                    filename = full_path[6:]  # Remove '/data/' prefix

                    # Trim at the first invalid character (if any)
                    import re
                    match = re.search(r'[^\w\s\-\.\(\)\+%,@\[\]{}:;!#$^&*=<>?\/]', filename)
                    if match:
                        filename = filename[:match.start()]

                    # Only add non-empty filenames
                    if filename.strip():
                        file_paths.append(filename)

        return file_paths

    async def dispose(self) -> None:
        """
        Clean up resources by closing the socket connection.
        
        This should be called when the client is no longer needed.
        """
        try:
            logger.info("TcpPrinterClient closing socket")
            await self.stop_keep_alive(logout=True)  # Stop keep-alive timer and send logout command
            if self._writer:
                self._writer.close()
                try:
                    await self._writer.wait_closed()
                except Exception:
                    pass
            self._reader = None
            self._writer = None
        except Exception as error:
            logger.error(f"Error during dispose: {error}")
