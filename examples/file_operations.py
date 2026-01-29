"""
FlashForge Python API - File Operations Example

Demonstrates file management and thumbnail operations.
"""

import asyncio

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery


async def main():
    """File operations."""

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

        print(f"Connected to {client.printer_name}\n")

        # List files on printer (TCP)
        print("Files on printer:")
        files = await client.files.get_file_list()
        if files:
            for i, filename in enumerate(files, 1):
                print(f"  {i}. {filename}")
        else:
            print("  No files found")

        # Get recent files with metadata (HTTP)
        print("\nRecent files:")
        recent = await client.files.get_recent_file_list()
        if recent:
            for entry in recent:
                hours = entry.printing_time // 3600
                minutes = (entry.printing_time % 3600) // 60
                print(f"  {entry.gcode_file_name}")
                print(f"    Print time: {hours}h {minutes}m")
                if entry.total_filament_weight:
                    print(f"    Filament: {entry.total_filament_weight}g")
        else:
            print("  No recent files")

        # Get thumbnail for a file
        if files:
            filename = files[0]
            print(f"\nGetting thumbnail for {filename}...")

            # Method 1: HTTP API (recommended)
            thumbnail_bytes = await client.files.get_gcode_thumbnail(filename)
            if thumbnail_bytes:
                output_path = f"thumbnail_{filename}.png"
                with open(output_path, "wb") as f:
                    f.write(thumbnail_bytes)
                print(f"  Saved to {output_path} ({len(thumbnail_bytes)} bytes)")
            else:
                print("  No thumbnail available")

            # Method 2: TCP client (alternative)
            thumbnail_info = await client.tcp_client.get_thumbnail(filename)
            if thumbnail_info and thumbnail_info.has_image_data():
                width, height = thumbnail_info.get_image_size()
                print(f"  Thumbnail size: {width}x{height}")

                # Save using built-in method
                if thumbnail_info.save_to_file_sync(f"tcp_thumbnail_{filename}.png"):
                    print("  Saved via TCP method")

                # Or get as base64 data URL
                data_url = thumbnail_info.to_base64_data_url()
                if data_url:
                    print(f"  Data URL length: {len(data_url)} chars")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
