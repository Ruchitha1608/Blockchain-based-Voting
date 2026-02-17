# Environment Variables Guide

Complete guide to all environment variables in the Blockchain Voting System.

## 📋 Quick Start

### Option 1: Auto-Generate (Recommended)

```bash
cd /Users/work/Maj
python3 generate_env.py
```

This creates `backend/.env` with cryptographically secure values.

### Option 2: Manual Setup

```bash
cd /Users/work/Maj/backend
cp .env.example .env
nano .env  # Edit the values
```

---

## 🔐 Environment Variables Explained

### 1. Database Configuration

#### `DATABASE_URL`
**Purpose:** PostgreSQL connection string
**Format:** `postgresql://user:password@host:port/database`

**Options:**
```bash
# Local PostgreSQL (no Docker)
DATABASE_URL=postgresql://voting_user:voting_pass@localhost:5432/voting_db

# Docker PostgreSQL
DATABASE_URL=postgresql://voting_user:voting_pass@postgres:5432/voting_db
```

**Requirements:**
- Must match PostgreSQL credentials
- Database must exist before running
- Use `localhost` for local testing
- Use `postgres` (service name) for Docker

---

### 2. Blockchain Configuration

#### `GANACHE_URL`
**Purpose:** Ethereum node connection
**Default:** `http://localhost:8545` (local) or `http://ganache:8545` (Docker)

**Options:**
```bash
# Local Ganache
GANACHE_URL=http://localhost:8545

# Docker Ganache
GANACHE_URL=http://ganache:8545

# Remote Ethereum node
GANACHE_URL=https://mainnet.infura.io/v3/YOUR_KEY
```

#### `GANACHE_NETWORK_ID`
**Purpose:** Network identifier
**Default:** `1337` (Ganache default)

**Common Values:**
- `1337` - Local Ganache
- `1` - Ethereum mainnet
- `5` - Goerli testnet
- `11155111` - Sepolia testnet

---

### 3. JWT Configuration

#### `JWT_SECRET` 🔐 CRITICAL
**Purpose:** Signs JWT access tokens
**Security:** MUST be at least 256 bits (32 characters)
**Generate:** Use `generate_env.py` or:

```python
import secrets
jwt_secret = secrets.token_urlsafe(64)
print(jwt_secret)
```

**Requirements:**
- Minimum 32 characters
- Use cryptographically secure random
- NEVER share or commit
- Change in production

#### `JWT_ALGORITHM`
**Purpose:** JWT signing algorithm
**Default:** `HS256` (HMAC with SHA-256)
**Options:** `HS256`, `HS384`, `HS512`, `RS256`

#### `ACCESS_TOKEN_EXPIRE_MINUTES`
**Purpose:** How long access tokens are valid
**Default:** `30` minutes
**Range:** `5-60` minutes

**Recommendations:**
- Development: `30` minutes
- Production: `15` minutes
- High security: `5` minutes

#### `REFRESH_TOKEN_EXPIRE_DAYS`
**Purpose:** How long refresh tokens are valid
**Default:** `7` days
**Range:** `1-30` days

**Recommendations:**
- Development: `7` days
- Production: `7` days
- High security: `1` day

---

### 4. Voting Session Configuration

#### `VOTING_SESSION_SECRET` 🔐 CRITICAL
**Purpose:** Signs short-lived voting session tokens
**Security:** Separate from JWT_SECRET for enhanced security

**Generate:**
```python
import secrets
session_secret = secrets.token_urlsafe(64)
print(session_secret)
```

**Why separate?**
- Voting sessions are one-time use
- Compromised session token doesn't expose admin system
- Can be rotated independently

---

### 5. Biometric Configuration

#### `BIOMETRIC_SALT_PEPPER` 🔐 CRITICAL
**Purpose:** Additional secret for biometric hashing
**Security:** Used in SHA-256 hash computation

**Generate:**
```python
import secrets
pepper = secrets.token_urlsafe(32)
print(pepper)
```

