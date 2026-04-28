"""
FlashForge Python API - Temperature Control Example

Demonstrates temperature management for extruder and print bed.
"""

import asyncio
import os

from flashforge import FlashForgeClient, FiveMClientConnectionOptions, PrinterDiscovery


def _build_connection_options(printer) -> FiveMClientConnectionOptions:
    return FiveMClientConnectionOptions(
        http_port=printer.event_port,
        tcp_port=printer.command_port,
    )


async def main():
    """Temperature control operations."""
    check_code = os.getenv("FLASHFORGE_CHECK_CODE", "").strip()
    if not check_code:
        print("Set FLASHFORGE_CHECK_CODE before running this example")
        return

    discovery = PrinterDiscovery()
    printers = await discovery.discover()

    if not printers:
        print("No printers found")
        return

    printer = printers[0]
    if not printer.serial_number:
        print("Discovered printer did not report a serial number")
        return

    async with FlashForgeClient(
        printer.ip_address,
        printer.serial_number,
        check_code,
        options=_build_connection_options(printer),
    ) as client:
        status = await client.get_printer_status()
        if not status:
            print("Failed to connect")
            return

        if not await client.init_control():
            print("Failed to initialize control")
            return

        print(f"Connected to {client.printer_name}\n")

        print("Current temperatures:")
        temps = await client.get_temperatures()
        if temps:
            extruder = temps.get_extruder_temp()
            bed = temps.get_bed_temp()
            if extruder:
                print(f"  Extruder: {extruder.current}C / {extruder.set}C")
            if bed:
                print(f"  Bed: {bed.current}C / {bed.set}C")

        print("\nSetting temperatures...")
        await client.temp_control.set_extruder_temp(200)
        await client.temp_control.set_bed_temp(60)
        print("  Extruder target: 200C")
        print("  Bed target: 60C")

        print("\nWaiting for extruder to heat...")
        await client.temp_control.set_extruder_temp(200, wait_for=True)
        print("  Extruder reached target temperature")

        print("\nMonitoring temperatures for 10 seconds...")
        for i in range(10):
            temps = await client.get_temperatures()
            if temps:
                extruder = temps.get_extruder_temp()
                bed = temps.get_bed_temp()
                if extruder and bed:
                    print(f"  [{i + 1}/10] Extruder: {extruder.current}C, Bed: {bed.current}C")
            await asyncio.sleep(1)

        print("\nCanceling heating...")
        await client.temp_control.cancel_extruder_temp()
        await client.temp_control.cancel_bed_temp()
        print("  Heating cancelled")

        print("\nWaiting for parts to cool to 50C...")
        if await client.temp_control.wait_for_part_cool(target_temp=50.0, timeout_seconds=300):
            print("  Parts cooled to safe temperature")
        else:
            print("  Cooling timeout or error")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
