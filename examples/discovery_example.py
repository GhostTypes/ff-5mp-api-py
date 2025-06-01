"""
FlashForge Python API - Printer Discovery Example

This example demonstrates how to discover FlashForge printers on the local network
using UDP broadcast messages.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path for development
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery


async def discover_and_connect_example():
    """Discovers printers and connects to the first one found."""

    print("=== FlashForge Printer Discovery Example ===\n")

    # Create discovery instance
    discovery = FlashForgePrinterDiscovery()

    print("[*] Searching for FlashForge printers on the network...")
    print("This may take up to 10 seconds...\n")

    try:
        # Discover printers with custom timeouts
        printers = await discovery.discover_printers_async(
            timeout_ms=8000,      # Total discovery time
            idle_timeout_ms=2000, # Time to wait after last response
            max_retries=2         # Number of retry attempts
        )

        if not printers:
            print("[ERROR] No FlashForge printers found on the network")
            print("\nTroubleshooting tips:")
            print("• Make sure your printer is powered on and connected to the network")
            print("• Check that your computer and printer are on the same network")
            print("• Verify that UDP traffic is not blocked by firewall")
            print("• Try running as administrator/root if needed")
            return

        print(f"[SUCCESS] Found {len(printers)} FlashForge printer(s):\n")

        # Display discovered printers
        for i, printer in enumerate(printers, 1):
            print(f"{i}. {printer}")

        print()

        # Try to connect to the first printer
        first_printer = printers[0]
        print(f"[*] Attempting to connect to '{first_printer.name}' at {first_printer.ip_address}...")

        # Note: You'll need to provide the actual serial number and check code
        # These are typically found on a label on your printer or in FlashPrint
        SERIAL_NUMBER = first_printer.serial_number or "your_serial_number"
        CHECK_CODE = "your_check_code"  # You need to replace this with actual check code

        if SERIAL_NUMBER == "your_serial_number" or CHECK_CODE == "your_check_code":
            print("[WARNING] Cannot connect - please update SERIAL_NUMBER and CHECK_CODE in the script")
            print("   These values are required for authentication with the printer")
            print("   You can find them on your printer's label or in FlashPrint software")
            return

        # Create client and connect
        async with FlashForgeClient(first_printer.ip_address, SERIAL_NUMBER, CHECK_CODE) as client:
            if await client.initialize():
                print(f"[SUCCESS] Successfully connected to {client.printer_name}")
                print(f"   Firmware: {client.firmware_version}")
                print(f"   Model: {'Pro' if client.is_pro else 'Standard'}")

                # Get basic status
                status = await client.get_printer_status()
                if status:
                    print(f"   Status: {status.machine_state}")
            else:
                print("[ERROR] Failed to connect to printer (check serial number and check code)")

    except Exception as e:
        print(f"[ERROR] Error during discovery: {e}")


async def discovery_only_example():
    """Simple discovery-only example."""

    print("=== Simple Discovery Example ===\n")

    discovery = FlashForgePrinterDiscovery()

    print("[*] Discovering printers...")
    printers = await discovery.discover_printers_async()

    if printers:
        print(f"[SUCCESS] Found {len(printers)} printer(s):")
        for printer in printers:
            print(f"  • {printer.name} ({printer.ip_address}) - S/N: {printer.serial_number}")
    else:
        print("[ERROR] No printers found")


async def advanced_discovery_example():
    """Advanced discovery example with custom settings and debug info."""

    print("=== Advanced Discovery Example ===\n")

    discovery = FlashForgePrinterDiscovery()

    print("[*] Running advanced discovery with custom settings...")
    print("   • Total timeout: 15 seconds")
    print("   • Idle timeout: 3 seconds")
    print("   • Max retries: 5")
    print()

    printers = await discovery.discover_printers_async(
        timeout_ms=15000,     # Longer total timeout
        idle_timeout_ms=3000, # Longer idle timeout
        max_retries=5         # More retries
    )

    if printers:
        print(f"[SUCCESS] Discovery completed! Found {len(printers)} printer(s):\n")

        for i, printer in enumerate(printers, 1):
            print(f"Printer {i}:")
            print(f"  Name: {printer.name}")
            print(f"  IP Address: {printer.ip_address}")
            print(f"  Serial Number: {printer.serial_number}")
            print()
    else:
        print("[ERROR] No printers discovered")


async def main():
    """Main function to run examples."""
    import argparse

    parser = argparse.ArgumentParser(description="FlashForge Printer Discovery Examples")
    parser.add_argument(
        "--example",
        choices=["discover-connect", "discovery-only", "advanced"],
        default="discover-connect",
        help="Which example to run"
    )

    args = parser.parse_args()

    if args.example == "discover-connect":
        await discover_and_connect_example()
    elif args.example == "discovery-only":
        await discovery_only_example()
    elif args.example == "advanced":
        await advanced_discovery_example()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[WARNING] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
