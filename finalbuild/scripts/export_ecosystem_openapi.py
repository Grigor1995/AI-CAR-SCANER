"""Export actual foundation request/response contracts without connecting to operator databases."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT/'finalbuild'


def main():
    # Isolate only this exporter process; never inspect a configured production DB.
    os.environ['DATABASE_URL'] = 'sqlite://'
    os.environ['AI_CAR_ECOSYSTEM_ENABLED'] = '0'
    os.environ.pop('AI_CAR_ENV_CONFIG', None)
    sys.path.insert(0, str(PROJECT))
    sys.path.insert(0, str(PROJECT/'backend'))
    from api.main import app
    source = app.openapi()
    paths = {path: body for path, body in source['paths'].items() if path.startswith('/api/v2/ecosystem/')}
    needed = set()

    def references(value):
        if isinstance(value, dict):
            if value.get('$ref', '').startswith('#/components/schemas/'):
                needed.add(value['$ref'].rsplit('/', 1)[1])
            for item in value.values(): references(item)
        elif isinstance(value, list):
            for item in value: references(item)

    references(paths)
    while True:
        previous = set(needed)
        for name in list(needed): references(source['components']['schemas'][name])
        if previous == needed: break
    output = {'openapi': source['openapi'],
              'info': {'title': 'AI Car Scanner ecosystem foundation', 'version': '0.1-foundation',
                       'description': 'Generated from implemented v2 routes; feature-gated and not a complete ecosystem.'},
              'paths': paths, 'components': {'schemas': {name: source['components']['schemas'][name] for name in sorted(needed)},
                                           'securitySchemes': source['components']['securitySchemes']}}
    target = ROOT/'docs/architecture/ecosystem-openapi.json'
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'Exported {len(paths)} foundation paths to {target}')


if __name__ == '__main__':
    main()
