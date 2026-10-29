"""Shared JSON environment configuration, with explicit process values winning."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys

PROJECT = Path(__file__).resolve().parents[1]


def environment_values(*, include_defaults=True, environ=None):
    environ = os.environ if environ is None else environ
    paths = [PROJECT / 'config/environment.json'] if include_defaults else []
    local = (Path(sys.executable).resolve().parent / 'environment.local.json'
             if getattr(sys, 'frozen', False) else PROJECT / 'config/environment.local.json')
    paths.append(local)
    explicit = environ.get('AI_CAR_ENV_CONFIG')
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f'Environment configuration not found: {path}')
        paths.append(path)
    values = {}
    global_root = PROJECT if getattr(sys, "frozen", False) else PROJECT.parent
    if include_defaults and (global_root / 'config/global_config.json').is_file():
        # Importing configuration here is backend/setup-only; thin native clients
        # deliberately do not import this module.
        from backend.configuration.runtime import ConfigManager
        config = ConfigManager(root=global_root, environ=environ).snapshot
        values.update({'AI_CAR_BACKEND_PORT': str(config.services.backend_port),
                       'LOCAL_LLM_SERVER_CONTEXT': str(config.ai.context),
                       'DIAGNOSTIC_LLM_PROVIDER': config.ai.provider,
                       'LOCAL_LLM_TEMPERATURE': str(config.ai.temperature),
                       'LOCAL_LLM_MAX_TOKENS': str(config.ai.max_tokens),
                       'LOCAL_LLM_SERVER_TIMEOUT_S': str(config.ai.timeout_seconds)})
        if config.ai.endpoint != 'http://127.0.0.1:8000':
            values['LOCAL_LLM_SERVER_URL'] = config.ai.endpoint
        if config.ai.model_path != 'models':
            model_path = Path(config.ai.model_path).expanduser()
            values['LOCAL_LLM_MODEL_PATH'] = str(model_path if model_path.is_absolute() else PROJECT / model_path)
    for path in paths:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('environment'), dict):
                raise ValueError('Expected version 1 and an environment object')
            for name, value in data['environment'].items():
                if not re.fullmatch(r'[A-Z_][A-Z0-9_]*', name) or not isinstance(value, (str, int, float, bool)):
                    raise ValueError('Environment names must be uppercase and values must be strings, numbers or booleans')
                if path == PROJECT / 'config/environment.json' and name in values:
                    continue
                values[name] = ('1' if value else '0') if isinstance(value, bool) else str(value)
        except (OSError, ValueError) as error:
            raise ValueError(f'Invalid environment configuration: {path}: {error}') from error
    return values


def apply_environment(environ=None):
    """Set missing environment values; never overwrite an explicit process ENV."""
    environ = os.environ if environ is None else environ
    for name, value in environment_values(environ=environ).items():
        environ.setdefault(name, value)
    return environ
