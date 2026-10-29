# Incremental extraction plan

1. Capture actual source ownership/imports/calls and shared-table coupling.
2. Add strict immutable global config snapshots with a legacy ENV bridge;
   preserve explicit process/local overrides, keep payments and unsafe writes disabled.
3. Extract a real read-only vehicle-catalog process with independent API/token,
   data files, liveness/readiness and optional gateway adapter. Embedded mode stays
   default so local calls do not gain unnecessary network overhead.
4. Keep identity/consent/private diagnostics/workshop/market transactions embedded
   until repository contracts and explicit transactional event delivery are ready.
   Do not claim a separate database owner merely by renaming these folders.
5. Generate language-aware source indices and extend the existing static HTML
   explorer with truthful resolution labels and bounded graph rendering.
6. Generate the three requested icon variants while retaining other UI assets.
7. Run config, extraction, parser/index, browser, API, native and regression checks;
   record actual PASS/BLOCKED status and remaining migration work.
