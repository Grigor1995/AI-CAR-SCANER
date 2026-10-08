# Domain Model and Diagnostic Flow

## 1. Core domain object

`DiagnosticSession` is the root of the diagnostic workflow.

It contains:

- `session_id`
- `state`
- `vehicle`
- `symptoms`
- `dtcs`
- `evidence`
- `hypotheses`
- `recommendations`
- `test_results`
- `measurements`
- `live_data`
- `connected_device_id`
- `connection_type`
- `audit_log`

The session is therefore the bridge between user-reported information, measured vehicle information, reasoning and recommended actions.

## 2. Evidence model

Evidence has explicit provenance:

| Source | Meaning |
|---|---|
| `USER_REPORTED` | User supplied fact |
| `TECHNICIAN_OBSERVED` | Technician/test observation |
| `VEHICLE_MEASURED` | Direct vehicle measurement |
| `ECU_REPORTED` | ECU/DTC reported information |
| `DATABASE` | Database-derived information |
| `OEM_DOCUMENT` | OEM documentation |
| `RULE` | Deterministic rule output |
| `ML_MODEL` | ML-derived inference |
| `LLM_INFERENCE` | LLM inference |
| `HISTORICAL_CASE` | Historical diagnostic case |

Evidence status is also explicit:

- `reported`
- `measured`
- `calculated`
- `inferred`
- `confirmed`
- `rejected`

This distinction is fundamental to the product's trust model.

## 3. Diagnostic reasoning flow

~~~mermaid
flowchart LR
    INPUT["Symptoms / DTCs / telemetry / tests"] --> EX["Evidence extraction & normalization"]
    EX --> RULES["Deterministic diagnostic rules"]
    RULES --> H["Hypotheses"]
    H --> Q["Missing questions"]
    H --> PLAN["Decision engine"]
    PLAN --> TEST["Next diagnostic test"]
    TEST --> RESULT["Observed result"]
    RESULT --> E["New evidence"]
    E --> RULES
    H --> RET["Knowledge retrieval"]
    RET --> SAFE["Safe prompt context"]
    SAFE --> LLM["Optional local/cloud LLM"]
    LLM --> EXPLAIN["Explanation / orchestration"]
    EXPLAIN -. never replaces .-> RULES
~~~

## 4. Example: LPG misfire

The repository contains a golden case named `LPG_MISFIRE_001`.

The deterministic engine recognizes a focused domain when the evidence indicates:

- dual-fuel LPG/petrol vehicle,
- a P03xx misfire DTC,
- misfire/shaking behavior,
- LPG-specific behavior,
- petrol-normal comparison.

The resulting hypothesis domains are:

1. LPG fuel delivery / mixture.
2. Ignition / combustion.
3. Air-fuel / intake.
4. Mechanical cylinder condition.

The system intentionally does **not** jump directly to “coil failure confirmed”.

Instead it proposes evidence-producing tests such as fuel pressure, injector/mixture checks, ignition checks and mechanical validation according to the decision catalog and current evidence.

## 5. Decision engine

`DiagnosticDecisionEngine` ranks diagnostic candidates using the current evidence and test metadata.

`DiagnosticTest` includes:

- purpose,
- expected observation,
- safety notes,
- priority score,
- expected information gain,
- estimated cost,
- risk level,
- prerequisites,
- target hypotheses.

The conceptual objective is:

~~~text
choose next test =
    high information value
    + strong evidence fit
    + acceptable cost
    + acceptable safety risk
~~~

The API additionally requires safety confirmation for MEDIUM/HIGH risk selected tests.

## 6. Session lifecycle

The model defines these states:

~~~text
CREATED
  ↓
VEHICLE_IDENTIFIED
  ↓
SYMPTOMS_COLLECTED
  ↓
INITIAL_ANALYSIS
  ↓
QUESTIONS_PENDING
  ↓
DATA_COLLECTION
  ↓
TESTING
  ↓
HYPOTHESIS_VALIDATION
  ↓
ROOT_CAUSE_FOUND
  ↓
REPAIR
  ↓
POST_REPAIR_VERIFICATION
  ↓
CLOSED
~~~

Not every session must traverse every state. The implementation can remain in analysis/testing when evidence is insufficient.

## 7. API lifecycle

A simplified request path is:

~~~text
POST /api/v1/sessions
  -> DiagnosticSession created

PUT /api/v1/sessions/{id}/vehicle
  -> vehicle identity added

POST /api/v1/sessions/{id}/symptoms
  -> USER_REPORTED evidence created

POST /api/v1/sessions/{id}/dtcs
  -> DTC + evidence created

POST /api/v1/sessions/{id}/analyze
  -> normalize evidence
  -> deterministic rules
  -> intelligence scoring/questions
  -> decision recommendations
  -> localization

POST /api/v1/intelligence/{id}/...
  -> record/interpret measured test evidence

GET /api/v1/decision/sessions/{id}/plan
  -> ranked diagnostic plan
~~~

## 8. Persistence model

There are two complementary persistence concepts in the current repository.

### Normalized SQLAlchemy schema

`diagnostic/db_models.py` defines:

- `vehicles`
- `diagnostic_sessions`
- `evidence`
- `vehicle_catalog_entries`

### Complete session snapshot

`diagnostic/session_persistence.py` defines `diagnostic_session_state`.

The API keeps the Pydantic `DiagnosticSession` in an in-process dictionary for fast access and writes the complete JSON-compatible session payload to the configured database.

This is currently a **snapshot persistence architecture**, not a full repository/service abstraction.

## 9. State ownership

| Concern | Current owner |
|---|---|
| HTTP routing | `backend/api` |
| Session runtime registry | `backend/api/state.py` |
| Session snapshot persistence | `diagnostic/session_persistence.py` |
| Domain model | `diagnostic/models.py` |
| Deterministic reasoning | `diagnostic/rules.py` |
| Decision/test selection | `diagnostic/decision.py` |
| Intelligence orchestration | `ai/reasoning/engine.py` |
| Retrieval orchestration | `ai/reasoning/pipeline.py` |
| RAG store | `ai/rag/store.py` |
| LLM selection | `ai/llm/factory.py` |
| VCI/device lifecycle | `device/manager.py` |
| Telemetry acquisition | `acquisition/service.py` |
