"""Inspect disposable source-tree caches; use --apply to remove them."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent / 'finalbuild/scripts/clean_repository.py'), run_name='__main__')
