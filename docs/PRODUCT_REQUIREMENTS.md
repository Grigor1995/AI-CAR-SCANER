# Product requirements — source and status

The following is the requested target, not a completion claim. This branch starts
Phase 0 and the first Phase 1 milestone. See FEATURE_MATRIX.md and
IMPLEMENTATION_REPORT.md for actual implementation status. Existing diagnostics,
native UI, vehicle assets and deterministic fallback remain authoritative.

---

# MASTER DEVELOPMENT PROMPT — AI CAR SCANNER

## Mission

Act as a Principal Software Architect, Senior C++ Engineer, Automotive Diagnostic Engineer, AI/ML Architect, Mobile Engineer, Backend Engineer, UI/UX Engineer, Security Engineer and Senior QA Automation Architect.

Upgrade the EXISTING AI CAR SCANNER application into a production-ready, multi-platform automotive diagnostics, vehicle monitoring, repair assistance, customer service and automotive marketplace ecosystem.

**IMPORTANT: DO NOT REBUILD THE PROJECT FROM SCRATCH.**

Reuse the current application, existing UI design, icons, navigation, diagnostic modules, AI functionality, vehicle catalog, backend, APIs, existing databases and automated tests wherever they are technically sound.

The system must support:

- Windows Desktop
- Android
- iOS
- Real ELM327 and custom automotive diagnostic hardware
- Bluetooth, BLE, Wi-Fi and USB where supported
- Online and offline diagnostics
- English, Armenian and Russian

The system must have exactly THREE primary application modes:

1. USER — vehicle owner/driver
2. CUSTOMER — automotive service center, mechanic or diagnostic professional
3. ADMIN — platform administrator

Additionally implement a MARKET merchant role and seller portal integrated into the ecosystem. MARKET is not a fourth primary diagnostic mode.

Users with multiple authorized roles may switch between their permitted workspaces.

---

# 1. Mandatory Existing Repository Audit

Before changing code:

1. Inspect the entire active repository and identify its actual root, project structure, branches and build commands.
2. Identify all existing Windows, Android, iOS and backend components.
3. Audit existing UI screens, designs, icon assets, themes and navigation.
4. Identify existing DiagnosticSession, OBD, AI, RAG, ML, rules engine and vehicle catalog modules.
5. Inspect current SQL schema, migrations, APIs and authentication.
6. Identify reusable functionality, incomplete features, bugs and duplication.
7. Run available tests and collect baseline coverage and performance.
8. Find platform-specific behavior and inconsistencies.
9. Identify available documentation and missing architecture decisions.

Possible existing technologies include PySide6/Qt, Kotlin, Swift, FastAPI, PostgreSQL and C++.

Verify the actual codebase before relying on them.

Do not delete, rename, rewrite or replace existing functional modules merely to simplify implementation.

Do not perform destructive Git operations.

Create:

- docs/CURRENT_SYSTEM_AUDIT.md
- docs/REUSE_AND_MIGRATION_PLAN.md
- docs/BASELINE_QA_REPORT.md

Classify every important component as REUSE, REFACTOR, EXTEND or REPLACE, with an explanation.

---

# 2. Architecture and Programming Languages

Priorities:

1. Low latency and efficient memory usage
2. Cross-platform compatibility
3. Reuse of existing implementation
4. Security and automotive safety
5. Offline-first functionality
6. Maintainability and testability
7. Fast development and reliable releases

## Recommended Architecture

Use modern C++20/23 where appropriate for high-performance shared functionality:

- OBD communication and protocol handling
- ELM327 and custom device abstraction
- CAN/ISO-TP/UDS data processing
- Diagnostic session state processing
- Diagnostic rules engine
- High-frequency telemetry processing
- Vehicle data decoding
- Data caching
- Computationally intensive prediction routines

Use SOLID principles and interface-based architecture.

Example interfaces:

- IDeviceConnector
- IOBDTransport
- IOBDProtocol
- IDiagnosticSession
- IVehicleDataProvider
- IRuleEngine
- IAIProvider
- INotificationProvider
- IScheduler
- IMarketplaceProvider

