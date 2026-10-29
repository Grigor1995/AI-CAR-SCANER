"""Shared JSON environment configuration, with explicit process values winning."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys

PROJECT = Path(__file__).resolve().parents[1]


def environment_values(*, include_defaults=True, environ=None, bootstrap=False):
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
        # runpy from repo root imports finalbuild.shared; module entrypoints
        # import shared. Resolve the same backend source without changing sys.path.
        if __package__.startswith('finalbuild.'):
            from finalbuild.backend.configuration import runtime
        else:
            from backend.configuration import runtime
        if bootstrap:
            data = runtime.source_data(global_root, environ)
        else:
            data = runtime.ConfigManager(root=global_root, environ=environ).snapshot.model_dump(mode='json')
        fields = {
            'AI_CAR_BACKEND_PORT': ('services', 'backend_port', int, 1, 65535),
            'LOCAL_LLM_SERVER_CONTEXT': ('ai', 'context', int, 512, 131072),
            'DIAGNOSTIC_LLM_PROVIDER': ('ai', 'provider', str, None, None),
            'LOCAL_LLM_TEMPERATURE': ('ai', 'temperature', (int, float), 0, 2),
            'LOCAL_LLM_MAX_TOKENS': ('ai', 'max_tokens', int, 64, 32768),
            'LOCAL_LLM_SERVER_TIMEOUT_S': ('ai', 'timeout_seconds', (int, float), 1, 600),
            'LOCAL_LLM_SERVER_URL': ('ai', 'endpoint', str, None, None),
            'LOCAL_LLM_MODEL_PATH': ('ai', 'model_path', str, None, None),
        }
        for name, (section, key, expected, low, high) in fields.items():
            group = data.get(section, {})
            if not isinstance(group, dict): raise ValueError('Invalid bootstrap configuration section')
            if key not in group: continue
            value = group[key]
            if isinstance(value, bool) or not isinstance(value, expected):
                raise ValueError('Invalid bootstrap configuration field type')
            if low is not None and not low <= value <= high:
                raise ValueError('Bootstrap configuration field outside allowed range')
            # Preserve legacy port-based URL construction and model discovery.
            if name == 'LOCAL_LLM_SERVER_URL' and value == 'http://127.0.0.1:8000': continue
            if name == 'LOCAL_LLM_MODEL_PATH':
                if value == 'models': continue
                model_path = Path(value).expanduser()
                value = model_path if model_path.is_absolute() else PROJECT / model_path
            values[name] = str(value)
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
