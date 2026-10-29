# User Mode

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

PARTIALLY IMPLEMENTED overall. Backend: account lifecycle, multi-vehicle
ownership, durable scoped sessions/evidence/test results, validated native snapshot
observations, histories, settings, consent revoke, directory and quotes.
Account browser on each native platform: registration, login/logout, role-selected
reads. Existing local diagnostic screens remain unchanged, not authenticated
mutation replacements. Production account verification providers, complete native
business editors and French diagnostic explanations are not finished.

A user creates an owned profile, creates /diagnostics with profile_id, submits
symptom/DTC evidence to /analyze, records an existing recommendation result via
/tests/{test_id}, reads updated hypotheses/session. OBD plan is read-only;
bridge decodes supported responses and labels hardware_verified false. Missing
channels remain null. Reports are canonical session output; business PDF UI/export
is not added by this increment.
