"""Copy canonical generated portraits into both native mobile resource bundles."""
from pathlib import Path
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    entries = json.loads((ROOT / 'shared/vehicle_catalog.json').read_text())['vehicles']
    keys = {(v['make'], v['model'], v['chassis']) for v in entries}
    for vehicle in sorted(keys):
        name = '_'.join(re.sub('[^a-z0-9]+', '-', x.lower()).strip('-') for x in vehicle) + '.png'
        source = ROOT / 'assets/vehicle_models' / name
        if not source.is_file():
            raise FileNotFoundError(source)
        for directory in ('apps/mobile-android/app/src/main/assets/vehicle_models',
                          'apps/mobile-ios/AICarScanner/VehicleModels'):
            destination = ROOT / directory / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    print(f'Synchronized {len(keys)} portraits to Android and iOS')


if __name__ == '__main__':
    main()
