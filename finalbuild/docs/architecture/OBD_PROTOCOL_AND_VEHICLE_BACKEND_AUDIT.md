# AI-CAR-SCANER — OBD Protocol / Worldwide Vehicle Catalog Audit

**Audit date:** 2026-10-22. **Branch:** feat/backend-obd-vehicle-registry-20261022.
**Status:** backend registry implementation added; actual hardware/E2E validation pending.
**Principle:** One backend-defined vehicle/protocol/image contract; desktop, Android
and iOS may present it differently. Native Bluetooth/USB permissions and
hardware access are transport concerns that cannot run on a distant server.

## Findings in existing main
- `data/vehicle_catalog.json`: **30 makes / 232 make-model names**.
  Broad, project-curated NHTSA vPIC-derived seed; its engine_families are only
  high-level hints, NOT actual engine-code fitments.
- `data/vehicle_fitment_catalog.json`: **22 chassis and 55 distinct
  engine entries by chassis** with year ranges, fuel and ECU guesses.
  They are not complete market/year/VIN-level engine listings.
- `shared/vehicle_catalog.json`: exploded offline car selector seed.
  Must not override newer authoritative backend results.
- `assets/vehicle_models`: 22 model/chassis-generated PNG + SVG designs.
  **Not real car photographs.**
- `backend/device/manager.py`: `VCIConnectionManager` is explicitly
  **simulator-only**. Real USB/BLE/Wi-Fi vehicle communication is not
  yet wired into the FastAPI device manager.
- `vehicle/obd/client.py`: ELM327-style generic emissions requests for VIN,
  DTC and selected live PIDs (read-only). Now has `ATDPN`/`ATDP` reporting.
- **Confirmed code defect found:** ELM init sends `ATS0` (no spaces), but
  the old hex decoder recognized only spaced byte pairs. The new decoder
  accepts both `410C0BB8` and `41 0C 0B B8`, plus common CAN header prefixes.
  Hardware-dependent ISO-TP multi-frame VIN reassembly still needs live tests.
- `vehicle/uds/client.py`: read-only UDS over an ISO-TP stack. Manufacturer
  definitions, addressing and gateway authentication are not universal.
- Android native OBD transports and iOS BLE discovery are separate from the
  backend VCI manager; the latter cannot magically access a phone's Bluetooth
  devices from a cloud server.

## Protocol coverage and honest implementation boundary

| Family | Main standards | Existing code | Status |
|---|---|---|---|
| Generic OBD-II | SAE J1850 PWM / VPW | ELM327 library | **Protocol-capable chip**, physical server integration pending |
| K-Line emissions | ISO 9141-2 | ELM327 library | Real adapter/vehicle validation pending |
| KWP2000 | ISO 14230-4 slow / fast | ELM327 library | Real adapter/vehicle validation pending |
| OBD over CAN | ISO 15765-4 11/29-bit, 250/500 kbit/s | ELM327 library | Real adapter/vehicle validation pending |
| Heavy duty | SAE J1939 (250/500) | Metadata only | Not implemented as real backend ECU scanner |
| Enhanced ECU | ISO 14229 UDS on CAN via ISO 15765-2 | Read-only ISO-TP client | Partially implemented, no hardware proof |
| Ethernet | ISO 13400-2 DoIP with UDS | Metadata only | Not implemented |
| Worldwide OBD | ISO 27145 WWH-OBD | Metadata only | Not implemented |
| OBDonUDS | SAE J1979-2 | Metadata only | Not implemented |
| KWP2000 on CAN | ISO 14230/15765 variants | Metadata only | Manufacturer-specific support not implemented |

ELM327 chip mode IDs: 0 automatic, 1 PWM, 2 VPW, 3 ISO 9141-2,
4 KWP slow, 5 KWP fast, 6 CAN 11/500, 7 CAN 29/500, 8 CAN 11/250,
9 CAN 29/250, A SAE J1939. `ATDPN` `A6` means adapter reports it
selected protocol 6 automatically; `A0` means *not yet selected*.
`ATDP` human-readable descriptions must not be mistaken for mode IDs.

Protocol standards do **not** imply ELM327 clones implement them correctly.
Actual ECU access needs real transport, vehicle handshake, correct CAN/K-line
timings, address/physical routing and possibly OEM licenses/security tokens.

## Vehicle-year protocol reasoning
All makes and models have **unverified protocol candidates** until the physical
adapter reports a diagnostic link; even that report is not proof of an
entire vehicle's enhanced ECU communications.
- Legacy vehicles can use J1850, ISO 9141-2, KWP or CAN depending on
  market/year/ECU; do not assign them from model names alone.
- From model year 2008, US light-duty generic OBD emissions communication
  moved to CAN, but do **not** generalize that rule to all markets or all ECUs.
- Trucks can use J1939/WWH-OBD; do not put J1939 in passenger-car assumptions.
- UDS, DoIP and OBDonUDS are different diagnostic service/transport layers;
  do not pretend they are ELM327 generic protocols.

## Backend endpoints — one source for all native clients

