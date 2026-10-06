#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv-desktop
.venv-desktop/bin/python -m pip install --upgrade pip
.venv-desktop/bin/python -m pip install -r apps/desktop/requirements.txt
