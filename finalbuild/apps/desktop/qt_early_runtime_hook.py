"""PyInstaller Desktop startup hook: initialize QtCore before other hooks.

The Windows Python 3.14 Desktop frozen binary crashed in PyInstaller's
pyi_rth_pyside6.py while importing QtCore, but an early QtCore import in an
earlier user runtime hook allowed the Desktop GUI to launch (2026-10-16).

This minimal workaround applies only to frozen Windows GUI startup; it does
not change source-mode execution or install/replace PySide6 packages.
"""
import sys

if sys.platform == "win32":
    from PySide6 import QtCore as _qt_core  # noqa: F401
