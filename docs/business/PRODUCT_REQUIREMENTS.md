> Target specification supplied by the user. Implementation status is recorded in FINAL_BUSINESS_MIGRATION_REPORT.md; this document is not a completion claim.

# CAR DIAGNOSTIC ANALYSIS SYSTEM
## BUSINESS LOGIC TRANSFORMATION — MASTER IMPLEMENTATION PROMPT
### Existing Project → User / Customer / Admin + Marketplace Ecosystem

# 1. MISSION

Act as a Principal Software Architect, Senior Backend Engineer, C++ Engineer, Automotive Diagnostic Engineer, Database Architect, AI Engineer, UI/UX Engineer, Security Engineer and Senior QA Automation Architect.

You are working on an EXISTING CAR DIAGNOSTIC ANALYSIS SYSTEM.

The goal is to transform the CURRENT business logic into a complete automotive diagnostic business ecosystem.

This is a BUSINESS LOGIC TRANSFORMATION, not a project rewrite.

Implement exactly THREE primary application modes:

1. USER — Vehicle Owner / Driver
2. CUSTOMER — Automotive Service Center / Mechanic
3. ADMIN — Platform Administrator

Additionally implement:

MARKET — Automotive Parts Seller Portal.

MARKET is a merchant role/workspace, not a fourth primary diagnostic mode.

The business logic must support Windows Desktop, Android and iOS.

## CRITICAL REQUIREMENTS

- Preserve the existing project.
- Preserve the existing UI visual style.
- Preserve the existing application icons.
- Preserve working AI/ML modules.
- Preserve working OBD functionality.
- Preserve diagnostic algorithms.
- Preserve existing real vehicle data support.
- Preserve the shared diagnostic core.
- Preserve working language and units functionality.
- Preserve existing online update functionality where implemented.
- Modify domain models, services, APIs and workflows to support the new business model.
- Refactor existing modules where needed.
- Do not blindly replace working implementations.
- Do not add CI/CD.
- Follow SOLID principles.
- Follow Clean Architecture.
- Respect existing Macroservice boundaries and improve them where necessary.
- Keep cross-platform compatibility.
- Add automated tests for all business logic changes.

Do not stop after writing a proposal.

Audit the codebase, prepare a migration plan, implement the changes, execute tests and update documentation.

---

# 2. ANALYZE CURRENT BUSINESS LOGIC

Before modifying source code:

1. Inspect the complete active repository.
2. Identify existing business entities.
3. Identify authentication and authorization.
4. Analyze current user registration.
5. Inspect existing diagnostic workflows.
6. Inspect OBD integration.
7. Analyze existing AI diagnostic workflows.
8. Inspect service architecture.
9. Inspect database models and migrations.
10. Identify all existing UI pages.
11. Inspect Settings and localization.
12. Identify current dependencies.
13. Analyze existing tests.
14. Identify cross-platform functionality.
15. Identify features that can be reused.

Produce a detailed comparison:

CURRENT BUSINESS LOGIC vs TARGET BUSINESS LOGIC.

Classify each component:

- KEEP
- EXTEND
- REFACTOR
- REPLACE
- NEW
- DEFER

Do not assume features exist unless confirmed in the actual code.

Never delete working implementation before validating its replacement.

---

# 3. TARGET BUSINESS ARCHITECTURE

Implement a role-based and organization-aware automotive ecosystem.

## Primary Modes

USER:
Owns and monitors vehicles.

CUSTOMER:
Provides professional automotive diagnostic and repair services.

ADMIN:
Manages platform accounts, organizations, permissions, marketplace and operational information.

## Merchant Role

MARKET:
Lists automotive products and provides offers to vehicle owners and service centers.

## Role Relationships

- One USER can register multiple vehicles.
- One CUSTOMER can serve multiple USER accounts.
- One USER can connect to multiple CUSTOMER organizations.
- CUSTOMER can employ multiple staff members.
- One MARKET merchant can manage multiple products and offers.
- ADMIN can manage and monitor the platform.
- A physical account may have more than one authorized role.
- Every organization relationship must be explicitly authorized.

Use server-side RBAC and resource-level permissions.

Do not rely on hiding UI elements as a security mechanism.

---

