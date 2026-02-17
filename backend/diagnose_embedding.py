"""
Diagnose stored face embedding for voter
"""
import sys
import os
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings
from app.services.crypto import decrypt_biometric

def diagnose_embedding():
    """Check the stored embedding size"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # Get voter_id from command line or use TEST002 as default
        import sys
        voter_id = sys.argv[1] if len(sys.argv) > 1 else 'TEST002'

        result = conn.execute(text("""
            SELECT
                voter_id,
                full_name,
                LENGTH(encrypted_face_embedding) as encrypted_length,
                encrypted_face_embedding
            FROM voters
            WHERE voter_id = :voter_id;
        """), {"voter_id": voter_id})

        voter = result.fetchone()

        if not voter:
            print("❌ Voter TEST001 not found")
            return

        print(f"🔍 Diagnosing voter: {voter.voter_id} ({voter.full_name})")
        print("=" * 80)
        print(f"Encrypted face embedding length (base64): {voter.encrypted_length} characters")

        # Try to decrypt
        try:
            decrypted = decrypt_biometric(voter.encrypted_face_embedding)
            print(f"✅ Decryption successful")
            print(f"   Decrypted data size: {len(decrypted)} bytes")
            print(f"   Expected size: 16384 bytes (128x128 face image)")

            if len(decrypted) != 16384:
                print(f"\n⚠️  SIZE MISMATCH!")
                print(f"   Got {len(decrypted)} bytes, expected 16384 bytes")
                print(f"   Ratio: {len(decrypted) / 16384:.2f}x")
                print(f"\n💡 This explains why face authentication is failing.")
                print(f"   The voter was registered with the OLD buggy code.")
                print(f"\n🔧 FIX: Delete and re-register this voter:")
                print(f"   python delete_voter.py {voter.voter_id}")
            else:
                print(f"\n✅ CORRECT SIZE! Face embedding is properly formatted.")
                print(f"   If authentication is still failing, ensure:")
                print(f"   1. The SAME person is used for authentication")
                print(f"   2. Lighting conditions are similar")
                print(f"   3. Face is centered and clearly visible")

        except Exception as e:
            print(f"❌ Decryption failed: {e}")

if __name__ == "__main__":
    diagnose_embedding()