Platform-specific implementation:

**Windows Desktop:** Retain the current working UI technology, including PySide6/Qt where already implemented. Integrate shared C++ components through appropriate bindings if justified.

**Android:** Kotlin UI, existing UI assets, C++ integration through JNI where necessary.

**iOS:** Swift UI, existing design parity, C++ integration through Objective-C++ or another well-supported interoperability boundary.

**Backend:** Retain existing FastAPI/Python services if they are appropriate. Optimize bottlenecks based on measurements, and move only justified hot paths to C++.

**Database:** Reuse PostgreSQL and current migrations; introduce new tables through safe migrations.

**AI:** Reuse existing LLM, RAG, ML and deterministic diagnostic modules.

Never migrate the whole system to another programming language without measured technical justification.

Create architecture decision records explaining each important technology choice.

## Performance Goals

- Keep UI interactions responsive.
- Optimize critical local diagnostic processing toward a p95 target of 90 ms where feasible, excluding physical OBD polling, network delays and LLM inference.
- Measure startup, navigation, diagnostic processing, protocol latency, memory and resource consumption separately.
- Support asynchronous I/O, caching and incremental updates.
- Prevent AI processing from blocking the UI.
- Avoid unnecessary background CPU and vehicle battery consumption.

---

# 3. USER MODE — Vehicle Owner

Implement a complete vehicle-owner workspace.

## 3.1 User Profile

User can register and manage:

- Full name
- Email address
- Mobile number with international prefix
- Preferred language
- Time zone
- Notification preferences
- Connected vehicles
- Vehicle make, model, year, engine and fuel type
- Diagnostic hardware
- Service history
- Diagnostic history

Support verified email and mobile number ownership.

Allow adding multiple vehicles.

Support vehicle identification through the shared catalog and optional VIN decoding.

Do not assume vehicle-specific specifications without verification.

## 3.2 Real-Time Vehicle Monitoring

Reuse existing Live Data modules.

Display available parameters such as:

- RPM
- Vehicle speed
- Engine coolant temperature
- Battery voltage
- Engine load
- Fuel trims
- O2/lambda sensor values
- Intake air temperature
- MAF/MAP values
- Available transmission data
- DTCs and freeze-frame data

Display only measurements actually supported and provided by the connected vehicle/device.

Support dynamic live charts, metric cards, unit conversion, timestamps and measurement provenance.

Clearly distinguish unavailable, unsupported, stale and invalid measurements.

## 3.3 Automatic Diagnostic Scheduling

User must be able to enable scheduled diagnostic checks.

Default schedule: EVERY DAY.

Allow configuration:

- Daily
- Weekly
- Custom time and time zone
- Manual only
- Diagnostic parameters
- Alert severity threshold
- Email enabled/disabled
- SMS enabled/disabled
- Quiet hours
- Alert throttling and cooldown period

Automatic diagnostic workflow:

1. Verify active authorization and user consent.
2. Check supported hardware and vehicle availability.
3. Establish secure OBD connection.
4. Collect eligible diagnostic measurements.
5. Check fault codes.
6. Compare with previous measurements.
7. Execute deterministic diagnostic rules.
8. Run supported AI/ML analysis.
9. Calculate diagnostic severity and confidence.
10. Save the report.
11. Notify the user if configured conditions are met.

IMPORTANT:

Do not assume a vehicle can be scanned while ignition is OFF or the diagnostic device is disconnected.

Respect iOS and Android background-execution restrictions.

Where the mobile operating system or OBD hardware cannot perform unattended daily diagnostics, use a supported backend/device gateway or queue the next eligible scan.

Expose scheduled, running, completed, missed, failed and deferred states.

Never mark an unperformed scan as successful.

Avoid battery drain from unnecessary ECU wake-ups.

## 3.4 Email and SMS

Use pluggable notification providers.

Send alerts for:

- New fault code
- Critical vehicle warnings
- Important diagnostic changes
- Repeated abnormal parameters
- Scheduled diagnostic summary
- Maintenance reminders

