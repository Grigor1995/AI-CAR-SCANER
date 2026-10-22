# AI-CAR-SCANER — Global Vehicle, OBD Protocol and Backend Ownership Audit
**22 October 2026 · working branch:** `feature/backend-unified-vehicle-obd-audit-20261022`

## Executive finding
There cannot be a truthful static "protocol for every car model" list. The
diagnostic link may vary across country, year, engine, ECU, OBD legislation,
VIN/equipment build and hardware adapter. One car may expose multiple networks.
"OBD-II" is a *regulated diagnostic interface*, CAN is a *network*, UDS is
an *application protocol*, and DoIP is diagnostic transport over Ethernet.
No VIN database proves which protocol a physically connected ECU is using.

This change establishes a **single backend-owned registry**, with
`market/year/class` protocol *candidates*, optional NHTSA VIN metadata,
read-only ELM327 ATSP0/0100/ATDPN protocol observation and Wikimedia Commons
license-aware real-photo candidates. It does **not** falsely claim universal
hardware support or that a photograph/fitment is verified for an exact VIN.

## 1. What the repository supported before this change

| Layer | Source modules | Verified implementation level |
|---|---|---|
| USB/serial ELM transport | `vehicle/obd/adapters/usb_serial.py` | Implemented; test fixtures, hardware acceptance pending |
| Wi-Fi TCP ELM | `vehicle/obd/adapters/tcp_wifi.py` | Implemented; physical VCI acceptance pending |
| BLE GATT ELM | `vehicle/obd/adapters/ble.py` | Implemented; adapter-specific TX/RX UUID needed |
| ELM327 generic OBD | `vehicle/obd/client.py`, `vehicle/obd/protocols/elm327.py` | Commands/PIDs 010C,0105,010D,0111, DTC 03, VIN 0902; tested with simulator |
| CAN / ISO-TP / UDS | `vehicle/can/`, `vehicle/isotp/`, `vehicle/uds/` | Software components and simulated tests; per-ECU physical setup unproven |
| J2534 PassThru | `vehicle/j2534/`, `vehicle/adapters/j2534.py` | Windows driver interface exists; hardware/vendor testing pending |
| Backend VCI | `backend/device/manager.py` | Previously simulator-only, including synthetic VIN/RPM values |
| Backend vehicle diagnostic HTTP | `backend/vehicle_diagnostic/service.py` | Deterministic simulator, explicitly NOT all real vehicle protocols |
| Android transport | Kotlin USB/Bluetooth/Wi-Fi adapters | Device-local, limited generic ELM commands; platform hardware tests pending |
| iOS transport | CoreBluetooth BLE discovery | Not equivalent to full real OBD service; adapter-specific GATT not complete |

**Important duplication found:** `finalbuild/vehicle` provided the real shared
drivers while `finalbuild/backend/vehicle` contained placeholder modules.
A compatibility shim now points the backend import path to the single canonical
`finalbuild/vehicle` implementation. This directory is backend-domain Python
code, NOT a separate client-specific protocol engine.

## 2. OBD/network classification and scope

| Protocol / family | Typical area | Added status |
|---|---|---|
| SAE J1850 PWM / VPW | Legacy North-American emissions OBD | ELM adapter-dependent, no per-VIN assignment |
| ISO 9141-2 K-Line | Legacy emissions OBD | ELM adapter-dependent |
| ISO 14230-4 KWP2000 slow/fast init | Legacy emissions OBD | ELM adapter-dependent |
| ISO 15765-4 11/29 bit CAN 250/500 kbit/s | Standard CAN-based emissions OBD | ELM adapter-dependent |
| SAE J1939 250/500 | Heavy-duty/commercial | 250 variant ELM-dependent; no full SPN/FMI app implementation claimed |
| ISO 14229 UDS on DoCAN | ECU diagnostics | Basic core simulator/software implementation, OEM addressing unknown |
| ISO 14229 UDS over DoIP / CAN FD | Modern ECU diagnostics | Metadata only, not a working adapter claim |
| ISO 27145 WWH-OBD | Heavy-duty standards | Metadata only |
| SAE J1979-2 OBDonUDS | Newer regulatory interfaces (market-specific rollout) | Metadata only; never assigned from year alone |
| VW KW1281 / SAE J2411 SWCAN / LIN / FlexRay / J1708 | Manufacturer/subsystem/legacy | Metadata only; not generic ELM vehicle compatibility |