# 4. USER MODE — VEHICLE OWNER BUSINESS LOGIC

USER is a driver or vehicle owner.

## 4.1 Account Management

Support:

- Registration
- Login/logout
- Email verification
- Phone verification
- Profile management
- Preferred language
- Preferred measurement units
- Time zone
- Notification settings
- Connected devices
- Vehicle ownership

A USER can own multiple vehicles.

## 4.2 Vehicle Management

USER can add and manage vehicles.

Store:

- Manufacturer
- Model
- Generation
- Production year
- Engine
- Fuel type
- Transmission
- VIN if available
- Registered diagnostic adapter
- Vehicle status
- Diagnostic history

Support a centralized vehicle catalog.

Validate available technical specifications.

## 4.3 Live Vehicle Diagnostics

USER can connect to supported OBD hardware and access real vehicle measurements.

Support:

- Live Data
- DTC Read
- Freeze Frames
- Vehicle measurements
- Engine parameters
- Battery status
- Supported ECU information
- Diagnostic history
- Diagnostic reports

Show only actually available and supported measurements.

All data must include appropriate timestamps and provenance.

## 4.4 Automatic Daily Diagnostics

Allow USER to enable automatic monitoring.

Default schedule when monitoring is enabled: EVERY DAY.

USER controls:

- Monitoring enable/disable
- Daily/weekly/custom schedule
- Time zone
- Email alerts
- SMS alerts
- Push notifications
- Severity threshold
- Alert frequency
- Quiet hours

### Monitoring Workflow

1. Check user consent.
2. Check monitoring schedule.
3. Check device availability.
4. Check vehicle connection.
5. Start a supported read-only diagnostic scan.
6. Read supported live data.
7. Retrieve relevant DTCs.
8. Compare historical measurements.
9. Run diagnostic rules.
10. Execute AI analysis where appropriate.
11. Detect abnormalities.
12. Save the diagnostic report.
13. Send notifications according to user preferences.

IMPORTANT:

Scheduled monitoring must never perform destructive ECU write operations.

Do not assume mobile devices can communicate with vehicles while disconnected or suspended.

Implement deferred, missed and failed scan states.

Support an optional compatible vehicle-side gateway for unattended scans.

Avoid excessive ECU polling and vehicle battery drain.

## 4.5 AI Symptom Diagnosis

USER can describe automotive symptoms in natural language.

Example:

"My vehicle shakes during acceleration but works normally at idle."

The AI system must:

1. Interpret symptoms.
2. Identify the selected vehicle.
3. Collect existing diagnostic evidence.
4. Analyze available live data.
5. Correlate DTC information.
6. Generate possible root causes.
7. Suggest useful diagnostic tests.
8. Accept test results.
9. Recalculate hypotheses.
10. Generate an updated recommendation.

Reuse existing AI, RAG, ML and diagnostic rules when functional.

AI must not invent measured data or technical specifications.

Support English, Armenian, Russian and French.

## 4.6 Nearby CUSTOMER Recommendations

USER can search for professional services.

Filter based on:

- City/location
- Vehicle brand
- Vehicle model
- Engine type
- Fault category
- Workshop specialization

Show:

- Workshop name
- Address
- Telephone
- Business details
- Supported services
- Contact options
- Available booking/contact information

Use authorized location data and verified provider information.

Do not invent workshop listings.

## 4.7 Repair and Replacement Guidance

USER can access verified repair references.

Provide:

- Suspected faulty component
- Supported part identification
- OEM references when verified
- Required tools
- Repair procedure
- Safety warnings
- Post-repair verification
- Related products from MARKET

For safety-critical work, require professional assistance.

---

# 5. CUSTOMER MODE — PROFESSIONAL AUTOMOTIVE SERVICE

CUSTOMER represents an automotive workshop, mechanic or diagnostic service center.

CUSTOMER inherits eligible USER diagnostic capabilities, plus professional features.

## 5.1 Business Registration

Store:

- Business name
- Business address
- Contact person
- Phone
- Email
- Working hours
- Location
- Supported services
- Vehicle specialization
- Verification status

Support multiple employees with separate accounts and permissions.

## 5.2 USER–CUSTOMER Relationship

CUSTOMER can invite USER accounts.

Support:

- Email invitations
- Phone invitations
- Secure links
- QR codes

The USER must explicitly approve the relationship.

A CUSTOMER can access only the vehicle data that the USER authorizes.

### Sharing Permissions

Support:

- Vehicle profile access
- Live Data access
- Diagnostic history access
- Reports access
- Maintenance history access
- Time-limited consent
- Permission revocation

CUSTOMER must not automatically gain access to every vehicle owned by USER.

Implement audit logging for data access.

## 5.3 CUSTOMER Dashboard

Display real data:

- Connected users
- Connected vehicles
- Active diagnostic sessions
- Recent faults
- Pending diagnostics
- Work orders
- Completed repairs
- Workshop activity
- Relevant MARKET offers

## 5.4 Professional Diagnostic Functionality

Provide:

- Advanced Live Data
- Multiple sensor comparison
- ECU diagnostic information
- DTC analysis
- AI diagnostics
- Technical references
- Professional tests
- Diagnostic history
- Work orders
- Repair reports

Reuse common USER diagnostic modules.

Do not duplicate diagnostic processing.

## 5.5 Wiring Diagrams

Integrate authorized wiring diagram data sources.

Support:

- Vehicle-specific diagrams
- Circuit search
- Component location
- Connector identification
- Pin references
- Wiring references
- Zoom/pan
- Related diagnostic procedures

Do not fabricate wiring diagrams.

Display unavailable data honestly.

## 5.6 AI Diagnostic Testing Methodology

CUSTOMER can execute professional AI-recommended tests.

Every test includes:

- Hypothesis
- Required equipment
- Preconditions
- Test instructions
- Expected result
- Actual result
- PASS / FAIL / UNKNOWN
- Supporting evidence
- Updated confidence
- Next recommended test

After a test result:

1. Save result to DiagnosticSession.
2. Update evidence.
3. Recalculate hypotheses.
4. Remove completed tests from pending recommendations unless retesting is justified.
5. Recommend the next informative test.
6. Update diagnostic reports.

## 5.7 Professional Repair Guidance

Provide:

- Replacement methodology
- Component references
- Technical documentation
- Verified specifications
- Repair checklist
- Post-repair testing
- Final vehicle report

## 5.8 MARKET Special Offers

CUSTOMER can access:

- Professional discounts
- Automotive spare parts
- Diagnostic equipment
- Special promotions
- Seller information
- Product availability
- Vehicle compatibility

Discount eligibility must be validated on the backend.

---

# 6. MARKET — AUTOMOTIVE SELLER PORTAL

MARKET is a dedicated seller workspace integrated into the platform.

## 6.1 Merchant Registration

Store:

- Shop name
- Address
- Email
- Telephone
- Business details
- Product specialization
- Merchant verification

## 6.2 Product Management

MARKET can:

- Add products
- Update products
- Upload images
- Specify part numbers
- Configure vehicle compatibility
- Update prices
- Update stock
- Publish/unpublish listings
- Configure offers

Product categories:

- Spare parts
- Automotive accessories
- Diagnostic devices
- Service equipment
- Maintenance products

## 6.3 Discount Engine

Support:

- Public discount
- CUSTOMER discount
- Service-center-specific discount
- Quantity discount
- Limited-time promotion
- Coupon codes

All discount calculations must be server-side.

## 6.4 Marketplace Integration

Connect MARKET with:

- USER repair recommendations
- CUSTOMER repair workflow
- Vehicle compatibility engine
- AI parts suggestions
- Professional customer offers

Never present unverified part compatibility as confirmed.

Paid promotions must not affect technical diagnostic ranking.

## 6.5 Future Payments

Payments are FUTURE SCOPE.

Prepare an extensible architecture for:

- Payment providers
- Orders
- Invoices
- Subscriptions
- Refunds

Do not implement payment gateways now.

Do not store payment credentials.

Do not create active checkout functionality.

---

# 7. ADMIN MODE — PLATFORM CONTROL

ADMIN manages the complete ecosystem.

## 7.1 Platform Dashboard

Display actual statistics:

- Total registered users
- Active users
- Registered CUSTOMERS
- Registered MARKET merchants
- Number of connected users per CUSTOMER
- Registered vehicles
- Vehicle manufacturers
- Models and engine types
- Diagnostic sessions
- Most common DTCs
- Monitoring activity
- AI analysis activity
- Marketplace products
- Notification delivery
- System health

