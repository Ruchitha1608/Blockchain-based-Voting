#!/usr/bin/env python3
"""
Generate secure .env file for development
"""
import secrets
import base64

print("Generating secure environment file...")
print()

# Generate secure random values
jwt_secret = secrets.token_urlsafe(64)
voting_session_secret = secrets.token_urlsafe(64)
biometric_pepper = secrets.token_urlsafe(32)
blockchain_pepper = secrets.token_urlsafe(32)

# Generate exactly 32-byte key for AES-256
encryption_key_bytes = secrets.token_bytes(32)
encryption_key = base64.urlsafe_b64encode(encryption_key_bytes).decode('utf-8')[:32]

# Make sure it's exactly 32 bytes
while len(encryption_key.encode('utf-8')) != 32:
    encryption_key_bytes = secrets.token_bytes(32)
    encryption_key = base64.urlsafe_b64encode(encryption_key_bytes).decode('utf-8')[:32]

env_content = f"""# Database Configuration
DATABASE_URL=postgresql://voting_user:voting_pass@localhost:5432/voting_db

# Blockchain Configuration
GANACHE_URL=http://localhost:8545
GANACHE_NETWORK_ID=1337

# JWT Configuration
JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Voting Session Configuration
VOTING_SESSION_SECRET={voting_session_secret}

# Biometric Configuration
BIOMETRIC_SALT_PEPPER={biometric_pepper}
BIOMETRIC_ENCRYPTION_KEY={encryption_key}
FACE_MODEL=ArcFace
FACE_THRESHOLD=0.68
FINGERPRINT_SDK=opencv
FINGERPRINT_THRESHOLD=0.75

# Blockchain Pepper (for voter ID hashing)
BLOCKCHAIN_PEPPER={blockchain_pepper}

# Security Configuration
MAX_AUTH_ATTEMPTS=3
SESSION_TIMEOUT_SECONDS=120
LOCKOUT_DURATION_MINUTES=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
"""

# Write to .env file
with open('backend/.env', 'w') as f:
    f.write(env_content)

print("✅ Generated backend/.env with secure values!")
print()
print("⚠️  IMPORTANT:")
print("   - These are cryptographically secure random values")
print("   - NEVER commit .env to version control")
print("   - Change these values in production")
print("   - Keep .env file secure (chmod 600)")
print()
print("📁 File location: backend/.env")
print()

# Print verification
print("Verification:")
print(f"  JWT Secret length: {len(jwt_secret)} characters")
print(f"  Encryption key length: {len(encryption_key)} characters ({len(encryption_key.encode('utf-8'))} bytes)")
print(f"  All secrets are cryptographically secure")
print()
print("🚀 You can now start the backend!")
