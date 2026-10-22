#!/usr/bin/env python3
"""Repository-wide native build entrypoint; safe to run from any directory."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "finalbuild/scripts/build_all.py"), run_name="__main__")
