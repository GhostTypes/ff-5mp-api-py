"""
FlashForge Python API - Basic Connection Example

Demonstrates the simplest way to connect to a FlashForge printer
and retrieve basic status information.
"""

import asyncio

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery


async def main():
    """Connect to printer and get basic status."""

    # Discover printers on network
    print("Discovering printers...")
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()

    if not printers:
        print("No printers found")
        return

    # Use first discovered printer
    printer = printers[0]
    print(f"Found: {printer.name} at {printer.ip_address}\n")

    # Connect to printer
    async with FlashForgeClient(
        printer.ip_address, printer.serial_number, printer.check_code
    ) as client:
        # Initialize connection
        if not await client.initialize():
            print("Failed to connect")
            return

        print(f"Connected to {client.printer_name}")
        print(f"Firmware: {client.firmware_version}\n")

        # Get printer status
        status = await client.get_printer_status()
        if status:
            print(f"State: {status.machine_state.value}")
            print(f"Extruder: {status.extruder.current}°C / {status.extruder.set}°C")
            print(f"Bed: {status.print_bed.current}°C / {status.print_bed.set}°C")

            if status.print_file_name:
                print(f"\nCurrent file: {status.print_file_name}")
                print(f"Progress: {status.print_progress}%")
                print(f"Layer: {status.current_print_layer}/{status.total_print_layers}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
