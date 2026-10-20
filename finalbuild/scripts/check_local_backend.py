"""Exercise the real Desktop launcher with isolated storage and a restart.

Run from finalbuild: python scripts/check_local_backend.py
Never connects to a configured user database or requires Qt/LLM/hardware.
"""
from pathlib import Path
import os
import socket
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import requests

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="ai-car-backend-check-") as folder:
        os.environ.update({
            "APPDATA": folder,
            "AI_CAR_BACKEND_HOST": "127.0.0.1",
            "AI_CAR_BACKEND_PORT": str(port),
            "AI_CAR_BACKEND_URL": f"http://127.0.0.1:{port}",
            "AI_CAR_USE_LOCAL_DATABASE": "1",
            "AI_CAR_DISABLE_LLM_AUTOSTART": "1",
        })
        from apps.desktop import main as launcher

        try:
            started = time.monotonic()
            launcher.start_backend()
            print(f"PASS: real launcher ready in {time.monotonic() - started:.2f}s")
            with requests.Session() as client:
                client.trust_env = False
                def request(method, path, **kwargs):
                    response = client.request(method, launcher.BACKEND_URL + path, timeout=10, **kwargs)
                    response.raise_for_status()
                    return response.json()

                assert request("GET", "/health")["status"] == "ok"
                catalog = request("GET", "/api/v1/vehicle-catalog/entries")
                assert catalog and all(isinstance(row["fuel"], list) for row in catalog)
                print(f"PASS: catalog contains {len(catalog)} rows with valid fuel lists")
                created = request("POST", "/api/v1/sessions", json={})
                sid = created["session_id"]
                path = f"/api/v1/sessions/{sid}"
                request("POST", path + "/symptoms", json={"raw_text": "Engine misfires on LPG; petrol runs normally"})
                request("POST", path + "/dtcs", json={"code": "P0302"})
                result = request("POST", path + "/analyze")
                assert result["hypotheses"] and result["recommendations"]
                print("PASS: session, symptoms, DTC and diagnostic analysis")
                launcher.stop_backend()
                launcher.start_backend()
                restored = request("GET", path)
                assert restored["dtcs"][0]["code"] == "P0302"
                assert restored["hypotheses"] == result["hypotheses"]
                assert len(request("GET", "/api/v1/vehicle-catalog/entries")) == len(catalog)
                print("PASS: session/analysis retained after restart; catalog unchanged")
        except Exception:
            log = Path(folder) / "AI-Car-Scanner/backend.log"
            if log.exists():
                print(log.read_text(encoding="utf-8", errors="replace")[-16000:], file=sys.stderr)
            raise
        finally:
            launcher.stop_backend()


if __name__ == "__main__":
    main()
