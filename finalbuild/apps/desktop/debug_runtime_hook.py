"""Diagnostic-only PyInstaller runtime hook for Windows frozen startup.

Used by scripts/debug_desktop_git_bash.sh; never included in release builds.
"""
import faulthandler
import os
from pathlib import Path
import sys
import time

_log_name = os.environ.get("AI_CAR_DEBUG_FAULT_LOG")
if _log_name:
    _log_path = Path(_log_name)
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    # Keep a process-global open handle so faulthandler can write on a native crash.
    _frozen_fault_log = _log_path.open("a", encoding="utf-8", buffering=1)
    _frozen_fault_log.write(
        "\n=== Frozen process started ===\n"
        f"timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"executable: {sys.executable}\n"
        f"python: {sys.version}\n"
        f"bundle: {getattr(sys, '_MEIPASS', '<missing>')}\n"
    )
    faulthandler.enable(file=_frozen_fault_log, all_threads=True)

# Experimental load-order test: PyInstaller's Qt runtime hook imports
# PySide6.QtCore to create embedded qt.conf. On the failing desktop bundle
# that native import raises 0xC0000005. Test it *before* other runtime hooks
# (notably pyi_rth_cryptography_openssl) without changing release behavior.
if os.environ.get("AI_CAR_EARLY_QTCORE", "0") == "1":
    _diagnostic_stream = globals().get("_frozen_fault_log", sys.stderr)
    print("[ISOLATION] importing PySide6.QtCore before other runtime hooks",
          file=_diagnostic_stream, flush=True)
    from PySide6 import QtCore
    print("[ISOLATION] PySide6.QtCore imported successfully: " + QtCore.__file__,
          file=_diagnostic_stream, flush=True)
