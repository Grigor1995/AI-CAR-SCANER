from dataclasses import dataclass

@dataclass(frozen=True)
class TenantContext:
    organization_id: str
    actor_id: str

class TenantIsolationError(PermissionError): pass

def require_same_tenant(context: TenantContext, organization_id: str):
    if context.organization_id != organization_id:
        raise TenantIsolationError("cross-organization access denied")
