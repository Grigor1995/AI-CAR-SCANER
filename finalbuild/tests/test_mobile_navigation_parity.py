"""Guard the mobile navigation labels against drifting from the Desktop sidebar."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IOS = ROOT / "apps/mobile-ios/AICarScanner/DiagnosticScreen.swift"
ANDROID = ROOT / "apps/mobile-android/app/src/main/java/com/aicarscaner/mobile/presentation/DashboardNavigation.kt"

ORDER = ["Dashboard", "Vehicles", "VCI / Devices", "Diagnostic", "Live Data",
         "Tests", "DTC", "AI Analysis", "Reports", "Teach AI"]


def test_android_dashboard_sections_follow_desktop_order():
    source = ANDROID.read_text(encoding="utf-8")
    section = source.split("val sections=listOf(", 1)[1].split("sections.forEachIndexed", 1)[0]
    positions = [section.index('"' + label + '"') for label in ORDER]
    assert positions == sorted(positions)


def test_ios_navigation_has_stable_tab_ids_and_desktop_labels():
    source = IOS.read_text(encoding="utf-8")
    segment = source.split("ForEach([", 1)[1].split("], id:", 1)[0]
    positions = [segment.index('"' + label + '"') for label in ORDER]
    assert positions == sorted(positions)
    assert "titles[index]" not in source
    assert "symbols[index]" not in source