User must have complete control over notification preferences.

Implement:

- Consent management
- Verified delivery destinations
- Retry mechanisms
- Deduplication
- Rate limiting
- Delivery status
- Audit logs
- Secure credential management

Do not expose personal contact details unnecessarily.

## 3.5 AI Symptom-Based Diagnosis

Allow users to write symptoms in Armenian, Russian or English.

Example:

"My vehicle shakes during acceleration below 2000 RPM."

AI must:

1. Analyze symptoms.
2. Retrieve active DiagnosticSession data.
3. Review live measurements.
4. Review available DTCs and freeze-frame data.
5. Identify possible root causes.
6. Rank hypotheses using verified evidence.
7. Recommend safe diagnostic tests.
8. Accept new test results.
9. Recalculate probabilities/confidence.
10. Update the diagnostic report.

Reuse existing AI and diagnostic modules.

Do not create a disconnected second diagnostic engine.

Every important diagnostic conclusion must have evidence provenance:

- USER_REPORTED
- ECU_REPORTED
- VEHICLE_MEASURED
- RULE
- ML
- LLM
- HISTORICAL_CASE

The LLM must not invent measurements or claim a component is defective without evidence.

The deterministic engine and verified results must remain authoritative for factual measurements.

## 3.6 Nearby Service Recommendations

Recommend automotive specialists based on:

- User-approved location or manually entered city
- Vehicle brand/model
- Relevant service specialization
- Fault category
- Available service center information
- Verified location and contact information

Show:

- Service center name
- Address
- Phone number
- Location/map
- Supported services
- Available contact or appointment link
- Rating only when supported by reliable data

Require explicit permission for device location access.

## 3.7 Parts Replacement Guidance

Provide vehicle-specific repair and replacement guidance where verified information exists.

Each repair guide should contain:

- Suspected defective component
- Exact part identification when verified
- OEM/OE cross references
- Required tools
- Safety precautions
- Replacement procedure
- Diagrams/images where licensed
- Torque specifications where reliably sourced
- Post-replacement testing
- Expected measurements
- Common installation mistakes
- Parts available through MARKET

Do not fabricate part numbers, torque values, pinouts or repair instructions.

For high-risk operations, clearly require qualified professional service.

---

# 4. CUSTOMER MODE — Automotive Service Center

CUSTOMER represents a workshop, mechanic, diagnostic center or professional automotive service.

CUSTOMER inherits the eligible USER diagnostic capabilities, plus professional functionality.

## 4.1 Service Center Profile

Store:

- Business name
- Business address
- Phone number
- Email address
- Contact person
- Working hours
- Supported services
- Specializations
- Supported vehicle makes
- Optional location
- Workshop staff accounts

Support multi-employee workshops with controlled permissions.

## 4.2 Customer-to-User Relationship

A workshop can invite vehicle owners to connect their accounts.

Support:

- Email invitation
- Phone invitation
- Invitation link or QR code
- Explicit user approval
- Per-vehicle access permissions
- Read-only diagnostic access by default
- Time-limited access
- Permission revocation
- Sharing audit history

A USER can connect with more than one CUSTOMER.

A CUSTOMER can manage many authorized USER accounts.

CUSTOMER can view approved:

- Vehicle profile
- Live data when available
- Diagnostic reports
- Fault history
- AI recommendations
- Relevant maintenance history

Do not share private data until the vehicle owner explicitly grants permission.

## 4.3 Professional Diagnostic Workspace

Include:

- Full OBD diagnostic tools
- Live measurement graphs
- DTC descriptions
- Vehicle-specific diagnostic trees
- Wiring diagrams
- Component references
- Known failure patterns
- AI diagnosis
- Advanced test methodology
- Diagnostic report generation
- Work orders
- Repair notes
- Repair history
- Customer vehicle management

Support comparison of current measurements with supported reference ranges and historical values.

## 4.4 Wiring Diagrams

Support authorized, legally sourced automotive wiring diagrams.

