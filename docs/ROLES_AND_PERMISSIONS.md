# Roles and permissions

Exactly three primary modes: USER, CUSTOMER, ADMIN. MARKET is a merchant portal
role, never a fourth mode. Registration grants USER only. Caller-provided role
lists/admin flags are rejected. Public creation of a service center grants its
creator CUSTOMER and owner membership; it does not verify the business or grant
platform ADMIN. Platform ADMIN/MARKET provisioning is an operator-controlled
future/admin milestone; there is no public self-elevation endpoint.

| Action | USER | CUSTOMER | ADMIN | MARKET |
|---|---|---|---|---|
| Own account/profile/vehicles | yes | eligible USER | eligible USER | eligible USER |
| Manage a service center | no | staff owner/admin in that center | no implicit bypass | no |
| Invite an owner | no | owner/admin in that center | no implicit bypass | no |
| Accept/revoke vehicle consent | vehicle owner only | same if owner | same if owner | same if owner |
| Read another owner's approved vehicle | no | current staff + unexpired scoped consent | not by role alone | no |
| Select primary workspace | authorized roles only | CUSTOMER role required | ADMIN role required | not a primary mode |
| Merchant products/offers | planned | read eligible offers later | moderation later | portal later |

Reuse professional_platform.models.Role for staff roles: owner/admin/technician/
viewer. These are scoped staff permissions, not global roles. Consent scopes in
the first milestone are read-only; live/report scope plumbing is reserved for
later authenticated diagnostic endpoints. A role claim in an old JWT cannot
substitute for a current database-backed account session.
