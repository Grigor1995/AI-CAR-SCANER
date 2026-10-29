# Configuration reference and adoption

| Category | Consumer / current scope | Class |
|---|---|---|
| schema_version | strict v1 loader + generated schema | startup |
| app language/units; ui theme/chart | allowed preference model/default policy; existing native user settings retained | user preference |
| app name/version/platform/timezone | deployment metadata; native product identities remain fixed | startup |
| native min20/preferred23/enabled=false | build policy/reference; no compiler/runtime switch | static build time |
| ai provider/context/temperature/max_tokens/timeout/endpoint | startup ENV bridge to existing provider/local AI runtime | startup |
| ai model_path | startup model selection when explicitly changed from discovery directory | startup |
| ai offline/RAG/rules/ML | declared policy; existing engine flags not rewritten in this increment | startup policy |
| services backend_port | backend/setup startup bridge | startup |
| services vehicle_catalog mode/url/enabled/token_env/version | actual local/HTTP catalog adapter | startup/security |
| services catalog timeout/retries | actual HTTP request policy; admin patchable | runtime reloadable |
| services database_url_env | DATABASE_URL secret reference; existing persistence bootstrap retained | sensitive |
| obd timeouts/poll/retry/buffer | validated policy baseline; existing transport-specific overrides retained pending native bridge contract migration | startup policy |
| obd read_only/write_policy | cannot weaken via config; existing operation authorization preserved | sensitive |
| monitoring / notifications | existing in-app behavior, no external provider configured | startup policy |
| marketplace.enabled | policy metadata; existing server feature gate remains authoritative | startup policy |
| marketplace purchase/checkout/payments/subscriptions | Literal false; no active purchase routes | sensitive/disabled |
| updates.enabled=false/signed_required=true | future policy only; no update daemon/download route | sensitive/disabled |

Authorized ENV paths: AI_CAR_BACKEND_PORT, DIAGNOSTIC_LLM_PROVIDER,
LOCAL_LLM_SERVER_CONTEXT/URL/TIMEOUT_S, LOCAL_LLM_TEMPERATURE/MAX_TOKENS,
AI_CAR_CATALOG_MODE/URL. Existing other legacy ENV values keep their existing
consumer behavior; they are not blindly mapped into global configuration.

Schema regeneration: run Python to serialize `GlobalConfig.model_json_schema()`;
contract tests assert schema and checked-in JSON agree. Each field's bounds/defaults
are available in `config/global_config.schema.json`. Never store real credentials
in either JSON, documentation or layout exports.
