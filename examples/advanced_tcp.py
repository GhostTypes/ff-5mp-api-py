"""
FlashForge Python API - Advanced TCP Example

Demonstrates low-level TCP operations and parsers.
"""
import asyncio
from flashforge import FlashForgeClient, FlashForgePrinterDiscovery


async def main():
    """Advanced TCP client operations."""
    
    # Discover and connect
    discovery = FlashForgePrinterDiscovery()
    printers = await discovery.discover_printers_async()
    
    if not printers:
        print("No printers found")
        return
    
    printer = printers[0]
    
    async with FlashForgeClient(
        printer.ip_address,
        printer.serial_number,
        printer.check_code
    ) as client:
        if not await client.initialize():
            print("Failed to connect")
            return
        
        await client.init_control()
        
        print(f"Connected to {client.printer_name}\n")
        
        # Send raw G-code command
        print("=== Raw G-code Commands ===\n")
        response = await client.tcp_client.send_command_async("~M105")
        print(f"M105 (Get Temperature) response:")
        print(f"  {response}\n")
        
        # Get printer info via TCP
        print("=== Printer Info (TCP) ===\n")
        printer_info = await client.tcp_client.get_printer_info()
        if printer_info:
            print(f"Type: {printer_info.type_name}")
            print(f"Firmware: {printer_info.firmware_version}")
            print(f"Build volume: {printer_info.x_size}x{printer_info.y_size}x{printer_info.z_size}mm\n")
        
        # Get temperature info
        print("=== Temperature Info (TCP) ===\n")
        temp_info = await client.tcp_client.get_temp_info()
        if temp_info:
            extruder = temp_info.get_extruder_temp()
            bed = temp_info.get_bed_temp()
            if extruder:
                print(f"Extruder: {extruder.current}°C / {extruder.set}°C")
            if bed:
                print(f"Bed: {bed.current}°C / {bed.set}°C")
            print()
        
        # Get location info
        print("=== Location Info (TCP) ===\n")
        location = await client.tcp_client.get_location_info()
        if location:
            print(f"X: {location.x_pos}mm")
            print(f"Y: {location.y_pos}mm")
            print(f"Z: {location.z_pos}mm\n")
        
        # Get endstop status
        print("=== Endstop Status (TCP) ===\n")
        endstop_status = await client.tcp_client.get_endstop_status()
        if endstop_status:
            print(f"Machine status: {endstop_status.machine_status.value}")
            print(f"Move mode: {endstop_status.move_mode.value}")
            print(f"LED enabled: {endstop_status.led_enabled}")
            
            if endstop_status.current_file:
                print(f"Current file: {endstop_status.current_file}")
            
            # Convenience methods
            if endstop_status.is_printing():
                print("Status: Printer is actively printing")
            elif endstop_status.is_paused():
                print("Status: Print is paused")
            elif endstop_status.is_ready():
                print("Status: Printer is ready")
            elif endstop_status.is_print_complete():
                print("Status: Print completed")
            print()
        
        # Get print status
        print("=== Print Status (TCP) ===\n")
        print_status = await client.tcp_client.get_print_status()
        if print_status:
            layer_progress = print_status.get_print_percent()
            sd_progress = print_status.get_sd_percent()
            
            print(f"Layer progress: {layer_progress}%")
            print(f"SD progress: {sd_progress}%")
            
            if print_status.is_complete():
                print("Print is complete")
            print()
        
        # Convenience methods
        print("=== Convenience Methods ===\n")
        is_ready = await client.tcp_client.is_printer_ready()
        print(f"Printer ready: {is_ready}")
        
        current_file = await client.tcp_client.get_current_print_file()
        if current_file:
            print(f"Current file: {current_file}")
        
        layer_pct, sd_pct, current_layer = await client.tcp_client.get_print_progress()
        print(f"Progress: {layer_pct}% (Layer {current_layer})")
        
        machine_state = await client.tcp_client.check_machine_state()
        print(f"Machine state: {machine_state}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
