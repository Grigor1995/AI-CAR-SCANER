BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_ecosystem

CREATE TABLE IF NOT EXISTS vehicle_profiles (id VARCHAR(64) PRIMARY KEY, payload JSON NOT NULL);

CREATE TABLE ecosystem_accounts (
    id VARCHAR(36) NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    mobile VARCHAR(20),
    language VARCHAR(2) NOT NULL,
    timezone VARCHAR(100) NOT NULL,
    active BOOLEAN NOT NULL,
    email_verified BOOLEAN NOT NULL,
    mobile_verified BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_eco_language CHECK (language IN ('en','hy','ru')),
    UNIQUE (email)
);

CREATE TABLE ecosystem_account_roles (
    account_id VARCHAR(36) NOT NULL,
    role VARCHAR(16) NOT NULL,
    PRIMARY KEY (account_id, role),
    CONSTRAINT ck_eco_role CHECK (role IN ('USER','CUSTOMER','ADMIN','MARKET')),
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id) ON DELETE CASCADE
);

CREATE TABLE ecosystem_auth_sessions (
    token_hash VARCHAR(64) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN NOT NULL,
    PRIMARY KEY (token_hash),
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id) ON DELETE CASCADE
);

CREATE INDEX ix_ecosystem_auth_sessions_account_id ON ecosystem_auth_sessions (account_id);

CREATE INDEX ix_ecosystem_auth_sessions_expires_at ON ecosystem_auth_sessions (expires_at);

CREATE TABLE ecosystem_service_centers (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(500) NOT NULL,
    phone VARCHAR(20),
    verified BOOLEAN NOT NULL,
    active BOOLEAN NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE ecosystem_staff (
    center_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    role VARCHAR(16) NOT NULL,
    active BOOLEAN NOT NULL,
    PRIMARY KEY (center_id, account_id),
    CONSTRAINT ck_eco_staff_role CHECK (role IN ('owner','admin','technician','viewer')),
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id) ON DELETE CASCADE,
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id) ON DELETE CASCADE
);

CREATE TABLE ecosystem_vehicle_ownership (
    profile_id VARCHAR(64) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (profile_id),
    FOREIGN KEY(profile_id) REFERENCES vehicle_profiles (id) ON DELETE CASCADE,
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id) ON DELETE CASCADE
);

CREATE INDEX ix_ecosystem_vehicle_ownership_account_id ON ecosystem_vehicle_ownership (account_id);

CREATE TABLE ecosystem_invitations (
    id VARCHAR(36) NOT NULL,
    center_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id) ON DELETE CASCADE,
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id) ON DELETE CASCADE
);

CREATE INDEX ix_ecosystem_invitations_account_id ON ecosystem_invitations (account_id);

CREATE TABLE ecosystem_access_consents (
    id VARCHAR(36) NOT NULL,
    owner_id VARCHAR(36) NOT NULL,
    center_id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(64) NOT NULL,
    invitation_id VARCHAR(36) NOT NULL,
    scopes JSON NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_eco_vehicle_consent UNIQUE (owner_id, center_id, profile_id),
    FOREIGN KEY(owner_id) REFERENCES ecosystem_accounts (id) ON DELETE CASCADE,
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id) ON DELETE CASCADE,
    FOREIGN KEY(profile_id) REFERENCES vehicle_profiles (id) ON DELETE CASCADE,
    FOREIGN KEY(invitation_id) REFERENCES ecosystem_invitations (id) ON DELETE CASCADE
);

CREATE INDEX ix_ecosystem_access_consents_owner_id ON ecosystem_access_consents (owner_id);

CREATE INDEX ix_ecosystem_access_consents_center_id ON ecosystem_access_consents (center_id);

CREATE TABLE ecosystem_audit_events (
    id VARCHAR(36) NOT NULL,
    actor_id VARCHAR(36),
    action VARCHAR(80) NOT NULL,
    target_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(actor_id) REFERENCES ecosystem_accounts (id) ON DELETE SET NULL
);

CREATE INDEX ix_ecosystem_audit_events_actor_id ON ecosystem_audit_events (actor_id);

CREATE INDEX ix_ecosystem_audit_events_created_at ON ecosystem_audit_events (created_at);

INSERT INTO alembic_version (version_num) VALUES ('0001_ecosystem') RETURNING alembic_version.version_num;

-- Running upgrade 0001_ecosystem -> 0002_business

CREATE TABLE ecosystem_technical_references (
    id VARCHAR(36) NOT NULL,
    kind VARCHAR(16) NOT NULL,
    payload JSON NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE ecosystem_diagnostics (
    id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(64) NOT NULL,
    actor_id VARCHAR(36) NOT NULL,
    center_id VARCHAR(36),
    payload JSON NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(actor_id) REFERENCES ecosystem_accounts (id),
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id),
    FOREIGN KEY(profile_id) REFERENCES vehicle_profiles (id)
);

CREATE INDEX ix_ecosystem_diagnostics_profile_id ON ecosystem_diagnostics (profile_id);

