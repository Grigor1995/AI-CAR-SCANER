# Component Hierarchy

## 1. Repository hierarchy

The product lives under `finalbuild/`.

~~~text
finalbuild/
├── apps/
│   ├── desktop/                  # Current Windows desktop workstation
│   ├── desktop_flutter_legacy/   # Legacy desktop Flutter implementation
│   ├── mobile/                   # Flutter/mobile foundation
│   ├── mobile-android/           # Native Android implementation
│   └── web/                      # Web foundation
│
├── backend/
│   ├── api/                      # HTTP routes and request boundary
│   ├── diagnostic/               # Core diagnostic domain
│   ├── ai/                       # AI, ML, RAG, reasoning and LLM adapters
│   ├── device/                   # VCI/device abstraction
│   ├── acquisition/              # Telemetry acquisition
│   ├── telemetry/                # Telemetry models/services
│   ├── vehicle/                  # Vehicle-domain capabilities
│   ├── multi_ecu/                # Multi-ECU coordination
│   ├── multi_bus/                # Multi-bus capabilities
│   ├── network_discovery/        # Passive/active network discovery
│   ├── platform/                 # Platform/tenant capabilities
│   ├── professional_platform/   # Professional diagnostic platform seams
│   ├── security/                 # Security foundations
│   └── observability/            # Observability foundations
│
├── device/                       # Device-side / future hardware boundary
├── vehicle/                      # Vehicle protocol/domain resources
├── models/                       # Local AI model documentation/resources
├── datasets/                     # Golden/test/dataset assets
├── data/                         # Runtime/data assets
├── tests/                        # Unit/API/integration/regression suites
├── infrastructure/              # Docker/Postgres/monitoring
├── scripts/                      # Local runtime and installation scripts
├── assets/                       # Application icons/assets
└── docs/
    ├── architecture/             # Architecture decisions and views
    └── device/                   # Device architecture
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
│   └── providers.py
├── evaluation/
│   ├── golden.py
│   └── grounding.py
├── ingestion/
│   ├── chunker.py
│   ├── dataset.py
│   ├── models.py
│   └── parsers.py
├── llm/
│   ├── factory.py
│   ├── llama_server.py
│   ├── openai_compatible.py
│   └── interfaces_guard.py
├── ml/
│   └── anomaly.py
├── rag/
│   ├── store.py
│   └── reranker.py
└── reasoning/
    ├── engine.py
    ├── evidence_extractor.py
    └── pipeline.py
~~~

### Responsibility

- `interfaces.py`: provider contracts.
- `reasoning/engine.py`: deterministic + AI-assisted reasoning loop.
- `reasoning/evidence_extractor.py`: converts natural language into structured evidence.
- `reasoning/pipeline.py`: deterministic reasoning → retrieval → safe prompt context.
- `rag/store.py`: knowledge document store/search abstraction.
- `rag/reranker.py`: retrieval ranking.
- `llm/*`: runtime provider adapters.
- `ml/*`: numeric anomaly detection.
- `evaluation/*`: golden/grounding evaluation.
- `ingestion/*`: knowledge ingestion pipeline.
- `embeddings/*`: embedding provider seam.

## 4. Diagnostic hierarchy

~~~text
DiagnosticSession
├── Vehicle
├── Symptoms
├── DTCs
├── Evidence[]
│   ├── provenance/source
│   ├── status
│   ├── confidence
│   └── metadata
├── Hypotheses[]
│   ├── supporting evidence
│   ├── contradicting evidence
│   └── status
├── Recommendations[]
│   ├── information gain
│   ├── cost
│   ├── safety/risk
│   └── target hypotheses
├── TestResults[]
├── Measurements[]
├── LiveData[]
├── Device connection
└── Audit log
~~~

## 5. Client hierarchy

### Desktop

The current desktop workstation contains both Python/PySide6 and Flutter-era source artifacts. The Python/PySide6 path is the current standalone workstation/runtime path, while `desktop_flutter_legacy` is retained as legacy source.

### Android

The native Android source contains:

- API client,
- diagnostic API,
- OBD clients for Bluetooth/Wi-Fi/USB,
- repository,
- ViewModel,
- diagnostic screen,
- vehicle catalog,
- settings/localization.

### Flutter/mobile

`apps/mobile` is a smaller cross-platform foundation containing device/OBD abstractions and shared vehicle catalog code.

## 6. Device hierarchy

~~~text
Diagnostic domain
      │
      ▼
Device abstraction
      │
      ├── Simulator
      ├── BLE transport
      ├── Wi-Fi transport
      ├── USB/serial transport
      ├── J2534 seam
      └── Future custom Android diagnostic device
~~~

The domain should consume normalized diagnostic operations rather than transport-specific implementation details.
