"""
FlashForge Python API - Job Control Example

Demonstrates print job management operations.
"""

import asyncio

from flashforge import FlashForgeClient, FlashForgePrinterDiscovery, MachineState


async def main():
    """Print job control operations."""

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

        # Check current status
        status = await client.get_printer_status()
        if status:
            print(f"Current state: {status.machine_state.value}")

            if status.machine_state == MachineState.PRINTING:
                print(f"Printing: {status.print_file_name}")
                print(f"Progress: {status.print_progress}%")
                print(f"Layer: {status.current_print_layer}/{status.total_print_layers}\n")

                # Pause print
                print("Pausing print...")
                if await client.job_control.pause_print_job():
                    print("  Print paused")
                    await asyncio.sleep(2)

                    # Resume print
                    print("Resuming print...")
                    if await client.job_control.resume_print_job():
                        print("  Print resumed")

                    # Optionally cancel
                    # print("Canceling print...")
                    # if await client.job_control.cancel_print_job():
                    #     print("  Print cancelled")

            elif status.machine_state == MachineState.READY:
                print("Printer is ready\n")

                # Upload and print a file
                file_path = "model.gcode"  # Path to your G-code file

                print(f"Uploading {file_path}...")
                if await client.job_control.upload_file(
                    file_path, start_print=True, level_before_print=True
                ):
                    print("  File uploaded and print started")
                else:
                    print("  Upload failed")

                # Or print a file already on the printer
                # print("Starting local file...")
                # if await client.job_control.print_local_file("existing_file.gcode"):
                #     print("  Print started")

        # Monitor print progress
        if status and status.machine_state == MachineState.PRINTING:
            print("\nMonitoring print progress...")
            for _i in range(5):
                status = await client.get_printer_status()
                if status:
                    print(
                        f"  Progress: {status.print_progress}% "
                        f"(Layer {status.current_print_layer}/{status.total_print_layers})"
                    )
                await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
