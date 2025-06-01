"""
Basic example demonstrating FlashForge TCP client functionality.

This example shows how to connect to a FlashForge printer via TCP,
initialize control, and perform basic operations.
"""

import asyncio
import logging

from flashforge.tcp import FlashForgeClient

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """
    Example demonstrating basic FlashForge TCP client usage.
    """
    # Replace with your printer's IP address
    printer_ip = "192.168.1.100"  # Change this to your printer's IP

    logger.info(f"Connecting to FlashForge printer at {printer_ip}")

    # Create the client
    client = FlashForgeClient(printer_ip)

    try:
        # Initialize control connection
        logger.info("Initializing control connection...")
        if await client.init_control():
            logger.info("✅ Control connection established successfully!")

            # Get printer information
            logger.info("Getting printer information...")
            printer_info = await client.get_printer_info()
            if printer_info:
                logger.info("📄 Printer Info:")
                logger.info(f"   Type: {printer_info.type_name}")
                logger.info(f"   Name: {printer_info.name}")
                logger.info(f"   Firmware: {printer_info.firmware_version}")
                logger.info(f"   Serial: {printer_info.serial_number}")

            # Get temperature information
            logger.info("Getting temperature information...")
            temp_info = await client.get_temp_info()
            if temp_info:
                extruder_temp = temp_info.get_extruder_temp()
                bed_temp = temp_info.get_bed_temp()

                logger.info("🌡️  Temperature Info:")
                if extruder_temp:
                    logger.info(f"   Extruder: {extruder_temp.get_current()}°C / {extruder_temp.get_set()}°C")
                if bed_temp:
                    logger.info(f"   Bed: {bed_temp.get_current()}°C / {bed_temp.get_set()}°C")

            # Get current location
            logger.info("Getting current location...")
            location = await client.get_location_info()
            if location:
                logger.info(f"📍 Current Position: X:{location.x} Y:{location.y} Z:{location.z}")

            # Get file list
            logger.info("Getting file list...")
            files = await client.get_file_list_async()
            if files:
                logger.info(f"📁 Files on printer ({len(files)} found):")
                for file in files[:5]:  # Show first 5 files
                    logger.info(f"   - {file}")
                if len(files) > 5:
                    logger.info(f"   ... and {len(files) - 5} more files")
            else:
                logger.info("📁 No files found on printer")

            # Test LED control
            logger.info("Testing LED control...")
            if await client.led_on():
                logger.info("💡 LED turned ON")
                await asyncio.sleep(2)
                if await client.led_off():
                    logger.info("💡 LED turned OFF")
                else:
                    logger.warning("⚠️  Failed to turn LED off")
            else:
                logger.warning("⚠️  Failed to turn LED on")

            logger.info("✅ All tests completed successfully!")

        else:
            logger.error("❌ Failed to initialize control connection")
            return

    except Exception as e:
        logger.error(f"❌ Error during testing: {e}")

    finally:
        # Clean up
        logger.info("Cleaning up connection...")
        await client.dispose()
        logger.info("✅ Connection closed")


if __name__ == "__main__":
    # Run the example
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("❌ Example interrupted by user")
    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