```http
GET /api/v1/vehicle-catalog/global-models?make=Mercedes-Benz
GET /api/v1/vehicle-catalog/curated-variants?make=Mercedes-Benz&model=E-Class&chassis=W211&year=2006
GET /api/v1/vehicle-catalog/obd-protocols
GET /api/v1/vehicle-catalog/protocol-hints?make=Mercedes-Benz&model=E-Class&year=2006&engine=M272%20E35%203.5
POST /api/v1/vehicle-catalog/parse-adapter-protocol
GET /api/v1/vehicle-catalog/image-metadata?make=Mercedes-Benz&model=E-Class&chassis=W211
GET /api/v1/vehicle-catalog/artwork?make=Mercedes-Benz&model=E-Class&chassis=W211
GET /api/v1/vehicle-catalog/commons-photo-candidates?make=Mercedes-Benz&model=E-Class&chassis=W211
GET /api/v1/vehicle-catalog/vpic-models?make=Mercedes-Benz&year=2006
```

`POST /parse-adapter-protocol` JSON example:
```json
{"adapter_id":"my-vci","atdpn":"A6","atdp":"AUTO ISO 15765-4 CAN"}
```

**Auth and trust:** the POST parses *client supplied data*, which must not be
equated with server-attested vehicle identity or VIN. Do not send raw VINs to
third-party services without the user's informed choice.

`/vpic-models`: optional live NHTSA public model lookup. Primarily
US-market information; it does not deliver a complete engine-option catalog.
`/commons-photo-candidates`: optional real-car photo search through fixed
Wikimedia Commons API. Responses carry the file page, author, license,
license URL and thumbnail, with mandatory visual model review. No claim that
every result is the selected generation, body style or trim.
Only openly reusable licenses are suggested. Pay attention to CC BY-SA
requirements and the limits of machine-readable Commons metadata.

The default `/artwork` endpoint returns bundled *generated* portraits, never
claims they are photographs. Offline portraits remain available if Wikimedia
Commons or vPIC are unreachable.

## Next release blockers / unfinished work

1. Attach real ELM/J2534/VCI transports to backend manager with reliable
   hardware capabilities, read-only generic OBD detection and repeatable
   permission-limited tests.
2. Add OEM-grade UDS/DoIP/J1939 implementations separately with real
   hardware and documented licensing; never send generic security-access,
   memory-write or reprogramming commands without operator control.
3. Validate each make/chassis/engine/year *per market* from OEM/VIN/ECU
   documents; `55 curated engines` is **not all car engines**.
4. Review/approve real Wikimedia photos for each of the 22 currently
   curated chassis; preserve title, creator, link, license/attribution and
   license compatibility. Do not silently replace generated assets.
5. Migrate the native clients to consume new backend selector/protocol/image
   endpoints; keep offline cache read-only and labeled fallback. Hardware
   connectors require native OS transport glue even if diagnosis is backend-owned.
6. Verify Windows (Python 3.14 + frozen backend_service.exe), Android emulator,
   iOS simulator and real vehicle scanner. **No real hardware PASS yet.**
7. Maintain existing dashboard/AI/recovery functionality: do not merge the
   obsolete diverged UI feature branch directly into main.

## Primary technical sources

- [ELM327 protocol families](https://elmelectronics.com/products/ics/obd/)
- [Global OBD protocol selector](https://www.snapon.com/DiagnosticsManuals/Help/OBDII/Content/Common/Help%20Topics/OBD/Protocol%20Selection.htm)
- [SAE J1979-2 OBDonUDS](https://saemobilus.sae.org/standards/j1979-2_202104-e-e-diagnostic-test-modes-obdonuds)
- [Softing diagnostic standards](https://automotive.softing.com/standards/protocols.html)
- [NHTSA vPIC APIs](https://vpic.nhtsa.dot.gov/api/Home/Index)
- [Wikimedia Imageinfo licensing metadata](https://www.mediawiki.org/wiki/API:Imageinfo)
- [Wikimedia attribution](https://attribution.wikimedia.org/attribution-signals/license.html)


## Local QA commands (no CI/CD)

From `finalbuild/` on Windows Git Bash:

```bash
python -m pytest -q tests/api/test_backend_vehicle_knowledge.py tests/vehicle/test_obd_client.py tests/vehicle/test_elm327.py
python scripts/run_desktop_tests.py --group vehicle-protocol
python -m pytest -q tests/api/test_low_coverage_vehicle_catalog_routes.py
python scripts/test_fastapi_startup.py --mode source
```

When the FastAPI service is already running:

```bash
curl -fsS 'http://127.0.0.1:8001/api/v1/vehicle-catalog/global-models?make=BMW'
curl -fsS 'http://127.0.0.1:8001/api/v1/vehicle-catalog/curated-variants?make=Mercedes-Benz&model=E-Class&chassis=W211'
curl -fsS 'http://127.0.0.1:8001/api/v1/vehicle-catalog/obd-protocols'
curl -fsS 'http://127.0.0.1:8001/api/v1/vehicle-catalog/runtime-capabilities'
curl -fsS -X POST -H 'Content-Type: application/json' -d '{"atdpn":"A6"}' \
  'http://127.0.0.1:8001/api/v1/vehicle-catalog/parse-adapter-protocol'
```

For the Windows frozen backend, REBUILD `backend_service.exe` after
checking out the feature branch: catalog JSON + image manifest + portraits
are now bundled. Test source/frozen FastAPI startup after the build.
Android/iOS have REST DTO accessors only; their UI screen integration and
hardware adapter E2E are not certified by these tests.
