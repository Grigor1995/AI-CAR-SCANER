"""Inspect local GGUF/runtime paths and actual AI endpoints without starting UI.

Run from finalbuild: python scripts/check_offline_ai.py
No model download, API key or cloud service is required by this check.
"""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
for index, directory in enumerate((ROOT, ROOT/'backend')):
    if str(directory) not in sys.path:
        sys.path.insert(index, str(directory))


def inspect():
    import os
    from apps.desktop import main as launcher
    from ai.llm.llama_server import LlamaServerConfig, LlamaServerLLMProvider
    model = launcher._resolve_model_path()
    server = launcher._resolve_llama_server()
    config = replace(LlamaServerConfig.from_env(), base_url=launcher.LLM_BASE_URL, model=model.name)
    result = {'configured_provider':os.getenv('DIAGNOSTIC_LLM_PROVIDER','llama-server'),
              'model_path':str(model), 'model_exists':model.is_file(),
              'model_candidates':[p.name for p in (launcher.ROOT/'models').glob('*.gguf')],
              'server_binary':str(server) if server else None,
              'local_runtime':LlamaServerLLMProvider(config).availability()}
    try:
        with urlopen(launcher.BACKEND_URL+'/api/v1/ai/provider',timeout=3) as response:
            result['backend_provider'] = json.loads(response.read().decode())
    except Exception as error:
        result['backend_provider'] = {'available':False,'reason':str(error)}
    result['ready'] = bool(result['local_runtime'].get('available'))
    if not result['ready']:
        if not model.is_file():
            result['next_step'] = 'Set LOCAL_LLM_MODEL_PATH to your GGUF, or keep one model in models/.'
        elif server is None:
            result['next_step'] = 'Install llama-server with its DLLs in tools/llama.cpp/, or set LOCAL_LLM_SERVER_PATH.'
        else:
            result['next_step'] = 'Run python -m apps.desktop.main --with-backend --local-ai; inspect llama-server.log if loading fails.'
    elif (result['backend_provider'].get('provider') != 'LlamaServerLLMProvider'
          or not result['backend_provider'].get('available')):
        result['ready'] = False
        result['next_step'] = 'Close the existing backend, then launch Desktop with --with-backend --local-ai.'
    return result


def main():
    result = inspect()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
