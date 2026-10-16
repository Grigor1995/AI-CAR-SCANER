"""Short-lived PySide6 packaging probe, independent of the application.

Build with PyInstaller in onedir + console mode to isolate Qt startup issues.
"""
from pathlib import Path
import sys

def stage(label: str) -> None:
    print(f"[QT-PROBE] {label}", flush=True)

stage("Python entrypoint reached")
stage(f"frozen={getattr(sys, 'frozen', False)}")
stage(f"executable={sys.executable}")
stage(f"bundle={getattr(sys, '_MEIPASS', '<source>')}")

stage("importing QtCore")
from PySide6.QtCore import QTimer
stage("importing QtGui")
from PySide6.QtGui import QIcon
stage("importing QtWidgets")
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

stage("creating QApplication")
app = QApplication([])
stage("QApplication created")
window = QMainWindow()
window.setWindowTitle("AI CAR SCANER Qt Packaging Probe")
window.setCentralWidget(QLabel("Qt frozen startup: OK"))
root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
icon = root / "assets" / "AI-Car-Scanner-mobile.png"
if icon.is_file():
    window.setWindowIcon(QIcon(str(icon)))
    stage(f"icon loaded={not window.windowIcon().isNull()}")
else:
    stage(f"icon missing: {icon}")
window.show()
stage("window shown")
QTimer.singleShot(1200, app.quit)
code = app.exec()
stage(f"Qt event loop exited, status={code}")
raise SystemExit(code)
