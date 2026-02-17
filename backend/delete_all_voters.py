#!/usr/bin/env python3
"""
Delete all voters from the database
Use this to reset the system when face authentication is not working
"""
from sqlalchemy import create_engine, text
from app.config import settings
import sys

def delete_all_voters():
    """Delete all voters from the database"""
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            # First, check how many voters exist
            result = conn.execute(text("SELECT COUNT(*) as count FROM voters"))
            count = result.fetchone().count

            if count == 0:
                print("✅ No voters in database - already clean")
                return

            print(f"Found {count} voter(s) in database")

            # Get voter details
            result = conn.execute(text("SELECT voter_id, full_name FROM voters"))
            voters = result.fetchall()

            print("\nVoters to be deleted:")
            print("-" * 60)
            for voter in voters:
                print(f"  • {voter.voter_id} - {voter.full_name}")

            print("\n⚠️  WARNING: This will delete ALL voters and related data!")
            print("   - Auth attempts")
            print("   - Vote submissions")

            response = input("\nAre you sure you want to continue? (yes/no): ")

            if response.lower() != 'yes':
                print("\n❌ Deletion cancelled")
                return

            # Delete related records first (due to foreign keys)
            print("\nDeleting related records...")

            # Delete auth attempts
            result = conn.execute(text("DELETE FROM auth_attempts"))
            conn.commit()
            print(f"  ✓ Deleted auth_attempts")

            # Delete vote submissions
            result = conn.execute(text("DELETE FROM vote_submissions"))
            conn.commit()
            print(f"  ✓ Deleted vote_submissions")

            # Delete voters
            result = conn.execute(text("DELETE FROM voters"))
            conn.commit()
            print(f"  ✓ Deleted all voters")

            print(f"\n✅ Successfully deleted {count} voter(s) and all related data")
            print("\n📝 Next steps:")
            print("   1. Go to http://localhost:3000/login")
            print("   2. Login as admin")
            print("   3. Go to Voter Registration")
            print("   4. Re-register all voters with fresh face/fingerprint images")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    delete_all_voters()
