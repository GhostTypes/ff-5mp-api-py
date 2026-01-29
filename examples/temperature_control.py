"""
FlashForge Python API - Temperature Control Example

Demonstrates temperature management for extruder and print bed.
"""

import asyncio

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery


async def main():
    """Temperature control operations."""

    # Discover and connect
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()

    if not printers:
        print("No printers found")
        return

    printer = printers[0]

    async with FlashForgeClient(
        printer.ip_address, printer.serial_number, printer.check_code
    ) as client:
        if not await client.initialize():
            print("Failed to connect")
            return

        await client.init_control()

        print(f"Connected to {client.printer_name}\n")

        # Get current temperatures
        print("Current temperatures:")
        temps = await client.get_temperatures()
        if temps:
            extruder = temps.get_extruder_temp()
            bed = temps.get_bed_temp()
            if extruder:
                print(f"  Extruder: {extruder.current}°C / {extruder.set}°C")
            if bed:
                print(f"  Bed: {bed.current}°C / {bed.set}°C")

        # Set temperatures
        print("\nSetting temperatures...")
        await client.temp_control.set_extruder_temp(200)
        await client.temp_control.set_bed_temp(60)
        print("  Extruder target: 200°C")
        print("  Bed target: 60°C")

        # Wait for heating (optional)
        print("\nWaiting for extruder to heat...")
        await client.temp_control.set_extruder_temp(200, wait_for=True)
        print("  Extruder reached target temperature")

        # Monitor temperatures
        print("\nMonitoring temperatures for 10 seconds...")
        for i in range(10):
            temps = await client.get_temperatures()
            if temps:
                extruder = temps.get_extruder_temp()
                bed = temps.get_bed_temp()
                if extruder and bed:
                    print(f"  [{i + 1}/10] Extruder: {extruder.current}°C, Bed: {bed.current}°C")
            await asyncio.sleep(1)

        # Cancel heating
        print("\nCanceling heating...")
        await client.temp_control.cancel_extruder_temp()
        await client.temp_control.cancel_bed_temp()
        print("  Heating cancelled")

        # Wait for cooling
        print("\nWaiting for parts to cool to 50°C...")
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
