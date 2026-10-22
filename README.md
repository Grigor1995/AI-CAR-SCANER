# AI-CAR-SCANER

Evidence-driven automotive diagnostic platform with a shared FastAPI backend, deterministic diagnostic rules, evidence-based hypotheses, optional AI/RAG assistance, vehicle simulation, and native client applications.

[Release notes](RELEASE_NOTES.md)

## Supported clients

- **Desktop:** Python + PySide6 workstation (finalbuild/apps/desktop).
- **Android:** native Kotlin + Jetpack Compose app (finalbuild/apps/mobile-android).
- **iOS:** native Swift + SwiftUI app (finalbuild/apps/mobile-ios).

The repository uses native client implementations. The browser/PWA client and its static Render deployment have been removed. The legacy Flutter client sources and their build scaffolding have been removed.

## Build all native apps

One entrypoint: `python build.py`. Run `python build.py --check` to verify native
toolchains. On Windows, build locally with `python build.py --targets desktop android`.
For Desktop + Android + iOS together, run the **Build all native apps** Actions
workflow, or `python build.py --ci --with-tests` with authenticated GitHub CLI.
[Full instructions, prerequisites and artifacts](finalbuild/docs/building/BUILD_ALL.md).

iOS output is an unsigned Simulator app; iPhone/App Store distribution requires
Apple signing configuration. Local Windows/Linux runs cannot compile iOS.

## Real OBD and shared vehicle data

[Protocol audit and support matrix](finalbuild/docs/obd/REAL_OBD_AUDIT.md) ·
[Backend/native bridge setup and APIs](finalbuild/docs/obd/SETUP_AND_API.md).

## Quick start

See [Windows setup](finalbuild/START_HERE_WINDOWS.md) for the local desktop/AI runtime and [project overview](finalbuild/README.md) for backend setup, tests, and architecture.

## Shared client behavior

The three native clients share the backend vehicle catalog and DiagnosticSession API. Language codes are English (en), Russian (ru), and Armenian (hy); theme modes are dark/light; diagnostic result values are PASS/FAIL/INCOMPLETE. See [the machine-readable client contract](finalbuild/config/client_contract.json) and [platform feature contract](finalbuild/PLATFORM_FEATURE_PARITY.md).

## Architecture and quality reports

- [Architecture documentation](finalbuild/docs/README.md)
- [Platform feature contract](finalbuild/PLATFORM_FEATURE_PARITY.md)
- [CI and quality report](report.md)

The results in report.md are tied to the specific commits and CI runs named in that report; they must not be interpreted as validation of later commits unless a matching run is linked.
