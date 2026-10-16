# Repository audit and Windows icon-preview build — 2026-10-16

## Scope and evidence

Repository: `Grigor1995/AI-CAR-SCANER`; reviewed GitHub `main`, starting
from commit `4f75d7d050e2b4cfc2a22ea4b83933fee8e6fcd3`. The reviewed tree
contained **475 Git blobs and 160 directories**, including the native
Desktop, Android and iOS clients, FastAPI backend, AI/RAG components, vehicle
protocol libraries, device support, data catalogs, tests, and documentation.

Evidence method: GitHub file/tree inspection plus the previous root
`report.md` audit. No local user checkout was mounted; the local uncommitted
changes and whether the *latest* artwork was pushed cannot be established.
The `main` commit `4f75d7d` (2026-10-16 08:48 UTC) is confirmed to contain `assets: install D&A TOOL icons on iOS Android and Desktop`, including newly added Desktop master/ICO/PNG and Android and iOS icon assets. Newer uncommitted local artwork, if any, cannot be inspected from GitHub.

This audit does **not** claim any newly measured code coverage, test success,
Windows executable run, Android emulator run, or iOS simulator result.

## Component inventory

| Area | Present implementation | Main gap / required verification |
| --- | --- | --- |
| Backend | FastAPI routers, DiagnosticSession, catalog and telemetry | Contract tests, database readiness, access controls |
| Diagnosis | Deterministic rules, evidence provenance, next-test decisions | Golden cases and multilingual recommendation/results tests |
| AI | Local llama-server interface, RAG/embeddings and grounding foundations | LLM/RAG runtime, timeout and unavailable-provider behavior |
| Desktop | Python/PySide6 UI, API client, PyInstaller GUI and backend service | Clean Windows build and real GUI launch; historical segmentation fault |
| Android | Kotlin/Compose, API client, transport foundations | Emulator/instrumentation tests, UI states, launcher icons |
| iOS | SwiftUI app, XcodeGen project, XCTest | Simulator test/coverage and icon checks |
| Vehicle | CAN, OBD, ISO-TP, UDS, J2534 abstractions and simulators | Physical adapter validation |
| Data | Catalog JSON files, global data and persistent sessions | Duplicate source reconciliation and readiness |
| CI | Backend/Desktop/Android jobs; separate manual iOS workflow | Coverage scope and UI-release gates |

## Findings ranked by priority

### P0 — Desktop runtime verification missing

The previous Windows `AICarScanner.exe` was observed to exit with a segmentation
fault while `python apps/desktop/main.py` was able to open the GUI. Neither
a successful PyInstaller invocation nor source-level Qt tests demonstrate that
the built GUI executes correctly. A fresh binary needs both a smoke launch and
manual UI validation on Windows. The preview builder below verifies icons,
but does **not** claim to fix the historical runtime crash.

### P1 — Icon provenance and visual parity

The Desktop spec regenerates Windows ICO, Desktop PNG and WEBP from
`assets/AI-Car-Scanner-master.png` via `prepare_windows_icon.py`. The D&A TOOL icon commit is present on GitHub `main`. If any newer icon
exists only as an uncommitted local ICO/PNG or unmerged branch, a GitHub build
from `main` will not include those *later* local edits. The Android launcher and
iOS app icon have their own assets; exact visual parity still requires review.

The PySide6 UI formerly selected WEBP before PNG. The code now prioritizes
the generated PNG for reliable Qt decoding, keeping WEBP/ICO fallbacks.

### P1 — Packaging and verification controls

Desktop packaging uses two separate one-file PyInstaller specs, for
`AICarScanner.exe` and `backend_service.exe`. Both binaries must be shipped
together. There are two identical Desktop spec locations:
`apps/desktop/AICarScanner.spec` and
`apps/desktop/specs/AICarScanner.spec`. The canonical standalone scripts use
the nested spec, so the duplicate is technical debt.

