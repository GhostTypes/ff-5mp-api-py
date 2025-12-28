# Protocols

FlashForge printers use a hybrid communication strategy with TCP, HTTP, and UDP protocols. Understanding these protocols is helpful for debugging and advanced usage.

## TCP Protocol

The TCP protocol provides low-level control and real-time status information.

### Connection Details

- **Port**: `8899`
- **Format**: ASCII G-code commands terminated by `\n`
- **Response**: Text-based, typically ending with `ok`

### Common Commands

| Command | Description |
|---------|-------------|
| `~M119` | Get endstop status and machine state |
| `~M105` | Get temperature readings |
| `M115` | Get machine information |
| `~M27` | Get print progress |
| `~M661` | List files on printer |
| `~M662 <filename>` | Get thumbnail for file |
| `~G28` | Home all axes |
| `~M104 S<temp>` | Set extruder temperature |
| `~M140 S<temp>` | Set bed temperature |
| `~M146 r255 g255 b255 F0` | Turn LEDs on |
| `~M146 r0 g0 b0 F0` | Turn LEDs off |

### Keep-Alive Mechanism

The TCP client maintains a persistent connection with automatic keep-alive:

- **Interval**: 5-10 seconds (adjusts based on error count)
- **Method**: Periodic status command (`M27`)
- **Purpose**: Prevents printer from timing out the session
- **Management**: Automatic (started by `init_control()`, stopped by `dispose()`)

### Command Format

Commands are prefixed with `~` and terminated with `\n`:

```
~M119\n
```

### Response Format

Responses are multi-line text ending with `ok`:

```
Endstop X-max:0 Y-max:0 Z-min:1
MachineStatus: READY
MoveMode: READY
Status S:0 L:0 J:0 F:0
LED: 1
CurrentFile: 
ok
```

### TCP Client Usage

The low-level TCP client is accessible via `client.tcp_client`:

```python
# Send raw command
response = await client.tcp_client.send_command_async("~M119")

# Use parser methods
printer_info = await client.tcp_client.get_printer_info()
temp_info = await client.tcp_client.get_temp_info()
endstop_status = await client.tcp_client.get_endstop_status()
```

## HTTP API

The HTTP API provides high-level operations and structured JSON responses.

### Connection Details

- **Port**: `8898`
- **Protocol**: HTTP/1.1
- **Format**: JSON payloads
- **Endpoints**: REST-like endpoints

### Common Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/command` | POST | Send control commands |
| `/product` | POST | Get product/control states |
| `/info` | POST | Get detailed machine info |
| `/gcodeList` | POST | Get recent file list |
| `/gcodeThumb` | POST | Get file thumbnail |
| `/upload` | POST | Upload G-code file |

### Command Structure

Commands are sent via POST with JSON payloads:

```json
{
  "serialNumber": "SN123456",
  "checkCode": "",
  "payload": {
    "cmd": "control",
    "args": {
      "command": "home"
    }
  }
}
```

### Response Format

Responses include a status code and data:

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "status": "ready",
    "temperature": 25.0
  }
}
```

### Authentication

Simple authentication using serial number and check code:

- **Serial Number**: Required for all HTTP requests
- **Check Code**: Usually empty for local network control
- **Purpose**: Identifies the printer and authorizes commands

### HTTP Client Usage

The HTTP layer is abstracted by control modules:

```python
# High-level methods use HTTP internally
await client.control.set_led_on()
await client.job_control.pause_print_job()
await client.temp_control.set_bed_temp(60)

# File operations
files = await client.files.get_recent_file_list()
thumbnail = await client.files.get_gcode_thumbnail("model.gcode")
```

## UDP Discovery Protocol

Discovery uses UDP broadcasting to find printers on the local network.

### Connection Details

- **Broadcast Port**: `48899`
- **Listen Port**: `18007` (client listens here for responses)
- **Protocol**: UDP broadcast
- **Packet**: 20-byte "magic" packet

### Discovery Packet

The discovery packet starts with `www.usr` and contains specific bytes:

```
Bytes: 77 77 77 2e 75 73 72 ... (20 bytes total)
```

### Discovery Response

Printers respond with their information:

```
Name: Adventurer 5M Pro
Serial: SN123456
IP: 192.168.1.100
```

### Discovery Usage

```python
from flashforge import FlashForgePrinterDiscovery

discovery = FlashForgePrinterDiscovery()
printers = await discovery.discover_printers_async(
    timeout_ms=3000,        # Total timeout
    idle_timeout_ms=1000,   # Idle timeout
    max_retries=3           # Retry attempts
)
```

### Discovery Limitations

- **Network Scope**: Only finds printers on same subnet
- **Firewall**: May be blocked by firewall rules
- **VLAN**: Won't work across VLANs
- **Solution**: Use manual connection with IP address if discovery fails

## Protocol Selection

The `FlashForgeClient` automatically selects the appropriate protocol:

| Operation | Protocol | Reason |
|-----------|----------|--------|
| Get temperatures | TCP | Real-time, low latency |
| Get machine info | HTTP | Structured JSON data |
| Control LEDs | HTTP or TCP | HTTP preferred, TCP fallback available |
| Home axes | TCP | Direct G-code control |
| Upload file | HTTP | File transfer |
| Get file list | TCP | Legacy compatibility |
| Get recent files | HTTP | Metadata available |

## Dual-Layer Architecture

The client uses both protocols simultaneously:

```
FlashForgeClient
    ├── HTTP Layer (port 8898)
    │   ├── Control commands
    │   ├── File operations
    │   └── Status queries
    │
    └── TCP Layer (port 8899)
        ├── G-code commands
        ├── Real-time status
        └── Keep-alive
```

### Initialization Sequence

1. **HTTP**: Send product command to get control states
2. **TCP**: Connect and send login command
3. **TCP**: Get printer info
4. **TCP**: Start keep-alive mechanism

### Concurrent Usage

Both protocols can be used concurrently:

```python
# HTTP and TCP operations can run in parallel
temps, status = await asyncio.gather(
    client.get_temperatures(),      # TCP
    client.get_printer_status()     # HTTP
)
```

## Protocol Debugging

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('flashforge')
logger.setLevel(logging.DEBUG)
```

### Monitor TCP Traffic

```python
# Send raw TCP command
response = await client.tcp_client.send_command_async("~M119")
print(f"Response: {response}")
```

### Check HTTP Requests

The HTTP client logs all requests when debug logging is enabled.

## Port Summary

| Protocol | Port | Purpose |
|----------|------|---------|
| TCP | 8899 | G-code commands, real-time control |
| HTTP | 8898 | REST API, file operations |
| UDP | 48899 | Discovery broadcast |
| UDP | 18007 | Discovery response listening |

## See Also

- **[API Reference](api_reference.md)** - Complete API documentation
- **[Getting Started](client.md)** - Quick start guide
- **[Advanced Topics](advanced.md)** - Connection management details
