CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY, email TEXT UNIQUE NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS vehicles (id UUID PRIMARY KEY, make TEXT NOT NULL, model TEXT NOT NULL, chassis TEXT, year INT, engine TEXT, fuel JSONB NOT NULL DEFAULT '[]', ecu TEXT, metadata JSONB NOT NULL DEFAULT '{}');
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS chassis TEXT;
CREATE TABLE IF NOT EXISTS diagnostic_sessions (id UUID PRIMARY KEY, vehicle_id UUID REFERENCES vehicles(id), state TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS evidence (id UUID PRIMARY KEY, session_id UUID NOT NULL REFERENCES diagnostic_sessions(id), fact TEXT NOT NULL, source TEXT NOT NULL, status TEXT NOT NULL, confidence DOUBLE PRECISION, source_ref TEXT, metadata JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS hypotheses (id UUID PRIMARY KEY, session_id UUID NOT NULL REFERENCES diagnostic_sessions(id), category TEXT NOT NULL, statement TEXT NOT NULL, status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS diagnostic_tests (id UUID PRIMARY KEY, session_id UUID NOT NULL REFERENCES diagnostic_sessions(id), name TEXT NOT NULL, purpose TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS knowledge_documents (id UUID PRIMARY KEY, title TEXT NOT NULL, manufacturer TEXT, model TEXT, year INT, engine TEXT, fuel TEXT, ecu TEXT, document_type TEXT, source TEXT, version TEXT, language TEXT, license TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS knowledge_chunks (id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES knowledge_documents(id), content TEXT NOT NULL, metadata JSONB NOT NULL DEFAULT '{}', embedding vector(768));

-- Phase 6: professional workshop platform
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS organization_memberships (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role TEXT NOT NULL CHECK (role IN ('owner','admin','technician','viewer')),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (organization_id, user_id)
);
CREATE TABLE IF NOT EXISTS fleets (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS fleet_vehicles (
    fleet_id UUID NOT NULL REFERENCES fleets(id) ON DELETE CASCADE,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    nickname TEXT,
    PRIMARY KEY (fleet_id, vehicle_id)
);
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL UNIQUE REFERENCES organizations(id),
    plan TEXT NOT NULL,
    status TEXT NOT NULL,
    seat_limit INT NOT NULL,
    vehicle_limit INT NOT NULL,
    renews_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    actor_user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_org_created ON audit_logs(organization_id, created_at DESC);
CREATE TABLE IF NOT EXISTS usage_snapshots (
    organization_id UUID NOT NULL REFERENCES organizations(id),
    period TEXT NOT NULL,
    active_technicians INT NOT NULL DEFAULT 0,
    active_vehicles INT NOT NULL DEFAULT 0,
    diagnostic_sessions INT NOT NULL DEFAULT 0,
    completed_sessions INT NOT NULL DEFAULT 0,
    dtcs_read INT NOT NULL DEFAULT 0,
    ai_analyses INT NOT NULL DEFAULT 0,
    offline_sync_operations INT NOT NULL DEFAULT 0,
    PRIMARY KEY (organization_id, period)
);

-- Phase 9: AI knowledge chunks for pgvector-backed RAG
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS ai_knowledge_chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR(256) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ai_knowledge_chunks_document ON ai_knowledge_chunks(document_id);

-- Phase 10: knowledge ingestion provenance and indexing metadata
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS source_uri TEXT;
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS content_type TEXT;
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS page_count INT NOT NULL DEFAULT 0;
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS char_count INT NOT NULL DEFAULT 0;
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS indexed_at TIMESTAMPTZ;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS chunk_index INT NOT NULL DEFAULT 0;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS page_start INT;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS page_end INT;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS start_char INT NOT NULL DEFAULT 0;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS end_char INT NOT NULL DEFAULT 0;
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS content_hash TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_documents_content_hash ON knowledge_documents(content_hash);
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_document_order ON knowledge_chunks(document_id, chunk_index);
CREATE INDEX IF NOT EXISTS ix_knowledge_documents_scope ON knowledge_documents(manufacturer, model, year, engine, ecu);

-- Phase 11: production hybrid vector retrieval
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR(256) NOT NULL,
    content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_rag_chunks_document ON rag_chunks(document_id);
CREATE INDEX IF NOT EXISTS ix_rag_chunks_metadata ON rag_chunks USING GIN(metadata);
CREATE INDEX IF NOT EXISTS ix_rag_chunks_tsv ON rag_chunks USING GIN(content_tsv);
CREATE INDEX IF NOT EXISTS ix_rag_chunks_embedding_hnsw ON rag_chunks USING hnsw (embedding vector_cosine_ops);

-- Phase 13: diagnostic decision/test-planning metadata
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS priority_score DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS expected_information_gain DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS estimated_cost DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS risk_level TEXT NOT NULL DEFAULT 'LOW';
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS prerequisites JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS target_hypotheses JSONB NOT NULL DEFAULT '[]'::jsonb;
CREATE INDEX IF NOT EXISTS ix_diagnostic_tests_session_priority ON diagnostic_tests(session_id, priority_score DESC);

-- Phase 14: real-time vehicle telemetry and signal intelligence
CREATE TABLE IF NOT EXISTS telemetry_samples (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    timestamp_ms BIGINT NOT NULL,
    pid TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT,
    source TEXT NOT NULL DEFAULT 'OBD',
    sequence BIGINT,
    quality TEXT NOT NULL DEFAULT 'GOOD',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_telemetry_session_pid_time ON telemetry_samples(session_id, pid, timestamp_ms);
CREATE INDEX IF NOT EXISTS ix_telemetry_session_time ON telemetry_samples(session_id, timestamp_ms);
CREATE TABLE IF NOT EXISTS telemetry_events (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    pid TEXT NOT NULL,
    event_type TEXT NOT NULL,
    start_ms BIGINT NOT NULL,
    end_ms BIGINT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    evidence_fact TEXT NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_telemetry_events_session_time ON telemetry_events(session_id, start_ms);

-- Phase 16: CAN / ISO-TP / UDS live diagnostic acquisition
CREATE TABLE IF NOT EXISTS protocol_trace_events (
    event_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    timestamp_ns BIGINT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('TX','RX')),
    protocol TEXT NOT NULL,
    arbitration_id BIGINT,
    data_hex TEXT NOT NULL,
    is_extended BOOLEAN NOT NULL DEFAULT FALSE,
    is_fd BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_protocol_trace_session_time ON protocol_trace_events(session_id, timestamp_ns);
CREATE INDEX IF NOT EXISTS ix_protocol_trace_session_protocol ON protocol_trace_events(session_id, protocol);

CREATE TABLE IF NOT EXISTS ecu_identities (
    session_id UUID PRIMARY KEY REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    vin TEXT,
    software_version TEXT,
    hardware_version TEXT,
    extra_dids JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS uds_dtc_records (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    raw_dtc INTEGER NOT NULL,
    code TEXT NOT NULL,
    status_byte INTEGER NOT NULL,
    service_subfunction INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_uds_dtc_session_code ON uds_dtc_records(session_id, code);

-- Phase 17: multi-ECU vehicle network and gateway topology
CREATE TABLE IF NOT EXISTS vehicle_ecu_nodes (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    ecu_id TEXT NOT NULL,
    name TEXT NOT NULL,
    request_id INTEGER NOT NULL,
    response_id INTEGER NOT NULL,
    bus TEXT NOT NULL DEFAULT 'CAN0',
    gateway_id TEXT,
    address_type TEXT NOT NULL DEFAULT 'NORMAL',
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, ecu_id)
);
CREATE INDEX IF NOT EXISTS ix_vehicle_ecu_nodes_session_bus ON vehicle_ecu_nodes(session_id, bus);
CREATE INDEX IF NOT EXISTS ix_vehicle_ecu_nodes_session_ids ON vehicle_ecu_nodes(session_id, request_id, response_id);

CREATE TABLE IF NOT EXISTS vehicle_gateways (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    gateway_id TEXT NOT NULL,
    name TEXT NOT NULL,
    bus TEXT NOT NULL DEFAULT 'CAN0',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, gateway_id)
);
CREATE INDEX IF NOT EXISTS ix_vehicle_gateways_session_bus ON vehicle_gateways(session_id, bus);

CREATE TABLE IF NOT EXISTS vehicle_gateway_routes (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    gateway_id TEXT NOT NULL,
    source_bus TEXT NOT NULL,
    target_bus TEXT NOT NULL,
    target_ecu_id TEXT NOT NULL,
    addressing TEXT NOT NULL DEFAULT 'NORMAL',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_gateway_routes_session_gateway ON vehicle_gateway_routes(session_id, gateway_id);

CREATE TABLE IF NOT EXISTS ecu_cross_correlations (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    correlation_type TEXT NOT NULL,
    code TEXT,
    ecu_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence TEXT NOT NULL,
    interpretation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ecu_cross_correlations_session ON ecu_cross_correlations(session_id, correlation_type);

-- Phase 18: multi-bus configuration and diagnostic routing
CREATE TABLE IF NOT EXISTS vehicle_can_buses (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    bus_name TEXT NOT NULL,
    bitrate INTEGER NOT NULL,
    can_fd BOOLEAN NOT NULL DEFAULT FALSE,
    data_bitrate INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, bus_name)
);
CREATE INDEX IF NOT EXISTS ix_vehicle_can_buses_session ON vehicle_can_buses(session_id, bus_name);

CREATE TABLE IF NOT EXISTS gateway_forwarding_events (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    gateway_id TEXT NOT NULL,
    source_bus TEXT NOT NULL,
    target_bus TEXT NOT NULL,
    arbitration_id INTEGER NOT NULL,
    direction TEXT NOT NULL,
    timestamp_ns BIGINT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_gateway_forwarding_session_time ON gateway_forwarding_events(session_id, created_at);

-- Phase 19: passive CAN network discovery and automatic ECU mapping
CREATE TABLE IF NOT EXISTS network_discovery_observations (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    bus_name TEXT NOT NULL,
    arbitration_id INTEGER NOT NULL,
    dlc INTEGER NOT NULL,
    data_hex TEXT NOT NULL,
    timestamp_ns BIGINT NOT NULL,
    direction TEXT NOT NULL DEFAULT 'RX',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_network_discovery_observations_session_bus_id
    ON network_discovery_observations(session_id, bus_name, arbitration_id, timestamp_ns);

CREATE TABLE IF NOT EXISTS network_discovery_candidates (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    candidate_id TEXT NOT NULL,
    bus_name TEXT NOT NULL,
    request_id INTEGER,
    response_id INTEGER,
    classification TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    observed_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, candidate_id)
);
CREATE INDEX IF NOT EXISTS ix_network_discovery_candidates_session_bus
    ON network_discovery_candidates(session_id, bus_name, confidence DESC);

-- Phase 20: active ECU verification and topology correlation
CREATE TABLE IF NOT EXISTS network_active_probe_results (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    candidate_id TEXT NOT NULL,
    bus_name TEXT NOT NULL,
    request_id INTEGER NOT NULL,
    response_id INTEGER NOT NULL,
    gateway_id TEXT,
    classification TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    responded BOOLEAN NOT NULL,
    identity JSONB NOT NULL DEFAULT '{}'::jsonb,
    successful_dids JSONB NOT NULL DEFAULT '[]'::jsonb,
    negative_responses JSONB NOT NULL DEFAULT '[]'::jsonb,
    error TEXT,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_network_active_probe_session_candidate
    ON network_active_probe_results(session_id, candidate_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_network_active_probe_session_classification
    ON network_active_probe_results(session_id, classification, confidence DESC);

CREATE TABLE IF NOT EXISTS network_topology_correlations (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    candidate_id TEXT NOT NULL,
    status TEXT NOT NULL,
    gateway_id TEXT,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_network_topology_correlations_session_status
    ON network_topology_correlations(session_id, status, created_at DESC);

-- Shared vehicle selector catalog. This is the single source of truth for
-- Make -> Model -> Chassis -> Year -> Engine -> ECU selection used by
-- desktop and mobile clients through the FastAPI catalog endpoints.
CREATE TABLE IF NOT EXISTS vehicle_catalog_entries (
    id UUID PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    chassis TEXT,
    year INT NOT NULL,
    engine TEXT NOT NULL,
    ecu TEXT,
    fuel JSONB NOT NULL DEFAULT '[]'::jsonb,
    source TEXT NOT NULL DEFAULT 'unknown',
    scope TEXT NOT NULL DEFAULT 'family-level',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (make, model, chassis, year, engine, ecu)
);
CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_make
    ON vehicle_catalog_entries(make);
CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_make_model
    ON vehicle_catalog_entries(make, model);
CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_model_chassis
    ON vehicle_catalog_entries(make, model, chassis);
CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_year
    ON vehicle_catalog_entries(make, model, chassis, year);
ALTER TABLE vehicle_catalog_entries ALTER COLUMN ecu DROP NOT NULL;
ALTER TABLE vehicle_catalog_entries ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE vehicle_catalog_entries ADD COLUMN IF NOT EXISTS scope TEXT NOT NULL DEFAULT 'family-level';

CREATE INDEX IF NOT EXISTS idx_vehicle_catalog_engine
    ON vehicle_catalog_entries(make, model, chassis, year, engine);