The existing Desktop CI allows widget tests to fail
(`continue-on-error: true`) because of a known PySide6 teardown crash.
It gates only selected logic modules at 95% coverage; this is not 95% coverage
for the whole Desktop application.

### P1 — API / release-readiness gaps from prior audit

Prior review in `report.md` flagged un-enforced API authentication helpers,
session persistence scaling and concurrent-write risks, a liveness endpoint
that does not prove catalog/database readiness, and metric fields that can
give misleading zero values. These are not fixed by a Windows packaging
workflow, and the current review did not rerun endpoint/security/performance
tests to establish remediation.

### P2 — Incomplete cross-platform gates and product parity

The GitHub CI has a 90% gate only over a selected backend module list; the
whole-backend run reports coverage without a matching global threshold.
Android collects coverage without a configured numerical gate; iOS XCTest is
manual-only with no numerical gate. Continue enforcing actual behavior with
an end-to-end diagnostic test on every platform before release.

The previous audit describes inconsistent Android/iOS catalog offline
fallbacks and localization / information-gain / estimated-cost handling.
These remain verification targets, not confirmed new failures.

## New Desktop icon-preview build

Added:
- `scripts/build_windows_icon_preview.ps1`: isolated Windows x64 build,
  separate `build-release/icon-preview` and `dist-release/icon-preview`,
  both GUI and backend executable, source-icon test suite, native icon check,
  ZIP distribution, and a generated JSON icon report;
- `apps/desktop/verify_icons.py`: Pillow integrity, PNG-versus-WEBP pixel
  equality, ICO 256x256 frame, Qt QIcon decoding and Windows embedded-EXE
  icon resource checks;
- `.github/workflows/desktop-icon-preview.yml`: **manual-only** hosted
  Windows builder, with artifacts retained for 14 days;
- `apps/desktop/ui.py`: prefer PNG for app/window icon.

The icon preview checks image packaging and the Windows executable resource.
It does **not** auto-launch the complete GUI; the downloadable README
describes how to open the app and inspect the titlebar, taskbar and Explorer
icons manually. It does not bundle proprietary model weights or a
`llama-server.exe` binary.

### Run locally

From the `finalbuild` directory in Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_windows_icon_preview.ps1
```

Result:
- `dist-release/AICarScanner-icon-preview.zip`
- `dist-release/icon-preview/AICarScanner.exe`
- `dist-release/icon-preview/backend_service.exe`
- `dist-release/icon-preview/desktop-icon-report.json`

The script does not alter the existing `dist/` folder or the
`dist-release/` files outside `icon-preview/` and the dedicated ZIP.
It does regenerate the three Desktop icons in `assets/` from the Desktop
master PNG; ensure that master contains the desired new icon before running.

### Run through GitHub Actions

After the desired icon source has been committed to `main`, open:
`Actions → Windows Desktop Icon Preview → Run workflow → main`.
This is deliberately **not** configured for automatic push or PR runs, to
avoid unexpected hosted-Windows runner consumption.

Download `AICarScanner-Windows-x64-Icon-Preview` from the workflow run.
Do not mark the build successful until the workflow finishes and the JSON
report says `PASS`.

## Verification status as of this report

| Verification | Status |
| --- | --- |
| GitHub source, assets and workflow configuration inspected | Completed |
| New builder, verifier and workflow committed | Completed |
| D&A TOOL icon source committed on GitHub main | **Confirmed** (`4f75d7d`) |
| Any newer unpublished icon changes in user's local working tree | Unknown |
| Python tests on new source | **Not run** |
| Windows PyInstaller build | **Not run** |
| Native icon test on compiled executable | **Not run** |
| Actual packaged GUI launch/crash regression | **Not run** |
| Backend integration and full tests | **Not run** |
| Android / iOS builds and tests | **Not run** |
| Actual coverage percentages | **Not measured** |

**Release decision: not release-ready until the Windows preview is built,
icons are visually checked on a real Windows desktop, the packaged GUI crash
is resolved, and the broader release gates are green.**
