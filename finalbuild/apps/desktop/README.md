# AI CAR SCANER — Cross-platform Flutter client

`apps/desktop` is the canonical Flutter client for the shared diagnostic platform.

See [`../PLATFORM_FEATURE_PARITY.md`](../PLATFORM_FEATURE_PARITY.md) for the single cross-platform feature contract and platform-specific limits.

## Supported client targets

- Windows
- Linux
- macOS
- Android
- iOS

Android currently has a dedicated native Compose client under `apps/mobile-android`. The Flutter client uses the same backend REST contracts and the same server-side diagnostic session/database.

## Shared data architecture

All clients communicate with the same FastAPI backend:

`POST/GET /api/v1/sessions`

The backend persists complete `DiagnosticSession` snapshots to the configured `DATABASE_URL`.

With the repository Docker setup:

`Android / Desktop / iOS -> FastAPI -> PostgreSQL + pgvector`

This means the session, vehicle, symptoms, DTCs, evidence, hypotheses, recommendations, test results and audit history can be shared between devices.

The clients should not maintain an independent authoritative diagnostic database.

## Desktop development

From `finalbuild/apps/desktop`:

```bash
flutter pub get
flutter run -d windows
```

Linux and macOS use the corresponding Flutter target.

## iOS development

The iOS runner has not been committed to this repository yet. On a macOS development machine with Xcode and Flutter installed, generate the platform runner once from this directory:

```bash
flutter create --platforms=ios .
flutter pub get
flutter run -d ios
```

Do not replace `lib/`; that is the shared application code.

## API configuration

Override the backend URL at build/run time:

```bash
flutter run -d windows --dart-define=API_URL=https://ai-car-scaner.onrender.com
```

For local development, override `API_URL` with your local FastAPI URL. The default is the shared Render backend so Desktop, Android, and iOS use the same service.

## Legacy Python desktop

The repository also contains the older PySide6 client files (`main.py`, `ui.py`, etc.). They are legacy/standalone tooling and are not the cross-platform Flutter client.