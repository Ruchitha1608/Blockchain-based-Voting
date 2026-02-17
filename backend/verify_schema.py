"""
Verify database schema changes
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from app.config import settings

def verify_schema():
    """Check if fingerprint columns are nullable"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # Query to check column nullability
        result = conn.execute(text("""
            SELECT
                column_name,
                is_nullable,
                data_type
            FROM information_schema.columns
            WHERE table_name = 'voters'
            AND column_name IN ('fingerprint_template_hash', 'encrypted_fingerprint_template')
            ORDER BY column_name;
        """))

        print("Voters table - Fingerprint column status:")
        print("=" * 60)
        for row in result:
            nullable_status = "✅ NULLABLE" if row.is_nullable == "YES" else "❌ NOT NULL"
            print(f"{row.column_name:40} {nullable_status}")

if __name__ == "__main__":
    verify_schema()
