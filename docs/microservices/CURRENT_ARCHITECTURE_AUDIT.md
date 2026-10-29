# Pre-extraction audit

Baseline 965ed9c, existing AI-CAR-SCANER, 2026-10-29. 1,151 tracked paths,
486 Python, 59 Kotlin, 20 Swift. C++ exists only as an experimental mean kernel;
there is no deployed native diagnostic core. Three fixed-role clients share one
FastAPI process. Existing 1105 common tests and five Desktop groups passed in
the preceding deployment split; these are baseline evidence, not current-run QA.

Existing global ENV JSON is flat, versioned, process-override aware, but has no
nested policy schema or authorized runtime configuration. Backend v2 business
APIs share SQLAlchemy identity/ownership/consent/diagnostic/workshop/merchant
transactions. Cross-domain joins in ecosystem/business_api.py and business_service.py
are real coupling and prevent independently claiming those domains are extracted.
Legacy APIs also own global sessions and telemetry samples. Vehicle catalog lookup
is a stateless cached read model over local JSON with no identity/private SQL.
It is the first low-risk independent process candidate. LLM inference already has
an external native llama-server HTTP boundary; do not rewrite inference in C++.

Native clients remain thin UI/transport. DiagnosticSession, rules, units, assets,
local legacy compatibility and permission checks must stay intact. No provider,
licensed wiring source, payment or broker is configured. No CI/CD will be added.
All remaining contexts are explicitly embedded/planned, not newly deployed services.
