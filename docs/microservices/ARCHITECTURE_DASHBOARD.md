# Architecture explorer

Open the preserved `docs/architecture/interactive_architecture.html` locally; all
scripts/data/styles are bundled. Original ten views/pan/zoom/theme/search/layer
controls remain. Twelve source views distinguish services, dependencies, files,
classes, calls, API/events, ownership, C++ experimental core, native platforms,
disabled purchase, and before/after migration. No health polling is fabricated.

Use the source service dropdown, search and kind filter to narrow actual indexed
files/symbols. Click a result for repository-relative path, span, signature,
breadcrumbs, members, incoming/outgoing calls/import evidence, API decorators and
bounded read-only numbered source preview. Back/forward preserve navigation.
Copy path uses clipboard with text fallback. Focus graph shows at most 61 selected
and neighboring nodes; lists cap at 100 and previews at 220 lines. Refine search to
reach additional results rather than rendering thousands of graph nodes.

Drag a node to reposition; Ctrl/Shift select multiple before dragging. A movement
threshold separates drag from click. Pan on background, wheel/toolbar zoom, fit,
layer collapse and auto-layout/reset remain. Positions persist by stable ID in
localStorage; export/import JSON validates bounded finite coordinates and schema
before replacing positions. Invalid storage/import never executes content.

Blue edges in source graphs mean static import/call bindings, not live requests.
Unknown relationships remain unresolved in the inspector; no speculative relation
is shown as verified. All deployment/runtime labels explicitly separate embedded,
optional standalone, planned and NOT_PROBED. Configuration section is a read-only
sanitized checked-in snapshot, not an admin editor or live deployment status.
