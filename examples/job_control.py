"""
FlashForge Python API - Job Control Example

Demonstrates print job management operations.
"""

import asyncio
import os

from flashforge import FlashForgeClient, FiveMClientConnectionOptions, MachineState, PrinterDiscovery


def _build_connection_options(printer) -> FiveMClientConnectionOptions:
    return FiveMClientConnectionOptions(
        http_port=printer.event_port,
        tcp_port=printer.command_port,
    )


async def main():
    """Print job control operations."""
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

        if status:
            print(f"Current state: {status.machine_state.value}")

            if status.machine_state == MachineState.PRINTING:
                print(f"Printing: {status.print_file_name}")
                print(f"Progress: {status.print_progress}%")
                print(f"Layer: {status.current_print_layer}/{status.total_print_layers}\n")

                print("Pausing print...")
                if await client.job_control.pause_print_job():
                    print("  Print paused")
                    await asyncio.sleep(2)

                    print("Resuming print...")
                    if await client.job_control.resume_print_job():
                        print("  Print resumed")

            elif status.machine_state == MachineState.READY:
                print("Printer is ready\n")

                file_path = "model.gcode"
                print(f"Uploading {file_path}...")
                if await client.job_control.upload_file(
                    file_path, start_print=True, level_before_print=True
                ):
                    print("  File uploaded and print started")
                else:
                    print("  Upload failed")

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
