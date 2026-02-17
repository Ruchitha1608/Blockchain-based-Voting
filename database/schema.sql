-- Blockchain Voting System Database Schema
-- PostgreSQL 16+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing types if they exist
DROP TYPE IF EXISTS admin_role CASCADE;
DROP TYPE IF EXISTS election_status CASCADE;
DROP TYPE IF EXISTS auth_method CASCADE;
DROP TYPE IF EXISTS auth_outcome CASCADE;
DROP TYPE IF EXISTS log_action CASCADE;
DROP TYPE IF EXISTS tx_type CASCADE;

-- Create ENUM types
CREATE TYPE admin_role AS ENUM (
    'super_admin',
    'election_administrator',
    'polling_officer',
    'auditor'
);

CREATE TYPE election_status AS ENUM (
    'draft',
    'configured',
    'active',
    'ended',
    'finalized'
);

CREATE TYPE auth_method AS ENUM (
    'face',
    'fingerprint'
);

CREATE TYPE auth_outcome AS ENUM (
    'success',
    'failure',
    'lockout'
);

CREATE TYPE log_action AS ENUM (
    'admin_created',
    'admin_updated',
    'admin_deleted',
    'admin_login',
    'admin_logout',
    'election_created',
    'election_updated',
    'election_started',
    'election_closed',
    'election_finalized',
    'voter_registered',
    'voter_updated',
    'candidate_added',
    'candidate_updated',
    'contract_deployed',
    'settings_changed'
);

CREATE TYPE tx_type AS ENUM (
    'deploy_controller',
    'deploy_registry',
    'deploy_booth',
    'deploy_tallier',
    'register_voter',
    'register_candidate',
    'open_voting',
    'cast_vote',
    'close_voting',
    'tally_results',
    'finalize_election'
);

-- =============================================================================
-- TABLE: admins
-- =============================================================================
CREATE TABLE admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    role admin_role NOT NULL DEFAULT 'polling_officer',
    mfa_secret VARCHAR(255),
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_by UUID REFERENCES admins(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT admins_username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT admins_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes for admins
CREATE INDEX idx_admins_username ON admins(username);
CREATE INDEX idx_admins_email ON admins(email);
CREATE INDEX idx_admins_role ON admins(role);
CREATE INDEX idx_admins_is_active ON admins(is_active);

-- =============================================================================
-- TABLE: elections
-- =============================================================================
CREATE TABLE elections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(300) NOT NULL,
    description TEXT,
    status election_status NOT NULL DEFAULT 'draft',
    voting_start_at TIMESTAMPTZ,
    voting_end_at TIMESTAMPTZ,
    contract_address VARCHAR(42),
    voting_contract_address VARCHAR(42),
    registry_contract_address VARCHAR(42),
    tally_contract_address VARCHAR(42),
    network_id INTEGER,
    deployer_address VARCHAR(42),
    created_by UUID REFERENCES admins(id) ON DELETE SET NULL,
    finalized_by UUID REFERENCES admins(id) ON DELETE SET NULL,
    finalized_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT elections_name_length CHECK (LENGTH(name) >= 3),
    CONSTRAINT elections_dates_valid CHECK (voting_end_at IS NULL OR voting_start_at IS NULL OR voting_end_at > voting_start_at),
    CONSTRAINT elections_contract_format CHECK (contract_address IS NULL OR contract_address ~* '^0x[a-fA-F0-9]{40}$')
);

-- Indexes for elections
CREATE INDEX idx_elections_status ON elections(status);
CREATE INDEX idx_elections_created_by ON elections(created_by);
CREATE INDEX idx_elections_voting_dates ON elections(voting_start_at, voting_end_at);
CREATE INDEX idx_elections_contract_address ON elections(contract_address);

-- =============================================================================
-- TABLE: constituencies
-- =============================================================================
CREATE TABLE constituencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    election_id UUID NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) NOT NULL,
    on_chain_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT constituencies_name_length CHECK (LENGTH(name) >= 2),
    CONSTRAINT constituencies_code_length CHECK (LENGTH(code) >= 2),
    CONSTRAINT constituencies_on_chain_id_positive CHECK (on_chain_id >= 0),
    CONSTRAINT constituencies_unique_per_election UNIQUE (election_id, code),
    CONSTRAINT constituencies_unique_on_chain_id UNIQUE (election_id, on_chain_id)
);

