#!/usr/bin/env python3
"""Build the Windows online Setup wizard locally using Inno Setup 6.3+."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent / 'finalbuild/scripts/build_windows_installer.py'), run_name='__main__')
