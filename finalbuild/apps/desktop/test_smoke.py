from pathlib import Path
import ast

ROOT = Path(__file__).parent


def test_desktop_source_syntax():
    for name in ("main.py", "ui.py", "api_client.py", "models.py", "storage.py", "prepare_windows_icon.py", "verify_icons.py", "backend_worker.py"):
        ast.parse(
            (ROOT / name).read_text(encoding="utf-8"),
            filename=name,
        )
