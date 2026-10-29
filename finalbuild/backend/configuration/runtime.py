"""Immutable startup snapshots plus a deliberately small, audited hot-reload surface.

Priority: model defaults, global JSON, environment overlay, allowlisted ENV,
then explicitly user-adjustable preferences. No secret values belong in JSON.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
import json
import os
import sys
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
ENV_PATHS = {"AI_CAR_BACKEND_PORT": ("services.backend_port", int),
             "DIAGNOSTIC_LLM_PROVIDER": ("ai.provider", str),
             "LOCAL_LLM_SERVER_CONTEXT": ("ai.context", int),
             "LOCAL_LLM_SERVER_URL": ("ai.endpoint", str),
             "LOCAL_LLM_TEMPERATURE": ("ai.temperature", float),
             "LOCAL_LLM_MAX_TOKENS": ("ai.max_tokens", int),
             "LOCAL_LLM_SERVER_TIMEOUT_S": ("ai.timeout_seconds", float),
             "AI_CAR_CATALOG_URL": ("services.vehicle_catalog.url", str),
             "AI_CAR_CATALOG_MODE": ("services.vehicle_catalog.mode", str)}
PREFERENCES = {"app.language", "app.units", "ui.theme", "ui.chart"}
RELOADABLE = {"services.vehicle_catalog.timeout_seconds", "services.vehicle_catalog.retries"}

class ConfigurationError(ValueError):
    """A sanitized error; raw configuration and credentials are never echoed."""

def merge(base, overlay):
    if not isinstance(overlay, dict):
        raise ConfigurationError("Configuration must be an object")
    result = deepcopy(base) if isinstance(base, dict) else {}
    for key, value in overlay.items():
        result[key] = merge(result.get(key, {}), value) if isinstance(value, dict) else value
    return result

def put(data, path, value):
    parts = path.split(".")
    target = data
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value

def read(path):
    try:
        if path.stat().st_size > 131072:
            raise ConfigurationError("Configuration exceeds size limit")
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result: raise ConfigurationError("Duplicate configuration key")
                result[key] = value
            return result
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, ValueError):
        raise ConfigurationError("Configuration file is missing or invalid JSON") from None

def source_data(root, env):
    """Stdlib-only document loading, shared by first-clone setup and runtime.

    This is syntax/version preflight, not a replacement for backend schema
    validation. Native clients never receive a configuration control plane.
    """
    directory = Path(root) / "config"
    data = read(directory / "global_config.json")
    if not isinstance(data, dict) or type(data.get('schema_version', 1)) is not int or data.get('schema_version', 1) != 1:
        raise ConfigurationError("Unsupported configuration schema version")
    name = env.get("AI_CAR_CONFIG_ENV", "development")
    if name not in {"development", "testing", "production"}:
        raise ConfigurationError("Unknown configuration environment")
    overlay = directory / "environments" / f"{name}.json"
    if overlay.is_file(): data = merge(data, read(overlay))
    elif name == "production": raise ConfigurationError("Production overlay must be explicitly installed")
    if type(data.get('schema_version', 1)) is not int or data.get('schema_version', 1) != 1:
        raise ConfigurationError("Unsupported configuration schema version")
    return data


def validate(data):
    from pydantic import ValidationError
    from .models import GlobalConfig
    # JSON conversion accepts JSON arrays as frozen tuples without type coercion.
    try:
        model = GlobalConfig.model_validate_json(json.dumps(data))
    except (ValidationError, ValueError, TypeError):
        raise ConfigurationError("Configuration schema validation failed") from None
    for url, paths in ((model.ai.endpoint, {"", "/", "/v1", "/v1/"}), (model.services.vehicle_catalog.url, {"", "/"})):
        parsed = urlsplit(url)
        try:
            if parsed.port == 0: raise ValueError("Invalid service port")
        except ValueError:
            raise ConfigurationError("Invalid service URL") from None
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ConfigurationError("Service URLs must be HTTP(S) origins without credentials")
        if parsed.path not in paths:
            raise ConfigurationError("Service URLs must be origins")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ConfigurationError("Remote services require HTTPS")
    return model

def classification(path):
    if path.startswith("native."): return "STATIC_BUILD_TIME"
    if path in PREFERENCES: return "USER_PREFERENCE"
    if path in RELOADABLE: return "RUNTIME_RELOADABLE"
    if path.startswith(("marketplace.", "obd.read_only", "obd.write_policy", "updates.")) or path.endswith("_env"):
        return "SECURITY_SENSITIVE"
    return "STARTUP_ONLY"

class ConfigManager:
    def __init__(self, root=ROOT, environ=None, preferences=None):
        env = os.environ if environ is None else environ
        from .models import GlobalConfig
        data = merge(GlobalConfig().model_dump(mode="json"), source_data(root, env))
        for key, (path, cast) in ENV_PATHS.items():
            if key in env:
                try: put(data, path, cast(env[key]))
                except (ValueError, TypeError): raise ConfigurationError("Invalid authorized environment override") from None
        for path, value in (preferences or {}).items():
            if path not in PREFERENCES: raise ConfigurationError("Preference is not user-adjustable")
            put(data, path, value)
        self._snapshot = validate(data)
        self._lock = RLock()
        self.revision = 1

    @property
    def snapshot(self):
        with self._lock: return self._snapshot

    def public_snapshot(self):
        with self._lock:
            data = self.snapshot.model_dump(mode="json")
            # Paths, origins and environment reference names are internal deployment data.
            return {"schema_version": 1, "revision": self.revision, "app": data["app"],
                    "ui": data["ui"], "marketplace": data["marketplace"],
                    "native": data["native"], "runtime_status": "not_probed"}

    def reload(self, changes, *, expected_revision, audit):
        """Caller must authorize admin; audit must durably succeed before publication."""
        with self._lock:
            if expected_revision != self.revision: raise ConfigurationError("Configuration revision conflict")
            if not changes or not set(changes) <= RELOADABLE:
                raise ConfigurationError("Only runtime-reloadable fields may change; other settings require restart")
            data = self._snapshot.model_dump(mode="json")
            for path, value in changes.items(): put(data, path, value)
            candidate = validate(data)
            audit({"revision": self.revision + 1, "paths": sorted(changes)})
            self._snapshot = candidate
            self.revision += 1
            return self.public_snapshot()

@lru_cache(maxsize=1)
def get_manager():
    return ConfigManager()
