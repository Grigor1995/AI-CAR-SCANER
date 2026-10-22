# Branch analysis and integration — 2026-10-22

## Inputs and target

All remote heads were fetched and inspected. The checkout originally fetched
only `main`, so an explicit `refs/heads/*` fetch was required to see both work
branches. Integration targets `main`; source branches are retained.

| Branch | Audited tip | Initial divergence from main |
|---|---|---|
| `main` | `32d44770027018c28ec803e5852169a3d7cfdfb1` | Baseline: current native UI, diagrams, translations, Session ID privacy, demo deck |
| `feature/neon-ui-desktop-android-ios` | `4de32cd23a5e314405e800eedf014f44c2fd03c4` | 40 branch-only commits; missing 16 main commits |
| `fix/desktop-v1-fastapi-recovery-20261021` | `d6c41b3115bde03e806d317104f99e02fe88ab38` | 30 branch-only commits; missing main's latest privacy/demo commit |

Changes were integrated on `integration/all-branches-20261022`, with a real merge
commit for each branch. No force push, remote history rewrite, source-branch
deletion, or blanket `ours` merge strategy is used.

## Review and conflict decisions

### Current UI and privacy

The older neon branch overlaps substantially with the subsequently implemented
native dashboard. Retained the latest main Android/iOS renderers, PNG model
portraits, model selection behavior, light/dark themes, localization, Analysis
workspace, diagrams and Session ID privacy. Its SVG/WebView rendering proposal
would regress the newer image-switching/privacy flow and was superseded.

The 22 historical SVG illustrations per asset set remain packaged. Desktop
prefers an exact PNG portrait and can fall back to the matching SVG only when
that PNG is absent. Added tests for valid legacy SVGs, PNG priority and actual
SVG fallback rendering. Existing PNG transparency/native-client hash checks pass.
No WebView renderer was reintroduced into Android/iOS.

Session IDs remain internal to API calls, persistence and history routing. The
current UI/report-export privacy tests remain active. Removed the obsolete
branch test requiring the ID to appear in an exported PDF: the replacement
privacy regression verifies its absence while preserving P0302/report content.

### FastAPI recovery and packaging

Selected the newer recovery implementation from the fix branch:

- Bounded restart budget and exponential backoff for Desktop-owned local children.
- Cancellation-aware startup and orderly supervisor shutdown.
- Healthy external APIs and remote hosts are not taken over.
- Exact loopback hostname matching and launcher/child port synchronization.
- Backend health polling and reconnection without repeated modal error dialogs.
- Separate acquisition-not-started, missing-session and backend-offline states.
- Frozen backend hidden imports include dynamically loaded routers/domain modules
  and SQLite catalog seeding; GUI packaging retains PrintSupport, current panels,
  artwork and recovery imports. Duplicate hidden-import entries were removed.
- Release-readiness scripts require fresh real source/frozen startup and actual
  source crash/recovery evidence; gates were not weakened.

Added launcher regression tests confirming `--no-backend` starts neither local
services nor a recovery supervisor, and an explicitly selected OpenAI-compatible
runtime does not launch a competing llama-server.

### AI runtime

Preserved model discovery through `/v1/models`, distinct server/model readiness,
`/v1` URL normalization, selected-language inference prompts and asynchronous
thread offloading of blocking urllib inference. The OpenAI-compatible default
is LM Studio's loopback port 1234, separate from FastAPI's port 8001.

Found and fixed a cross-branch navigation mismatch: the outer Desktop stack
holds the application shell at index 0, so checking that stack for Live Data
index 4 prevented provider refresh after recovery. The callback now checks the
actual navigation selection. Added a regression using the real shell/navigation.

Also localized the newly introduced recovery/acquisition/missing-session labels
for Armenian and Russian and verified the displayed acquisition-error text.

## Final validation on the integrated source

| Check | Result |
|---|---|
| Main Python suite | **574 passed, 2 skipped**; no failures |
| Main Python coverage (`backend`, `vehicle`, `device`) | **97.41% statements; 87.48% branches** |
| Desktop isolated matrix | **383 passed, 1 skipped**; every process exits successfully |
| Desktop coverage | **90.19%** complete source inventory; **91.17%** production core (11 modules); both 90% gates pass |
| Real FastAPI source startup | **PASS**; actual loopback HTTP service, isolated SQLite, cleanup PASS |
| Real FastAPI crash/recovery | **PASS**; replacement PID differs, health restored, cleanup PASS |
| Android JVM + supplemental native UI | **89 + 14 passed** (103-case combined run); 0 failures |
| Android build | Debug APK and androidTest compilation PASS |
| Android lint | PASS; 0 errors, 21 existing warnings |
| iOS | 10 Swift files syntax-parse successfully; native runtime sources preserved from main |
| Python critical static checks | Ruff E9/F63/F7/F82: 0 findings; compileall passes |
| Release tooling syntax | Windows shell runner and PyInstaller specs compile/parse |

The Python skips are PostgreSQL/pgvector integration and Windows-only owned
process-tree cleanup. The latter is also counted in the overlapping Desktop
suite. Do not sum suite counts as unique test cases.

Native Android rendering checks use the supplemental cloud Robolectric/API-35
harness, not a physical device. Xcode/iOS simulator execution, Windows frozen EXE
runtime/build validation, live AI models and actual OBD hardware remain outside
this Linux validation. Static PyInstaller checks do not prove frozen startup.
The existing demo deck is a dated pre-integration snapshot, not a report of
these newly merged recovery/runtime changes.

## Reproduce from finalbuild

```bash
python -m pip install -r backend/requirements-dev.txt -r apps/desktop/requirements-dev.txt
QT_QPA_PLATFORM=offscreen AI_CAR_DISABLE_LLM_AUTOSTART=1 AI_CAR_USE_LOCAL_DATABASE=1 \
  python -m pytest tests -q --cov=backend --cov=vehicle --cov=device --cov-branch
python scripts/run_desktop_tests.py --min-coverage 90 --min-core-coverage 90
python scripts/test_fastapi_startup.py --mode source
python scripts/test_fastapi_recovery_integration.py
```

From `apps/mobile-android`:

```bash
./gradlew :app:testDebugUnitTest :app:createDebugUnitTestCoverageReport \
  :app:compileDebugAndroidTestKotlin :app:assembleDebug :app:lintDebug
```

Cloud artifacts: `/workspace/merge-review/` for main/static/Android logs and
Python JUnit/coverage; `finalbuild/desktop-test-reports/` for the Desktop matrix,
coverage, source startup probe and crash/recovery JSON/log evidence. Generated
coverage and runtime artifacts are not committed.
