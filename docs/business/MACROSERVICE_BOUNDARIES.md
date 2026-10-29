# Macroservice Boundaries

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Logical modules in the existing backend process:
identity/access; vehicles/consents; diagnostics + existing AI/OBD; workshop/staff;
marketplace/moderation; settings; monitoring lifecycle/in-app notifications;
administrative governance. Existing platform update infrastructure retained.
Future billing remains inactive. These are module seams, not fake independent
services or distributed transactions. Adapter transport stays native/local;
domain decisions stay shared backend. External verification/delivery/licensed
repair/gateway interfaces require actual providers before deployment.
