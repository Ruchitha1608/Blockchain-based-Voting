"""
Delete a voter to allow re-registration
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def delete_voter(voter_id: str):
    """Delete a voter and all related records"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.begin() as conn:
        # Check if voter exists
        result = conn.execute(
            text("SELECT voter_id, full_name FROM voters WHERE voter_id = :voter_id"),
            {"voter_id": voter_id}
        )
        voter = result.fetchone()

        if not voter:
            print(f"❌ Voter {voter_id} not found")
            return

        print(f"🗑️  Deleting voter: {voter.voter_id} ({voter.full_name})")

        # Drop both no_update and no_delete rules temporarily
        conn.execute(text("DROP RULE IF EXISTS auth_attempts_no_delete ON auth_attempts"))
        conn.execute(text("DROP RULE IF EXISTS auth_attempts_no_update ON auth_attempts"))
        print("   ℹ️  Temporarily disabled append-only rules")

        # Update auth_attempts to NULL out the voter_id
        conn.execute(
            text("UPDATE auth_attempts SET voter_id = NULL WHERE voter_id = (SELECT id FROM voters WHERE voter_id = :voter_id)"),
            {"voter_id": voter_id}
        )
        print("   ✅ Nullified voter_id in auth_attempts")

        # Delete the voter
        conn.execute(
            text("DELETE FROM voters WHERE voter_id = :voter_id"),
            {"voter_id": voter_id}
        )
        print("   ✅ Deleted voter record")

        # Recreate both rules
        conn.execute(text("CREATE RULE auth_attempts_no_delete AS ON DELETE TO auth_attempts DO INSTEAD NOTHING"))
        conn.execute(text("CREATE RULE auth_attempts_no_update AS ON UPDATE TO auth_attempts DO INSTEAD NOTHING"))
        print("   ✅ Re-enabled append-only rules")

        print(f"\n✅ Successfully deleted voter {voter_id}")
        print("You can now re-register this voter with corrected data.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_voter.py <voter_id>")
        print("Example: python delete_voter.py TEST001")
        sys.exit(1)

    voter_id = sys.argv[1]
    delete_voter(voter_id)
