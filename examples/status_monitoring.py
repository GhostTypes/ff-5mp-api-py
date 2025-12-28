"""
FlashForge Python API - Status Monitoring Example

Demonstrates real-time status monitoring and continuous updates.
"""
import asyncio
from flashforge import FlashForgeClient, FlashForgePrinterDiscovery, MachineState


async def monitor_status(client, duration_seconds=30):
    """Monitor printer status continuously."""
    print(f"Monitoring status for {duration_seconds} seconds...\n")
    
    start_time = asyncio.get_event_loop().time()
    last_state = None
    
    while (asyncio.get_event_loop().time() - start_time) < duration_seconds:
        status = await client.get_printer_status()
        
        if status:
            # Print state changes
            if status.machine_state != last_state:
                print(f"State changed: {status.machine_state.value}")
                last_state = status.machine_state
            
            # Print status based on state
            if status.machine_state == MachineState.PRINTING:
                print(f"  Progress: {status.print_progress}% "
                      f"(Layer {status.current_print_layer}/{status.total_print_layers})")
                print(f"  File: {status.print_file_name}")
                print(f"  Extruder: {status.extruder.current}°C")
                print(f"  Bed: {status.print_bed.current}°C")
            
            elif status.machine_state == MachineState.HEATING:
                print(f"  Extruder: {status.extruder.current}°C -> {status.extruder.set}°C")
                print(f"  Bed: {status.print_bed.current}°C -> {status.print_bed.set}°C")
            
            elif status.machine_state == MachineState.READY:
                print(f"  Ready - Extruder: {status.extruder.current}°C, "
                      f"Bed: {status.print_bed.current}°C")
        
        await asyncio.sleep(2)


async def monitor_temperatures(client, duration_seconds=20):
    """Monitor temperature changes."""
    print(f"\nMonitoring temperatures for {duration_seconds} seconds...\n")
    
    for i in range(duration_seconds // 2):
        temps = await client.get_temperatures()
        if temps:
            extruder = temps.get_extruder_temp()
            bed = temps.get_bed_temp()
            
            if extruder and bed:
                print(f"[{i*2}s] Extruder: {extruder.current}°C/{extruder.set}°C, "
                      f"Bed: {bed.current}°C/{bed.set}°C")
        
        await asyncio.sleep(2)


async def monitor_print_progress(client, check_interval=5):
    """Monitor print progress until complete."""
    print("\nMonitoring print progress...\n")
    
    while True:
        status = await client.get_printer_status()
        
        if not status:
            print("Failed to get status")
            break
        
        if status.machine_state == MachineState.PRINTING:
            print(f"Progress: {status.print_progress}%")
            print(f"Layer: {status.current_print_layer}/{status.total_print_layers}")
            print(f"Time: {status.formatted_run_time}")
            print(f"ETA: {status.print_eta}\n")
        
        elif status.machine_state == MachineState.COMPLETED:
            print("Print completed!")
            break
        
        elif status.machine_state == MachineState.CANCELLED:
            print("Print was cancelled")
            break
        
        elif status.machine_state == MachineState.ERROR:
            print(f"Error occurred: {status.error_code}")
            break
        
        else:
            print(f"State: {status.machine_state.value}")
            break
        
        await asyncio.sleep(check_interval)


async def main():
    """Run status monitoring examples."""
    
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
        
        print(f"Connected to {client.printer_name}\n")
        
        # Monitor general status
        await monitor_status(client, duration_seconds=30)
        
        # Monitor temperatures
        await monitor_temperatures(client, duration_seconds=20)
        
        # Monitor print progress (if printing)
        status = await client.get_printer_status()
        if status and status.machine_state == MachineState.PRINTING:
            await monitor_print_progress(client, check_interval=5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"Error: {e}")