## 7.2 USER Management

ADMIN can:

- View registered accounts
- Manage account status
- Manage roles
- Inspect aggregate vehicle statistics
- Investigate authorized support cases
- Review security events

## 7.3 CUSTOMER Management

ADMIN can:

- View registered workshops
- Review business information
- Approve/disable workshops
- Inspect connected USER counts
- Review authorized activity
- Monitor workshop services

## 7.4 MARKET Management

ADMIN can:

- Approve merchants
- Moderate product listings
- Review offers
- Review product categories
- Investigate abuse
- Manage marketplace availability

## 7.5 Platform Administration

Support:

- Role management
- Feature flags
- System health
- Device analytics
- Notification providers
- Vehicle catalog maintenance
- AI provider configuration
- Update management
- Audit logs
- Security monitoring

Admin must have comprehensive management capabilities without unrestricted or unaudited access to private user data.

---

# 8. BUSINESS DOMAIN AND MACROSERVICE RESTRUCTURING

Refactor business logic according to SOLID and Clean Architecture.

Use clear domain boundaries:

1. Identity & Access
2. Vehicle Management
3. Diagnostic Management
4. AI Analysis
5. Monitoring & Notifications
6. Customer / Workshop Management
7. Marketplace
8. Administration
9. Settings & Localization
10. Update Management
11. Future Billing — inactive

Do not assume every domain requires a separate deployed process.

Preserve a modular architecture with well-defined interfaces.

Use independently deployable services only where technically justified.

## Required Architectural Principles

- SOLID
- Single responsibility
- Dependency inversion
- Interface segregation
- Clean separation of UI, domain and infrastructure
- Explicit service contracts
- Domain ownership
- Server-side authorization
- Testable business logic
- Reusable components
- Safe error handling
- Minimal unnecessary dependencies

If the current backend is Python/FastAPI, retain it unless migration is justified.

If existing C++ code is present, use it where appropriate.

Do not move the entire backend to C++ merely to change the business model.

C++ optimization is a separate, performance-driven decision.

---

# 9. DATABASE BUSINESS MODEL MIGRATION

Analyze the existing schema and implement safe migrations.

Required conceptual entities:

- accounts
- roles
- permissions
- user_profiles
- organizations
- service_centers
- service_center_staff
- customer_user_connections
- consent_grants
- vehicles
- vehicle_ownership
- diagnostic_devices
- diagnostic_sessions
- live_measurements
- dtcs
- diagnostic_hypotheses
- recommended_tests
- test_results
- monitoring_schedules
- monitoring_runs
- notification_preferences
- notifications
- notification_deliveries
- repair_guides
- wiring_references
- work_orders
- merchants
- products
- product_vehicle_compatibility
- offers
- discounts
- audit_logs

## Migration Requirements

- Preserve existing production data.
- Use versioned migrations.
- Avoid destructive table replacement.
- Preserve existing diagnostic history.
- Migrate legacy roles where possible.
- Add appropriate relationships and constraints.
- Support USER–CUSTOMER many-to-many relationships.
- Support multi-vehicle ownership.
- Support organization-level access.
- Avoid duplicate vehicle and diagnostic records.
- Provide a backup and rollback plan.
- Test migrations on representative data.

If data cannot be migrated automatically, document the issue and use a safe explicit mapping process.

---

# 10. API BUSINESS LOGIC TRANSFORMATION

Analyze current APIs and introduce or adapt endpoints.

Suggested API domains:

/api/v1/auth
/api/v1/users
/api/v1/vehicles
/api/v1/devices
/api/v1/diagnostics
/api/v1/live-data
/api/v1/monitoring
/api/v1/notifications
/api/v1/customers
/api/v1/customer-connections
/api/v1/repair-guides
/api/v1/wiring
/api/v1/marketplace
/api/v1/admin
/api/v1/settings
/api/v1/updates

Requirements:

- Validate authentication.
- Validate role permissions.
- Validate object ownership.
- Enforce consent.
- Apply tenant isolation.
- Validate inputs.
- Handle errors consistently.
- Use explicit API contracts.
- Maintain compatibility where feasible.
- Document breaking changes.

