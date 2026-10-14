# Local Python Coverage Audit

## Current test baseline

Latest developer-provided local test results, before this coverage measurement:

- Main Python suite: **202 passed, 1 skipped** in 26.80 seconds.
- Desktop UI POM suite: **28 passed** in 3.26 seconds.
- No warning summary was present in the supplied outputs.
- **Coverage percentage has not been measured yet.** Passing tests alone does not establish code coverage.

The main suite and Qt UI suite are intentionally run separately. `pytest.ini` discovers `tests/` by default; the desktop UI tests live under `apps/desktop/tests/` and are invoked explicitly.

## Step 1 — collect a Python source coverage baseline

Run from `finalbuild/` in the activated project virtual environment. The first run measures backend, device/protocol roots and the named Desktop production modules while using the current main suite.

```bash
python -m pytest -q tests \
  --cov=backend \
  --cov=vehicle \
  --cov=device \
  --cov=apps.desktop.api_client \
  --cov=apps.desktop.models \
  --cov=apps.desktop.storage \
  --cov=apps.desktop.main \
  --cov=apps.desktop.backend_worker \
  --cov=apps.desktop.ui \
  --cov=apps.desktop.prepare_windows_icon \
  --cov-report=term-missing \
  --cov-report=json:coverage-python-audit.json
```

## Step 2 — append Desktop tests to the same measurement

Use the **same `--cov` source arguments** and add `--cov-append` so results from the first run are retained. The widget suite known to have a native Qt teardown issue is excluded; the POM tests are included.

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q apps/desktop/tests \
  --ignore=apps/desktop/tests/test_ui_widgets.py \
  --cov=backend \
  --cov=vehicle \
  --cov=device \
  --cov=apps.desktop.api_client \
  --cov=apps.desktop.models \
  --cov=apps.desktop.storage \
  --cov=apps.desktop.main \
  --cov=apps.desktop.backend_worker \
  --cov=apps.desktop.ui \
  --cov=apps.desktop.prepare_windows_icon \
  --cov-append \
  --cov-report=term-missing \
  --cov-report=xml:coverage-python-audit.xml \
  --cov-report=json:coverage-python-audit.json \
  --cov-report=html:htmlcov-coverage-audit
```

After this run, `coverage-python-audit.json` represents the combined measurement for the two test runs. Keep this as a local artifact; do not commit generated coverage output.

## Step 3 — list source files below 70%

Run this Bash here-document from the same `finalbuild/` directory. It reads the JSON report and prints the total percentage plus every measured production source file below 70%, including files at 0%.

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("coverage-python-audit.json")
if not path.is_file():
    raise SystemExit("Missing coverage-python-audit.json; complete Steps 1 and 2 first.")

data = json.loads(path.read_text(encoding="utf-8"))
print(f"Combined scoped coverage: {data['totals']['percent_covered']:.2f}%")
low = []
for filename, item in data["files"].items():
    summary = item["summary"]
    statements = summary.get("num_statements", 0)
    if statements and summary.get("percent_covered", 0.0) < 70.0:
        low.append((
            summary.get("percent_covered", 0.0),
            filename,
            statements,
            summary.get("missing_lines", 0),
            item.get("missing_lines", []),
        ))

if not low:
    print("No measured source files are below 70%.")
else:
    print(f"Source files below 70%: {len(low)}")
    for percent, filename, statements, missing_count, lines in sorted(low):
        line_list = ",".join(map(str, lines))
        print(f"{percent:6.2f}% | {filename} | missing statements={missing_count}/{statements} | lines={line_list}")
PY
```

## How to interpret the result

- This is a **scoped Python audit**, not whole-repository or all-platform coverage. Android and iOS require their own native coverage reports.
- The existing CI 90% backend gate is limited to selected diagnostic, telemetry, multi-ECU, simulator, global-data and AI modules. It is not a 90% whole-project gate.
- The existing desktop 95% gate measures a smaller set of API-client/model/storage modules; it does not mean every Desktop production file has 95% coverage.
- First identify genuine active production files at 0%, then add focused tests for those files and for important uncovered branches. Next raise active production files toward the 70% target and the measured scoped total toward 70%.
- Do not include generated files, test files, obsolete code or intentionally platform-specific files in the production denominator without first confirming they are active.
- No CI is required for this audit. Run locally, then use the JSON summary and low-coverage list to plan the next small batch of tests.
