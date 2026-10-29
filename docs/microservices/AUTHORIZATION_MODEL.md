# Authorization

Existing opaque revocable account sessions, active/expiry checks, workshop staff,
ownership and scoped consent remain the source of truth. USER/CUSTOMER/ADMIN are
server roles; MARKET is a separate presentation/merchant portal, not a privilege.
ADMIN has no automatic private vehicle/session bypass. Existing legacy API blocking
in ecosystem mode is preserved. New catalog gateway routes require an account.

Independent catalog authorization is a deployment bearer credential, never a user
password or frontend secret. No native client receives it. Public liveness exposes
only service identity/version/alive status. Ready/data require service authentication.
No customer database or account model is imported into the catalog service.

Runtime configuration changes require an existing authenticated ADMIN, optimistic
revision check and durable existing audit record before snapshot publication.
Security policy (read-only OBD, signed updates, disabled payment features), endpoints,
models and compile-time policy cannot be enabled or changed by runtime patch.
This remains a single-backend-process control plane, not a distributed lease system.