-- Indexes for constituencies
CREATE INDEX idx_constituencies_election_id ON constituencies(election_id);
CREATE INDEX idx_constituencies_code ON constituencies(code);
CREATE INDEX idx_constituencies_on_chain_id ON constituencies(on_chain_id);

-- =============================================================================
-- TABLE: candidates
-- =============================================================================
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    election_id UUID NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    constituency_id UUID NOT NULL REFERENCES constituencies(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    party VARCHAR(200),
    bio TEXT,
    on_chain_id INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID REFERENCES admins(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT candidates_name_length CHECK (LENGTH(name) >= 2),
    CONSTRAINT candidates_on_chain_id_positive CHECK (on_chain_id >= 0),
    CONSTRAINT candidates_unique_on_chain_per_election UNIQUE (election_id, on_chain_id)
);

-- Indexes for candidates
CREATE INDEX idx_candidates_election_id ON candidates(election_id);
CREATE INDEX idx_candidates_constituency_id ON candidates(constituency_id);
CREATE INDEX idx_candidates_on_chain_id ON candidates(on_chain_id);
CREATE INDEX idx_candidates_is_active ON candidates(is_active);

-- =============================================================================
-- TABLE: voters
-- =============================================================================
CREATE TABLE voters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    voter_id VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(300) NOT NULL,
    address TEXT,
    age SMALLINT NOT NULL,
    constituency_id UUID NOT NULL REFERENCES constituencies(id) ON DELETE RESTRICT,
    face_embedding_hash VARCHAR(512) NOT NULL,
    fingerprint_template_hash VARCHAR(512) NOT NULL,
    biometric_salt VARCHAR(64) NOT NULL,
    encrypted_face_embedding TEXT NOT NULL,
    encrypted_fingerprint_template TEXT NOT NULL,
    blockchain_voter_id VARCHAR(66) NOT NULL UNIQUE,
    has_voted BOOLEAN NOT NULL DEFAULT FALSE,
    voted_at TIMESTAMPTZ,
    vote_tx_hash VARCHAR(66),
    failed_auth_count SMALLINT NOT NULL DEFAULT 0,
    locked_out BOOLEAN NOT NULL DEFAULT FALSE,
    lockout_at TIMESTAMPTZ,
    registered_by UUID REFERENCES admins(id) ON DELETE SET NULL,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT voters_age_minimum CHECK (age >= 18),
    CONSTRAINT voters_age_maximum CHECK (age <= 120),
    CONSTRAINT voters_name_length CHECK (LENGTH(full_name) >= 2),
    CONSTRAINT voters_blockchain_id_format CHECK (blockchain_voter_id ~* '^0x[a-fA-F0-9]{64}$'),
    CONSTRAINT voters_voted_consistency CHECK ((has_voted = TRUE AND voted_at IS NOT NULL AND vote_tx_hash IS NOT NULL) OR (has_voted = FALSE)),
    CONSTRAINT voters_lockout_consistency CHECK ((locked_out = TRUE AND lockout_at IS NOT NULL) OR (locked_out = FALSE))
);

-- Indexes for voters
CREATE INDEX idx_voters_voter_id ON voters(voter_id);
CREATE INDEX idx_voters_blockchain_voter_id ON voters(blockchain_voter_id);
CREATE INDEX idx_voters_constituency_id ON voters(constituency_id);
CREATE INDEX idx_voters_has_voted ON voters(has_voted);
CREATE INDEX idx_voters_locked_out ON voters(locked_out);
CREATE INDEX idx_voters_face_hash ON voters(face_embedding_hash);
CREATE INDEX idx_voters_fingerprint_hash ON voters(fingerprint_template_hash);