Do not duplicate diagnostic APIs per mode unnecessarily.

Use shared diagnostic endpoints with proper permission checks.

---

# 11. UI TRANSFORMATION — PRESERVE CURRENT DESIGN

Keep the CURRENT project UI design and icon assets.

Do not redesign the application.

Use existing:

- Colors
- Cards
- Buttons
- Icons
- Header navigation
- Dashboard components
- Live data visualization
- Diagnostic screens
- Layout conventions
- Theme system

Modify navigation and displayed functionality according to the selected role.

## USER Navigation

- Dashboard
- My Vehicles
- Live Data
- AI Diagnostics
- Auto Monitoring
- Notifications
- Nearby Services
- Repair Guides
- Settings

## CUSTOMER Navigation

- Professional Dashboard
- Connected Users
- Vehicles
- Live Diagnostics
- AI Diagnostic Assistant
- Test Methodology
- Wiring Diagrams
- Repair Guides
- Work Orders
- Marketplace Offers
- Settings

## ADMIN Navigation

- Dashboard
- Users
- Service Centers
- Vehicles Analytics
- Diagnostic Analytics
- Marketplace
- Notifications
- Update Management
- System Monitoring
- Settings

## MARKET Portal Navigation

- Merchant Dashboard
- Products
- Inventory
- Vehicle Compatibility
- Discounts
- Promotions
- Merchant Settings

Implement role-based navigation without duplicating shared screens.

Maintain Windows, Android and iOS visual parity.

If additional icons are required, create them using the exact current icon style.

---

# 12. SETTINGS AND LOCALIZATION

Keep or implement a complete Settings system.

## Languages

Support:

- Armenian — hy
- Russian — ru
- French — fr
- English — en

English is the fallback language.

Translate:

- UI
- Business workflows
- Reports
- Notifications
- Error messages
- AI explanations
- Diagnostic tests

## Measurement Units

Support:

- km/h / mph
- km / miles
- °C / °F
- kPa / bar / psi
- L/100 km / km/L / mpg
- Nm / lb-ft
- kW / hp
- Liters / US gallons

Maintain canonical engineering measurements internally.

Perform unit conversions accurately at appropriate boundaries.

## Other Settings

- Theme
- Notification preferences
- Email/mobile number
- Device connection
- Monitoring schedule
- AI provider
- Privacy
- Data-sharing permissions
- Online updates
- Account security

Settings must persist and work consistently across supported platforms.

---

# 13. REAL OBD AND AI INTEGRATION

Business logic changes must not break automotive diagnostics.

Preserve or extend:

- ELM327 connectivity
- Bluetooth/BLE/Wi-Fi/USB interfaces where supported
- OBD-II
- CAN
- ISO-TP
- KWP2000
- ISO 9141
- J1850
- Supported UDS operations
- Live Data
- DTC handling
- DiagnosticSession
- AI diagnosis
- Diagnostic test recommendation

Read-only operations must be the default.

ECU Write functionality requires explicit authorization, verified hardware support and operation-specific safety checks.

Do not expose dangerous write operations through automatic monitoring.

Use one shared diagnostic engine across USER and CUSTOMER modes.

CUSTOMER receives professional features through permissions, not a duplicated diagnostic engine.

Preserve evidence provenance:

- USER_REPORTED
- ECU_REPORTED
- VEHICLE_MEASURED
- RULE
- ML
- LLM
- HISTORICAL_CASE

---

# 14. ONLINE UPDATES

Preserve or implement platform-appropriate update management.

Windows:

- Update check
- Version comparison
- Signed package verification
- Safe installation
- Recovery where supported

Android:

- Supported Android update mechanisms
- Play Store update integration where applicable

iOS:

- App Store-compatible update checks
- Version notifications
- Release notes

Do not implement unsupported self-updating executable code on mobile platforms.

No CI/CD pipelines.

---

# 15. INTERACTIVE BUSINESS ARCHITECTURE DASHBOARD

Create or update:

docs/architecture/business_architecture_dashboard.html

Build a functional interactive architecture dashboard using the CURRENT project UI style.

Include:

## Business Model View