Features:

- Vehicle/model/engine selection
- Circuit search
- Component search
- Connector descriptions
- Pin reference
- Signal reference
- Zoom and pan
- Highlighted circuit paths
- Related repair procedures

Use licensed OEM or authorized third-party diagram providers where necessary.

Never generate fabricated wiring diagrams and present them as official manufacturer diagrams.

## 4.5 Professional Testing Methodology

AI must generate a structured and actionable troubleshooting plan:

- Hypothesis
- Evidence
- Recommended test
- Tools needed
- Preconditions
- Safety requirements
- Expected results
- Actual results
- PASS / FAIL / UNKNOWN
- Confidence impact
- Next recommended test

After every test result:

- Update DiagnosticSession.
- Mark completed tests.
- Avoid unnecessarily repeating completed tests.
- Recalculate remaining diagnostic hypotheses.
- Suggest the next most informative safe test.

Use information gain when selecting the next test, provided uncertainty can be meaningfully estimated.

## 4.6 Professional Repair Documentation

Provide:

- Replacement guidelines
- Verified service references
- Known failure patterns
- Test result history
- Repair verification checklist
- Final diagnostic summary
- Exportable report

PDF export is preferred for professional reports.

## 4.7 MARKET Integration

CUSTOMER should receive relevant automotive parts and tool offers.

Display:

- Compatible products
- Sellers
- Price
- Stock availability
- Customer-specific discount
- Validity dates
- Verified compatibility
- Warranty where provided
- Seller contact information

Clearly label sponsored or paid placement.

Separate paid recommendations from the technical fault-ranking process.

---

# 5. MARKET — Seller Portal

Create a dedicated merchant role and portal.

MARKET integrates with the three primary modes without becoming an independent diagnostic mode.

## 5.1 Seller Registration

Support:

- Shop name
- Address
- Email
- Mobile number
- Business information
- Shop location
- Verification status
- Merchant administrator
- Staff access

Admin must approve merchants when required by platform policy.

## 5.2 Product Management

Seller can:

- Add products
- Update products
- Upload product images
- Manage part numbers
- Specify supported vehicle compatibility
- Configure pricing
- Manage stock
- Add manufacturer and product references
- Set warranty information
- Publish and unpublish listings

## 5.3 Discounts and Special Offers

Support:

- General discounts
- CUSTOMER-only discounts
- Discounts for specific service centers
- Product-category promotions
- Time-limited offers
- Coupon codes
- Quantity-based discounts

Backend must validate all pricing and discount eligibility.

## 5.4 Parts Matching

Match parts against:

- Vehicle make/model/year
- Engine designation
- Fuel type where relevant
- Verified OEM part references
- Confirmed catalog compatibility
- Diagnostic recommendations

Never claim compatibility from product-title similarity alone.

Explicitly show unknown or unverified compatibility.

---

# 6. ADMIN MODE

ADMIN manages the entire platform.

## 6.1 Dashboard

Provide real-time or appropriately refreshed analytics for:

- Total registered users
- Active users
- Registered CUSTOMERS
- Registered MARKET sellers
- Connected vehicles
- Vehicle makes and models
- Active diagnostic sessions
- Completed diagnostic sessions
- Automatic scan success/failure
- Most frequent fault categories
- Service center usage
- Marketplace activity
- Notification delivery status
- Platform health
- AI processing health
- Device connection statistics

All displayed analytics must be calculated from real data.

Never use fabricated production statistics.

## 6.2 Account Management

Admin can manage:

- USER accounts
- CUSTOMER accounts
- MARKET accounts
- Role assignment
- Account status
- Business verification
- Marketplace moderation
- Abuse reports
- Access permissions
- Subscription and service tiers if introduced

## 6.3 Customer Analytics

Display for each service center:

- Number of connected users
- Authorized vehicle count
- Vehicle makes/models
- Diagnostic activity
- Completed and pending work orders
- Service specialization
- Workshop staff

Respect user consent and data access policies.

## 6.4 Platform Management