**Security Notes:**
- Combined with per-voter salt
- Adds extra layer to rainbow table attacks
- Change ONLY during initial setup (can't change after voters registered)

#### `BIOMETRIC_ENCRYPTION_KEY` 🔐 CRITICAL
**Purpose:** AES-256-GCM encryption key for biometric data
**Requirements:** **EXACTLY 32 bytes**

**Generate:**
```python
import secrets
import base64
key_bytes = secrets.token_bytes(32)
key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')[:32]
# Ensure exactly 32 bytes
while len(key.encode('utf-8')) != 32:
    key_bytes = secrets.token_bytes(32)
    key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')[:32]
print(key)
```

**⚠️ IMPORTANT:**
- Must be EXACTLY 32 bytes (256 bits)
- Cannot change after voters registered
- Losing this key = losing biometric data
- Backup securely!

#### `FACE_MODEL`
**Purpose:** Face recognition model
**Default:** `ArcFace`
**Options:** `ArcFace`, `VGG-Face`, `Facenet`, `OpenFace`, `DeepFace`

**Recommendations:**
- `ArcFace` - Best accuracy (recommended)
- `Facenet` - Faster, good accuracy
- `VGG-Face` - Balanced

#### `FACE_THRESHOLD`
**Purpose:** Minimum similarity for face match
**Default:** `0.68`
**Range:** `0.0` to `1.0` (0% to 100% similarity)

**Guidelines:**
- `0.60` - Loose (faster, more false positives)
- `0.68` - Balanced (recommended)
- `0.75` - Strict (fewer false positives, may reject valid users)

**Tuning:**
```python
# Test with your images
from app.services.biometric.face import FaceService
service = FaceService()
# Try different thresholds: 0.60, 0.65, 0.68, 0.70, 0.75
```

#### `FINGERPRINT_SDK`
**Purpose:** Fingerprint processing library
**Default:** `opencv`
**Options:** `opencv`, `neurotechnology`, `innovatrics`

**Note:** Currently only OpenCV is fully implemented

#### `FINGERPRINT_THRESHOLD`
**Purpose:** Minimum similarity for fingerprint match
**Default:** `0.75`
**Range:** `0.0` to `1.0`

**Guidelines:**
- `0.70` - Loose
- `0.75` - Balanced (recommended)
- `0.80` - Strict

---

### 6. Blockchain Pepper

#### `BLOCKCHAIN_PEPPER` 🔐 CRITICAL
**Purpose:** Additional secret for blockchain voter ID generation
**Algorithm:** `keccak256(voter_id + BLOCKCHAIN_PEPPER)`

**Generate:**
```python
import secrets
blockchain_pepper = secrets.token_urlsafe(32)
print(blockchain_pepper)
```

**Security:**
- Ensures blockchain voter IDs can't be reversed
- Without pepper, attacker can't link blockchain IDs to voters
- Change ONLY during initial setup

---

### 7. Security Configuration

#### `MAX_AUTH_ATTEMPTS`
**Purpose:** Failed authentication attempts before lockout
**Default:** `3`
**Range:** `1-10`

**Recommendations:**
- Development: `5`
- Production: `3`
- High security: `2`

#### `SESSION_TIMEOUT_SECONDS`
**Purpose:** Polling booth idle timeout
**Default:** `120` seconds (2 minutes)
**Range:** `30-600` seconds

**Recommendations:**
- `120` - Balanced
- `60` - High traffic polling stations
- `180` - Elderly/disabled friendly

#### `LOCKOUT_DURATION_MINUTES`
**Purpose:** How long voter is locked after max failed attempts
**Default:** `30` minutes
**Range:** `5-1440` minutes (5 min to 24 hours)

**Recommendations:**
- Development: `5` minutes
- Production: `30` minutes
- High security: `60` minutes

---

### 8. Redis Configuration

#### `REDIS_URL`
**Purpose:** Redis connection for session management
**Format:** `redis://host:port/db`

**Options:**
```bash
# Local Redis
REDIS_URL=redis://localhost:6379/0

# Docker Redis
REDIS_URL=redis://redis:6379/0

# Redis with password
REDIS_URL=redis://:password@localhost:6379/0

# Redis Cluster
REDIS_URL=redis://node1:6379,node2:6379,node3:6379/0
```

---

### 9. Logging Configuration

#### `LOG_LEVEL`
**Purpose:** Minimum log level
**Default:** `INFO`
**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**When to use:**
- `DEBUG` - Development, troubleshooting
- `INFO` - Production (recommended)
- `WARNING` - Reduce log volume
- `ERROR` - Only errors and critical issues

#### `LOG_FORMAT`
**Purpose:** Log output format
**Default:** `json`
**Options:** `json`, `text`

**When to use:**
- `json` - Production, log aggregation (recommended)
- `text` - Development, human-readable

---

## 🔒 Security Best Practices

### 1. Generate Secure Values

```bash
# Auto-generate everything
python3 generate_env.py
```

### 2. File Permissions

```bash
# Protect .env file
chmod 600 backend/.env

# Verify
ls -la backend/.env
# Should show: -rw------- (only owner can read/write)
```

### 3. Git Protection

```bash
# Ensure .env is in .gitignore
echo "backend/.env" >> .gitignore
echo ".env" >> .gitignore

# Verify not tracked
git status backend/.env
# Should show: "not tracked"
```

### 4. Separate Environments

```bash
# Different .env for each environment
backend/.env.development
backend/.env.staging
backend/.env.production

# Load based on environment
cp backend/.env.production backend/.env
```

### 5. Secrets Management (Production)

Use dedicated secrets management:
- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

---

## ✅ Validation

### Check Your .env File

```bash
cd /Users/work/Maj/backend

# Test loading
python3 << 'EOF'
from app.config import settings

print("✅ Configuration loaded successfully!")
print(f"   App: {settings.APP_NAME}")
print(f"   DB: {settings.DATABASE_URL[:30]}...")
print(f"   Blockchain: {settings.GANACHE_URL}")
print(f"   JWT Secret length: {len(settings.JWT_SECRET)} chars")
print(f"   Encryption key length: {len(settings.BIOMETRIC_ENCRYPTION_KEY)} bytes")

# Verify encryption key is exactly 32 bytes
assert len(settings.BIOMETRIC_ENCRYPTION_KEY.encode('utf-8')) == 32, "Encryption key must be 32 bytes"
print("   ✓ Encryption key is valid")
EOF
```

---

## 🚨 Common Issues

### Issue: "Encryption key must be exactly 32 bytes"

**Solution:**
```bash
python3 << 'EOF'
import secrets
import base64
key_bytes = secrets.token_bytes(32)
key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')[:32]
while len(key.encode('utf-8')) != 32:
    key_bytes = secrets.token_bytes(32)
    key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')[:32]
print(f"BIOMETRIC_ENCRYPTION_KEY={key}")
EOF
```

### Issue: "JWT secret too short"

**Solution:**
```bash
python3 << 'EOF'
import secrets
print(f"JWT_SECRET={secrets.token_urlsafe(64)}")
EOF
```

### Issue: Database connection refused

**Solutions:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres  # For Docker
pg_isready -U voting_user  # For local

# Update DATABASE_URL
# Docker: postgres:5432
# Local: localhost:5432
```

---

## 📝 Quick Reference

### Required Secrets (Auto-generate these)

| Variable | Length | Critical |
|----------|--------|----------|
| JWT_SECRET | 64+ chars | ⚠️ YES |
| VOTING_SESSION_SECRET | 64+ chars | ⚠️ YES |
| BIOMETRIC_SALT_PEPPER | 32+ chars | ⚠️ YES |
| BIOMETRIC_ENCRYPTION_KEY | 32 bytes | ⚠️ YES |
| BLOCKCHAIN_PEPPER | 32+ chars | ⚠️ YES |

### Configurable Values (Tune as needed)

| Variable | Default | Range |
|----------|---------|-------|
| FACE_THRESHOLD | 0.68 | 0.60-0.80 |
| FINGERPRINT_THRESHOLD | 0.75 | 0.70-0.85 |
| MAX_AUTH_ATTEMPTS | 3 | 1-10 |
| SESSION_TIMEOUT_SECONDS | 120 | 30-600 |

---

## 🎯 Ready to Test?

1. Generate secure .env:
   ```bash
   python3 generate_env.py
   ```

2. Verify it works:
   ```bash
   cd backend
   python3 -c "from app.config import settings; print('✅ Config OK')"
   ```

3. Start testing modules!

---

**Security Reminder:** 🔐
- Never commit .env
- Use different secrets per environment
- Rotate secrets regularly (every 90 days)
- Keep backups secure
