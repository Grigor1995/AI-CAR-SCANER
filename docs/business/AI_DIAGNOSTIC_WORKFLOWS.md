# Ai Diagnostic Workflows

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Authenticated diagnostic creation reuses the canonical Vehicle and DiagnosticSession,
excluding arbitrary private profile metadata. Evidence inputs validate symptom text
and DTC format. Existing DiagnosticIntelligenceEngine analyzes the same rules and
recommendation flow. Test result must reference a current recommendation; append
to canonical history/evidence then recalculate. UNKNOWN maps to INCOMPLETE.
No product/offer/discount enters technical confidence ranking.

Native snapshot decoding preserves source native_transport_bridge and
hardware_verified=false, with timestamps and missing channels as null. It is a
client-observed transport claim, not independently verified hardware. Read-only
polling plan is shared; actual transport authorization/hardware remains necessary.
Existing LLM/RAG optional providers are retained, not falsely tested with a model.
Full French AI/test explanations and authenticated business PDF UI are PLANNED.

Business diagnostic responses now reuse existing EN/HY/RU localization on detached copies. Canonical stored categories/evidence remain untranslated. French preference uses an explicit English fallback with Content-Language: en and X-Language-Fallback: true; full French diagnostic explanations are not claimed.
