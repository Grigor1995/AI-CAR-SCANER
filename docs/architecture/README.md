# Interactive architecture

Open `interactive_architecture.html`. All JavaScript/CSS/data are local and
require no CDN. If browser policy blocks local file URLs, from the repository
root run:

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Then open `http://127.0.0.1:8765/architecture/interactive_architecture.html`.

Select any of ten views, search module/API/responsibility text, filter layers
and offline/online paths, click modules/arrows, collapse groups, drag background
to pan, use mouse-wheel/buttons to zoom, and switch dark/light appearance.
The layout adapts to narrow viewports. Planned modules are dashed and labeled;
view descriptions distinguish current topology from incomplete product flows.

`architecture-data.js` is the maintained diagram model. Generate matching
Mermaid views with:

```bash
python finalbuild/scripts/export_architecture_mermaid.py
```

`architecture.mmd` is the high-level alias; each other `.mmd` is a selectable
view's source. The production proposal for C++ is explicitly not an implemented
core. MARKET is a portal role, not a fourth primary mode.

`ecosystem-openapi.json` contains generated implemented request/response schemas,
including the opaque bearer scheme and localized error envelope. Regenerate:

```bash
python finalbuild/scripts/export_ecosystem_openapi.py
```

Actual browser QA is reproducible with
`python finalbuild/scripts/check_architecture_browser.py --browser /path/to/chromium`.
It uses a temporary browser profile and local HTTP server, not external sites.
Execution evidence is under `../evidence/architecture-browser-checks.json`;
the PNG is supporting evidence, not a replacement for the interactive diagram.

## Measured performance audit

Open [performance_architecture_dashboard.html](performance_architecture_dashboard.html)
for the bundled architecture graph, measured baseline, paired before/after data
and isolated C++ experiment. See [performance reports](../performance/FINAL_PERFORMANCE_REPORT.md)
for reproduction commands and unmeasured hardware/platform limitations.

## Business transformation

Open [business_architecture_dashboard.html](business_architecture_dashboard.html)
for current business roles, permission boundaries, before/after views and explicit
partial/planned components. See [business report](../business/FINAL_BUSINESS_MIGRATION_REPORT.md)
for actual implemented scope, local run and remaining provider/native UI work.
