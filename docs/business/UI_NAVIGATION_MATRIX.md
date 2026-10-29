# Ui Navigation Matrix

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

| Platform | Existing UI preserved | New account browser | Complete business mutation UI |
|---|---|---|---|
| Desktop | YES | Application menu → USER/CUSTOMER/ADMIN • MARKET; register/login/logout, role-selected reads | PARTIAL |
| Android | YES | Application ⋮ menu → same workspace; native Compose fields/cards and transient token | PARTIAL |
| iOS | YES | Application ⋮ menu → same SwiftUI sheet | PARTIAL; Xcode NOT VERIFIED |

Server navigation supplies only permitted workspaces/pages and translated labels
in en/hy/ru/fr. MARKET is separate portal entitlement, not a fourth diagnostic mode.
USER reads owned profiles, monitoring, notifications, directory, marketplace,
settings. CUSTOMER reads memberships/staff inbox/marketplace/settings. ADMIN reads
actual aggregates/accounts/audit. MARKET reads owned shops/settings.
Business API editing flows are available and tested; native forms for inventory,
sharing, scheduling, work orders and authenticated diagnostics are NOT complete.
Raw structured account read output is an early browser, not a completed product
screen or full target parity. Existing local diagnostic screens remain legacy mode.
