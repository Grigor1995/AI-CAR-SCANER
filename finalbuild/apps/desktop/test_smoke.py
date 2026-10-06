from pathlib import Path
import ast

ROOT = Path(__file__).parent
for name in ("main.py", "ui.py", "api_client.py", "models.py", "storage.py"):
    ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)
print("PySide6 desktop source syntax: OK")
