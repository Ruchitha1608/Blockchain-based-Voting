#!/usr/bin/env python3
"""
Real-time monitoring of face/fingerprint authentication attempts
Run this in a separate terminal while testing authentication
"""
import time
from sqlalchemy import create_engine, text
from app.config import settings
from datetime import datetime

def monitor_auth():
    """Monitor authentication attempts in real-time"""
    engine = create_engine(settings.DATABASE_URL)

    print("=" * 80)
    print("FACE AUTHENTICATION MONITOR")
    print("=" * 80)
    print("\n👁️  Watching for authentication attempts...")
    print("   (Press Ctrl+C to stop)\n")

    last_count = 0

    try:
        while True:
            with engine.connect() as conn:
                # Check total auth attempts
                result = conn.execute(text('SELECT COUNT(*) as count FROM auth_attempts'))
                current_count = result.fetchone().count

                # If new attempts detected, show details
                if current_count > last_count:
                    result = conn.execute(text('''
                        SELECT
                            aa.attempted_at,
                            v.voter_id,
                            v.full_name,
                            aa.auth_method,
                            aa.outcome,
                            aa.similarity_score,
                            aa.failure_reason,
                            aa.ip_address
                        FROM auth_attempts aa
                        JOIN voters v ON aa.voter_id = v.id
                        ORDER BY aa.attempted_at DESC
                        LIMIT 1
                    '''))

                    attempt = result.fetchone()

                    if attempt:
                        print("\n" + "=" * 80)
                        print(f"🔔 NEW AUTHENTICATION ATTEMPT")
                        print("=" * 80)
                        print(f"Time:       {attempt.attempted_at}")
                        print(f"Voter:      {attempt.voter_id} ({attempt.full_name})")
                        print(f"Method:     {attempt.auth_method.upper()}")
                        print(f"IP Address: {attempt.ip_address}")
                        print("-" * 80)

                        if attempt.outcome == 'success':
                            print(f"✅ RESULT:    SUCCESS")
                            print(f"📊 Similarity: {attempt.similarity_score:.4f}")
                            if attempt.similarity_score:
                                if attempt.similarity_score >= 0.90:
                                    print(f"   💯 Excellent match!")
                                elif attempt.similarity_score >= 0.75:
                                    print(f"   👍 Good match")
                                elif attempt.similarity_score >= 0.68:
                                    print(f"   ✓ Acceptable match")
                        else:
                            print(f"❌ RESULT:    {attempt.outcome.upper()}")
                            if attempt.similarity_score:
                                print(f"📊 Similarity: {attempt.similarity_score:.4f}")
                                print(f"   ⚠️  Below threshold (0.68)")
                            if attempt.failure_reason:
                                print(f"💬 Reason:    {attempt.failure_reason}")

                        print("=" * 80)

                    last_count = current_count

                # Show current status every 5 seconds
                if int(time.time()) % 5 == 0:
                    result = conn.execute(text('SELECT COUNT(*) as count FROM voters'))
                    voter_count = result.fetchone().count

                    result = conn.execute(text('''
                        SELECT COUNT(*) as success
                        FROM auth_attempts
                        WHERE outcome = 'success'
                    '''))
                    success_count = result.fetchone().success

                    result = conn.execute(text('''
                        SELECT COUNT(*) as failed
                        FROM auth_attempts
                        WHERE outcome = 'failure'
                    '''))
                    failed_count = result.fetchone().failed

                    print(f"\r📊 Status: {voter_count} voters | {success_count} success | {failed_count} failed | {current_count} total attempts", end='', flush=True)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")
        print("\n📊 Final Statistics:")

        with engine.connect() as conn:
            result = conn.execute(text('''
                SELECT
                    outcome,
                    auth_method,
                    COUNT(*) as count,
                    AVG(similarity_score) as avg_similarity
                FROM auth_attempts
                GROUP BY outcome, auth_method
                ORDER BY outcome, auth_method
            '''))

            stats = result.fetchall()

            if stats:
                print("\n" + "=" * 60)
                for stat in stats:
                    avg_sim = f"{stat.avg_similarity:.4f}" if stat.avg_similarity else "N/A"
                    print(f"{stat.auth_method.upper():15} | {stat.outcome.upper():10} | Count: {stat.count:3} | Avg Similarity: {avg_sim}")
                print("=" * 60)
            else:
                print("   No authentication attempts recorded")

if __name__ == "__main__":
    monitor_auth()
