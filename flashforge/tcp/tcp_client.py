"""
Low-level TCP client for communicating with FlashForge 3D printers.

This module provides the foundational TCP communication layer, managing socket connections,
sending raw commands, handling responses, maintaining keep-alive connections, and supporting
legacy raw-binary uploads used by Adventurer-class printers.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .gcode.gcodes import GCodes

logger = logging.getLogger(__name__)

# Regex for invalid characters in filenames
INVALID_FILENAME_CHARS_PATTERN = re.compile(r"[^\w\s\-\.\(\)\+%,@\[\]{}:;!#$^&*=<>?\/]")


@dataclass(slots=True)
class FlashForgeTcpClientOptions:
    """Optional transport overrides for the TCP client."""

    port: int | None = None


class FlashForgeTcpClient:
    """
    Foundational TCP client for communicating with FlashForge printers.

    This class manages the socket connection, serializes commands over a single stream,
    and handles protocol-specific response completion behavior such as the widened M661
    settle window and legacy M28/M29 upload semantics.
    """

    def __init__(self, hostname: str, options: FlashForgeTcpClientOptions | None = None) -> None:
        self.hostname = hostname
        self.port = options.port if options and options.port is not None else 8899
        self.timeout = 5.0

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._keep_alive_task: asyncio.Task[None] | None = None
        self._keep_alive_cancellation_token = False
        self._keep_alive_errors = 0
        self._socket_lock = asyncio.Lock()

        logger.info("TcpPrinterClient creation")
        logger.info("Initialized (connection will be established on first command)")

    async def start_keep_alive(self) -> None:
        """Start the TCP keep-alive loop."""
        if self._keep_alive_task and not self._keep_alive_task.done():
            return

        self._keep_alive_cancellation_token = False

        async def run_keep_alive() -> None:
            try:
                while not self._keep_alive_cancellation_token:
                    result = await self.send_command_async(GCodes.CMD_PRINT_STATUS)
                    if result is None:
                        self._keep_alive_errors += 1
                        break

                    if self._keep_alive_errors > 0:
                        self._keep_alive_errors -= 1

                    await asyncio.sleep(5.0 + self._keep_alive_errors * 1.0)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.error("KeepAlive encountered an exception: %s", error)

        self._keep_alive_task = asyncio.create_task(run_keep_alive())

    async def stop_keep_alive(self, logout: bool = False) -> None:
        """Stop the keep-alive loop, optionally logging out first."""
        if logout:
            try:
                await self.send_command_async(GCodes.CMD_LOGOUT)
            except Exception:
                pass

        self._keep_alive_cancellation_token = True

        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass

        self._keep_alive_task = None
        logger.info("Keep-alive stopped.")

    async def send_command_async(self, cmd: str) -> str | None:
        """
        Send a command string to the printer asynchronously via the TCP socket.

        Commands are serialized over a single socket lock so the reader can safely
        associate each response with the command that produced it.
        """
        async with self._socket_lock:
            logger.debug("sendCommand: %s", cmd)
            try:
                await self._check_socket()

                if self._writer is None:
                    logger.error("Writer is None after _check_socket, cannot send command")
                    return None

                self._writer.write((cmd + "\n").encode("ascii"))
                await self._writer.drain()

                if self.should_skip_response_wait(cmd):
                    return ""

                reply = await self._receive_multi_line_replay_async(cmd)
                if reply is not None:
                    return reply

                logger.warning("Invalid or no reply received, resetting connection to printer.")
                await self._reset_socket()
                await self._check_socket()
                return None

            except Exception as error:
                logger.error("Error while sending command: %s", error)
                return None

    async def upload_file(self, local_file_path: str, remote_file_name: str | None = None) -> bool:
        """
        Upload a file to legacy printer storage using the M28/raw-binary/M29 flow.
        """
        file_path = Path(local_file_path)
        if not file_path.exists() or not file_path.is_file():
            logger.error("Upload failed: %s is not a file.", local_file_path)
            return False

        normalized_file_name = self._normalize_legacy_upload_filename(
            remote_file_name or local_file_path
        )
        if not normalized_file_name:
            logger.error("Upload failed: remote file name resolved to an empty value.")
            return False

        start_command = (
            GCodes.CMD_PREP_FILE_UPLOAD.replace("%%size%%", str(file_path.stat().st_size))
            .replace("%%filename%%", normalized_file_name)
        )

        async with self._socket_lock:
            try:
                await self._check_socket()
                if self._writer is None:
                    logger.error("Upload failed: writer is unavailable.")
                    return False

                self._writer.write((start_command + "\n").encode("ascii"))
                await self._writer.drain()

                start_response = await self._receive_multi_line_replay_async(start_command)
                if not start_response or not self._is_successful_upload_boundary_response(
                    start_command, start_response
                ):
                    logger.error("Upload failed: printer rejected M28 upload initialization.")
                    return False

                with file_path.open("rb") as upload_stream:
                    while chunk := upload_stream.read(64 * 1024):
                        self._writer.write(chunk)
                        await self._writer.drain()

                self._writer.write((GCodes.CMD_COMPLETE_FILE_UPLOAD + "\n").encode("ascii"))
                await self._writer.drain()

                finish_response = await self._receive_multi_line_replay_async(
                    GCodes.CMD_COMPLETE_FILE_UPLOAD
                )
                if not finish_response:
                    logger.error("Upload failed: printer did not respond to M29 upload finalization.")
                    return False

                return self._is_successful_upload_boundary_response(
                    GCodes.CMD_COMPLETE_FILE_UPLOAD, finish_response
                )
            except Exception as error:
                logger.error("Upload failed for %s: %s", normalized_file_name, error)
                await self._reset_socket()
                return False

    async def _check_socket(self) -> None:
        """Reconnect the TCP socket if it is not ready."""
        fix = False

        if self._writer is None or self._reader is None:
            fix = True
        elif self._writer.is_closing():
            fix = True

        if not fix:
            return

        logger.warning("Reconnecting to TCP socket...")
        await self._connect()
        await self.start_keep_alive()

    async def _connect(self) -> None:
        """Establish a TCP connection to the printer."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.hostname, self.port),
                timeout=self.timeout,
            )
        except Exception as error:
            logger.error("Failed to connect to %s:%s: %s", self.hostname, self.port, error)
            raise

    async def _reset_socket(self) -> None:
        """Reset the current socket connection."""
        await self.stop_keep_alive()
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    async def _receive_multi_line_replay_async(self, cmd: str) -> str | None:
        """Receive a complete multi-line reply for the given command."""
        if not self._reader:
            return None

        answer = bytearray()
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        last_data_time: float | None = None
        completion_seen = False
        is_binary = self.is_binary_command(cmd)
        timeout_seconds = self.get_command_timeout_ms(cmd) / 1000.0
        settle_delay_seconds = self.get_response_completion_delay_ms(cmd, is_binary) / 1000.0
        inactivity_delay_seconds = self.get_inactivity_completion_delay_ms(cmd) / 1000.0

        while True:
            elapsed = loop.time() - start_time
            remaining_timeout = timeout_seconds - elapsed
            if remaining_timeout <= 0:
                logger.error(
                    "ReceiveMultiLineReplayAsync timed out after %sms",
                    self.get_command_timeout_ms(cmd),
                )
                return None

            read_timeout = min(0.1, remaining_timeout) if answer else min(1.0, remaining_timeout)

            try:
                data = await asyncio.wait_for(self._reader.read(8192), timeout=read_timeout)
            except TimeoutError:
                now = loop.time()
                if completion_seen and (
                    settle_delay_seconds == 0
                    or (last_data_time is not None and now - last_data_time >= settle_delay_seconds)
                ):
                    break

                if (
                    answer
                    and self.should_use_inactivity_completion(cmd)
                    and last_data_time is not None
                    and now - last_data_time >= inactivity_delay_seconds
                ):
                    break
                continue

            if not data:
                logger.error("Connection closed by remote host")
                return None

            answer.extend(data)
            last_data_time = loop.time()

            if is_binary:
                if self.is_binary_response_complete(cmd, answer):
                    if settle_delay_seconds == 0:
                        break
                    completion_seen = True
                continue

            text_so_far = answer.decode("utf-8", errors="ignore")
            if self.is_text_response_complete(cmd, text_so_far):
                if settle_delay_seconds == 0:
                    break
                completion_seen = True

        if is_binary:
            result = answer.decode("latin1")
            if not result:
                logger.error("Received empty binary response.")
                return None
            return result

        try:
            result = self.normalize_text_response(cmd, answer.decode("utf-8"))
        except UnicodeDecodeError:
            result = self.normalize_text_response(cmd, answer.decode("latin1"))

        if not result:
            logger.error("ReceiveMultiLineReplayAsync received an empty response.")
            return None
        return result

    def should_skip_response_wait(self, _cmd: str) -> bool:
        """Determine whether a command should return as soon as it is written."""
        return False

    def is_binary_command(self, cmd: str) -> bool:
        """Determine whether a command returns binary payload data."""
        return cmd.startswith(GCodes.CMD_GET_THUMBNAIL)

    def is_text_response_complete(self, _cmd: str, response: str) -> bool:
        """Determine when a text response is complete."""
        return "ok" in response

    def should_use_inactivity_completion(self, cmd: str) -> bool:
        """Determine whether a command should complete after a quiet period."""
        return self._is_legacy_upload_boundary_command(cmd)

    def get_inactivity_completion_delay_ms(self, cmd: str) -> int:
        """Delay used for inactivity-based completion."""
        if self._is_legacy_upload_boundary_command(cmd):
            return 250
        return 200

    def get_response_completion_delay_ms(self, cmd: str, binary: bool) -> int:
        """Delay added after the completion marker is seen to allow trailing data to arrive."""
        if binary:
            return 1500
        if cmd == GCodes.CMD_LIST_LOCAL_FILES:
            return 1200
        return 0

    def is_binary_response_complete(self, _cmd: str, response: bytearray) -> bool:
        """Determine whether a binary response buffer is complete."""
        try:
            header = bytes(response[:100]).decode("ascii", errors="ignore")
            return "ok" in header
        except Exception:
            return False

    def normalize_text_response(self, _cmd: str, response: str) -> str:
        """Normalize text responses before returning them to callers."""
        return response

    def get_command_timeout_ms(self, cmd: str) -> int:
        """Return the socket timeout to use for a given command."""
        if cmd == GCodes.CMD_LIST_LOCAL_FILES or self.is_binary_command(cmd):
            return 10000
        if self._is_legacy_upload_boundary_command(cmd):
            return 10000
        if cmd == GCodes.CMD_HOME_AXES or cmd == "~G28":
            return 15000
        return 5000

    async def get_file_list_async(self) -> list[str]:
        """Retrieve a list of G-code files stored on the printer."""
        response = await self.send_command_async(GCodes.CMD_LIST_LOCAL_FILES)
        if response:
            return self._parse_file_list_response(response)
        return []

    def _parse_file_list_response(self, response: str) -> list[str]:
        """Parse the raw string response from the M661 list-files command."""
        segments = response.split("::")
        file_paths: list[str] = []

        for segment in segments:
            data_index = segment.find("/data/")
            if data_index == -1:
                continue

            full_path = segment[data_index:]
            if not full_path.startswith("/data/"):
                continue

            filename = full_path[6:]
            match = INVALID_FILENAME_CHARS_PATTERN.search(filename)
            if match:
                filename = filename[: match.start()]

            if filename.strip():
                file_paths.append(filename)

        return file_paths

    async def dispose(self) -> None:
        """Clean up resources by closing the socket connection."""
        try:
            logger.info("TcpPrinterClient closing socket")
            await self.stop_keep_alive(logout=True)
            if self._writer:
                self._writer.close()
                try:
                    await self._writer.wait_closed()
                except Exception:
                    pass
            self._reader = None
            self._writer = None
        except Exception as error:
            logger.error("Error during dispose: %s", error)

    def _normalize_legacy_upload_filename(self, file_name: str) -> str:
        normalized_path = file_name.replace("\\", "/")
        without_legacy_prefix = re.sub(r"^0:/user/", "", normalized_path, flags=re.IGNORECASE)
        without_legacy_prefix = re.sub(
            r"^/data/",
            "",
            without_legacy_prefix,
            flags=re.IGNORECASE,
        )
        return PurePosixPath(without_legacy_prefix).name

    def _is_legacy_upload_boundary_command(self, cmd: str) -> bool:
        return bool(re.match(r"^~?M(28|29)\b", cmd.strip(), flags=re.IGNORECASE))

    def _is_successful_upload_boundary_response(self, cmd: str, response: str) -> bool:
        normalized = response.replace("\r\n", "\n").strip()
        if not normalized:
            return False

        if re.search(
            r"error:|control failed\.|file is not available|cannot create file|not enough space",
            normalized,
            flags=re.IGNORECASE,
        ):
            return False

        bare_command = cmd.strip().removeprefix("~").split(maxsplit=1)[0]
        return (
            "ok" in normalized
            or "Received." in normalized
            or re.search(rf"\b{re.escape(bare_command)}\b", normalized, flags=re.IGNORECASE)
            is not None
        )
