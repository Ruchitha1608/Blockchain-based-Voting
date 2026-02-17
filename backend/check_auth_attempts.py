"""
Check authentication attempts and similarity scores
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_auth_attempts():
    """Display recent authentication attempts with similarity scores"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                a.attempted_at,
                v.voter_id,
                v.full_name,
                a.auth_method,
                a.outcome,
                a.similarity_score,
                a.failure_reason,
                a.ip_address
            FROM auth_attempts a
            LEFT JOIN voters v ON a.voter_id = v.id
            ORDER BY a.attempted_at DESC
            LIMIT 10;
        """))

        attempts = result.fetchall()

        if not attempts:
            print("ℹ️  No authentication attempts found yet.")
            return

        print(f"📊 Last {len(attempts)} authentication attempt(s):\n")
        print("=" * 140)
        print(f"{'Time':<20} {'Voter ID':<12} {'Name':<20} {'Method':<12} {'Outcome':<10} {'Similarity':<12} {'Reason':<40}")
        print("=" * 140)

        for a in attempts:
            time_str = a.attempted_at.strftime("%Y-%m-%d %H:%M:%S") if a.attempted_at else "N/A"
            voter_id = a.voter_id or "Unknown"
            name = a.full_name or "Unknown"
            similarity = f"{a.similarity_score:.4f}" if a.similarity_score else "N/A"
            reason = (a.failure_reason[:37] + "...") if a.failure_reason and len(a.failure_reason) > 40 else (a.failure_reason or "N/A")

            print(f"{time_str:<20} {voter_id:<12} {name:<20} {a.auth_method:<12} {a.outcome:<10} {similarity:<12} {reason:<40}")

        print("=" * 140)
        print(f"\n💡 Current face recognition threshold: {settings.FACE_THRESHOLD} (similarity must be >= this value)")
        print(f"   Similarity scores range from 0.0 (no match) to 1.0 (perfect match)")

if __name__ == "__main__":
    check_auth_attempts()