Implement:

- Feature flags
- Role and permission configuration
- Vehicle catalog administration
- AI model configuration
- Notification provider monitoring
- Service integrations
- System audit logs
- Diagnostic error monitoring
- Marketplace administration
- Access reviews
- Operational reports

Use least-privilege administration, strong authentication, detailed auditing and protected access to sensitive user records.

---

# 7. Shared Diagnostic and AI Architecture

All three primary modes must use the SAME diagnostic infrastructure.

Centralize:

- Vehicle catalog
- DiagnosticSession
- Evidence collection
- DTC decoding
- OBD connectivity
- Diagnostic rules
- AI orchestration
- Test recommendations
- Prediction updates
- Measurement history
- Notifications
- Repair documentation
- Marketplace compatibility matching

Do not duplicate diagnostic business logic across Windows, Android and iOS.

Preserve:

- Manual diagnostic mode
- Deterministic fallback
- Offline diagnostic functionality
- Multilingual recommendations
- Historical test results
- Diagnostic confidence and provenance

Support AI provider abstraction:

- Local LLM
- Remote LLM
- Deterministic fallback
- Optional ML predictor

Implement structured AI outputs validated against defined schemas.

Never allow an LLM to directly execute unrestricted vehicle ECU write commands.

---

# 8. OBD and Hardware Connectivity

Audit and extend the existing connectivity layer.

Support compatible combinations of:

- ELM327
- Custom diagnostic hardware
- Bluetooth Classic
- Bluetooth LE
- Wi-Fi
- USB/serial

Include platform-specific compatibility constraints.

Protocol support must be capability-driven, not claimed universally.

Evaluate and implement relevant supported standards:

- OBD-II / SAE J1979
- ISO 15765-4 CAN
- ISO 9141-2
- ISO 14230 KWP2000
- SAE J1850 PWM/VPW
- ISO-TP
- UDS / ISO 14229 where supported and authorized

Include:

- Device discovery
- Connection status
- Timeouts
- Retries
- Protocol detection
- Adapter capability detection
- ECU capability detection
- Session recovery
- Disconnect handling
- Simulation mode
- Connection diagnostics

Read-only operations must be the default.

Require explicit user approval, supported hardware and appropriate safety checks before any potentially modifying vehicle operation.

---

# 9. Database Design

Extend the current database with a consistent relational model.

Evaluate entities such as:

- accounts
- roles
- permissions
- user_profiles
- service_centers
- service_center_staff
- service_center_user_links
- access_consents
- vehicles
- diagnostic_devices
- diagnostic_sessions
- diagnostic_measurements
- trouble_codes
- diagnostic_hypotheses
- recommended_tests
- diagnostic_test_results
- maintenance_records
- diagnostic_schedules
- diagnostic_scan_runs
- alert_rules
- notifications
- notification_deliveries
- repair_guides
- repair_references
- merchants
- products
- product_vehicle_compatibility
- offers
- discount_eligibility
- audit_logs

Use proper keys, foreign keys, indexes, constraints and migrations.

Include account isolation and explicit workshop-user authorization.

Do not let client requests bypass server-side ownership checks.

Plan data retention, backup, export and deletion mechanisms.

---

# 10. UI/UX — Preserve Current Visual Design

CRITICAL REQUIREMENT:

**USE THE CURRENT UI AND CURRENT ICONS.**

Do not replace the existing design with a new dashboard template.

Preserve existing:

- Color palette
- Icon family
- Desktop appearance
- Mobile appearance
- Vehicle dashboard concept
- Navigation style
- Existing diagnostic views
- Existing component styling
- Light/dark themes where available

Extend the interface while remaining visually consistent.

## Mode-Based UI

USER:

- My Vehicles
- Dashboard
- Live Data
- AI Diagnosis
- Auto Monitoring
- Notifications
- Service Centers
- Repair Guidance
- Account Settings

CUSTOMER:

- Professional Dashboard
- Connected Users
- Customer Vehicles
- Live Diagnostics
- AI Diagnostic Assistant
- Test Methodology
- Wiring Diagrams
- Repair Guides
- Work Orders
- Marketplace Offers

