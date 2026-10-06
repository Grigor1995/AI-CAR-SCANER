import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BACKEND=ROOT/'backend'
for p in (BACKEND, ROOT):
    if str(p) not in sys.path: sys.path.append(str(p))
