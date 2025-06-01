"""
FlashForge Python API - Unified Client Example

This example demonstrates how to use the main FlashForgeClient class to control
a FlashForge 3D printer using both HTTP and TCP communication layers.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path for development
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flashforge import FlashForgeClient, MachineState


async def comprehensive_example():
    """Comprehensive example showing FlashForgeClient capabilities."""

    # Printer connection details (update these for your printer)
    IP_ADDRESS = "192.168.0.177"  # Replace with your printer's IP
    SERIAL_NUMBER = "SNMOMC9900728"  # Replace with actual serial number
    CHECK_CODE = "e5c2bf77"  # Replace with actual check code

    print("=== FlashForge Python API - Unified Client Demo ===\n")

    # Create and initialize the client
    async with FlashForgeClient(IP_ADDRESS, SERIAL_NUMBER, CHECK_CODE) as client:
        print(f"Connecting to printer at {IP_ADDRESS}...")

        # Initialize connection
        if not await client.initialize():
            print("Failed to connect to printer!")
            return

        print(f"Connected to {client.printer_name}")
        print(f"   Model: {'Pro' if client.is_pro else 'Standard'}")
        print(f"   Firmware: {client.firmware_version}")
        print(f"   MAC Address: {client.mac_address}")
        print(f"   Lifetime Print Time: {client.lifetime_print_time}")
        print(f"   Lifetime Filament: {client.lifetime_filament_meters}")
        print()

        # Initialize control interface
        print("Initializing control interface...")
        if await client.init_control():
            print("Control interface initialized")
            print(f"   LED Control Available: {client.led_control}")
            print(f"   Filtration Control Available: {client.filtration_control}")
        else:
            print("Failed to initialize control interface")
        print()

        # Get current printer status
        print("Getting printer status...")
        status = await client.get_printer_status()
        if status:
            print(f"Printer Status: {status.machine_state}")
            print(f"   Current Layer: {status.current_print_layer}")
            print(f"   Total Layers: {status.total_print_layers}")
            print(f"   Print Progress: {status.print_progress * 100:.1f}%")
        else:
            print("Failed to get printer status")
        print()

        # Get temperature information
        print("Getting temperature readings...")
        try:
            temps = await client.get_temperatures()
            if temps:
                print("Temperature Info:")
                extruder = temps.get_extruder_temp()
                bed = temps.get_bed_temp()
                if extruder:
                    print(f"   Extruder: {extruder.get_current()}°C (Target: {extruder.get_set()}°C)")
                if bed:
                    print(f"   Bed: {bed.get_current()}°C (Target: {bed.get_set()}°C)")
            else:
                print("Failed to get temperature information")
        except Exception as e:
            print(f"Error getting temperatures: {e}")
        print()

        # File operations
        print("Getting file list...")
        try:
            files = await client.files.get_file_list()
            if files:
                print(f"Found {len(files)} files on printer:")
                for i, file_info in enumerate(files):  # Show first 5 files
                    print(f"   {i + 1}. {file_info}")
            else:
                print("No files found on printer")
        except Exception as e:
            print(f"Error getting file list: {e}")
        print()

        # TCP client operations
        print("Demonstrating TCP client operations...")
        try:
            # Get detailed printer info via TCP
            printer_info = await client.tcp_client.get_printer_info()
            if printer_info:
                print("TCP Printer Info:")
                print(f"   Type: {printer_info.type_name}")
                print(f"   Firmware: {printer_info.firmware_version}")
                print(f"   Machine Name: {printer_info.name}")
                print(f"   Print Dimensions: {printer_info.dimensions}")

            # Get current position
            location = await client.tcp_client.get_location_info()
            if location:
                print("Current Position:")
                print(f"   X: {location.x}mm")
                print(f"   Y: {location.y}mm")
                print(f"   Z: {location.z}mm")

        except Exception as e:
            print(f"Error in TCP operations: {e}")
        print()

        print("Demo completed successfully!")
        print(f"   Client info: {client}")


async def simple_example():
    """Simple example for quick testing."""

    # Replace with your printer details
    IP_ADDRESS = "192.168.0.202"
    SERIAL_NUMBER = "SNMOMC9900728"
    CHECK_CODE = "e5c2bf77"

    print("=== Simple FlashForge Client Example ===\n")

    client = FlashForgeClient(IP_ADDRESS, SERIAL_NUMBER, CHECK_CODE)

    try:
        if await client.initialize():
            print(f"Connected to {client.printer_name}")

            # Get basic status
            status = await client.get_printer_status()
            if status:
                print(f"Status: {status.machine_state}")
                print(f"Progress: {status.print_progress * 100:.1f}%")

            # Get temperatures
            temps = await client.get_temperatures()
            if temps:
                extruder = temps.get_extruder_temp()
                bed = temps.get_bed_temp()
                if extruder:
                    print(f"Extruder: {extruder.get_current()}°C")
                if bed:
                    print(f"Bed: {bed.get_current()}°C")
        else:
            print("Failed to connect")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        await client.dispose()


async def main():
    """Main function to run examples."""
    import argparse

    parser = argparse.ArgumentParser(description="FlashForge Python API Examples")
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Run simple example instead of comprehensive demo"
    )

    args = parser.parse_args()

    if args.simple:
        await simple_example()
    else:
        await comprehensive_example()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
