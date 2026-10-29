# Data Sharing And Consent

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Per-request checks: token active, account active, membership active, center
active, exact ownership matches grant owner, owner account active, grant unrevoked,
expiry in future, named scope present, staff level sufficient for mutation.
Session center binding prevents another center reading shared history via guessed
session IDs. Owner can inspect their own workshop sessions. Personal sessions
are not made visible to a workshop just because it holds another vehicle grant.
Dashboard record counts also respect report/history or maintenance-read scope.

Scopes distinguish vehicle/report/history/live reads from diagnostics/maintenance
writes. Canonical profile metadata is excluded when creating scoped sessions.
Account/password hashes/auth tokens are never SQL-row response serialization.
Private reads and business writes record actor/action/target, not bearer/password.
No unrestricted ADMIN private-data path is added.
