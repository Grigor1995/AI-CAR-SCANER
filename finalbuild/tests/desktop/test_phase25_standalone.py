from pathlib import Path


def test_standalone_specs_exist():
    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "desktop" / "specs" / "AICarScanner.spec").exists()
    assert (root / "apps" / "desktop" / "specs" / "backend_service.spec").exists()


def test_desktop_main_references_backend_service():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps" / "desktop" / "main.py").read_text()
    assert "backend_service.exe" in text
    assert 'getattr(sys, "frozen", False)' in text


def test_build_script_is_present():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "build_windows_standalone.ps1"
    text = script.read_text()
    assert script.exists()
    assert "backend_service.spec" in text
    assert "AICarScanner.spec" in text
