# Local setup and run (Git Bash / Python)

From the repository root:

```sh
git pull origin main
python runner.py setup --skip-ai
```

Run the shared backend in one terminal (add `--local-ai` when your GGUF and
llama-server are installed):

```sh
python runner.py backend --migrate
```

Open each desired separate Desktop app in another terminal:

```sh
python runner.py desktop --app user
python runner.py desktop --app customer
python runner.py desktop --app market
```

Android emulator, backend running on the host:

```sh
python runner.py android --app user --api-url http://10.0.2.2:8001
```

Use `--app customer` or `--app market` for the other apps. iOS builds require
macOS/Xcode: `python build.py --targets ios`. Desktop/Android local builds:
`python build.py --targets desktop android --with-tests`.

Optional independently running catalog: activate the repository `.venv`, generate
one secret in your shell and retain it only in the two process environments:

```sh
export AI_CAR_VEHICLE_SERVICE_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
cd finalbuild
python -m backend.services.vehicle_catalog --port 8011
```

Start backend from root in a second terminal with the SAME token set securely,
then `export AI_CAR_CATALOG_MODE=remote` and `python runner.py backend --migrate`.
Default catalog URL is loopback port8011. Remote hosts require HTTPS. Do not paste
real token values into Git, screenshots, bug reports or configuration JSON.
To roll back restart backend with `AI_CAR_CATALOG_MODE=embedded`.

Offline source explorer: open `docs/architecture/interactive_architecture.html`.
Rebuild after code changes with `python scripts/architecture/generate_index.py`
(install `scripts/architecture/requirements.txt` into the active developer venv).