The backend reports **21 named definitions** covering these categories.
Only read-only standard OBD PID 00 replies count as observed ECU
communication in the new `elm327_probe.py`. A bare `ATDPN` result is
*adapter-reported*, not ECU verified.

**Never use guessed protocol candidates to send manufacturer-specific write,
coding, erase-DTC, seed/key/security-access, immobilizer or programming
commands.** No such operations are added.

### Regional heuristics
- US covered passenger/light-duty MY2008+ → CAN OBD is expected; 11/29 ID must be auto-detected.
- US MY1996–2007 → older J1850, ISO 9141-2, KWP2000 or emerging CAN; make/era is a weak ordering hint.
- EU/EEA EOBD applicability depends on fuel, vehicle category, registration and year; the catalog offers candidates, not an exact protocol assertion.
- BEV emissions-OBD support is **not assumed**; manufacturer-specific networks differ.
- Heavy-duty J1939, ISO 27145 and J1979-2 have their own compliance scope. US/CARB schedules are not applicable worldwide.

Authoritative references:
- Elm Electronics: https://www.elmelectronics.com/products/ics/obd/
- Snap-on global OBD protocol documentation:
  https://www.snapon.com/DiagnosticsManuals/Help/OBDII/Content/Common/Help%20Topics/OBD/Protocol%20Selection.htm
- ISO 27145 WWH-OBD: https://www.iso.org/obp/ui/
- CARB J1979-2 heavy-duty guidance: https://ww2.arb.ca.gov/sae-j1979-2-guidance
- EU emissions-OBD law: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A01970L0220-20070101

## 3. Global vehicle list and engine accuracy

Existing repository assets:
- `data/vehicle_catalog.json`: **30 makes**, hundreds of global *model-family*
  records, multi-year ranges and broad engine-family/fuel descriptions.
- `data/vehicle_fitments.json`: **22 curated make/model/chassis combinations**
  with sample engine/ECU labels and limited year coverage.
- `shared/vehicle_catalog.json`: **369 offline example rows**, not global data.

New backend endpoints expose these **separately with an explicit scope**.
NHTSA vPIC optional real-time APIs can find additional makes/models, and decode
a 17-character VIN for manufacturer-submitted *engine information*. NHTSA's
VIN coverage is US intended-sale/import and may be incomplete for Armenia,
Japan-domestic and other world-market vehicles. No engine-family hint is
promoted to an exact OEM VIN fitment without evidence.

NHTSA API official documentation: https://vpic.nhtsa.dot.gov/api/Home/Index

## 4. Real car images / Wikipedia/Wikimedia licensing

The generated 22 model PNG portraits already existed in the repository and
are now served through a backend **fallback** endpoint so clients need not
independently decide which portrait to show. They are **not OEM photos**.

`/photo` queries the **Wikimedia Commons API**, not a scraped article page.
It requests only appropriately licensed image metadata, returns title, author,
source file page, license and license URL, and marks the model photo
`candidate_unverified`. No candidate is silently included in APK/IPA/EXE.
Search title matching is not sufficient to verify trim, body style, market or
exact model year. No photo is returned when no suitably named/free-licensed
candidate is available.

Before distributing a chosen photo, manually inspect the file page, actual
attribution, allowed use and share-alike conditions. Creative Commons
attribution (title, author, source, license) guidance:
https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse

## 5. Canonical Backend contract for ALL three UI clients

