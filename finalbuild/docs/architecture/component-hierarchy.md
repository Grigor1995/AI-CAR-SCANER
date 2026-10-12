# Component Hierarchy

## 1. Repository hierarchy

The product lives under finalbuild/.

~~~text
finalbuild/
├── apps/
│   ├── desktop/                  # Python / PySide6 workstation
│   ├── mobile-android/           # Native Kotlin / Jetpack Compose app
│   ├── mobile-ios/               # Native Swift / SwiftUI app
│   └── web/                      # Web foundation
├── backend/                      # API, diagnostic domain, AI, devices and telemetry
├── device/                       # Device-side / future hardware boundary
├── vehicle/                      # Vehicle protocol/domain resources
├── models/                       # Local AI model documentation/resources
├── datasets/                     # Golden/test/dataset assets
├── data/                          # Runtime/data assets
├── tests/                         # Unit/API/integration/regression suites
├── infrastructure/               # Docker/Postgres/monitoring
├── scripts/                       # Local runtime and installation scripts
├── assets/                        # Application icons/assets
└── docs/                          # Architecture and device documentation
~~~

## 2. Backend hierarchy

~~~mermaid
flowchart TB
  API["api"]
  DIAG["diagnostic"]
  AI["ai"]
  DEV["device"]
  ACQ["acquisition"]
  TEL["telemetry"]
  VEH["vehicle"]
  DISC["network_discovery / multi_bus / multi_ecu"]
  PLATFORM["platform / security / observability"]

  API --> DIAG
  API --> AI
  API --> DEV
  API --> ACQ
  API --> TEL
  API --> VEH
  API --> DISC
  PLATFORM -. cross-cutting .-> API
  DIAG --> AI
  ACQ --> TEL
  DEV --> VEH
  AI --> DIAG
  AI --> TEL
~~~

## 3. AI hierarchy

~~~text
backend/ai/
├── interfaces.py
├── live_analysis.py
├── embeddings/
├── evaluation/
├── ingestion/
├── llm/
├── ml/
├── rag/
└── reasoning/
~~~

The AI layer provides contextual knowledge and explanations. Deterministic diagnostics remain the authority for evidence state and supported conclusions.

## 4. Diagnostic hierarchy

~~~text
DiagnosticSession
├── Vehicle
├── Symptoms
├── DTCs
├── Evidence[] (provenance, status, confidence, metadata)
├── Hypotheses[] (supporting/contradicting evidence, status)
├── Recommendations[] (information gain, cost, safety, target hypotheses)
├── TestResults[]
├── Measurements[]
├── LiveData[]
├── Device connection
└── Audit log
~~~

## 5. Native client hierarchy

### Desktop — Python / PySide6

The desktop workstation includes the API client, domain models, persistence helpers, UI, worker/runtime orchestration, and standalone packaging specifications.

### Android — Kotlin / Jetpack Compose

The native Android client includes the API client, diagnostic API, BLE/Wi-Fi/USB OBD transport foundations, repository, ViewModel, diagnostic screen, vehicle catalog, settings, and localization.

### iOS — Swift / SwiftUI

The native iOS client includes API/model layers, diagnostic screens, settings, localization, and a CoreBluetooth BLE discovery foundation. Adapter connection and live OBD streaming remain incomplete.

## 6. Device hierarchy

~~~text
Diagnostic domain
      |
      v
Device abstraction
      ├── Simulator
      ├── BLE transport
      ├── Wi-Fi transport
      ├── USB/serial transport
      ├── J2534 seam
      └── Future custom diagnostic device
~~~

The domain should consume normalized diagnostic operations rather than transport-specific implementation details.
