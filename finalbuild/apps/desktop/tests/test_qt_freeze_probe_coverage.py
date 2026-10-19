"""Qt packaging startup probe coverage: exercise both icon branches safely.

This test uses Qt test doubles and never opens a visible window, contacts a
backend, rewrites user assets, or changes the Python virtual environment.
The separate frozen EXE smoke tests remain the native packaging acceptance.
"""
from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from PySide6 import QtCore, QtGui, QtWidgets


@pytest.mark.parametrize("icon_present", [False, True], ids=["missing-icon", "bundled-icon"])
def test_qt_startup_probe_runs_main_path_and_reports_icon_state(
    monkeypatch, tmp_path: Path, capsys, icon_present: bool
):
    """Run the actual apps.desktop.qt_freeze_probe module through importlib.

    Importing the probe (instead of reading its source or using runpy) also
    gives coverage.py its normal package/module identity under --cov=apps.desktop.
    """
    assets = tmp_path / "assets"
    assets.mkdir()
    if icon_present:
        (assets / "AI-Car-Scanner-mobile.png").write_bytes(b"test-icon-placeholder")

    events: list[str] = []

    class FakeApplication:
        def __init__(self, argv):
            assert argv == []
            events.append("app created")

        def quit(self):
            events.append("app quit")

        def exec(self):
            events.append("app exec")
            return 0

    class FakeWindow:
        def setWindowTitle(self, title):
            assert title == "AI CAR SCANER Qt Packaging Probe"

        def setCentralWidget(self, widget):
            assert widget == "Qt frozen startup: OK"

        def setWindowIcon(self, icon):
            assert icon == "fake-icon"
            events.append("icon applied")

        def windowIcon(self):
            return SimpleNamespace(isNull=lambda: False)

        def show(self):
            events.append("window shown")

    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(QtCore, "QTimer", SimpleNamespace(
        singleShot=lambda milliseconds, callback: (
            events.append(f"timer {milliseconds}ms"), callback()
        )
    ))
    monkeypatch.setattr(QtGui, "QIcon", lambda _: "fake-icon")
    monkeypatch.setattr(QtWidgets, "QApplication", FakeApplication)
    monkeypatch.setattr(QtWidgets, "QMainWindow", FakeWindow)
    monkeypatch.setattr(QtWidgets, "QLabel", lambda text: text)

    module_name = "apps.desktop.qt_freeze_probe"
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    try:
        with pytest.raises(SystemExit) as completed:
            importlib.import_module(module_name)
        assert completed.value.code == 0
    finally:
        # The probe is an executable script, not an application library.
        # Avoid leaving it half-imported in the main test interpreter.
        sys.modules.pop(module_name, None)

    printed = capsys.readouterr().out
    assert "[QT-PROBE] QApplication created" in printed
    assert "[QT-PROBE] window shown" in printed
    assert "[QT-PROBE] Qt event loop exited, status=0" in printed
    if icon_present:
        assert "icon loaded=True" in printed
        assert "icon applied" in events
    else:
        assert "icon missing:" in printed
        assert "icon applied" not in events
    assert events == (
        ["app created"]
        + (["icon applied"] if icon_present else [])
        + ["window shown", "timer 1200ms", "app quit", "app exec"]
    )
