# AI diagnosis and provider boundaries

Reuse `ai/llm/factory.py`, current local llama-server and HTTP providers,
RAG ingestion/retrieval, `ai/interfaces.py`, anomaly detection and deterministic
reasoning. The local GGUF configuration/installer remains unchanged in this
foundation branch. Existing language localization remains EN/HY/RU.

Factual readings come from the ECU/device with timestamps/provenance; LLM
outputs are proposals validated against schemas, not new measurements. Tests
and verified evidence revise hypotheses. Unknown data stays unknown. No
unrestricted tool-to-ECU-write execution is introduced.

Future work: evidence-required structured repair plans, privacy-scoped retrieval,
provider failure/circuit-breaker policy, per-mode authorizations and calibrated
uncertainty evaluation. External LLM health, GGUF inference quality and provider
billing are not validated by deterministic fixture tests.