-- =============================================================================
-- TABLE: auth_attempts (APPEND-ONLY)
-- =============================================================================
CREATE TABLE auth_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    voter_id UUID REFERENCES voters(id) ON DELETE SET NULL,
    session_id UUID,
    polling_station VARCHAR(200),
    auth_method auth_method NOT NULL,
    outcome auth_outcome NOT NULL,
    failure_reason VARCHAR(500),
    similarity_score DECIMAL(5,4),
    ip_address INET,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT auth_attempts_similarity_range CHECK (similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1))
);

-- Indexes for auth_attempts
CREATE INDEX idx_auth_attempts_voter_id ON auth_attempts(voter_id);
CREATE INDEX idx_auth_attempts_session_id ON auth_attempts(session_id);
CREATE INDEX idx_auth_attempts_outcome ON auth_attempts(outcome);
CREATE INDEX idx_auth_attempts_attempted_at ON auth_attempts(attempted_at DESC);
CREATE INDEX idx_auth_attempts_auth_method ON auth_attempts(auth_method);

-- Make auth_attempts append-only (prevent UPDATE and DELETE)
CREATE RULE auth_attempts_no_update AS ON UPDATE TO auth_attempts DO INSTEAD NOTHING;
CREATE RULE auth_attempts_no_delete AS ON DELETE TO auth_attempts DO INSTEAD NOTHING;

-- =============================================================================
-- TABLE: vote_submissions (APPEND-ONLY)
-- =============================================================================
CREATE TABLE vote_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    voter_id UUID NOT NULL REFERENCES voters(id) ON DELETE RESTRICT,
    election_id UUID NOT NULL REFERENCES elections(id) ON DELETE RESTRICT,
    session_id UUID NOT NULL,
    tx_hash VARCHAR(66) NOT NULL UNIQUE,
    block_number BIGINT NOT NULL,
    gas_used BIGINT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT vote_submissions_unique_voter_election UNIQUE (voter_id, election_id),
    CONSTRAINT vote_submissions_tx_hash_format CHECK (tx_hash ~* '^0x[a-fA-F0-9]{64}$'),
    CONSTRAINT vote_submissions_block_positive CHECK (block_number > 0),
    CONSTRAINT vote_submissions_gas_positive CHECK (gas_used IS NULL OR gas_used > 0)
);

-- Indexes for vote_submissions
CREATE INDEX idx_vote_submissions_voter_id ON vote_submissions(voter_id);
CREATE INDEX idx_vote_submissions_election_id ON vote_submissions(election_id);
CREATE INDEX idx_vote_submissions_tx_hash ON vote_submissions(tx_hash);
CREATE INDEX idx_vote_submissions_session_id ON vote_submissions(session_id);
CREATE INDEX idx_vote_submissions_submitted_at ON vote_submissions(submitted_at DESC);

-- Make vote_submissions append-only (prevent UPDATE and DELETE)
CREATE RULE vote_submissions_no_update AS ON UPDATE TO vote_submissions DO INSTEAD NOTHING;
CREATE RULE vote_submissions_no_delete AS ON DELETE TO vote_submissions DO INSTEAD NOTHING;

-- =============================================================================
-- TABLE: audit_logs (APPEND-ONLY)
-- =============================================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES admins(id) ON DELETE SET NULL,
    action log_action NOT NULL,
    target_table VARCHAR(100),
    target_id UUID,
    details JSONB,
    ip_address INET,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for audit_logs
CREATE INDEX idx_audit_logs_admin_id ON audit_logs(admin_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_occurred_at ON audit_logs(occurred_at DESC);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_table, target_id);
CREATE INDEX idx_audit_logs_details ON audit_logs USING gin(details);

-- Make audit_logs append-only (prevent UPDATE and DELETE)
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

-- =============================================================================
-- TABLE: blockchain_txns
-- =============================================================================
CREATE TABLE blockchain_txns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    election_id UUID REFERENCES elections(id) ON DELETE SET NULL,
    tx_type tx_type NOT NULL,
    tx_hash VARCHAR(66) NOT NULL UNIQUE,
    block_number BIGINT,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42),
    gas_used BIGINT,
    status BOOLEAN NOT NULL DEFAULT TRUE,
    raw_event JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT blockchain_txns_tx_hash_format CHECK (tx_hash ~* '^0x[a-fA-F0-9]{64}$'),
    CONSTRAINT blockchain_txns_from_address_format CHECK (from_address ~* '^0x[a-fA-F0-9]{40}$'),
    CONSTRAINT blockchain_txns_to_address_format CHECK (to_address IS NULL OR to_address ~* '^0x[a-fA-F0-9]{40}$'),
    CONSTRAINT blockchain_txns_block_positive CHECK (block_number IS NULL OR block_number > 0)
);

