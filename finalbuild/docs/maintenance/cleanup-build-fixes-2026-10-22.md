# Repository cleanup and local builder repair — 2026-10-22

## Reported failure

The Windows Desktop log showed three failing tests, while both coverage gates
passed. Android was interrupted with KeyboardInterrupt; the supplied log did
not show an Android compiler failure.

- The default llama-server URL test inherited LLM_BASE_URL=...:1234, although
  its assertion intentionally checks the unconfigured :8000 default. It now
  clears both URL overrides inside that test.
- The launcher error-path test depended on the user's selected AI provider.
  It now explicitly selects llama-server for the branch it exercises.
- PDF export now uses an explicit 10-point font and black printable text,
  avoiding pixel-only default system fonts and dark-theme ink. The regression
  checks that diagnostic content remains extractable and private IDs remain
  absent, including when the document initially has a pixel-only font.
  Native Windows PDF behavior still needs confirmation on Windows.

Application AI settings and coverage thresholds were preserved.

## Builder behavior

Commands display live output while retaining complete logs. Python child
output is unbuffered. Timeout/Ctrl+C terminates the builder-owned command
process group/tree. Ctrl+C records CANCELLED and NOT_RUN targets and returns
130 without a raw interruption traceback. Other independent targets still
run after an ordinary target failure.

Desktop reports now belong to each timestamped run under
`artifacts/<run>/desktop/test-reports/`. The test runner accepts report paths
outside finalbuild and records absolute log/JUnit paths.

## Cleanup scope

Reviewed tracked source, native asset loaders, build/test scripts, ignores and
build outputs. Removed 44 unused mobile SVG illustrations (22 per platform),
after verifying both native loaders use PNG and each removed SVG has its PNG
counterpart. All 66 PNG model portraits remain. Desktop's SVG fallback remains
used and tested. Historical reports and the requested PPTX/demo evidence remain.
The branch merge report describes the earlier merge state; this cleanup
supersedes its statement that mobile SVGs remain packaged.

Added root Python cache/venv/coverage ignores. Generated SDKs, caches, build
artifacts and user environments remain local. Added root pytest configuration
and removed current-directory assumptions in golden-case fixture paths so
`python -m pytest` works from the repository root without collecting the
manual live-server probe in scripts/test_llama_server.py.

## Validation

- Root Python suite: 591 passed, 2 skipped.
- Desktop matrix with inherited external AI provider/URL: 384 passed,
  1 skipped; all five groups PASS; production core coverage 91.17%, combined
  Desktop source coverage 90.20%.
- Android: unified builder with --with-tests PASS; debug APK produced;
  assembleDebug, JVM tests and lintDebug successful. Existing cached tasks
  are reported by Gradle as up-to-date.
- Regression checks cover command failure/log retention, timeout/live output,
  cancellation summary and pending targets, PDF content/privacy and fonts.
- This Linux environment does not validate Windows EXE packaging or native
  iOS/Xcode builds. No claim of Windows/macOS packaging success is made.