ADMIN:

- Platform Dashboard
- User Management
- Service Centers
- Vehicle Fleet Analytics
- Marketplace
- Device and Diagnostic Analytics
- Monitoring
- System Configuration
- Security and Audit

MARKET Portal:

- Merchant Dashboard
- Products
- Inventory
- Vehicle Compatibility
- Discounts
- Offers
- Seller Profile

Reuse existing UI components wherever possible.

Ensure platform-specific native behavior without unnecessary design differences.

Maintain visual and functional parity between Windows, Android and iOS.

Avoid adding duplicate navigation menus or inconsistent icon sets.

Support Armenian, Russian and English across all new screens and diagnostic messages.

---

# 11. Security, Privacy and Reliability

Implement:

- Secure authentication
- Role-based access control
- Server-side authorization
- Multi-tenant isolation
- Encryption in transit
- Secure credential storage
- Token lifecycle management
- Optional MFA for privileged accounts
- Consent-based diagnostic data sharing
- Access revocation
- Audit logging
- API rate limiting
- Input validation
- Sensitive data redaction
- Data retention and deletion
- Backup/recovery
- Abuse prevention

Apply secure-by-default configurations.

Do not expose private live vehicle data, precise location or personal contact details without appropriate authorization.

Integrate external SMS/email/map services through provider abstractions and environment-based configuration.

Do not hardcode secrets.

---

# 12. INTERACTIVE ARCHITECTURE DIAGRAM

Create a real interactive architecture visualization, NOT a static screenshot.

Output:

docs/architecture/interactive_architecture.html

The diagram must support:

- Zoom in/out
- Mouse-wheel zoom
- Mouse drag/pan
- Clickable components
- Expand/collapse logical groups
- Search
- Layer filtering
- Interactive descriptions
- Relationship details
- Communication direction
- Offline/online paths
- Dark/light appearance
- Responsive layout

Include the following layers:

1. Windows / Android / iOS UI
2. Authentication and RBAC
3. USER / CUSTOMER / ADMIN / MARKET
4. Local C++ Diagnostic Core
5. Device and OBD Transport
6. DiagnosticSession
7. AI/ML/RAG/Rules
8. FastAPI Backend
9. PostgreSQL and storage
10. Scheduler
11. Email/SMS Notifications
12. Repair Data Providers
13. Marketplace
14. External Service and Location Providers
15. Logging/Observability

When clicking a module, show:

- Responsibility
- Technology
- Input/output
- Dependencies
- Relevant API
- Data flow
- Security boundary
- Failure handling
- Related documentation

Provide separate selectable views for:

- High-Level Architecture
- USER Diagnostic Flow
- CUSTOMER Diagnostic Flow
- Automated OBD Monitoring
- AI Diagnostic Decision Flow
- Notifications
- Marketplace
- Admin and Permission Management
- Offline/Online Synchronization
- Cross-Platform Integration

The HTML should be locally runnable with any required JavaScript assets bundled locally.

Also generate Mermaid source diagrams as maintainable documentation.

---

# 13. COMPLETE PROJECT DOCUMENTATION

Generate professional technical documentation:

docs/PRODUCT_REQUIREMENTS.md
docs/FEATURE_MATRIX.md
docs/ROLES_AND_PERMISSIONS.md
docs/SYSTEM_ARCHITECTURE.md
docs/ARCHITECTURE_DECISIONS.md
docs/DATABASE_DESIGN.md
docs/API_SPECIFICATION.md
docs/OBD_CONNECTIVITY.md
docs/DIAGNOSTIC_ENGINE.md
docs/AI_DIAGNOSIS.md
docs/AUTO_MONITORING.md
docs/NOTIFICATION_SYSTEM.md
docs/MARKETPLACE.md
docs/SECURITY_AND_PRIVACY.md
docs/UI_UX_PARITY.md
docs/TEST_METHODOLOGY.md
docs/TEST_CASE_MATRIX.md
docs/PERFORMANCE_TESTING.md
docs/DEVELOPMENT_PLAN.md
docs/DEPLOYMENT_GUIDE.md
docs/RISK_REGISTER.md
docs/IMPLEMENTATION_REPORT.md

