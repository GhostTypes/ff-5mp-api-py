"""
FlashForge Python API - Discovery Example

Demonstrates various ways to discover and connect to FlashForge printers.
"""

import asyncio

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery


async def basic_discovery():
    """Simple printer discovery."""
    print("=== Basic Discovery ===\n")

    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()

    if printers:
        print(f"Found {len(printers)} printer(s):")
        for printer in printers:
            print(f"  {printer.name} at {printer.ip_address}")
    else:
        print("No printers found")


async def discovery_with_custom_timeouts():
    """Discovery with custom timeout settings."""
    print("\n=== Discovery with Custom Timeouts ===\n")

    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async(
        timeout_ms=5000,  # Total timeout: 5 seconds
        idle_timeout_ms=1500,  # Idle timeout: 1.5 seconds
        max_retries=2,  # Retry twice
    )

    if printers:
        print(f"Found {len(printers)} printer(s)")
        for i, printer in enumerate(printers, 1):
            print(f"\nPrinter {i}:")
            print(f"  Name: {printer.name}")
            print(f"  IP: {printer.ip_address}")
            print(f"  Serial: {printer.serial_number}")
    else:
        print("No printers found")


async def manual_connection():
    """Connect without discovery using known IP address."""
    print("\n=== Manual Connection ===\n")

    # Use known printer details
    ip_address = "192.168.1.100"
    serial_number = "SN123456"
    check_code = ""

    print(f"Connecting to {ip_address}...")

    async with FlashForgeClient(ip_address, serial_number, check_code) as client:
        if await client.initialize():
            print(f"Connected to {client.printer_name}")
            print(f"Firmware: {client.firmware_version}")
        else:
            print("Connection failed")


async def discovery_with_error_handling():
    """Discovery with comprehensive error handling."""
    print("\n=== Discovery with Error Handling ===\n")

    try:
        discovery = FlashForgePrinterDiscovery()
        printers = await discovery.discover_printers_async()

        if not printers:
            print("No printers found")
            print("\nTroubleshooting:")
            print("  - Ensure printer is powered on")
            print("  - Check network connection")
            print("  - Verify firewall settings")
            return

        # Try to connect to first printer
        printer = printers[0]
        print(f"Connecting to {printer.name}...")

        async with FlashForgeClient(
            printer.ip_address, printer.serial_number, printer.check_code
        ) as client:
            if await client.initialize():
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
    await discovery_with_custom_timeouts()
    await manual_connection()
    await discovery_with_error_handling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
