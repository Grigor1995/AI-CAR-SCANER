# Regression report

Final measured results are recorded in `docs/evidence/microservices-validation.json`
and FINAL_IMPLEMENTATION_REPORT.md after local checks finish. Earlier failing
runs found and fixed legacy LLM URL/port precedence. A Desktop Qt logic
run exposed cyclic native wrapper collection on an HTTP worker thread. Test teardown
now collects those wrappers on the GUI thread while retaining one QApplication;
the final complete rerun passes. No thresholds
are lowered and a failed run is never relabeled as success.

Android build/compile/test/lint succeeded for USER, CUSTOMER and MARKET after
product icon wiring (199 tasks; 75 executed, 124 cached, 2m53s). Browser original
interactions plus 12 source views, bounded graph, source search, layout validation
and real node drag passed in Chromium. These are actual local checks.

BLOCKED: Windows executable/installer runtime, macOS Xcode/iOS runtime/signing,
physical Bluetooth/Wi-Fi/USB OBD and model/hardware protocols, notification delivery
providers and licensed repair/wiring data. No live payment or update service exists.
Docker packaging was updated statically; image execution was not claimed tested.

Desktop final: all five groups PASS, combined source coverage 90.06%, production
core 90.36% against the unchanged >=90% gate. Logic: 229 passed/1 skipped;
diagnostic-e2e: 6; negative: 68; UI POM: 142; UI widgets: 25.

Common suite final: 1133 passed, 2 skipped in 72.36s. Separate real gateway/catalog
HTTP smoke: 13 checks pass, including account-protected five operations, catalog
shutdown → 503 with identity still working, and embedded rollback preserving bearer/account.
