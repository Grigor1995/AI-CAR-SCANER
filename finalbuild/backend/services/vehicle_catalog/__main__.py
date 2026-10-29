"""Native-client independent catalog process entry point."""
from pathlib import Path
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Read-only vehicle catalog service')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8011)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import uvicorn
    uvicorn.run('services.vehicle_catalog.app:app', host=args.host, port=args.port)

if __name__ == '__main__': main()