Documents must describe the actual repository and implemented design, not hypothetical components presented as completed.

Where necessary, document proposed functionality separately from implemented functionality.

---

# 14. TEST METHODOLOGY

Design and implement a comprehensive automated testing strategy.

## Unit Tests

Cover:

- Diagnostic rules
- Vehicle data validation
- Role permissions
- Schedule calculations
- Alert thresholds
- Discount calculations
- Part compatibility
- AI output validation
- Measurement provenance
- Data transformation

## Integration Tests

Cover:

- Authentication + RBAC
- USER + CUSTOMER permissions
- Customer invitation + consent
- Backend + Database
- Scheduler + OBD availability
- Diagnostic engine + AI
- Email/SMS provider interfaces
- Market + Customer discount
- Admin + Analytics
- Offline-to-online synchronization

## End-to-End Tests

USER scenarios:

- Register and verify account
- Add vehicle
- Connect ELM327
- Display real live data
- Run manual scan
- Enable daily automatic scan
- Simulate abnormal measurement
- Receive configured notification
- Enter symptom
- Complete suggested tests
- Obtain diagnostic report
- Connect a service center
- Revoke service center access

CUSTOMER scenarios:

- Register business
- Invite USER
- Obtain explicit access consent
- View authorized vehicle data
- Review AI diagnostic result
- Execute guided test workflow
- Open licensed wiring diagram
- Generate repair report
- View eligible parts discounts

ADMIN scenarios:

- Manage accounts and roles
- Approve merchant
- Verify access restrictions
- Review connected-user statistics
- Monitor alerts
- View system status
- Review audit logs

MARKET scenarios:

- Create merchant account
- Add compatible part
- Add price and stock
- Configure CUSTOMER discount
- Verify correct eligibility
- Publish/unpublish product
- Prevent incorrect vehicle matching

## Negative Tests

Include:

- No OBD connection
- Ignition OFF
- Invalid/unsupported PID
- Corrupted CAN response
- Partial ISO-TP frame
- Timeout
- Duplicate DTC
- Unsupported vehicle
- Missing VIN data
- Incorrect engine variant
- Invalid phone/email
- Failed SMS
- Failed email
- Duplicate scheduled scan
- Offline backend
- Unauthorized live data access
- Revoked consent
- Cross-tenant data request
- Expired token
- Incorrect marketplace discount
- AI response without evidence
- UI language mismatch
- Device disconnected during test

## Hardware and Protocol Tests

Use simulators and real hardware when available.

Explicitly separate:

- Simulator PASS
- Real hardware PASS
- Not Executed
- Blocked
- Unsupported

Never claim real-device coverage from simulator-only tests.

## Regression Test

Preserve the existing golden diagnostic scenario:

Mercedes-Benz W211 E350 M272, LPG-related misfire/shaking during acceleration, DTC P0302, petrol operation normal.

Validate evidence processing, hypothesis ranking, recommended testing, test result updates and recalculation.

## Coverage and Quality Gates

Target at least 90% automated coverage for suitable production core logic, while prioritizing meaningful assertions and critical branch coverage.

Measure separately:

- C++ core coverage
- Backend coverage
- Android test coverage
- iOS test coverage
- Desktop UI tests
- API tests
- Contract tests
- Integration tests
- E2E tests
- Performance tests
- Security tests

Collect genuine execution results.

Do not report PASS for unexecuted tests.

---

# 15. DEVELOPMENT PLAN

Create a realistic phase-based development roadmap.

For every phase include:

- Objective
- Scope
- Dependencies
- Architecture changes
- Source modules
- API changes
- Database migrations
- UI screens
- Automated tests
- Acceptance criteria
- Risks
- Estimated engineering effort
- Deliverables

Recommended order:

