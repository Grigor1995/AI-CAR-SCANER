# Flutter mobile client

Phase 2 adds the platform seam for BLE OBD devices. Flutter owns Bluetooth permissions, scanning and lifecycle. The shared backend/vehicle layer owns protocol semantics.

Android/iOS device support must be validated against the actual VCI's BLE profile; UUIDs are not hard-coded.
