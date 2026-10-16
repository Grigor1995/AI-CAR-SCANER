# Pre-build code and file cleanup — 2026-10-16

## Status and review method

Repository: `Grigor1995/AI-CAR-SCANER`. Changes applied to `main`.
Cleanup was based on the GitHub repository tree, direct source inspection,
existing packaging contracts, documentation, and searches for file references.
The user's private local working tree is **not accessible** through the GitHub
connector. No Windows build, local pytest run, emulator, or Xcode test was
executed during this cleanup. No CI workflow was dispatched.

This is a **non-destructive cleanup of confirmed obsolete code**, not a
claim that the entire codebase is now defect-free.

## Removed after checking references

| Deleted file | Why removal was safe |
| --- | --- |
| `apps/desktop/AICarScanner.spec` | Duplicate of the canonical `apps/desktop/specs/AICarScanner.spec`; supported builders and packaging tests refer to the nested spec |
| `test+llm.py` | Old standalone scratch script importing `llama_cpp`, which conflicts with the current external `llama-server.exe` runtime; no tracked callers found |

Git history retains these files; they can be recovered if needed.

## Code cleanup and fixes

1. `apps/desktop/api_client.py`: when no explicit `AI_CAR_BACKEND_URL`
   is set, the Desktop client now uses `AI_CAR_BACKEND_PORT` (default
   `8001`) like the launcher; this closes the silent custom-port mismatch.
2. `apps/desktop/tests/test_api_client.py`: tests for default port,
   custom port, explicit environment URL and explicit constructor URL.
3. `tests/desktop/test_phase32_ports_and_timeout.py`: now verifies the
   Desktop API client agrees with the launcher when port `8002` is selected.
4. `apps/desktop/specs/AICarScanner.spec`: no longer packages whichever
   arbitrary `llama-server.exe` is found on the builder's PATH into the
   one-file GUI. The optional server remains a separate runtime dependency
   handled by the standalone build script. Removes redundant packaged
   `assets/ai-car-scanner-icon.png`; Qt uses the dedicated Desktop PNG,
   WEBP and ICO files.
5. `apps/desktop/verify_icons.py`: corrects the help text to use the
   real source-mode icon-check command instead of an unsupported
   `AICarScanner.exe --verify-icons` switch.
6. `.github/workflows/ci.yml`: replaces `python apps/desktop/test_smoke.py`
   (which only defines a pytest test and performs zero checks) with
   `python -m pytest -q apps/desktop/test_smoke.py`.
7. `apps/desktop/test_smoke.py`: includes the icon preparer, icon verifier
   and backend worker in the AST syntax checks.
8. `apps/desktop/README.md`: clarifies how to invoke the Desktop smoke
   check.
9. `finalbuild/README.md`: removes five broken links to absent historical
   phase documentation and points to present architecture files; documents
   the isolated Windows icon preview workflow.

## Deliberately retained, not automatically deleted

| Candidate | Reason for retaining |
| --- | --- |
| `vehicle/` and `backend/vehicle/` | Real import paths and tests depend on different responsibilities; superficial directory-name similarity is not proof of duplication |
| `scripts/seed_vehicle_catalog.py` and `backend/scripts/seed_vehicle_catalog.py` | Different inputs/ID schemes/database write behavior; reconciliation requires an explicit migration plan, not file deletion |
| `data/vehicle_catalog.json`, `data/vehicle_fitment_catalog.json`, `data/vehicle_fitments.json`, `shared/vehicle_catalog.json` | Active sources/fallbacks; consolidation must preserve contracts and offline behavior |
| `apps/web/README.md` | Future web UI placeholder, no runtime cost; preserved instead of arbitrarily deleting planned feature space |
| `apps/desktop/build_windows.ps1` | Compatibility wrapper around the canonical script; harmless and may be called outside tracked scripts |
| Platform-specific Android launcher resources / iOS icon asset | Required by native platform packaging; apparent binary duplication is expected |
| `report.md` and historical architecture docs | Prior evidence and design decisions; do not rewrite history as if tests were re-run |

## Verification checklist before the Desktop build

From `finalbuild` with Python dependencies installed:

```powershell
python -m pytest -q apps/desktop/test_smoke.py
python -m pytest -q apps/desktop/tests/test_api_client.py tests/desktop/test_phase32_ports_and_timeout.py
python -m pytest -q apps/desktop/tests/test_prepare_windows_icon_coverage.py
python -m pytest -q tests/desktop/test_phase25_standalone.py
python -m pytest -q apps/desktop/tests --ignore=apps/desktop/tests/test_ui_widgets.py
```

Then run the normal backend suite and review failures. The historical
PySide6 widget-teardown crash is unresolved by this cleanup and remains a
separate task. The native Windows `AICarScanner.exe` has **not** been
launched or smoke-tested here.

The icon-preview build remains **manual-only**:
`scripts/build_windows_icon_preview.ps1` or
`Actions → Windows Desktop Icon Preview → Run workflow` after these
checks are complete. No builder output ZIP is claimed at cleanup time.

## Release gating

**Code/file cleanup applied; runtime validation pending; Windows build
not started.** Do not treat the static review or committed tests as passed
test executions. After validating the targeted suites, proceed to an
isolated Windows x64 builder run, inspect native executable icons, and
manually verify the GUI opens without the historical segmentation fault.
