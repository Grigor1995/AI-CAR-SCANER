# Expanded generation portraits and read-only protocol support

Date: 2026-10-22. Baseline: `ec4c103`.

## Vehicle selection and images

The shared selection catalog expands from **50 to 70 generation references**,
with **199 named engine options**. The 20 additions include Corolla E210,
Camry XV70, RAV4 XA50, Prius XW50, Land Cruiser J200, Civic FC/FK, CR-V RW/RT,
Rogue T32, Sentra B17, C-Class W205, BMW 5 Series F10/X5 F15, Elantra AD,
Sportage QL, Jetta A6, Lexus ES XV60, Mazda6 GJ, Audi Q5 8R and Lada Granta/Vesta.

All **70 references have a distinct transparent RGBA PNG**. There are 51 newly
generated illustrations, including one replacement of an existing portrait.
Original generation files were copied without changing their pixels. The
manifest `data/generated_vehicle_portraits.json` records image hashes,
dimensions, generator and source asset IDs. These are AI illustrations,
not actual manufacturer photographs or certified trim/geometry references.

The scope is the application's seeded generation selector, not every model in
the broader global research registry or arbitrary user-created profiles.
Year ranges and engine combinations remain explicitly unverified selector
candidates. Selecting a model does not establish engine fitment or bus support.

Images live in `assets/vehicle_models` and are served by the backend. Existing
native offline caches remain available; the updated Elantra AD cache is synced
across Desktop/Android/iOS. The 50 additional files do not need to be copied
into every mobile package. A running, updated backend supplies them to the
existing native image loaders. Docker and frozen-backend specs already include
this canonical asset directory. Restart the backend after updating source.

Audit or register image-generator outputs from `finalbuild/`:

```bash
python scripts/vehicle_portraits.py --audit
python scripts/vehicle_portraits.py --import-manifest /path/to/generated-records.json
```

Import records are objects with `id` and `path`. The importer validates complete
RGBA files and rejects duplicate references/identical illustrations before
copying. It preserves the originals. The audit checks all seeded references
for missing assets, transparency and duplicate file hashes. It does not certify
that generated styling exactly matches every real production variant.

## Implemented capabilities

| Family | Implemented behavior | Boundary |
|---|---|---|
| ELM generic OBD-II | Existing auto, J1850 PWM/VPW, ISO 9141-2, KWP slow/fast, four ISO 15765 CAN selections; shared PID/DTC/VIN decoding | Adapter implements the electrical bus; negotiated ECU support still required |
| UDS on classical CAN via ELM | New explicit 11-/29-bit CAN addressing/filter configuration, UDS 22 and 19/02, validated service/DID responses | Complete generic PID-00 evidence and observed CAN required; not EV/non-emissions discovery; no extended/mixed ISO-TP addressing |
| ISO 13400 DoIP TCP | New routing activation, diagnostic acknowledgements, alive responses, bounded response-pending handling, UDS 22/19 reads | Explicit gateway and logical ECU/tester addresses; no UDP discovery, TLS-only gateway authentication, OEM routing/authentication or security bypass |
| SAE J1939-73 | New passive DM1/DM2 SPN/FMI/occurrence/lamp decoding, including complete TP.BAM captures | No active bus acquisition/request driver or RTS/CTS; legacy conversion-method SPNs remain raw |
| SAE J1708/J1587 | New passive checksum, MID and fixed/variable/extended PID framing | Complete captured packet required; no electrical driver, timing/arbitration or OEM parameter scaling |
| CAN FD, WWH-OBD, OBDonUDS, proprietary OEM networks | Registry describes their scope and prerequisites | Wire drivers/regulatory DID profiles remain unimplemented; metadata is not support |

ELM UDS holds one lock across header/filter changes, response and restoration.
Generic polling cannot interleave commands under a different ECU header.
After the read, the original generic initialization is restored; failed
restoration disconnects the adapter. UDS pending-only, negative, mismatched or
truncated replies are rejected. DoIP connections close on completion, error,
timeout or cancellation. Read requests never send DTC clear, security access,
actuator, coding or programming services.