- USER
- CUSTOMER
- ADMIN
- MARKET
- Relationships
- Permissions
- Business workflows

## Technical Architecture View

- Windows/Android/iOS applications
- Shared diagnostic core
- Authentication
- Business services
- Backend API
- Database
- AI
- OBD
- Monitoring
- Notification providers
- Marketplace
- Updates

## Interactive Features

- Zoom
- Pan
- Search
- Clickable nodes
- Expand/collapse
- Layer filters
- Dependency highlighting
- Data-flow visualization
- Permission visualization

Clicking each node must display:

- Responsibility
- Business rules
- API
- Database entities
- Dependencies
- Permissions
- Related source files
- Related documentation

Also include a BEFORE vs AFTER business architecture view.

Do not invent runtime statistics.

---

# 16. COMPLETE DOCUMENTATION

Create or update:

docs/business/
- CURRENT_BUSINESS_LOGIC.md
- TARGET_BUSINESS_LOGIC.md
- BUSINESS_LOGIC_GAP_ANALYSIS.md
- PRODUCT_REQUIREMENTS.md
- BUSINESS_RULES.md
- ROLES_AND_PERMISSIONS.md
- USER_MODE.md
- CUSTOMER_MODE.md
- ADMIN_MODE.md
- MARKETPLACE.md
- USER_CUSTOMER_RELATIONSHIPS.md
- DATA_SHARING_AND_CONSENT.md
- BUSINESS_ARCHITECTURE.md
- MACROSERVICE_BOUNDARIES.md
- DATABASE_MIGRATION.md
- API_CHANGES.md
- UI_NAVIGATION_MATRIX.md
- AI_DIAGNOSTIC_WORKFLOWS.md
- MONITORING_AND_ALERTS.md
- SETTINGS.md
- FUTURE_PAYMENTS.md
- TEST_METHODOLOGY.md
- TEST_CASE_MATRIX.md
- IMPLEMENTATION_PLAN.md
- FINAL_BUSINESS_MIGRATION_REPORT.md

Documentation must reflect the real implementation.

Mark each feature:

- IMPLEMENTED
- PARTIALLY IMPLEMENTED
- PLANNED
- BLOCKED
- UNSUPPORTED

---

# 17. COMPREHENSIVE TEST METHODOLOGY

Create automated tests for the new business rules.

## USER Tests

- Registration/login
- Multiple vehicle ownership
- OBD connection
- Live Data
- Manual scan
- Automatic scan scheduling
- Notifications
- AI symptom diagnosis
- Repair recommendations
- CUSTOMER invitation approval
- CUSTOMER access revocation

## CUSTOMER Tests

- Workshop registration
- Multiple staff accounts
- USER invitations
- Consent validation
- Authorized Live Data
- Professional diagnostics
- Wiring diagram access
- AI testing methodology
- Repair reports
- MARKET discounts

## ADMIN Tests

- Account management
- Role changes
- Service-center management
- Merchant approval
- Dashboard analytics
- Audit logging
- Unauthorized data-access prevention

## MARKET Tests

- Merchant registration
- Product creation
- Product updates
- Vehicle compatibility
- Stock management
- Discount calculation
- CUSTOMER discount eligibility

## Security and Negative Tests

- Unauthorized vehicle access
- Cross-CUSTOMER data access
- Revoked permissions
- Expired consent
- Invalid role
- Missing authentication
- Duplicate invitations
- Incorrect marketplace discounts
- Invalid vehicle compatibility
- Unavailable OBD device
- Failed notifications
- Backend offline
- Missing sensor data
- AI response without evidence

## Cross-Platform Tests

Verify business flow parity across:

- Windows
- Android
- iOS

## Quality Requirements

- Run existing regression tests.
- Extend tests for new business rules.
- Target at least 90% meaningful critical business-logic coverage.
- Record real PASS/FAIL/SKIPPED/BLOCKED/NOT RUN results.
- Do not claim unsupported platforms or hardware were verified.

---

# 18. IMPLEMENTATION DEVELOPMENT PLAN

## PHASE 0 — Analysis

- Analyze current repository.
- Identify current business rules.
- Inspect architecture.
- Build current vs target feature matrix.
- Identify migration risks.

Deliverable:
Business Logic Gap Analysis.