| Route | Responsibility |
|---|---|
| GET /api/v1/vehicle-registry/stats | Data scope and counts |
| GET /api/v1/vehicle-registry/makes?q= | Local seeded global makes |
| GET /api/v1/vehicle-registry/models?make=...&year=... | Model family / years / engine-family guidance |
| GET /api/v1/vehicle-registry/fitments?make=...&model=... | Curated chassis/engine/ECU *hints* |
| GET /api/v1/vehicle-registry/vpic/makes | Optional live vPIC make discovery |
| GET /api/v1/vehicle-registry/vpic/models?make=...&year=... | Optional live vPIC model discovery |
| POST /api/v1/vehicle-registry/vin | NHTSA VIN/engine decode; user must consent to upstream request |
| GET /api/v1/vehicle-registry/protocols | Full protocol taxonomy and support level |
| GET /api/v1/vehicle-registry/compatibility?year=...&market=... | Unverified candidate ordering and any reported ELM code |
| GET /api/v1/vehicle-registry/detected-elm?raw=A6 | Normalize observed ATDPN, no fabricated ECU proof |
| GET /api/v1/vehicle-registry/portrait?make=...&model=...&chassis=... | Backend-generated portrait PNG / fallback |
| GET /api/v1/vehicle-registry/photo?make=...&model=...&chassis=... | Attribution/license-aware Commons *candidate* metadata |
| GET /api/v1/devices/{device_id}/obd/protocol | **Physical local VCI opt-in only** read-only ELM probe |

Desktop, Android and iOS have thin API methods for this contract. Their
presentation, OS permission handling, graphics and raw USB/BLE/Wi-Fi bridge
remain platform-specific. **Full migration of existing native make/model
selection screens away from their legacy local fallback lists is NOT complete
and is a separate release gate.** A mobile phone's BLE/USB radio cannot be
controlled by a remote cloud FastAPI process; its native bridge must continue
to own physical transport while backend owns data and diagnostic logic.

## 6. Local testing (NO CI/CD)

From `finalbuild` on the feature branch:

```bash
python -m pytest -q \
  tests/vehicle/protocol/test_registry_catalog.py \
  tests/vehicle/protocol/test_elm327_probe.py \
  tests/vehicle/test_global_catalog_registry.py \
  tests/vehicle/test_vehicle_external_registry.py \
  tests/vehicle/test_canonical_vehicle_core.py \
  tests/vehicle/devices/test_optin_vci_backend.py \
  tests/api/test_vehicle_registry_routes.py

python -m pytest -q tests/vehicle tests/api
bash scripts/run_full_desktop_qa_git_bash.sh --coverage-90
```

With local backend running, examples:

```bash
curl -fsS http://127.0.0.1:8001/api/v1/vehicle-registry/stats
curl -fsS "http://127.0.0.1:8001/api/v1/vehicle-registry/models?make=Mercedes-Benz&year=2006"
curl -fsS "http://127.0.0.1:8001/api/v1/vehicle-registry/compatibility?year=2006&market=EU&make=Mercedes-Benz"
curl -fsS "http://127.0.0.1:8001/api/v1/vehicle-registry/photo?make=Mercedes-Benz&model=E-Class&chassis=W211"
```

Optional local **physical** USB/BLE/Wi-Fi backend VCI (not cloud):

```bash
export AI_CAR_ENABLE_PHYSICAL_VCI=1
export AI_CAR_BACKEND_HOST=127.0.0.1
python -m apps.desktop.main --with-backend
```

Physical adapters require installed drivers, OS permission, supported
connection type, and relevant hardware. The feature still requires a genuine
OBD protocol observation on multiple model/year/market examples. Do not
confuse unit/simulator results with hardware compatibility.

## 7. Outstanding blockers before main merge/release

1. **Windows packaged FastAPI:** check new shared vehicle import/shim and
   bundled JSON/image assets in `backend_service.exe`.
2. **Physical hardware:** run USB ELM adapters with legacy K-Line and modern
   CAN vehicles, optionally J2534; capture ATDPN and real 41 00 replies.
3. **Backend DB:** exercise PostgreSQL and SQLite with old catalog endpoints
   plus new registry endpoints; avoid huge unfiltered flattened-year exports.
4. **Android/iOS:** compile on real Android toolchain / Xcode and use new
   backend registry in vehicle pickers (legacy offline hardcoded fallbacks remain).
5. **Model photos:** manually license/verify Commons candidates; show credit
   in three UIs, and keep offline fallback art.
6. **Coverage:** new Python files lower global coverage until tests are run.
   No new test PASS or ≥90% gate claim is made before local verification.

**Status:** implementation and unit tests added to feature branch;
runtime results and hardware verification **PENDING**. No CI/CD invoked.