## Shared backend APIs

All advanced operations live in the backend. Native clients provide byte IO
and presentation; there are no new diagnostic formulas in Android/iOS.

| POST endpoint | Input |
|---|---|
| `/api/v1/obd/uds/elm/read` | `device_id`, explicit `request_id`/`response_id`, exactly one `did` or `dtc_status_mask` |
| `/api/v1/obd/uds/doip/read` | Reachable `host`, optional `port`, `source_address`, `target_address`, exactly one `did` or `dtc_status_mask` |
| `/api/v1/obd/j1939/decode` | One `arbitration_id` and hex `data` |
| `/api/v1/obd/j1939/decode-bam` | `frames`: ordered list of announcement/data CAN frames with `arbitration_id` and hex `data` |
| `/api/v1/obd/j1708/decode` | Hex `data` including the checksum |

DoIP example, with addresses deliberately supplied by the operator rather
than guessed from a vehicle name:

```json
{
  "host": "192.168.0.10",
  "port": 13400,
  "source_address": 3584,
  "target_address": 1,
  "did": 61840,
  "timeout": 5
}
```

`61840` is hexadecimal `F190` (VIN DID). The example addresses are not a
vehicle-specific connection prescription. Advanced reads return raw positive
UDS responses; no generic interpretation of arbitrary OEM DIDs is invented.
Passive frame decoding cannot prove that the frames came from a real ECU.
Advanced operations do not automatically append DTCs/evidence to a diagnostic
session or claim complete ECU/network coverage.

## Validation

Loopback tests exercise real TCP framing for DoIP and ELM, routing refusal,
acknowledgements/alive checks, response pending, negative/mismatched replies,
truncation, wrong CAN width, generic OBD restoration and command serialization.
Capture fixtures cover J1939 BAM sequence/source/padding failures and J1587
checksum/parameter boundaries. No physical vehicle or adapter validation was
performed. iOS device/Xcode validation remains unavailable on this Linux host.

Reference standards: ISO 13400-2 (DoIP), ISO 14229-1 (UDS), ISO 15765-2,
SAE J1939-21/-73, SAE J1708/J1587, and the linked ELM command documentation in
[the original audit](REAL_OBD_AUDIT.md). Implementation tests establish only
specified code behavior, not certification to those standards.

## Executed results

| Check | Result |
|---|---|
| Root Python suite | 802 passed, 2 skipped |
| Selected new advanced protocol/API modules | 93.31% combined coverage; 90% gate passed |
| Desktop isolated regression matrix | 387 passed, 1 skipped; source/core coverage 90.42% / 91.39% |
| Portrait inventory | 70/70 available, transparent, distinct hashes |
| Native portrait packaging regression | 6 passed |
| Real FastAPI source process startup | Passed |
| Android unified debug build, unit tests and lint | Passed; 91 JVM tests, no device execution |
| iOS | Swift syntax only; no Xcode/device run |

The Python and Desktop suites overlap; counts are not unique totals. Coverage
is scoped to `vehicle.doip`, `vehicle.uds.read_only`, `obd.j1939`, `obd.j1587`
and `api.advanced_obd_routes`, not all vehicle protocols or the entire repository.
The UDS decoder's existing confirmed-DTC flag was also corrected to use ISO
14229 status bit 3; bit 0 (`testFailed`) alone is not a confirmed DTC. Regression
cases distinguish pending, failed, confirmed and warning-indicator states.

The local Android APK was 53,879,592 bytes, SHA-256
`64191536fb771c345078a902185c0c92ed45e317deb65fe567e6e08f97827e14`.
It is a build-validation artifact, not a published release binary.

Reproduce from the repository root:

```bash
python -m pytest -q --cov=vehicle.doip --cov=vehicle.uds.read_only --cov=obd.j1939 --cov=obd.j1587 --cov=api.advanced_obd_routes --cov-fail-under=90
```