-- Indexes for blockchain_txns
CREATE INDEX idx_blockchain_txns_election_id ON blockchain_txns(election_id);
CREATE INDEX idx_blockchain_txns_tx_hash ON blockchain_txns(tx_hash);
CREATE INDEX idx_blockchain_txns_tx_type ON blockchain_txns(tx_type);
CREATE INDEX idx_blockchain_txns_from_address ON blockchain_txns(from_address);
CREATE INDEX idx_blockchain_txns_recorded_at ON blockchain_txns(recorded_at DESC);
CREATE INDEX idx_blockchain_txns_raw_event ON blockchain_txns USING gin(raw_event);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER set_updated_at_admins
    BEFORE UPDATE ON admins
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_elections
    BEFORE UPDATE ON elections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_candidates
    BEFORE UPDATE ON candidates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_updated_at_voters
    BEFORE UPDATE ON voters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to prevent vote reset
CREATE OR REPLACE FUNCTION prevent_vote_reset()
RETURNS TRIGGER AS $$
BEGIN
    -- Prevent has_voted from being set to FALSE after being TRUE
    IF OLD.has_voted = TRUE AND NEW.has_voted = FALSE THEN
        RAISE EXCEPTION 'Cannot reset has_voted flag once set to true';
    END IF;

    -- Prevent vote_tx_hash from being cleared after being set
    IF OLD.vote_tx_hash IS NOT NULL AND NEW.vote_tx_hash IS NULL THEN
        RAISE EXCEPTION 'Cannot clear vote_tx_hash once set';
    END IF;

    -- Prevent voted_at from being cleared after being set
    IF OLD.voted_at IS NOT NULL AND NEW.voted_at IS NULL THEN
        RAISE EXCEPTION 'Cannot clear voted_at timestamp once set';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply prevent_vote_reset trigger
