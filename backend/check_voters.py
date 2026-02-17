"""
Check registered voters in database
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_voters():
    """Display all registered voters"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                v.voter_id,
                v.full_name,
                v.age,
                c.name as constituency,
                v.has_voted,
                v.failed_auth_count,
                v.locked_out,
                v.registered_at,
                CASE
                    WHEN v.face_embedding_hash IS NOT NULL THEN 'Yes'
                    ELSE 'No'
                END as has_face,
                CASE
                    WHEN v.fingerprint_template_hash IS NOT NULL THEN 'Yes'
                    ELSE 'No'
                END as has_fingerprint
            FROM voters v
            JOIN constituencies c ON v.constituency_id = c.id
            ORDER BY v.registered_at DESC;
        """))

        voters = result.fetchall()

        if not voters:
            print("❌ No voters registered yet!")
            print("\nPlease register a voter first:")
            print("1. Go to http://localhost:3000/admin/voters")
            print("2. Fill in voter details and capture face image")
            print("3. Click 'Register Voter'")
            return

        print(f"✅ Found {len(voters)} registered voter(s):\n")
        print("=" * 120)
        print(f"{'Voter ID':<15} {'Name':<25} {'Age':<5} {'Constituency':<20} {'Face':<8} {'Fingerprint':<12} {'Voted':<8}")
        print("=" * 120)

        for v in voters:
            print(f"{v.voter_id:<15} {v.full_name:<25} {v.age:<5} {v.constituency:<20} {v.has_face:<8} {v.has_fingerprint:<12} {'Yes' if v.has_voted else 'No':<8}")

        print("=" * 120)

if __name__ == "__main__":
    check_voters()
