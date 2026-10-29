# Global backend configuration

`global_config.json` is the canonical version-1 deployment baseline. The schema
is generated from `finalbuild/backend/configuration/models.py`. Validate it with
the local microservices tests; unknown fields and unsafe feature flags fail closed.
See [configuration architecture](../docs/microservices/CONFIGURATION_ARCHITECTURE.md)
and [adopted fields / staged policies](../docs/microservices/GLOBAL_CONFIG_REFERENCE.md).

Select `AI_CAR_CONFIG_ENV=development` (default), `testing` or `production`.
Production needs an explicitly installed `environments/production.json`, based
on the tracked example. Operator production configuration is Git-ignored.
Secrets remain in ENV; JSON contains only authorized ENV variable reference names.
Legacy `finalbuild/config/environment.json`, local and explicit ENV config continue
to work; explicit process values win. Do not edit compile-time policy to expect
a runtime C++ rebuild or enable disabled payments by JSON.