## PHASE 1 — Domain Model and Permissions

- USER/CUSTOMER/ADMIN/MARKET roles
- Organization model
- Account relationships
- Permissions
- Consent management
- Database migrations

Deliverable:
Functional role and domain foundation.

## PHASE 2 — USER Business Logic

- Vehicle management
- Diagnostics
- Live data
- Scheduled checks
- Notifications
- AI symptoms
- Service recommendations
- Repair guidance

Deliverable:
Complete USER workflow.

## PHASE 3 — CUSTOMER Business Logic

- Workshop registration
- Connected users
- Live Data permissions
- Professional diagnostics
- AI test methodology
- Wiring diagrams
- Work orders
- Repair reports

Deliverable:
Complete CUSTOMER workflow.

## PHASE 4 — MARKET Business Logic

- Merchant registration
- Products
- Vehicle compatibility
- Stock
- Discounts
- Promotions

Deliverable:
Functional merchant portal without payments.

## PHASE 5 — ADMIN Business Logic

- User management
- CUSTOMER management
- MARKET management
- Vehicle analytics
- System administration
- Activity dashboards

Deliverable:
Complete administration workspace.

## PHASE 6 — Cross-Platform UI Integration

- Role-based navigation
- Shared UI components
- Permissions
- Current icon reuse
- Localization
- Settings
- Windows/Android/iOS parity

Deliverable:
Unified business functionality across all supported platforms.

## PHASE 7 — Integration and Regression

- OBD integration
- AI integration
- Notifications
- Database consistency
- Online updates
- Authorization
- Security
- Full automated testing

Deliverable:
Verified integrated application.

## PHASE 8 — Documentation and Interactive Dashboard

- Final architecture
- Business relationships
- Database documentation
- API documentation
- Interactive business architecture dashboard
- Test reports
- Development status

Deliverable:
Complete project documentation and final migration report.

---

# 19. DEFINITION OF DONE

A business feature is complete only when:

1. Business rules are implemented.
2. Database integration works.
3. Backend API works.
4. Permissions are enforced.
5. Current UI style is preserved.
6. The workflow functions end to end.
7. Error handling is implemented.
8. Automated tests have been executed.
9. Documentation is updated.
10. The architecture dashboard reflects the actual implementation.

Do not mark mock screens as completed features.

Do not invent test results.

Do not delete legacy code before confirming safe replacement.

Do not implement active payment processing.

Do not add CI/CD.

---

# 20. FINAL EXECUTION INSTRUCTION

Start by analyzing the existing project.

Identify all differences between the current business logic and the target USER/CUSTOMER/ADMIN + MARKET business model.

Create a detailed gap analysis and implementation plan.

Then modify actual application code incrementally.

Prioritize:

1. Business entities
2. User roles and permissions
3. Database relationships
4. Backend services and APIs
5. USER workflows
6. CUSTOMER workflows
7. MARKET workflows
8. ADMIN workflows
9. Cross-platform UI integration
10. Regression testing and documentation

Use SOLID principles and preserve existing service boundaries.

Retain the current design, icons, functioning OBD modules, AI capabilities and cross-platform architecture.

Optimize code where justified, but do not perform an unnecessary full rewrite or language migration.

Implement actual working features rather than placeholders.

Provide a complete implementation report with exact modified files, test results, known limitations and remaining work.

# FINAL OBJECTIVE

Transform the EXISTING CAR DIAGNOSTIC ANALYSIS SYSTEM into a complete business ecosystem:

USER — Vehicle Owners

CUSTOMER — Automotive Professionals

ADMIN — Platform Management

MARKET — Automotive Product Sellers

With shared diagnostics, AI-assisted troubleshooting, real-time data, professional repair workflows, scheduled monitoring, notifications, service-center relationships and marketplace integration.

PRESERVE EXISTING CODE WHERE FUNCTIONAL.

PRESERVE CURRENT UI AND ICONS.

FOLLOW SOLID AND CLEAN ARCHITECTURE.

NO CI/CD.

PAYMENTS RESERVED FOR FUTURE DEVELOPMENT.

IMPLEMENT, TEST AND DOCUMENT THE ACTUAL BUSINESS LOGIC TRANSFORMATION.