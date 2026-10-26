# Branch integration and cleanup audit — 2026-10-26

Repository: `Grigor1995/AI-CAR-SCANER`. Target branch: `main`.
Review was based on GitHub comparisons, current sources and available CI metadata. It was **not** a complete local Windows/Android/iOS test run.

## Merge result

| Source branch | Assessment against main | Decision |
|---|---|---|
| `docs/mobile-ui-demo-screenshots-20261026` | 3 commits ahead, 0 behind before integration; native Compose screenshots included in an updated 10-page demo PDF | Merged via #24; eligible for deletion |
| `integrate/branch-audit-cleanup-20261026` | New branch from current main; targeted Desktop slider features and tests | Merged via #27; eligible for deletion |
| `feature/backend-unified-vehicle-obd-audit-20261022` | No unique commits; 55 behind | Already included; eligible for deletion |
| `feature/neon-ui-desktop-android-ios` | No unique commits; 143 behind | Already included; eligible for deletion |
| `fix/desktop-v1-fastapi-recovery-20261021` | No unique commits; 138 behind | Already included; eligible for deletion |
| `fix/mobile-desktop-catalog-parity-20261022` | No unique commits; 24 behind | Already included; eligible for deletion |
| `design/neon-3d-ui-review-20261023` | 19 old commits diverged from current main; conflicts with modern 3D Desktop/mobile changes | Draft #25 retained, not directly merged; current main already has newer UI, and missing Desktop sliders were ported in #27 |
| `feat/backend-obd-vehicle-registry-20261022` | 43 commits ahead, 91 behind at audit; differs from the newer OBD routes, discovery, acquisition/reconnect, catalog logic | Draft #26 retained for careful reconciliation; **do not force merge or discard unique commits** |

## Functional notes

- PDF #24 preserves its five Desktop pages and appends five pages containing ten committed Android Compose rendering captures. These are fixture-based Robolectric native-graphics captures, **not physical phone or emulator screenshots**. No iOS capture was fabricated.
- PR #27 cherry-ports the missing neon-themed Desktop Live Data simulator sliders, keeping the latest Desktop launcher and layout. Includes an added regression test (not asserted to have run successfully).
- The design review branch contains experimental Qt gradients/icon code, but replacing current production UI files with its older versions would undo newer navigation, icon, and responsive-layout changes.
- The backend audit branch includes vehicle/protocol knowledge modules not in main and older route alterations. Main meanwhile has `backend/api/obd_routes.py`, `backend/obd/protocols.py`, current `vehicle/diagnostic_discovery.py`, and a separate Oct 26 OBD audit. Integration requires a conflict-by-conflict code review and targeted tests.
- Recent Desktop Full QA workflow runs on main had failures. **No green CI gate is claimed for these integrations.**

## Cleanup policy

Only delete branches whose head commit is an ancestor of current main. Do not delete `main`, `design/neon-3d-ui-review-20261023`, or `feat/backend-obd-vehicle-registry-20261022` while their unique work remains unmerged. Never force-push or rewrite shared history.

A one-time GitHub Actions workflow can remove the six known fully merged branches, but only after checking each branch tip is an ancestor of main. If Action permissions/runners block the workflow, deletion must be run with a permitted GitHub account. Keep PR #25/#26 as drafts until the conflicting implementations are reviewed and tested.
