# Full repository audit and cleanup — 2026-10-22

Baseline: `5cccbc2`. Scope: all Git-tracked files, including Desktop, backend,
Android, iOS, tests, assets, scripts, CI, deployment configuration and docs.

The [file/declaration inventory](repository-inventory-2026-10-22.csv) records
670 surviving baseline files, sizes, SHA-256 hashes and named declarations.
Python uses AST parsing: 367 files, 461 classes and 2,299 functions/methods,
including tests. Kotlin/Swift declaration lists are lexical inventories;
compilation/syntax checks are separate below. The inventory excludes these two
new audit deliverables and generated/ignored SDKs, caches, environments and
build outputs. This is a snapshot, not a claim that every execution path ran.

## Removed after checking repository references

| Area | Cleanup |
|---|---|
| Python | 85 unused/duplicate imports, another import made obsolete by class removal, unused local bindings and an unreachable return |
| Classes/functions | 16 unused Python classes and 18 associated/standalone functions or methods, including two duplicate test functions; all removed declarations had their consumers checked |
| Unused files | `backend/platform/tenant.py`, `device/device-services/device_service.py`, `device/sdk/device_sdk.py`; these disconnected placeholders were not used by active tenant authorization, device connections or native clients |
| AI | Unimplemented `CloudLLMProvider`/`OpenAICompatibleProvider` placeholders and unused `ai/rag/quality_defaults.json`; actual HTTP OpenAI-compatible and llama-server providers remain |
| Domain helpers | Unused Timer, Technician, ReportRequest, AndroidDeviceInfo, SimulatorAdapter, FlowControl and AcquisitionError declarations; unused UDS ecu_reset wrapper |
| Duplicate tests | Removed `tests/ai/test_phase32_llama_server_config.py`, which was byte-identical to `test_phase31_llama_server.py`; retained both unique assertions and made the URL default test independent of LLM_BASE_URL |
| Android code | Unused CreateSessionRequest DTO, LiveDataTile composable and three imports |
| Android resources | Eight unused icons: app_icon.webp plus seven ic_launcher_round variants; both manifest icon fields already reference ic_launcher |
| Dependencies | Removed unused core pydantic-settings/NumPy, unused Android navigation-compose/ui-tooling-preview, and redundant dev PyYAML entry; optional embedding dependencies remain separate |

Thirteen whole tracked files were removed. The function/declaration counts
include methods inside removed classes; they are not counts of separate
files. Test count fell by exactly two because of the byte-identical duplicate.

## Preserved after checking dynamic use

- FastAPI route decorators, Pydantic validators, Qt paintEvent, HTMLParser and
  HTTP server callbacks, pytest fixtures/tests, SwiftUI @main/CoreBluetooth
  callbacks, Kotlin delegated-property operators and LruCache overrides.
- Package API re-exports: added explicit __all__ declarations and made
  api.state.vci_manager an explicit re-export; routes import it from there.
- SQLAlchemy models: metadata/schema registration is a consumer even when a
  class name has no direct call site. Existing databases/schema remain intact.
- J2534 driver seams and transport interfaces: optional hardware integration
  contracts; unused parameters are part of those interfaces.
- Standalone build/diagnostic scripts, release acceptance tooling, historical
  evidence, PPTX/demo source and images, active offline catalogs and native
  asset copies. Directory-name similarity is not proof of duplication between
  vehicle/ and backend/vehicle/.
- httpx2: Starlette TestClient imports it dynamically. A clean installation
  exposed its use; it remains a dev requirement. NumPy may still be installed
  transitively when optional embedding providers are selected.

Static name/reference checks are evidence for review, not automatic permission
to delete framework hooks, schema registrations or external integration APIs.

## Maintenance fixes

- Added the narrow F401/F811/F821/F841 Ruff gate to CI; all checks pass.
- Corrected CI coverage targets for global_data and ai.live_analysis. The old
  file-like targets emitted module-not-imported warnings and omitted them.
- Qt widget tests are now a required CI step; removed the obsolete tolerated
  failure setting after the lifecycle fix and passing matrix verification.
- CI also reacts to root build.py/pytest.ini changes.
- Ignored generated Android .kotlin directories; fixed the broken documentation
  link to device components; updated the dependency map.

## Validation

| Check | Result |
|---|---|
| Clean Python environment installed from requirements | PASS; core runs without numpy/pydantic_settings |
| Full Python suite with external LLM URL/provider in the shell | **589 passed, 2 skipped** |
| Backend/core CI coverage selection, including corrected modules | **95.89%**, required >=90%; no module-not-imported warnings |
| Desktop five-group regression matrix | **384 passed, 1 skipped**, all groups PASS |
| Desktop core/source coverage | **91.17% / 90.20%** |
| Real source FastAPI subprocess startup | **PASS**, readiness reached |
| Unified Android builder with tests | **PASS**, APK produced |
| Android compileDebugKotlin / compileDebugAndroidTestKotlin | **PASS** |
| Android JVM tests | **89 passed, 0 failures/errors** |
| Android assembleDebug / lintDebug / unit coverage generation | **PASS**; 12 lint warnings, 0 errors, 0 UnusedResources findings |
| Swift parsing | **10 files PASS** |
| Python/spec AST, JSON, YAML, XML/plist/SVG and bash -n | **PASS** |
| Internal backend import graph / selected Ruff checks / diff whitespace | **PASS** |

Desktop and root suites overlap; their counts must not be summed as unique
cases. Remaining skips cover optional PostgreSQL integration and Windows-only
owned-process cleanup. No physical OBD device/emulator tests, Windows frozen
EXE build, PowerShell execution, or native Xcode typecheck/XCTest were run on
this Linux host. Swift syntax parsing is not native iOS build validation.
