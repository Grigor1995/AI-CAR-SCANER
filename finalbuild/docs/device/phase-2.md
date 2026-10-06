# Phase 2 device contract

A device reports:
- manufacturer/model/firmware
- connection type
- capabilities
- transport parameters

The UI must not assume a device supports every protocol. Capability negotiation controls which operations are exposed.

Example:
```json
{"connection_type":"BLE","capabilities":{"obd":true,"can":false,"uds":false}}
```

Future custom Android hardware can implement the same adapter contract without modifying diagnostic reasoning.
