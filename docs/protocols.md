# Protocols

FlashForge printers utilize a hybrid communication strategy, employing both TCP and HTTP protocols for different tasks. The `FlashForgeClient` abstracts this away, but understanding the underlying protocols can be helpful for debugging or advanced usage.

## TCP Protocol

The TCP protocol is used for:
*   Real-time control (movement, homing).
*   Detailed temperature readings.
*   G-code command transmission.
*   Keep-alive mechanisms.
*   Legacy support.

### Connection Details
*   **Port**: `8899`
*   **Format**: ASCII G-code commands terminated by `\n`.
*   **Response**: Text-based, typically ending with `ok`.

### Common Commands
*   `~M119`: Get endstop status.
*   `~M105`: Get temperature.
*   `M115`: Get machine info.

### Keep-Alive
The client maintains a persistent TCP connection with a keep-alive mechanism (usually polling status) to ensure the printer remains responsive and doesn't timeout the session.

## HTTP API

The HTTP API is used for:
*   High-level status information (JSON).
*   File management (listing, uploading).
*   Camera control.
*   Complex configuration commands.
*   Retrieving the "Machine Detail" status object.

### Connection Details
*   **Port**: `8898`
*   **Endpoints**: REST-like endpoints (e.g., `/command`, `/product`, `/info`).

### Command Structure
Commands are sent via POST requests to specific endpoints. The payload often includes the printer's serial number and a "check code" for simple authentication.

Example Payload:
```json
{
  "serialNumber": "SN123456",
  "checkCode": "",
  "payload": {
    "cmd": "control",
    "args": { ... }
  }
}
```

## Discovery Protocol (UDP)

Discovery is handled via UDP broadcast.

*   **Broadcast Port**: `48899`
*   **Listening Port**: `18007` (The client listens here for responses).
*   **Packet**: A specific 20-byte "magic" packet starting with `www.usr`.

When the printer receives this packet, it broadcasts a response containing its name, serial number, and IP address.
