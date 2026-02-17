-- Migration: Make fingerprint fields optional in voters table
-- Date: 2026-02-13
-- Reason: Allow voter registration without fingerprint for testing/fallback scenarios

-- Make fingerprint_template_hash nullable
ALTER TABLE voters
ALTER COLUMN fingerprint_template_hash DROP NOT NULL;

-- Make encrypted_fingerprint_template nullable
ALTER TABLE voters
ALTER COLUMN encrypted_fingerprint_template DROP NOT NULL;

-- Update comments to reflect optional nature
COMMENT ON COLUMN voters.encrypted_fingerprint_template IS 'AES-256-GCM encrypted fingerprint template for similarity comparison (optional)';
COMMENT ON COLUMN voters.fingerprint_template_hash IS 'SHA-256 hash of fingerprint template for integrity verification (optional)';
