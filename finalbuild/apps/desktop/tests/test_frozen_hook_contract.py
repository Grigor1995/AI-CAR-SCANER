"""PyInstaller startup diagnostics: cover the original Windows regression path.

Run the actual runtime-hook Python source with an isolated log file; unlike
frozen EXE smoke, this does NOT claim to validate native bootloader behavior.
"""
from __future__ import annotations

import faulthandler
from pathlib import Path
import runpy



HOOK = Path(__file__).resolve().parents[1] / "debug_runtime_hook.py"
EARLY_HOOK = Path(__file__).resolve().parents[1] / "qt_early_runtime_hook.py"


def test_debug_runtime_hook_is_inert_when_not_opted_in(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_CAR_DEBUG_FAULT_LOG", raising=False)
    monkeypatch.delenv("AI_CAR_EARLY_QTCORE", raising=False)
    output = runpy.run_path(str(HOOK), run_name="pyinstaller_runtime_hook_test")
    assert "_frozen_fault_log" not in output
    assert not list(tmp_path.iterdir())


def test_debug_runtime_hook_records_frozen_boot_environment(monkeypatch, tmp_path):
    target = tmp_path / "nested" / "runtime-faults.log"
    monkeypatch.setenv("AI_CAR_DEBUG_FAULT_LOG", str(target))
    monkeypatch.setenv("AI_CAR_EARLY_QTCORE", "0")
    enabled = []
    monkeypatch.setattr(
        faulthandler, "enable",
        lambda *, file, all_threads: enabled.append((file, all_threads)),
    )
    output = runpy.run_path(str(HOOK), run_name="pyinstaller_runtime_hook_test")
    try:
        handle = output["_frozen_fault_log"]
        assert enabled == [(handle, True)]
        handle.flush()
        text = target.read_text(encoding="utf-8")
        assert "Frozen process started" in text
        assert "executable: " in text
        assert "python: " in text
        assert "bundle: " in text
    finally:
        output["_frozen_fault_log"].close()


def test_debug_runtime_hook_early_qtcore_diagnostic(monkeypatch, tmp_path):
    target = tmp_path / "frozen-early.log"
    monkeypatch.setenv("AI_CAR_DEBUG_FAULT_LOG", str(target))
    monkeypatch.setenv("AI_CAR_EARLY_QTCORE", "1")
    monkeypatch.setattr(faulthandler, "enable", lambda **_: None)
    output = runpy.run_path(str(HOOK), run_name="pyinstaller_runtime_hook_test")
    try:
        output["_frozen_fault_log"].flush()
        text = target.read_text(encoding="utf-8")
        assert "importing PySide6.QtCore before other runtime hooks" in text
        assert "PySide6.QtCore imported successfully" in text
    finally:
        output["_frozen_fault_log"].close()


def test_production_early_qtcore_hook_never_requires_project_venv_changes():
    # Runpy uses the exact same frozen-runtime source. On Windows this imports
    # QtCore; other platforms intentionally skip it.
    runpy.run_path(str(EARLY_HOOK), run_name="pyinstaller_runtime_hook_test")
