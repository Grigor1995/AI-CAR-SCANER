# Shared OBD backend: setup and API

See [advanced reads and generation portraits](EXPANDED_CATALOG_AND_PROTOCOLS.md)
for the newer ELM UDS, DoIP, J1939 and J1708/J1587 interfaces.

## Two deployment modes

**Backend beside the vehicle:** Desktop/PC/Raspberry Pi runs the backend and
connects to an ELM-compatible Wi-Fi TCP, USB serial or configured BLE GATT
adapter. Remote clients use that backend's device/telemetry APIs. USB serial
requires OS drivers/permissions. BLE requires the adapter's actual TX/RX GATT
UUIDs; there is no universal ELM BLE UUID.

**Backend on a remote server:** Android uses its native Bluetooth SPP, Wi-Fi or
USB byte transport, gets initialization/polling commands from the backend and
posts the raw responses for decoding. Native USB bulk transport is adapter-
specific and is not a complete driver for all USB-serial chipsets. iOS supports
the new Wi-Fi TCP bridge; its CoreBluetooth screen currently discovers BLE
peripherals and does not implement a universal BLE connection. iOS USB/SPP
support cannot be assumed without the appropriate accessory/OS integration.

For Desktop, from finalbuild:

```bash
python -m apps.desktop.main --with-backend
```

In Desktop Live Data, use **Start connected adapter** after binding a connected
physical device to the diagnostic session. The backend resolves its transport.
**Start simulator** remains an explicit, separately labeled option.

For a standalone source backend, from finalbuild (Git Bash/Linux/macOS):

```bash
export PYTHONPATH="$PWD:$PWD/backend"
export DATABASE_URL="sqlite:///./diagnostic.sqlite3"
export AI_CAR_DESKTOP_LOCAL_DB=1
python -m apps.desktop.backend_worker
```

The launcher defaults to loopback port 8001. Set AI_CAR_BACKEND_HOST to a
reachable interface when other devices need access. Database state and device
access belong to the backend host. A cloud backend cannot open the phone's
Bluetooth radio or a car-local USB port directly.

## Android backend selection

Build from the repository root for the Android emulator's host-machine backend:

```bash
python build.py --targets android --with-tests --android-api-url http://10.0.2.2:8001/
```

Or directly from finalbuild/apps/mobile-android:

```bash
./gradlew :app:assembleDebug -PapiBaseUrl=http://10.0.2.2:8001/
```

Use the backend's LAN/HTTPS address for a physical phone. The default remains
the configured hosted API. Deploy/update the backend with these endpoints
before running a new native bridge build. iOS uses its existing API URL setting.

## Read-only APIs

| Endpoint | Purpose |
|---|---|
| GET /api/v1/obd/protocols | Registry with implemented/adapter-only/unimplemented statuses |
| GET /api/v1/obd/plan?protocol_id=auto | Initialization, discovery and polling command lists |
| GET /api/v1/obd/detected-protocol?raw=A6 | Interpret a captured ATDPN reply; not model inference |
| POST /api/v1/obd/decode | Raw responses → values, units, per-command errors and protocol |
| GET /api/v1/vehicle-reference | Generation/engine/source/image references |
| GET /api/v1/vehicle-reference/compatibility | Candidate protocols; make/model/year required, engine/market optional |
| GET /api/v1/vehicle-reference/{reference_id}/image | Backend image, or explicit 404 |
| GET /api/v1/vehicle-reference/image?make=…&model=…&chassis=… | Image lookup for existing native vehicle records |
| GET /api/v1/vehicle-catalog/entries | Existing database rows plus labeled reference candidates |
| POST /api/v1/devices/scan/{usb\|ble\|simulator} | Server-host discovery; Wi-Fi requires explicit probing |
| POST /api/v1/devices/wifi/probe | Register a reachable server-local TCP adapter |
| POST /api/v1/devices/{device_id}/connect | Config includes protocol_id, default auto; BLE needs tx_uuid/rx_uuid |
| GET /api/v1/devices/{device_id}/obd/protocol | Negotiate with 0100 and report ATDPN |
| GET /api/v1/devices/{device_id}/obd/live-data | Shared decoded values from the server-local adapter |
| POST /api/v1/acquisition/sessions/{session_id}/start | Explicit simulator, physical transport/device_id, or adapter=bound for the session device |

Example native bridge body:

```json
{
  "responses": {"010C": "41 0C 1A F8", "0105": "41 05 7B", "ATDPN": "A6"}
}
```

An optional internal session_id appends valid samples to that session's backend
telemetry and acquisition records. The UI does not display that identifier.
Do not combine native and server-local acquisition for one active session.
The existing telemetry analysis endpoints operate on these captured samples.
Unknown/invalid PID values remain null with errors; no diagnosis is inferred
merely from selecting a vehicle or establishing a socket connection.

## Import actual Commons photos

With Wikipedia/Commons access, from finalbuild:

```bash
python -m pip install 'Pillow>=13,<14'
python scripts/import_wikimedia_vehicles.py --limit 50
```

Use --make Toyota to restrict the import, or --force to refresh existing
manifest entries. Images and attribution are stored in data/vehicle_images.
Keep the manifest with those images. The backend serves them to all native
clients; there is no need to duplicate newly imported photos in each app.
The container includes data/, and the Windows backend spec includes the image
manifest/folder when it exists at build time. Rebuild/redeploy those packages
after importing. No network download happens during backend startup.

See [audit and limitations](REAL_OBD_AUDIT.md) before interpreting protocol
registry entries as vehicle/hardware validation.
