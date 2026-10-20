# Desktop backend startup and PostgreSQL timeouts

A `psycopg.errors.ConnectionTimeout` for localhost:5432 means the configured
PostgreSQL server is unavailable. Increasing the GUI deadline does not repair
the database. Old logs can refer to other checkouts: each launch now records its
UTC timestamp, checkout root, interpreter, and selected storage mode, without
printing database URLs or environment values.

## Local Desktop (Windows Git Bash)

Close previous Desktop/backend processes first. From the intended checkout's
`finalbuild` directory, activate its virtual environment and install dependencies:

```bash
source .venv/Scripts/activate
python -m pip install -r backend/requirements.txt -r apps/desktop/requirements.txt
AI_CAR_USE_LOCAL_DATABASE=1 python -m apps.desktop.main
```

If the venv lives elsewhere, use that environment's activation script instead.
`python -c 'import sys; print(sys.executable)'` identifies the interpreter in use.
Local SQLite storage is `%APPDATA%/AI-Car-Scanner/diagnostic.sqlite` (the home
folder replaces APPDATA on systems without it). Sessions persist across restarts.
The bundled curated catalog is inserted without overwriting existing entries.
This is selection guidance, not VIN-level fitment verification.

Without DATABASE_URL the Desktop launcher chooses local SQLite automatically.
An explicit DATABASE_URL is respected unless AI_CAR_USE_LOCAL_DATABASE=1 is set.
This flag selects separate local storage; it does not migrate, delete or recover
records from another database. Direct Uvicorn startup retains its existing
configuration semantics; the Desktop launcher owns the automatic local setup.
Already healthy backend processes are reused: changing a storage setting does
not reconfigure a process that is already running.

## PostgreSQL deployment

Keep DATABASE_URL configured, clear AI_CAR_USE_LOCAL_DATABASE, and start/reach
the configured PostgreSQL service. Neither credentials nor connection values
should be pasted into chat or committed. Session/catalog connection attempts
have a default per-address three-second connect timeout, configurable with
AI_CAR_DB_CONNECT_TIMEOUT_S (1–30). DNS, multiple addresses and other database
operations may add time; this is not a total query deadline. Failed persistence
initialization reports an explicit configuration error without silently changing
storage. The GUI startup budget defaults to 60 seconds for slow Windows imports.

PostgreSQL/pgvector RAG and a local LLM remain separate optional services.
SQLite validates the local diagnostic/session/catalog workflow, not pgvector.
The Qt font warning is a separate GUI warning and is not the PostgreSQL error.

## Real process validation

```bash
python scripts/check_local_backend.py
```

This runs the real Desktop backend launcher on a free loopback port with a fresh
temporary SQLite database. It checks health, a nonempty catalog with valid fuel
lists, session creation, symptoms, P0302 analysis, then stop/start and persistence.
It uses the installed Desktop `requests` dependency; no Qt, external PostgreSQL,
AI model, adapter or user database is required. Temporary state is removed after
the check and only the process started by the check is stopped.

For a failing real launch, inspect the latest section of:

```bash
tail -n 100 "$APPDATA/AI-Car-Scanner/backend.log"
```

A source change requires rebuilding frozen executables; pulling does not update
a previously built AICarScanner.exe/backend_service.exe pair. The backend spec
now includes the catalog seed data needed for local initialization. Windows
frozen execution must still be validated on Windows.