## PHASE 0 — Audit and Baseline

Audit current application, code, UI, test coverage and architecture.

## PHASE 1 — Foundation

Shared RBAC, account model, user/customer relationships, consent, database migrations and architectural interfaces.

## PHASE 2 — USER

Vehicle management, live data reuse, automatic monitoring, scheduler, SMS/email, AI symptom integration and service recommendations.

## PHASE 3 — CUSTOMER

Workshop account, connected users, professional diagnostics, wiring diagrams, test methodology, work orders and repair guides.

## PHASE 4 — MARKET

Merchant portal, product catalog, compatibility, inventory, customer discounts and marketplace integrations.

## PHASE 5 — ADMIN

Platform management, analytics, merchant approval, activity dashboards, audit and operational monitoring.

## PHASE 6 — Cross-Platform and Performance

Windows/Android/iOS parity, native integrations, C++ optimization where justified, offline handling and compatibility.

## PHASE 7 — Security and Production Readiness

Full regression, permission tests, notification reliability, backup/recovery, performance benchmarks, release builds and deployment validation.

Phases should be divided into small deliverable milestones.

Each milestone must leave the repository in a buildable, testable condition.

---

# 16. Mandatory Implementation Rules

1. Do not start with a large rewrite.
2. Complete the repository audit first.
3. Reuse existing functionality whenever appropriate.
4. Keep the current UI design and existing icons.
5. Maintain one shared vehicle catalog and diagnostic model.
6. Use safe database migrations.
7. Introduce feature flags for incomplete features.
8. Never fabricate sensor values, hardware support or AI confidence.
9. Do not promise unsupported background OBD scans.
10. Do not expose personal vehicle data without authorization.
11. Do not introduce undocumented breaking API changes.
12. Write automated tests for important changes.
13. Execute available tests and report actual outcomes.
14. Ensure Windows, Android and iOS architecture remains compatible.
15. Keep Armenian/Russian/English localization consistent.
16. Clearly separate completed and proposed functionality.
17. Do not claim integration with external providers unless actually configured and tested.
18. Do not replace proven working UI components merely to change their appearance.
19. Preserve existing golden diagnostic regression scenarios.
20. Optimize based on measurements, not assumptions.

---

# 17. Expected Final Delivery

Deliver:

A. Complete current-codebase audit

B. Production architecture specification

C. Interactive HTML architecture diagram

D. Complete role/feature/permission matrix

E. Database model and migration strategy

F. API contracts

G. UI extension plan based on EXISTING UI and ICONS

H. Comprehensive test methodology

I. Automated test suites and execution reports

J. Performance and security findings

K. Step-by-step development roadmap

L. Actual implementation for the approved phases

M. Updated project documentation

N. Final implementation status report

The report must contain:

- Implemented features
- Reused components
- Modified files
- New files
- Database migrations
- API changes
- Tests executed
- PASS / FAIL / SKIPPED / BLOCKED counts
- Code coverage
- Known limitations
- Performance results
- Platform compatibility status
- Remaining tasks

## Definition of Done

A feature is complete only when:

- Functionality is implemented.
- Required authorization works.
- Existing UI conventions are respected.
- Relevant API/database integration works.
- Tests exist and have been executed.
- Error handling is implemented.
- Documentation is updated.
- No known critical regression remains.

## Execution Instructions

Start with a real audit of the active repository.

Produce the full architecture, interactive diagram, documentation, test methodology and prioritized development plan.

Then begin implementation from the foundational milestone, using small, verifiable changes.

Do not stop at generic advice or pseudocode.

Implement actual application code where execution access permits, maintain compatibility, and provide evidence of completed work.

If a required dependency, hardware device, licensed data source, external provider or build environment is unavailable, identify the blocker clearly and provide a testable interface or simulator without claiming production functionality.

**FINAL OBJECTIVE: Transform the existing AI CAR SCANNER application into a high-performance, secure, AI-powered, multi-platform automotive diagnostics and professional service ecosystem while preserving its existing user interface, icons and working modules.**
