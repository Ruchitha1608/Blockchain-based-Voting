"""
Run database migration to make fingerprint fields optional
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    """Execute the migration to make fingerprint fields nullable"""

    # Create database engine
    engine = create_engine(settings.DATABASE_URL)

    migration_sql = """
-- Make fingerprint_template_hash nullable
ALTER TABLE voters
ALTER COLUMN fingerprint_template_hash DROP NOT NULL;

-- Make encrypted_fingerprint_template nullable
ALTER TABLE voters
ALTER COLUMN encrypted_fingerprint_template DROP NOT NULL;

-- Update comments to reflect optional nature
COMMENT ON COLUMN voters.encrypted_fingerprint_template IS 'AES-256-GCM encrypted fingerprint template for similarity comparison (optional)';
COMMENT ON COLUMN voters.fingerprint_template_hash IS 'SHA-256 hash of fingerprint template for integrity verification (optional)';
"""

    try:
        with engine.begin() as conn:
            # Execute ALTER statements one by one
            statements = [
                "ALTER TABLE voters ALTER COLUMN fingerprint_template_hash DROP NOT NULL",
                "ALTER TABLE voters ALTER COLUMN encrypted_fingerprint_template DROP NOT NULL",
                "COMMENT ON COLUMN voters.encrypted_fingerprint_template IS 'AES-256-GCM encrypted fingerprint template for similarity comparison (optional)'",
                "COMMENT ON COLUMN voters.fingerprint_template_hash IS 'SHA-256 hash of fingerprint template for integrity verification (optional)'"
            ]

            for statement in statements:
                print(f"Executing: {statement[:80]}...")
                conn.execute(text(statement))

        print("\n✅ Migration completed successfully!")
        print("Fingerprint fields are now optional in the voters table.")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Running database migration: Make fingerprint fields optional")
    print("=" * 60)
    run_migration()
