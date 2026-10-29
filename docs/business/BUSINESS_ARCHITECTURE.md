# Business Architecture

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Native PySide6/Compose/SwiftUI clients → FastAPI v2 boundary → identity and
object-scoped business services → canonical diagnostic engine / SQL persistence.
Legacy local APIs remain feature-off compatible; ecosystem mode blocks anonymous
legacy /api paths. No silent partial auth wrapping of legacy endpoints.

Business API is orchestration; services own consent/quote/schedule/diagnostic
rules; strict Pydantic contracts validate inputs; SQLAlchemy models own aggregates.
DiagnosticRecord stores one canonical DiagnosticSession payload plus profile/center
binding and optimistic version. Model logic is not duplicated per platform/role.
Monitoring has lifecycle records but no autonomous gateway executor. Notifications
have in-app storage but no delivery service. No new deployed microservice or C++
module is justified by this business change.
