"""
FlashForge Python API - Discovery Example

Demonstrates various ways to discover and connect to FlashForge printers.
"""

import asyncio
import os

from flashforge import (
    DiscoveryOptions,
    FlashForgeClient,
    FiveMClientConnectionOptions,
    PrinterDiscovery,
)


def _get_check_code() -> str | None:
    check_code = os.getenv("FLASHFORGE_CHECK_CODE", "").strip()
    return check_code or None


def _build_connection_options(printer) -> FiveMClientConnectionOptions:
    return FiveMClientConnectionOptions(
        http_port=printer.event_port,
        tcp_port=printer.command_port,
    )


async def basic_discovery():
    """Simple printer discovery."""
    print("=== Basic Discovery ===\n")

    discovery = PrinterDiscovery()
    printers = await discovery.discover()

    if printers:
        print(f"Found {len(printers)} printer(s):")
        for printer in printers:
            print(
                f"  {printer.name} at {printer.ip_address} "
                f"(model={printer.model.value}, tcp={printer.command_port}, http={printer.event_port})"
            )
    else:
        print("No printers found")


async def discovery_with_custom_timeouts():
    """Discovery with custom timeout settings."""
    print("\n=== Discovery with Custom Timeouts ===\n")

    discovery = PrinterDiscovery()
    printers = await discovery.discover(
        DiscoveryOptions(
            timeout=5000,
            idle_timeout=1500,
            max_retries=2,
        )
    )

    if printers:
        print(f"Found {len(printers)} printer(s)")
        for i, printer in enumerate(printers, 1):
            print(f"\nPrinter {i}:")
            print(f"  Name: {printer.name}")
            print(f"  IP: {printer.ip_address}")
            print(f"  Serial: {printer.serial_number}")
            print(f"  TCP Port: {printer.command_port}")
            print(f"  HTTP Port: {printer.event_port}")
    else:
        print("No printers found")


async def manual_connection():
    """Connect without discovery using known printer details."""
    print("\n=== Manual Connection ===\n")

    check_code = _get_check_code()
    if not check_code:
        print("Set FLASHFORGE_CHECK_CODE before running this example")
        return

    ip_address = "192.168.1.100"
    serial_number = "SN123456"

    print(f"Connecting to {ip_address}...")

    async with FlashForgeClient(ip_address, serial_number, check_code) as client:
        status = await client.get_printer_status()
        if status:
            print(f"Connected to {client.printer_name}")
            print(f"Firmware: {client.firmware_version}")
        else:
            print("Connection failed")


async def discovery_with_error_handling():
    """Discovery with comprehensive error handling."""
    print("\n=== Discovery with Error Handling ===\n")

    check_code = _get_check_code()
    if not check_code:
        print("Set FLASHFORGE_CHECK_CODE before running this example")
        return

    try:
        discovery = PrinterDiscovery()
        printers = await discovery.discover()

        if not printers:
            print("No printers found")
            print("\nTroubleshooting:")
            print("  - Ensure printer is powered on")
            print("  - Check network connection")
            print("  - Verify firewall settings")
            return

        printer = printers[0]
        if not printer.serial_number:
            print("Discovered printer did not report a serial number")
            return

        print(f"Connecting to {printer.name}...")

        async with FlashForgeClient(
            printer.ip_address,
            printer.serial_number,
            check_code,
            options=_build_connection_options(printer),
        ) as client:
            status = await client.get_printer_status()
            if status:
                print(f"Status: {status.machine_state.value}")
            else:
                print("Failed to initialize connection")

    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all discovery examples."""
    await basic_discovery()
    #await discovery_with_custom_timeouts()
    #await manual_connection()
    #await discovery_with_error_handling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
