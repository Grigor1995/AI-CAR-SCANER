window.BUSINESS_DATA={
  "nodes": [
    {
      "id": "user",
      "name": "USER",
      "layer": "Roles",
      "status": "IMPLEMENTED",
      "responsibility": "Vehicle owner; explicit per-vehicle sharing; no workshop or admin bypass.",
      "rules": "Vehicle owner; explicit per-vehicle sharing; no workshop or admin bypass.",
      "api": "/accounts; /me; /vehicles",
      "entities": "Account, Ownership",
      "dependencies": "Identity",
      "permissions": "Authenticated owner",
      "files": "backend/ecosystem/api.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 20,
      "y": 20
    },
    {
      "id": "customer",
      "name": "CUSTOMER",
      "layer": "Roles",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Workshop staff and professional features through grants; native mutation forms remain incomplete.",
      "rules": "Workshop staff and professional features through grants; native mutation forms remain incomplete.",
      "api": "/service-centers; /staff-invitations",
      "entities": "ServiceCenter, Staff, Consent",
      "dependencies": "Workshop, Identity",
      "permissions": "Active staff role + explicit resource scope",
      "files": "backend/ecosystem/business_api.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 290,
      "y": 20
    },
    {
      "id": "admin",
      "name": "ADMIN",
      "layer": "Roles",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Governance, aggregates and moderation; private diagnostics remain inaccessible without ownership/consent.",
      "rules": "Governance, aggregates and moderation; private diagnostics remain inaccessible without ownership/consent.",
      "api": "/admin/*",
      "entities": "AccountRole, AuditEvent",
      "dependencies": "Identity, Marketplace",
      "permissions": "ADMIN checked on every request",
      "files": "backend/ecosystem/business_api.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 560,
      "y": 20
    },
    {
      "id": "market",
      "name": "MARKET portal",
      "layer": "Roles",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Merchant portal, not primary diagnostic mode; no checkout or payment collection.",
      "rules": "Merchant portal, not primary diagnostic mode; no checkout or payment collection.",
      "api": "/merchants; /products",
      "entities": "Merchant, Product, Offer",
      "dependencies": "Identity",
      "permissions": "MARKET plus merchant ownership",
      "files": "backend/ecosystem/business_service.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 830,
      "y": 20
    },
    {
      "id": "clients",
      "name": "Windows / Android / iOS",
      "layer": "Clients",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Three independent USER/CUSTOMER/MARKET apps on each platform; one shared backend. Account registration/login, fixed-role reads and business onboarding work; full business editors remain partial.",
      "rules": "Three independent USER/CUSTOMER/MARKET apps on each platform; one shared backend. Account registration/login, fixed-role reads and business onboarding work; full business editors remain partial.",
      "api": "/auth/login; /navigation",
      "entities": "Transient bearer only",
      "dependencies": "Backend API",
      "permissions": "Server authorization; no credentials in preferences",
      "files": "apps/user/main.py; apps/customer/main.py; apps/market/main.py; apps/desktop/product_app.py; mobile-android productFlavors; mobile-ios project.yml",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 20,
      "y": 160
    },
    {
      "id": "identity",
      "name": "Identity & settings",
      "layer": "Core",
      "status": "IMPLEMENTED",
      "responsibility": "Scrypt, revocable bearer, primary modes and account preferences. French preference/error/navigation supported; full native French is partial.",
      "rules": "Scrypt, revocable bearer, primary modes and account preferences. French preference/error/navigation supported; full native French is partial.",
      "api": "/auth; /settings",
      "entities": "Account, AuthSession, Settings",
      "dependencies": "SQL database",
      "permissions": "Account active, token active/unexpired",
      "files": "backend/ecosystem/api.py; business_schemas.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 290,
      "y": 160
    },
    {
      "id": "vehicle",
      "name": "Vehicle ownership",
      "layer": "Core",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Reuse canonical catalog/profile schema. No automatic assignment of anonymous legacy records. New owned vehicles supported; migration needs explicit mapping.",
      "rules": "Reuse canonical catalog/profile schema. No automatic assignment of anonymous legacy records. New owned vehicles supported; migration needs explicit mapping.",
      "api": "/vehicles",
      "entities": "vehicle_profiles, Ownership",
      "dependencies": "Catalog",
      "permissions": "Owner; named consent for workshop",
      "files": "backend/ecosystem/service.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 560,
      "y": 160
    },
    {
      "id": "diagnostic",
      "name": "Shared diagnostics",
      "layer": "Core",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Canonical DiagnosticSession; evidence, tests and recalculation persist. Bridge observes validated decoded values, never invents missing data.",
      "rules": "Canonical DiagnosticSession; evidence, tests and recalculation persist. Bridge observes validated decoded values, never invents missing data.",
      "api": "/diagnostics/*",
      "entities": "DiagnosticRecord JSON",
      "dependencies": "AI, OBD",
      "permissions": "Owner or active staff with current diagnostic/report/live scope",
      "files": "backend/ecosystem/business_service.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 830,
      "y": 160
    },
    {
      "id": "ai",
      "name": "AI / RAG / rules",
      "layer": "Core",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Reuse deterministic engine and existing optional inference providers. No paid product influences hypothesis ranking. Full French explanations pending.",
      "rules": "Reuse deterministic engine and existing optional inference providers. No paid product influences hypothesis ranking. Full French explanations pending.",
      "api": "/diagnostics/{id}/analyze",
      "entities": "Canonical session evidence",
      "dependencies": "Existing ai/reasoning + ai/llm",
      "permissions": "Diagnostic authorization required",
      "files": "backend/ai/reasoning/engine.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 20,
      "y": 300
    },
    {
      "id": "obd",
      "name": "OBD / native bridge",
      "layer": "Core",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Read-only polling plan and native snapshots; actual vehicle/gateway requires authorized connected hardware. No writes in monitoring.",
      "rules": "Read-only polling plan and native snapshots; actual vehicle/gateway requires authorized connected hardware. No writes in monitoring.",
      "api": "/diagnostics/{id}/obd-plan; /live",
      "entities": "DiagnosticRecord.live_data",
      "dependencies": "Native transport",
      "permissions": "Explicit diagnostic write scope; hardware_verified false",
      "files": "backend/obd/decoding.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 290,
      "y": 300
    },
    {
      "id": "workshop",
      "name": "Workshop relationships",
      "layer": "Business",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Staff invitations require acceptance. Work orders use separate maintenance scopes. Directory only lists active verified businesses.",
      "rules": "Staff invitations require acceptance. Work orders use separate maintenance scopes. Directory only lists active verified businesses.",
      "api": "/work-orders; /directory",
      "entities": "StaffInvitation, WorkOrder, DirectoryDetails",
      "dependencies": "Consent, Identity",
      "permissions": "Scope and staff role rechecked including revoke/expiry",
      "files": "backend/ecosystem/business_api.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 560,
      "y": 300
    },
    {
      "id": "monitor",
      "name": "Monitoring schedules",
      "layer": "Business",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Durable daily/weekly/custom schedules and idempotent DEFERRED/MISSED runs. Background executor/gateway scan is not implemented.",
      "rules": "Durable daily/weekly/custom schedules and idempotent DEFERRED/MISSED runs. Background executor/gateway scan is not implemented.",
      "api": "/monitoring; /dispatch",
      "entities": "MonitoringSchedule, MonitoringRun",
      "dependencies": "Owner consent, Gateway (BLOCKED)",
      "permissions": "Owner only, explicit monitoring consent, read-only",
      "files": "backend/ecosystem/business_service.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 830,
      "y": 300
    },
    {
      "id": "notify",
      "name": "Notifications",
      "layer": "Business",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Durable in-app monitoring notices/read state. Email/SMS/push providers and quiet-hours delivery worker are BLOCKED.",
      "rules": "Durable in-app monitoring notices/read state. Email/SMS/push providers and quiet-hours delivery worker are BLOCKED.",
      "api": "/notifications",
      "entities": "Notification, Settings",
      "dependencies": "External providers (BLOCKED)",
      "permissions": "Account-scoped, no false delivery success",
      "files": "backend/ecosystem/business_api.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 20,
      "y": 440
    },
    {
      "id": "products",
      "name": "Marketplace & references",
      "layer": "Business",
      "status": "PARTIALLY IMPLEMENTED",
      "responsibility": "Moderated stock/prices, best eligible non-stacking discounts, declared fitment; verified compatibility not asserted. Curated repair/wiring registry; licensed provider unavailable.",
      "rules": "Moderated stock/prices, best eligible non-stacking discounts, declared fitment; verified compatibility not asserted. Curated repair/wiring registry; licensed provider unavailable.",
      "api": "/marketplace/products; /quote; /references",
      "entities": "Product, Offer, TechnicalReference",
      "dependencies": "Admin, Merchant",
      "permissions": "Verified active seller + approved listing; professional discount needs active verified workshop membership",
      "files": "backend/ecosystem/business_service.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 290,
      "y": 440
    },
    {
      "id": "database",
      "name": "SQL persistence",
      "layer": "Infrastructure",
      "status": "IMPLEMENTED",
      "responsibility": "Versioned additive migration 0002; keep all foundation and legacy rows. Back up before downgrade which removes new workflow data.",
      "rules": "Versioned additive migration 0002; keep all foundation and legacy rows. Back up before downgrade which removes new workflow data.",
      "api": "Alembic upgrade head",
      "entities": "Existing SQLAlchemy metadata",
      "dependencies": "SQLite / PostgreSQL adapter",
      "permissions": "Explicit DATABASE_URL, no silent data move",
      "files": "backend/migrations/versions/0002_business_workflows.py",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 560,
      "y": 440
    },
    {
      "id": "updates",
      "name": "Platform updates / future billing",
      "layer": "Infrastructure",
      "status": "PLANNED",
      "responsibility": "Existing update mechanisms retained. Store/signing configuration not validated. Payments intentionally inactive.",
      "rules": "Existing update mechanisms retained. Store/signing configuration not validated. Payments intentionally inactive.",
      "api": "Existing platform update APIs",
      "entities": "No payment credentials/tables",
      "dependencies": "Platform distribution",
      "permissions": "No arbitrary mobile self-updating code",
      "files": "docs/business/FUTURE_PAYMENTS.md",
      "docs": "../business/FINAL_BUSINESS_MIGRATION_REPORT.md",
      "x": 830,
      "y": 440
    }
  ],
  "edges": [
    [
      "user",
      "identity"
    ],
    [
      "customer",
      "identity"
    ],
    [
      "admin",
      "identity"
    ],
    [
      "market",
      "identity"
    ],
    [
      "clients",
      "identity"
    ],
    [
      "identity",
      "vehicle"
    ],
    [
      "vehicle",
      "diagnostic"
    ],
    [
      "diagnostic",
      "ai"
    ],
    [
      "diagnostic",
      "obd"
    ],
    [
      "customer",
      "workshop"
    ],
    [
      "workshop",
      "diagnostic"
    ],
    [
      "vehicle",
      "monitor"
    ],
    [
      "monitor",
      "notify"
    ],
    [
      "market",
      "products"
    ],
    [
      "admin",
      "products"
    ],
    [
      "identity",
      "database"
    ],
    [
      "diagnostic",
      "database"
    ]
  ]
};
