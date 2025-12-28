"""
LED Control Examples

Demonstrates different approaches to controlling printer LEDs:
1. Standalone TCP LED control (for aftermarket LEDs or direct TCP connections)
2. Dual-mode scenario (HTTP client using internal TCP as fallback)

Use Cases:
- Printers with aftermarket LED installations not detected by HTTP API
- Cases where led_control capability flag incorrectly reports False
- Direct TCP-only connections without HTTP API access
"""

import asyncio

from flashforge import FlashForgeClient
from flashforge.tcp.ff_client import FlashForgeClient as TcpClient


async def standalone_tcp_led_control():
    """
    Example 1: Standalone TCP LED Control
    
    Use this approach when connecting directly via TCP without the HTTP API.
    This is useful for aftermarket LED installations or when you need direct
    G-code control.
    """
    print("=== Standalone TCP LED Control ===\n")
    
    client = TcpClient("192.168.1.100")
    
    try:
        if not await client.connect():
            print("Failed to connect via TCP")
            return
        
        if not await client.init_control():
            print("Failed to initialize control session")
            return
        
        print("Connected via TCP")
        
        print("Turning LEDs on...")
        if await client.led_on():
            print("LEDs turned on successfully")
        else:
            print("Failed to turn LEDs on")
        
        await asyncio.sleep(2)
        
        print("Turning LEDs off...")
        if await client.led_off():
            print("LEDs turned off successfully")
        else:
            print("Failed to turn LEDs off")
        
    finally:
        await client.disconnect()
        print("Disconnected\n")


async def dual_mode_led_control():
    """
    Example 2: Dual-Mode LED Control
    
    Use this approach when using the HTTP API but need to fall back to TCP
    for LED control. This is useful when:
    - The printer has aftermarket LEDs not detected by the HTTP API
    - The led_control capability flag is incorrectly False
    - HTTP LED control fails but TCP works
    """
    print("=== Dual-Mode LED Control (HTTP + TCP Fallback) ===\n")
    
    client = FlashForgeClient("192.168.1.100")
    
    try:
        if not await client.initialize():
            print("Failed to initialize HTTP client")
            return
        
        if not await client.init_control():
            print("Failed to initialize control session")
            return
        
        print(f"Connected to printer")
        print(f"LED control capability: {client.led_control}")
        
        if client.led_control:
            print("\nUsing HTTP API for LED control...")
            await client.control.set_led_on()
            await asyncio.sleep(2)
            await client.control.set_led_off()
        else:
            print("\nHTTP LED control not available, using TCP fallback...")
            print("Accessing internal TCP client...")
            
            tcp_client = client.tcp_client
            
            print("Turning LEDs on via TCP...")
            if await tcp_client.led_on():
                print("LEDs turned on successfully (TCP)")
            else:
                print("Failed to turn LEDs on (TCP)")
            
            await asyncio.sleep(2)
            
            print("Turning LEDs off via TCP...")
            if await tcp_client.led_off():
                print("LEDs turned off successfully (TCP)")
            else:
                print("Failed to turn LEDs off (TCP)")
        
        print("\nLED control completed")
        
    finally:
        await client.disconnect()
        print("Disconnected\n")


async def main():
    """Run all LED control examples."""
    print("FlashForge LED Control Examples\n")
    print("These examples demonstrate TCP-based LED control,")
    print("which uses M146 G-code commands instead of HTTP API.\n")
    print("=" * 50)
    print()
    
    await standalone_tcp_led_control()
    
    await asyncio.sleep(1)
    
    await dual_mode_led_control()
    
    print("=" * 50)
    print("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
