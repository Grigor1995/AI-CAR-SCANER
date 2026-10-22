"""Audit or register generated catalog PNG cutouts without editing image pixels.

python scripts/vehicle_portraits.py --audit
python scripts/vehicle_portraits.py --import-manifest /path/to/generated-records.json
Input records: [{"id": "catalog_reference_id", "path": "/path/to/generated.png"}]
Original generated files are retained; only byte-identical copies are staged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def inspect_png(path: Path) -> dict:
    from PIL import Image
    with Image.open(path) as image:
        if image.format != 'PNG' or image.mode != 'RGBA':
            raise ValueError(f'{path.name}: expected RGBA PNG')
        low, high = image.getchannel('A').getextrema()
        if low != 0 or high < 128 or min(image.size) < 200:
            raise ValueError(f'{path.name}: requires transparent background and visible vehicle')
        dimensions = list(image.size)
    return {'sha256': sha256(path.read_bytes()).hexdigest(), 'dimensions': dimensions}


def register(records: list[dict], root: Path = ROOT):
    path = root/'data/vehicle_reference.json'
    catalog = json.loads(path.read_text(encoding='utf-8'))
    cars = {row['id']: row for row in catalog['vehicles']}
    seen, staged = set(), []
    for record in records:
        key, source = record['id'], Path(record['path'])
        if key not in cars or key in seen:
            raise ValueError(f'Unknown or duplicated vehicle reference: {key}')
        seen.add(key)
        metadata = inspect_png(source)
        staged.append((key, source, metadata))
    if len({info['sha256'] for _, _, info in staged}) != len(staged):
        raise ValueError('Different vehicle generations must not reuse an identical illustration')
    manifest_path = root/'data/generated_vehicle_portraits.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'schema_version':1,'vehicles':{}}
    for key, source, metadata in staged:
        destination = root/'assets/vehicle_models'/f'{key}.png'
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
        cars[key]['image'] = {'path': destination.relative_to(root).as_posix(), 'kind':'generated_illustration',
                             'attribution':'AI-generated vehicle illustration; not a manufacturer photograph'}
        manifest['vehicles'][key] = metadata | {'path':cars[key]['image']['path'],
            'kind':'generated_illustration','generator':'image_gen',
            'generated_asset_id':source.stem,'registered_at':datetime.now(timezone.utc).isoformat(),
            'notice':'Illustration only; vehicle geometry/trim is not manufacturer-certified'}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return len(staged)


def audit(root: Path = ROOT) -> dict:
    cars = json.loads((root/'data/vehicle_reference.json').read_text(encoding='utf-8'))['vehicles']
    missing, invalid, hashes = [], [], {}
    for car in cars:
        relative = car['image'].get('path')
        if not relative or not (root/relative).is_file():
            missing.append(car['id']); continue
        try:
            metadata = inspect_png(root/relative)
            hashes.setdefault(metadata['sha256'],[]).append(car['id'])
        except ValueError as error:
            invalid.append({'id':car['id'],'error':str(error)})
    duplicated = [ids for ids in hashes.values() if len(ids)>1]
    return {'generations':len(cars),'available':len(cars)-len(missing)-len(invalid),
            'missing':missing,'invalid':invalid,'duplicate_images':duplicated,
            'status':'FAIL' if missing or invalid or duplicated else 'PASS'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--audit',action='store_true')
    group.add_argument('--import-manifest',type=Path)
    args = parser.parse_args(argv)
    if args.import_manifest:
        print(json.dumps({'registered':register(json.loads(args.import_manifest.read_text(encoding='utf-8')))}))
        return 0
    result = audit()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(result['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
