# Custom Android Diagnostic Device — Phase 5

## Device responsibilities
- Workshop UI
- BLE/Wi-Fi/USB connection management
- Local diagnostic data
- Offline diagnostic operations
- Synchronization
- Device health
- OTA lifecycle
- Custom VCI transport

## Device states
`NORMAL -> DIAGNOSTIC -> NORMAL`

`NORMAL -> OTA -> NORMAL`

`NORMAL -> RECOVERY -> NORMAL`

Invalid transitions are rejected.

## Security requirements before production hardware
- Secure boot
- Hardware-backed key storage
- Signed application packages
- Signed firmware
- TLS certificate validation
- Pairing authorization
- Device identity certificates
- Audit events
- Rollback protection