CREATE TABLE ecosystem_directory_details (
    center_id VARCHAR(36) NOT NULL,
    payload JSON NOT NULL,
    PRIMARY KEY (center_id),
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id)
);

CREATE TABLE ecosystem_merchants (
    id VARCHAR(36) NOT NULL,
    owner_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(500) NOT NULL,
    phone VARCHAR(20),
    verified BOOLEAN NOT NULL,
    active BOOLEAN NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(owner_id) REFERENCES ecosystem_accounts (id)
);

CREATE INDEX ix_ecosystem_merchants_owner_id ON ecosystem_merchants (owner_id);

CREATE TABLE ecosystem_monitoring_schedules (
    id VARCHAR(36) NOT NULL,
    owner_id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(64) NOT NULL,
    enabled BOOLEAN NOT NULL,
    payload JSON NOT NULL,
    next_due TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(owner_id) REFERENCES ecosystem_accounts (id),
    FOREIGN KEY(profile_id) REFERENCES vehicle_profiles (id),
    CONSTRAINT uq_eco_monitoring_vehicle UNIQUE (owner_id, profile_id)
);

CREATE INDEX ix_ecosystem_monitoring_schedules_next_due ON ecosystem_monitoring_schedules (next_due);

CREATE INDEX ix_ecosystem_monitoring_schedules_owner_id ON ecosystem_monitoring_schedules (owner_id);

CREATE TABLE ecosystem_notifications (
    id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    kind VARCHAR(60) NOT NULL,
    payload JSON NOT NULL,
    read BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id)
);

CREATE INDEX ix_ecosystem_notifications_account_id ON ecosystem_notifications (account_id);

CREATE TABLE ecosystem_settings (
    account_id VARCHAR(36) NOT NULL,
    payload JSON NOT NULL,
    PRIMARY KEY (account_id),
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id)
);

CREATE TABLE ecosystem_staff_invitations (
    id VARCHAR(36) NOT NULL,
    center_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    role VARCHAR(16) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted BOOLEAN NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(account_id) REFERENCES ecosystem_accounts (id),
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id)
);

CREATE INDEX ix_ecosystem_staff_invitations_account_id ON ecosystem_staff_invitations (account_id);

CREATE TABLE ecosystem_work_orders (
    id VARCHAR(36) NOT NULL,
    center_id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(64) NOT NULL,
    title VARCHAR(300) NOT NULL,
    notes VARCHAR(10000) NOT NULL,
    status VARCHAR(20) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_eco_order_status CHECK (status IN ('OPEN','IN_PROGRESS','COMPLETED')),
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id),
    FOREIGN KEY(profile_id) REFERENCES vehicle_profiles (id)
);

CREATE INDEX ix_ecosystem_work_orders_center_id ON ecosystem_work_orders (center_id);

CREATE TABLE ecosystem_monitoring_runs (
    id VARCHAR(36) NOT NULL,
    schedule_id VARCHAR(36) NOT NULL,
    due_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(16) NOT NULL,
    reason VARCHAR(200) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_eco_monitoring_status CHECK (status IN ('DEFERRED','MISSED','FAILED','COMPLETED')),
    FOREIGN KEY(schedule_id) REFERENCES ecosystem_monitoring_schedules (id),
    CONSTRAINT uq_eco_monitoring_run UNIQUE (schedule_id, due_at)
);

CREATE INDEX ix_ecosystem_monitoring_runs_schedule_id ON ecosystem_monitoring_runs (schedule_id);

CREATE TABLE ecosystem_products (
    id VARCHAR(36) NOT NULL,
    merchant_id VARCHAR(36) NOT NULL,
    payload JSON NOT NULL,
    price_minor INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL,
    stock INTEGER NOT NULL,
    listed BOOLEAN NOT NULL,
    moderation VARCHAR(16) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_eco_moderation CHECK (moderation IN ('PENDING','APPROVED','REJECTED')),
    CONSTRAINT ck_eco_product_values CHECK (price_minor >= 0 AND stock >= 0),
    FOREIGN KEY(merchant_id) REFERENCES ecosystem_merchants (id)
);

CREATE INDEX ix_ecosystem_products_merchant_id ON ecosystem_products (merchant_id);

CREATE TABLE ecosystem_offers (
    id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    basis_points INTEGER NOT NULL,
    audience VARCHAR(16) NOT NULL,
    center_id VARCHAR(36),
    minimum_quantity INTEGER NOT NULL,
    coupon VARCHAR(40),
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_eco_offer_values CHECK (basis_points BETWEEN 1 AND 9000 AND minimum_quantity > 0),
    FOREIGN KEY(center_id) REFERENCES ecosystem_service_centers (id),
    FOREIGN KEY(product_id) REFERENCES ecosystem_products (id)
);

CREATE INDEX ix_ecosystem_offers_product_id ON ecosystem_offers (product_id);

UPDATE alembic_version SET version_num='0002_business' WHERE alembic_version.version_num = '0001_ecosystem';

COMMIT;
