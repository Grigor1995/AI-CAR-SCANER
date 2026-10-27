#!/usr/bin/env python3
"""Clone-to-run setup and native app launcher. Run --help for commands."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent / 'finalbuild/scripts/local_runner.py'), run_name='__main__')
