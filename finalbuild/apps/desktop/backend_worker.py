from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    # In a PyInstaller build the backend package is bundled under the
    # executable's extraction directory. In source mode, ROOT points at the
    # repository and backend is a normal package directory.
    if getattr(sys, "frozen", False):
        root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        root = Path(__file__).resolve().parents[2]

    backend = root / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

    import uvicorn

    host = os.environ.get("AI_CAR_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("AI_CAR_BACKEND_PORT", "8001"))
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        log_level=os.environ.get("AI_CAR_BACKEND_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
