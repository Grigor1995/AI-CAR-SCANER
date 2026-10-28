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

COMMIT;

