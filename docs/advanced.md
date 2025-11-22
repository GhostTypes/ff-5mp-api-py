# Advanced Topics

## Async/Await Patterns

The FlashForge API is fully asynchronous, leveraging Python's `asyncio` library. This ensures that network operations (like waiting for a printer response) do not block your main application loop.

### Best Practices

1.  **Always use `await`**: All methods interacting with the network are coroutines and must be awaited.
2.  **Context Managers**: Use `async with` for the client to ensure connections are properly closed.
3.  **Concurrency**: You can run multiple commands in parallel using `asyncio.gather()`, but be careful with commands that modify printer state (like movement), as the printer processes G-code sequentially.

### Example: Concurrent Status Checks

```python
async def check_multiple_printers(ips):
    tasks = []
    for ip in ips:
        client = FlashForgeClient(ip, "serial", "")
        tasks.append(client.get_printer_status())

    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Process results...
```

## Error Handling

The API can raise exceptions when network errors occur or when the printer returns invalid data.

### Common Exceptions

*   `aiohttp.ClientError`: Base class for HTTP networking errors.
*   `asyncio.TimeoutError`: Raised if an operation takes too long.
*   `OSError` / `ConnectionRefusedError`: TCP connection failures.

### Handling Connection Failures

The `FlashForgeClient` includes logic to attempt reconnection for TCP sockets. However, if the printer is turned off or network is lost, you should handle these cases in your application code.

```python
try:
    await client.initialize()
except Exception as e:
    print(f"Failed to connect: {e}")
```

## Manual Connection (Without Discovery)

If discovery doesn't work (e.g., across subnets), you can connect manually if you know the IP.

```python
# You still need the serial number for some HTTP commands
client = FlashForgeClient("192.168.1.50", "SERIAL_NUMBER_HERE", "")
```

If you don't know the serial number, you might be able to fetch it via a generic status query if the printer supports it, but currently, the constructor requires it.

## Type Hints & Safety

This library uses standard Python type hints. It is compatible with `mypy` and modern IDEs (VS Code, PyCharm) for autocompletion and static analysis.

```python
from flashforge.models import FFMachineInfo

async def process_status(info: FFMachineInfo) -> None:
    # IDE knows 'info' has a 'machine_state' property
    if info.machine_state == "printing":
        pass
```

## G-code Thumbnails

FlashForge printers store thumbnail images for G-code files. You can retrieve these using the `client.files.get_gcode_thumbnail(filename)` method.

```python
thumbnail_bytes = await client.files.get_gcode_thumbnail("my_print.gcode")
if thumbnail_bytes:
    with open("thumbnail.png", "wb") as f:
        f.write(thumbnail_bytes)
```

The returned bytes are typically a PNG image.

## Endstop Monitoring

You can check the status of the printer's endstops (limit switches) using the `~M119` command via the TCP interface. While there isn't a high-level helper method for this yet, you can use the low-level TCP client:

```python
# Send raw G-code command
response = await client.tcp_client.send_command_async("~M119")
print(response)
# Example output: "X_min:0 Y_min:0 Z_min:0 ok"
```
