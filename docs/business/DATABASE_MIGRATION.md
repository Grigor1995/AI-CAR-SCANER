# Database Migration

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

Version 0002_business follows 0001_ecosystem and adds exactly 12 tables:
ecosystem_settings, ecosystem_diagnostics, ecosystem_staff_invitations,
ecosystem_work_orders, ecosystem_merchants, ecosystem_products, ecosystem_offers,
ecosystem_monitoring_schedules, ecosystem_monitoring_runs,
ecosystem_notifications, ecosystem_directory_details, ecosystem_technical_references.
All foundation/legacy tables and rows are preserved. Foreign keys, indexed owner/
center/product/schedule keys, nonnegative stock/price, moderation/status checks,
unique schedule and due-run constraints enforce boundaries. Diagnostics use
SQLAlchemy optimistic version checks; stale saves return conflict.

French is stored in account Settings instead of destructive replacement of the
legacy account language constraint. /me retains legacy account language; /settings
is authoritative for the full four-language preference. No anonymous vehicle is
automatically assigned to an account. Production legacy histories require an
explicit verified owner mapping/import process, not guessed ownership.

Back up database and file assets before upgrade. For SQLite, stop writers and use
sqlite backup API or a consistent application backup; for PostgreSQL use pg_dump
with an audited restore test. Apply alembic upgrade head to a copied staging DB
first. Tests exercise legacy row preservation and schema roundtrip.
Downgrade to 0001 removes new workflow tables/data: export/back up these first.
Do not downgrade a live business installation without maintenance window and
restore plan. Live PostgreSQL migration/concurrency remains NOT RUN; SQLite
migration and offline PostgreSQL DDL were validated.
