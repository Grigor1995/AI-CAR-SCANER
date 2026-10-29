# Global configuration

Canonical `config/global_config.json`, generated Draft 2020-12 JSON Schema and
`config/environments/{development,testing,production.example}.json`. Version 1,
unknown fields rejected, strict scalar validation, frozen nested Pydantic models.
Snapshot is immutable; callers receive new serialized public copies. Production
requires an explicitly installed `production.json`; example is never auto-activated.
No model download, credential or endpoint is fetched from arbitrary remote config.

Precedence: typed defaults → canonical global JSON → selected environment overlay
(`AI_CAR_CONFIG_ENV`) → documented allowlisted process ENV → allowed preferences.
Legacy environment.json/local/AI_CAR_ENV_CONFIG still work as a compatibility input;
explicit process ENV wins. Default AI endpoint does not override a legacy custom
port. Existing model auto-discovery remains operational when model_path is `models`.

Classification: native.* STATIC_BUILD_TIME; catalog timeout/retries RUNTIME_RELOADABLE;
app language/units and UI chart/theme USER_PREFERENCE; credentials references,
OBD write safety, payments and updates SECURITY_SENSITIVE; remaining STARTUP_ONLY.
Changing JSON cannot compile C++ or dynamically replace llama-server. Endpoint and
model changes require restart. Only existing ADMIN can patch the two reloadable
read-adapter policies. Audit failure leaves previous snapshot/revision untouched.
Revision is process-local; runtime overrides deliberately reset on restart.

Secrets are environment references only; no password/token/API key fields exist.
Remote catalog requires HTTPS, origins reject userinfo/query/fragment. Public
snapshot excludes model paths, internal URLs and secret ENV references. Error
messages never serialize Pydantic raw input. Offline explorer shows safe checked-in
policy defaults, explicitly not live runtime health or mutable control plane.

First-clone runner bootstrap uses only the shared stdlib JSON/version reader and
bounded startup-field preflight, so no backend/Pydantic install is required to
start setup. Once dependencies are installed, setup validates the full schema in
the project venv before proceeding. Backend startup always uses full validation;
bootstrap mode is not a service configuration/security fallback. Root imports
(`finalbuild.shared`) and module imports (`shared`) resolve the same config source.