CREATE TRIGGER prevent_vote_reset_voters
    BEFORE UPDATE ON voters
    FOR EACH ROW
    EXECUTE FUNCTION prevent_vote_reset();

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Create initial super admin (password: Admin@123456)
-- Password hash is Argon2id hash of 'Admin@123456'
-- NOTE: This should be changed immediately in production
INSERT INTO admins (username, email, password_hash, role, is_active)
VALUES (
    'superadmin',
    'admin@voting.system',
    '$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHRoZXJl$qJ3dQqJ1Z2vKq0lPpZbZ8Q5hQKz6wYxGq8fU9lKqU/g',
    'super_admin',
    TRUE
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to get election statistics
CREATE OR REPLACE FUNCTION get_election_stats(election_uuid UUID)
RETURNS TABLE(
    total_constituencies BIGINT,
    total_candidates BIGINT,
    total_registered_voters BIGINT,
    total_votes_cast BIGINT,
    turnout_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM constituencies WHERE election_id = election_uuid),
        (SELECT COUNT(*) FROM candidates WHERE election_id = election_uuid AND is_active = TRUE),
        (SELECT COUNT(*) FROM voters v
         INNER JOIN constituencies c ON v.constituency_id = c.id
         WHERE c.election_id = election_uuid),
        (SELECT COUNT(*) FROM voters v
         INNER JOIN constituencies c ON v.constituency_id = c.id
         WHERE c.election_id = election_uuid AND v.has_voted = TRUE),
        (SELECT
            CASE
                WHEN COUNT(*) = 0 THEN 0
                ELSE ROUND((COUNT(*) FILTER (WHERE v.has_voted = TRUE) * 100.0) / COUNT(*), 2)
            END
         FROM voters v
         INNER JOIN constituencies c ON v.constituency_id = c.id
         WHERE c.election_id = election_uuid);
END;
$$ LANGUAGE plpgsql;

-- Function to check if voter can vote
CREATE OR REPLACE FUNCTION can_voter_vote(voter_uuid UUID, election_uuid UUID)
RETURNS TABLE(
    can_vote BOOLEAN,
    reason VARCHAR(200)
) AS $$
DECLARE
    v_has_voted BOOLEAN;
    v_locked_out BOOLEAN;
    v_constituency_id UUID;
    e_status election_status;
    e_voting_start TIMESTAMPTZ;
    e_voting_end TIMESTAMPTZ;
BEGIN
    -- Get voter details
    SELECT has_voted, locked_out, constituency_id
    INTO v_has_voted, v_locked_out, v_constituency_id
    FROM voters
    WHERE id = voter_uuid;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Voter not found'::VARCHAR(200);
        RETURN;
    END IF;

    -- Get election details
    SELECT e.status, e.voting_start_at, e.voting_end_at
    INTO e_status, e_voting_start, e_voting_end
    FROM elections e
    INNER JOIN constituencies c ON c.election_id = e.id
    WHERE e.id = election_uuid AND c.id = v_constituency_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Election not found for voter constituency'::VARCHAR(200);
        RETURN;
    END IF;

    -- Check conditions
    IF v_has_voted THEN
        RETURN QUERY SELECT FALSE, 'Voter has already cast vote'::VARCHAR(200);
        RETURN;
    END IF;

    IF v_locked_out THEN
        RETURN QUERY SELECT FALSE, 'Voter is locked out due to failed authentication attempts'::VARCHAR(200);
        RETURN;
    END IF;

    IF e_status != 'active' THEN
        RETURN QUERY SELECT FALSE, 'Election is not active'::VARCHAR(200);
        RETURN;
    END IF;

    IF e_voting_start IS NOT NULL AND NOW() < e_voting_start THEN
        RETURN QUERY SELECT FALSE, 'Voting has not started yet'::VARCHAR(200);
        RETURN;
    END IF;

    IF e_voting_end IS NOT NULL AND NOW() > e_voting_end THEN
        RETURN QUERY SELECT FALSE, 'Voting has ended'::VARCHAR(200);
        RETURN;
    END IF;

    -- All checks passed
    RETURN QUERY SELECT TRUE, 'Voter is eligible to vote'::VARCHAR(200);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE admins IS 'System administrators with different role levels';
COMMENT ON TABLE elections IS 'Elections with smart contract references';
COMMENT ON TABLE constituencies IS 'Electoral constituencies within elections';
COMMENT ON TABLE candidates IS 'Candidates registered for constituencies';
COMMENT ON TABLE voters IS 'Registered voters with biometric data (hashed)';
COMMENT ON TABLE auth_attempts IS 'Append-only log of all authentication attempts';
COMMENT ON TABLE vote_submissions IS 'Append-only log of all vote submissions';
COMMENT ON TABLE audit_logs IS 'Append-only log of all administrative actions';
COMMENT ON TABLE blockchain_txns IS 'Record of all blockchain transactions';

COMMENT ON COLUMN voters.encrypted_face_embedding IS 'AES-256-GCM encrypted quantized face embedding for similarity comparison';
COMMENT ON COLUMN voters.encrypted_fingerprint_template IS 'AES-256-GCM encrypted fingerprint template for similarity comparison';
COMMENT ON COLUMN voters.face_embedding_hash IS 'SHA-256 hash of face embedding for integrity verification';
COMMENT ON COLUMN voters.fingerprint_template_hash IS 'SHA-256 hash of fingerprint template for integrity verification';
COMMENT ON COLUMN voters.blockchain_voter_id IS 'Keccak256 hash sent to blockchain for anonymity';

-- =============================================================================
-- GRANTS (Optional - for production with separate users)
-- =============================================================================

-- Grant appropriate permissions to application user
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO voting_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO voting_app_user;
-- REVOKE UPDATE, DELETE ON auth_attempts, vote_submissions, audit_logs FROM voting_app_user;

-- Grant read-only permissions to auditor role
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO voting_auditor_user;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
