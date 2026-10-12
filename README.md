# AI-CAR-SCANER

Evidence-driven automotive diagnostic platform with a shared FastAPI backend, deterministic diagnostic rules, evidence-based hypotheses, optional AI/RAG assistance, vehicle simulation, and native client applications.

## Supported clients

- **Desktop:** Python + PySide6 workstation (finalbuild/apps/desktop).
- **Android:** native Kotlin + Jetpack Compose app (finalbuild/apps/mobile-android).
- **iOS:** native Swift + SwiftUI app (finalbuild/apps/mobile-ios).

The repository uses native client implementations. The legacy Flutter client sources and their build scaffolding have been removed.

## Quick start

See [Windows setup](finalbuild/START_HERE_WINDOWS.md) for the local desktop/AI runtime and [project overview](finalbuild/README.md) for backend setup, tests, and architecture.

## Architecture and quality reports

- [Architecture documentation](finalbuild/docs/README.md)
- [Platform feature contract](finalbuild/PLATFORM_FEATURE_PARITY.md)
- [CI and quality report](report.md)

The results in report.md are tied to the specific commits and CI runs named in that report; they must not be interpreted as validation of later commits unless a matching run is linked.
