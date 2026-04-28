"""
FlashForge Python API - Basic Connection Example

Demonstrates the simplest way to connect to a FlashForge printer
and retrieve basic status information.
"""

import asyncio
import os

from flashforge import FlashForgeClient, FiveMClientConnectionOptions, PrinterDiscovery


async def main():
    """Connect to printer and get basic status."""
    check_code = os.getenv("FLASHFORGE_CHECK_CODE", "").strip()
    if not check_code:
        print("Set FLASHFORGE_CHECK_CODE before running this example")
        return

    print("Discovering printers...")
    discovery = PrinterDiscovery()
    printers = await discovery.discover()

    if not printers:
        print("No printers found")
        return

    printer = printers[0]
    if not printer.serial_number:
        print("Discovered printer did not report a serial number")
        return

    options = FiveMClientConnectionOptions(
        http_port=printer.event_port,
        tcp_port=printer.command_port,
    )

    print(f"Found: {printer.name} at {printer.ip_address}\n")

    async with FlashForgeClient(
        printer.ip_address,
        printer.serial_number,
        check_code,
        options=options,
    ) as client:
        status = await client.get_printer_status()
        if not status:
            print("Failed to connect")
            return

        print(f"Connected to {client.printer_name}")
        print(f"Firmware: {client.firmware_version}\n")

        print(f"State: {status.machine_state.value}")
        print(f"Extruder: {status.extruder.current}C / {status.extruder.set}C")
        print(f"Bed: {status.print_bed.current}C / {status.print_bed.set}C")

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
