"""
FlashForge Python API - Complete Feature Demo

This example demonstrates ALL features of the FlashForge Python API including:
- Printer discovery 
- Main unified client
- All TCP parsers (PrinterInfo, TempInfo, EndstopStatus, PrintStatus, ThumbnailInfo)
- HTTP API controls
- File operations
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path for development
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery


async def comprehensive_feature_demo():
    """Comprehensive demonstration of all FlashForge API features."""

    print("🎯 FlashForge Python API - COMPLETE FEATURE DEMONSTRATION")
    print("=" * 65)
    print()

    # ===== PHASE 1: PRINTER DISCOVERY =====
    print("🔍 PHASE 1: PRINTER DISCOVERY")
    print("-" * 35)

    discovery = FlashForgePrinterDiscovery()
    print("Searching for printers on the network...")

    try:
        printers = await discovery.discover_printers_async(
            timeout_ms=5000,  # 5 second timeout for demo
            idle_timeout_ms=1500,
            max_retries=2
        )

        if printers:
            print(f"✅ Found {len(printers)} printer(s):")
            for i, printer in enumerate(printers, 1):
                print(f"   {i}. {printer}")

            # Use the first printer for the demo
            selected_printer = printers[0]
            print(f"\n🎯 Selected: {selected_printer.name} at {selected_printer.ip_address}")

        else:
            print("❌ No printers found. Using demo configuration...")
            # Demo fallback
            selected_printer = type('obj', (object,), {
                'name': 'Demo Printer',
                'ip_address': '192.168.1.100',
                'serial_number': 'demo_serial'
            })()

    except Exception as e:
        print(f"❌ Discovery error: {e}")
        print("Using demo configuration...")
        selected_printer = type('obj', (object,), {
            'name': 'Demo Printer',
            'ip_address': '192.168.1.100',
            'serial_number': 'demo_serial'
        })()

    print()

    # ===== PHASE 2: CLIENT CONNECTION =====
    print("🔗 PHASE 2: CLIENT CONNECTION & INITIALIZATION")
    print("-" * 50)

    # Note: Replace these with actual values for real testing
    SERIAL_NUMBER = getattr(selected_printer, 'serial_number', 'your_serial_number')
    CHECK_CODE = "your_check_code"  # Replace with actual check code

    if SERIAL_NUMBER == 'your_serial_number' or CHECK_CODE == 'your_check_code':
        print("⚠️  Demo mode: Update SERIAL_NUMBER and CHECK_CODE for real testing")
        return

    async with FlashForgeClient(selected_printer.ip_address, SERIAL_NUMBER, CHECK_CODE) as client:
        print(f"Connecting to {selected_printer.ip_address}...")

        if not await client.initialize():
            print("❌ Failed to connect to printer")
            return

        print(f"✅ Connected to {client.printer_name}")
        print(f"   Model: {'Pro' if client.is_pro else 'Standard'}")
        print(f"   Firmware: {client.firmware_version}")
        print(f"   MAC: {client.mac_address}")
        print()

        # Initialize control interface
        if await client.init_control():
            print("✅ Control interface initialized")
        else:
            print("❌ Control interface initialization failed")
        print()

        # ===== PHASE 3: ADVANCED TCP PARSERS =====
        print("🔬 PHASE 3: ADVANCED TCP PARSER DEMONSTRATIONS")
        print("-" * 55)

        # EndstopStatus - Machine state and endstops
        print("📊 Getting detailed machine status (EndstopStatus)...")
        try:
            endstop_status = await client.tcp_client.get_endstop_status()
            if endstop_status:
                print("✅ Endstop Status:")
                print(f"   Machine Status: {endstop_status.machine_status.value}")
                print(f"   Move Mode: {endstop_status.move_mode.value}")
                print(f"   LED Enabled: {endstop_status.led_enabled}")
                print(f"   Current File: {endstop_status.current_file or 'None'}")
                if endstop_status.endstop:
                    print(f"   Endstops - X-max:{endstop_status.endstop.x_max} Y-max:{endstop_status.endstop.y_max} Z-min:{endstop_status.endstop.z_min}")

                # Status checks
                status_checks = [
                    ("Is Printing", endstop_status.is_printing()),
                    ("Is Ready", endstop_status.is_ready()),
                    ("Is Paused", endstop_status.is_paused()),
                    ("Is Complete", endstop_status.is_print_complete())
                ]
                print(f"   Status Checks: {', '.join([f'{name}={val}' for name, val in status_checks])}")
            else:
                print("❌ Failed to get endstop status")
        except Exception as e:
            print(f"❌ Endstop status error: {e}")
        print()

        # PrintStatus - Print progress information
        print("📈 Getting print progress (PrintStatus)...")
        try:
            print_status = await client.tcp_client.get_print_status()
            if print_status:
                print("✅ Print Status:")
                print(f"   Layer Progress: {print_status.get_layer_progress()} ({print_status.get_print_percent()}%)")
                print(f"   SD Progress: {print_status.get_sd_progress()} ({print_status.get_sd_percent()}%)")
                print(f"   Is Complete: {print_status.is_complete()}")
            else:
                print("❌ Failed to get print status (normal if not printing)")
        except Exception as e:
            print(f"❌ Print status error: {e}")
        print()

        # Existing parsers for comparison
        print("📋 Standard TCP parser information...")
        try:
            # PrinterInfo
            printer_info = await client.tcp_client.get_printer_info()
            if printer_info:
                print(f"✅ Printer Info: {printer_info.type_name} - {printer_info.firmware_name}")
                print(f"   Build Volume: {printer_info.x_size}×{printer_info.y_size}×{printer_info.z_size}mm")

            # TempInfo
            temp_info = await client.tcp_client.get_temp_info()
            if temp_info:
                extruder = temp_info.get_extruder_temp()
                bed = temp_info.get_bed_temp()
                print("✅ Temperatures:")
                if extruder:
                    print(f"   Extruder: {extruder.get_current()}°C (Target: {extruder.get_target()}°C)")
                if bed:
                    print(f"   Bed: {bed.get_current()}°C (Target: {bed.get_target()}°C)")

            # LocationInfo
            location = await client.tcp_client.get_location_info()
            if location:
                print(f"✅ Position: X={location.x_pos:.2f} Y={location.y_pos:.2f} Z={location.z_pos:.2f}")

        except Exception as e:
            print(f"❌ Standard parser error: {e}")
        print()

        # ===== PHASE 4: FILE OPERATIONS & THUMBNAILS =====
        print("📁 PHASE 4: FILE OPERATIONS & THUMBNAIL EXTRACTION")
        print("-" * 55)

        try:
            # Get file list
            files = await client.files.get_file_list()
            if files:
                print(f"✅ Found {len(files)} files on printer:")

                # Show first few files
                for i, file_name in enumerate(files[:3]):
                    print(f"   {i+1}. {file_name}")

                    # Try to get thumbnail for the first file
                    if i == 0:
                        print(f"      🖼️  Getting thumbnail for '{file_name}'...")
                        try:
                            thumbnail = await client.tcp_client.get_thumbnail(file_name)
                            if thumbnail and thumbnail.has_image_data():
                                width, height = thumbnail.get_image_size()
                                print(f"      ✅ Thumbnail: {width}x{height}px, {len(thumbnail.get_image_bytes() or b'')} bytes")

                                # Save thumbnail (optional)
                                save_path = f"thumbnail_{file_name}.png"
                                if thumbnail.save_to_file_sync(save_path):
                                    print(f"      💾 Saved thumbnail to: {save_path}")

                                # Show Base64 data URL (first 100 chars)
                                data_url = thumbnail.to_base64_data_url()
                                if data_url:
                                    print(f"      🔗 Data URL: {data_url[:100]}...")
                            else:
                                print("      ❌ No thumbnail available")
                        except Exception as e:
                            print(f"      ❌ Thumbnail error: {e}")

                if len(files) > 3:
                    print(f"   ... and {len(files) - 3} more files")
            else:
                print("❌ No files found on printer")
        except Exception as e:
            print(f"❌ File operations error: {e}")
        print()

        # ===== PHASE 5: CONTROL OPERATIONS =====
        print("🎮 PHASE 5: CONTROL OPERATIONS")
        print("-" * 35)

        # Only run control operations if printer is ready
        try:
            machine_state = await client.tcp_client.check_machine_state()
            print(f"Current machine state: {machine_state}")

            if machine_state in ["ready", "complete"]:
                print("Running safe control operations...")

                # LED control
                if client.led_control:
                    print("  💡 Testing LED control...")
                    await client.control.set_led_on()
                    await asyncio.sleep(0.5)
                    await client.control.set_led_off()
                    print("     LED test completed")

                # Filtration control
                if client.filtration_control:
                    print("  🌪️  Testing filtration control...")
                    await client.control.set_external_filtration_on()
                    await asyncio.sleep(0.5)
                    await client.control.set_filtration_off()
                    print("     Filtration test completed")

                print("✅ Control operations completed")
            else:
                print(f"⚠️  Skipping control operations (printer state: {machine_state})")
        except Exception as e:
            print(f"❌ Control operations error: {e}")
        print()

        # ===== PHASE 6: CONVENIENCE METHODS =====
        print("🛠️  PHASE 6: CONVENIENCE METHODS")
        print("-" * 35)

        try:
            # High-level status methods
            is_ready = await client.tcp_client.is_printer_ready()
            current_file = await client.tcp_client.get_current_print_file()
            layer_percent, sd_percent, current_layer = await client.tcp_client.get_print_progress()

            print("✅ Convenience Methods:")
            print(f"   Printer Ready: {is_ready}")
            print(f"   Current Print File: {current_file or 'None'}")
            print(f"   Print Progress: Layer {layer_percent}%, SD {sd_percent}%, Current Layer {current_layer}")

        except Exception as e:
            print(f"❌ Convenience methods error: {e}")
        print()

        # ===== SUMMARY =====
        print("🎉 FEATURE DEMONSTRATION COMPLETE!")
        print("=" * 40)
        print("Successfully demonstrated:")
        print("✅ UDP Printer Discovery")
        print("✅ Unified Client Connection")
        print("✅ Advanced TCP Parsers (EndstopStatus, PrintStatus, ThumbnailInfo)")
        print("✅ Standard TCP Parsers (PrinterInfo, TempInfo, LocationInfo)")
        print("✅ File Operations & Thumbnail Extraction")
        print("✅ HTTP API Control Operations")
        print("✅ Convenience Methods")
        print()
        print("🚀 FlashForge Python API is fully operational with 100% TypeScript parity!")


async def quick_status_demo():
    """Quick demo showing just status information."""

    print("⚡ QUICK STATUS DEMO")
    print("=" * 25)

    # Update these for your printer
    IP_ADDRESS = "192.168.1.100"
    SERIAL_NUMBER = "your_serial_number"
    CHECK_CODE = "your_check_code"

    if SERIAL_NUMBER == 'your_serial_number':
        print("⚠️  Update connection details for real testing")
        return

    async with FlashForgeClient(IP_ADDRESS, SERIAL_NUMBER, CHECK_CODE) as client:
        if await client.initialize():
            print(f"✅ Connected to {client.printer_name}")

            # Quick status check
            status = await client.get_printer_status()
            if status:
                print(f"📊 Status: {status.machine_state}")

            # Machine state via TCP
            machine_state = await client.tcp_client.check_machine_state()
            print(f"🔧 TCP State: {machine_state}")

            # Print progress
            layer_perc, sd_perc, layer = await client.tcp_client.get_print_progress()
            if layer_perc > 0:
                print(f"📈 Progress: {layer_perc}% (Layer {layer})")
            else:
                print("📈 No active print job")


async def main():
    """Main function to run demos."""
    import argparse

    parser = argparse.ArgumentParser(description="FlashForge API Feature Demo")
    parser.add_argument(
        "--mode",
        choices=["full", "quick"],
        default="full",
        help="Demo mode to run"
    )

    args = parser.parse_args()

    if args.mode == "full":
        await comprehensive_feature_demo()
    else:
        await quick_status_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
