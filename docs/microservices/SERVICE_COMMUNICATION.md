# Communication and failure handling

Native clients → authenticated backend REST. Existing telemetry/transport bridges
keep their platform mechanisms. Gateway → catalog optionally uses GET over HTTP
on loopback or HTTPS remotely. A 32–512 ASCII non-whitespace service token comes
only from `AI_CAR_VEHICLE_SERVICE_TOKEN`; missing/invalid token fails closed.
Never commit a real token. Gateway refuses redirects, caps response size at 4 MiB,
checks top-level DTO shape and uses 0.1–30 second timeout with 0–2 read retries.
HTTP 429/502/503/504 and network failures may retry; auth/validation failures and
invalid JSON do not. No mutation is retried. Retry budget is intentionally small;
there is no speculative broker/circuit-breaker background loop.

Correlation IDs accept bounded safe characters or are generated, returned in
X-Correlation-ID and propagated to the catalog. No user data is put in the header.
Catalog downtime does not prevent unrelated backend APIs from operating. Errors
stay sanitized. Remote service TLS termination/credential rotation and network
isolation are operator responsibilities; this increment is not an mTLS platform.
