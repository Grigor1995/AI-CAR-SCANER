# Shared diagnostic engine

Canonical data is `diagnostic.models.DiagnosticSession`; deterministic
`diagnostic.rules` and `ai.reasoning.engine` already normalize evidence, rank
hypotheses, select tests and replay outcomes. Keep TestResult and history as
source of truth; avoid separate user/workshop engines. No scoring rewrite is
part of foundation.

Provenance includes USER_REPORTED, ECU_REPORTED, VEHICLE_MEASURED, RULE,
ML_MODEL, LLM_INFERENCE, HISTORICAL_CASE and SIMULATOR. The existing enum names
are retained rather than renamed to match shorter product labels. Simulator
measurements never become vehicle-measured evidence. Existing heuristic
confidence scores must not be presented as calibrated failure probabilities.

Golden regression: W211 E350 M272, LPG shaking/misfire under load, petrol normal,
P0302. Validate LPG evidence/ranking, recommended discriminating tests, outcome
recalculation and absence of unsupported confirmed-component claims. New
account ownership will wrap this same model in milestone 1B.
