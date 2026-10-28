# Deployment and rollout

Keep existing `runner.py`, `build.py`, `installer.py` and native build guides.
Local native builds remain independent of ecosystem foundation. Do not enable
the incomplete account boundary for existing native clients until their login
adapters have migrated.

Foundation rollout target: back up configured DATABASE_URL, run Alembic upgrade
explicitly, run authenticated API smoke tests against the actual database, then
set AI_CAR_ECOSYSTEM_ENABLED=1 and restart behind HTTPS. With the flag off,
existing local APIs behave as before. With the flag on, legacy API paths are
denied and new endpoints require ownership-aware access. This is intentional,
not a silent backward-compatible remote deployment.

SQLite verifies portable behavior locally; production PostgreSQL migration,
backup restore, signing, iOS build, real hardware and notification providers
require their actual environments. Rolling back the feature flag preserves
schema/data. Downgrade only after an explicit data-retention decision.
Credentials go in process ENV or ignored local JSON overrides. No deployment,
release publishing, CI/CD, SMS or email is performed by this branch.

## Exact local foundation smoke-test commands

From the repository root (use the prepared venv Python):

```bash
export DATABASE_URL='sqlite:///ecosystem.sqlite'
python -m alembic -c finalbuild/backend/alembic.ini upgrade head
export AI_CAR_ECOSYSTEM_ENABLED=1
cd finalbuild
python -m apps.desktop.backend_worker
```

This starts only the API; it does not add native login UI. Test the v2 OpenAPI
contracts at `/docs`. The feature blocks legacy API paths intentionally. Leave
the flag unset/0 for normal current Desktop/mobile diagnosis. The runner now
binds loopback by default, preserving emulator routing; physical LAN access
requires an explicit trusted-network host override. Use a migrated PostgreSQL
URL with the installed driver (`postgresql+psycopg://...`) for deployment checks.

The architecture opens as a local file on ordinary browsers. If file URLs are
blocked by browser policy, serve bundled assets locally without a CDN:

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Open `http://127.0.0.1:8765/architecture/interactive_architecture.html`.
