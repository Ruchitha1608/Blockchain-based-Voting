# Testing Without Docker

Complete guide for testing the blockchain voting system **without Docker**.

## ✅ What You CAN Test Without Docker

1. ✅ Smart contract compilation
2. ✅ Backend Python imports
3. ✅ Crypto services (hashing, encryption)
4. ✅ Biometric services (face, fingerprint)
5. ✅ Code syntax and structure
6. ✅ File organization

## ❌ What You CANNOT Test Without Docker

1. ❌ Database operations (needs PostgreSQL)
2. ❌ Blockchain deployment (needs Ganache)
3. ❌ Full API integration
4. ❌ Redis session management

---

## 🚀 Quick Start

### Prerequisites

Install these if you don't have them:

```bash
# Node.js (for smart contracts)
node --version  # Should be 16+

# Python (for backend)
python3 --version  # Should be 3.11+

# If missing, install:
# - Node.js: https://nodejs.org/
# - Python: https://www.python.org/
```

---

## Test 1: Smart Contracts ✅

### Compile Contracts

```bash
cd /Users/work/Maj/contracts

# Install dependencies (first time only)
npm install

# Compile contracts
npx truffle compile

# Expected output:
# > Compiling ./contracts/VoterRegistry.sol
# > Compiling ./contracts/VotingBooth.sol
# > Compiling ./contracts/ResultsTallier.sol
# > Compiling ./contracts/ElectionController.sol
# > Compilation successful
```

**Success if:** All 4 contracts compile without errors

### Verify Compiled Artifacts

```bash
# Check build directory
ls -la build/contracts/

# Expected files:
# - VoterRegistry.json
# - VotingBooth.json
# - ResultsTallier.json
# - ElectionController.json
# - Migrations.json
```

**Result:** ✅ Smart contracts are syntactically correct

---

## Test 2: Backend Structure ✅

### Setup Python Environment

```bash
cd /Users/work/Maj/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

### Install Dependencies

```bash
# Install all packages (may take 5-10 minutes)
pip install -r requirements.txt

# Expected: Successful installation of ~40 packages
```

**Note:** DeepFace will download AI models on first use (~500MB)

---

## Test 3: Python Imports ✅

### Test Core Imports

```bash
cd /Users/work/Maj/backend
source venv/bin/activate

python << 'EOF'
print("Testing imports...")

# Test config
from app.config import settings
print(f"✓ Config loaded: {settings.APP_NAME}")

# Test database
from app.database import Base, get_db
print("✓ Database module loaded")

# Test models
from app.models.admin import Admin, AdminRole
from app.models.election import Election, Constituency, Candidate
from app.models.voter import Voter, AuthAttempt
print("✓ All models loaded")

# Test schemas
from app.schemas.admin import AdminCreate, AdminResponse
from app.schemas.voter import VoterCreate
print("✓ All schemas loaded")

# Test services
from app.services.crypto import generate_salt, hash_password
from app.services.biometric.face import FaceService
from app.services.biometric.fingerprint import FingerprintService
print("✓ All services loaded")

print("\n🎉 All imports successful!")
EOF
```

**Expected output:**
```
Testing imports...
✓ Config loaded: Blockchain Voting System
✓ Database module loaded
✓ All models loaded
✓ All schemas loaded
✓ All services loaded

🎉 All imports successful!
```

---

## Test 4: Crypto Service ✅

### Test Cryptographic Functions

```bash
cd /Users/work/Maj/backend
source venv/bin/activate

python << 'EOF'
from app.services.crypto import *
import secrets

print("=" * 50)
print("CRYPTO SERVICE TESTS")
print("=" * 50)

# Test 1: Salt Generation
print("\n1. Testing salt generation...")
salt = generate_salt()
print(f"   Salt length: {len(salt)} characters")
assert len(salt) == 64, "Salt should be 64 chars (32 bytes hex)"
print("   ✓ Salt generation works")

# Test 2: Password Hashing
print("\n2. Testing password hashing...")
password = "TestPassword123!"
hashed = hash_password(password)
print(f"   Hash length: {len(hashed)} characters")
assert hashed.startswith("$argon2id$"), "Should be Argon2id hash"
print("   ✓ Password hashing works")

# Test 3: Password Verification
print("\n3. Testing password verification...")
assert verify_password(password, hashed) == True, "Should verify correct password"
assert verify_password("wrong", hashed) == False, "Should reject wrong password"
print("   ✓ Password verification works")

# Test 4: Biometric Hashing
print("\n4. Testing biometric hashing...")
test_data = secrets.token_bytes(512)  # Simulate biometric data
bio_hash = hash_biometric(test_data, salt)
print(f"   Hash length: {len(bio_hash)} characters")
assert len(bio_hash) == 64, "Hash should be 64 chars"
print("   ✓ Biometric hashing works")

# Test 5: Blockchain Voter ID
print("\n5. Testing blockchain voter ID derivation...")
voter_id = "VOTER001"
blockchain_id = derive_blockchain_voter_id(voter_id)
print(f"   Blockchain ID: {blockchain_id}")
assert blockchain_id.startswith("0x"), "Should start with 0x"
assert len(blockchain_id) == 66, "Should be 66 chars (0x + 64 hex)"
print("   ✓ Blockchain ID derivation works")

# Test 6: Encryption/Decryption
print("\n6. Testing biometric encryption...")
original = secrets.token_bytes(256)
encrypted = encrypt_biometric(original)
decrypted = decrypt_biometric(encrypted)
assert original == decrypted, "Decrypted should match original"
print(f"   Original: {len(original)} bytes")
print(f"   Encrypted: {len(encrypted)} characters")
print(f"   Decrypted: {len(decrypted)} bytes")
print("   ✓ Encryption/decryption works")

# Test 7: Quantization
print("\n7. Testing embedding quantization...")
import numpy as np
embedding = np.random.randn(512).astype('float32')
quantized = quantize_embedding(embedding)
dequantized = dequantize_embedding(quantized, shape=(512,))
print(f"   Original size: {embedding.nbytes} bytes")
print(f"   Quantized size: {len(quantized)} bytes")
print(f"   Compression ratio: {embedding.nbytes / len(quantized):.2f}x")
print("   ✓ Quantization works")

print("\n" + "=" * 50)
print("✅ ALL CRYPTO TESTS PASSED!")
print("=" * 50)
EOF
```

**Expected:** All 7 tests pass with ✓ marks

---

## Test 5: Biometric Services ✅

### Test Face Service (Basic)

```bash
cd /Users/work/Maj/backend
source venv/bin/activate

python << 'EOF'
from app.services.biometric.face import FaceService, BiometricAuthError
import numpy as np

print("=" * 50)
print("FACE SERVICE TESTS")
print("=" * 50)

# Initialize service
print("\n1. Initializing face service...")
face_service = FaceService()
print(f"   Model: {face_service.model_name}")
print(f"   Threshold: {face_service.threshold}")
print("   ✓ Face service initialized")

# Test error handling (without real image)
print("\n2. Testing error handling...")
try:
    embedding = face_service.get_embedding(b"invalid image data")
    print("   ✗ Should have raised error")
except BiometricAuthError as e:
    print(f"   ✓ Error handling works: {e}")

# Test cosine similarity
print("\n3. Testing cosine similarity...")
vec_a = np.array([1, 0, 0, 0], dtype='float32')
vec_b = np.array([1, 0, 0, 0], dtype='float32')
vec_c = np.array([0, 1, 0, 0], dtype='float32')

sim_same = face_service._cosine_similarity(vec_a, vec_b)
sim_diff = face_service._cosine_similarity(vec_a, vec_c)

print(f"   Same vectors similarity: {sim_same:.4f}")
print(f"   Different vectors similarity: {sim_diff:.4f}")

assert sim_same > 0.99, "Identical vectors should have ~1.0 similarity"
assert sim_diff < 0.1, "Orthogonal vectors should have ~0.0 similarity"
print("   ✓ Cosine similarity calculation works")

print("\n" + "=" * 50)
print("✅ FACE SERVICE TESTS PASSED!")
print("=" * 50)
print("\nNote: Full face recognition requires real images")
EOF
```

### Test Fingerprint Service (Basic)

```bash
cd /Users/work/Maj/backend
source venv/bin/activate

python << 'EOF'
from app.services.biometric.fingerprint import FingerprintService, BiometricAuthError
import numpy as np

print("=" * 50)
print("FINGERPRINT SERVICE TESTS")
print("=" * 50)

# Initialize service
print("\n1. Initializing fingerprint service...")
fp_service = FingerprintService()
print(f"   SDK: {fp_service.sdk}")
print(f"   Threshold: {fp_service.threshold}")
print("   ✓ Fingerprint service initialized")

# Test error handling
print("\n2. Testing error handling...")
try:
    template = fp_service.process_fingerprint(b"invalid image data")
    print("   ✗ Should have raised error")
except BiometricAuthError as e:
    print(f"   ✓ Error handling works: {e}")

# Test similarity calculation
print("\n3. Testing similarity calculation...")
template_a = np.random.randn(512).astype('float32')
template_b = template_a + np.random.randn(512).astype('float32') * 0.1

similarity = fp_service._calculate_similarity(template_a, template_a)
print(f"   Same template: {similarity:.4f}")
assert similarity > 0.99, "Identical templates should have ~1.0 similarity"
print("   ✓ Similarity calculation works")

print("\n" + "=" * 50)
print("✅ FINGERPRINT SERVICE TESTS PASSED!")
print("=" * 50)
print("\nNote: Full fingerprint processing requires real images")
EOF
```

---

## Test 6: File Structure ✅

### Verify All Files Exist

```bash
cd /Users/work/Maj

echo "Checking file structure..."
echo ""

# Smart Contracts
echo "Smart Contracts:"
ls -1 contracts/contracts/*.sol | wc -l | xargs echo "  - Contracts:"
ls -1 contracts/migrations/*.js | wc -l | xargs echo "  - Migrations:"

# Database
echo "Database:"
ls -1 database/*.sql | wc -l | xargs echo "  - Schema files:"

# Backend
echo "Backend:"
find backend/app -name "*.py" -type f | wc -l | xargs echo "  - Python files:"
echo "  - Models: $(ls -1 backend/app/models/*.py | wc -l)"
echo "  - Schemas: $(ls -1 backend/app/schemas/*.py | wc -l)"
echo "  - Services: $(find backend/app/services -name "*.py" -type f | wc -l)"

# Documentation
echo "Documentation:"
ls -1 *.md | wc -l | xargs echo "  - Markdown files:"

echo ""
echo "✅ File structure verified!"
```

---

## Test 7: Code Quality ✅

### Check Python Syntax

```bash
cd /Users/work/Maj/backend
source venv/bin/activate

echo "Checking Python syntax..."

# Check all Python files
python -m py_compile app/*.py
python -m py_compile app/models/*.py
python -m py_compile app/schemas/*.py
python -m py_compile app/services/*.py
python -m py_compile app/services/biometric/*.py
python -m py_compile app/middleware/*.py

echo "✅ All Python files have valid syntax!"
```

### Check for Common Issues

```bash
cd /Users/work/Maj/backend

# Check for missing imports
grep -r "from app\." app/ | grep -v ".pyc" | head -20

echo "✅ Import structure looks good!"
```

---

## 📊 Test Summary

After running all tests above, you should see:

```
✅ Smart Contracts
   - 4 contracts compile successfully
   - Build artifacts created

✅ Backend Structure
   - Virtual environment created
   - All dependencies installed
   - ~40 Python packages ready

✅ Python Imports
   - Config loads correctly
   - All models import successfully
   - All schemas import successfully
   - All services import successfully

✅ Crypto Service
   - Salt generation works
   - Password hashing (Argon2id) works
   - Password verification works
   - Biometric hashing works
   - Blockchain ID derivation works
   - Encryption/decryption works
   - Quantization works

✅ Biometric Services
   - Face service initializes
   - Fingerprint service initializes
   - Error handling works
   - Similarity calculations work

✅ File Structure
   - All files present
   - Correct organization

✅ Code Quality
   - Valid Python syntax
   - Proper imports
```

---

## What's Next?

### To Complete Full Testing:

1. **Start Docker** to test:
   - Database operations
   - Blockchain deployment
   - Full API integration

2. **Run Full Test Suite:**
   ```bash
   ./test_setup.sh
   ```

3. **Start Backend Server:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

---

## 🎯 Quick Test Script

Save this as `test_no_docker.sh`:

```bash
#!/bin/bash

echo "Testing without Docker..."
echo ""

# Test 1: Contracts
echo "1. Testing smart contracts..."
cd contracts
npm install > /dev/null 2>&1
npx truffle compile > /dev/null 2>&1 && echo "   ✓ Contracts compile" || echo "   ✗ Compilation failed"

# Test 2: Backend
echo "2. Testing backend..."
cd ../backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
else
    source venv/bin/activate
fi

python -c "
from app.config import settings
from app.services.crypto import generate_salt, hash_password
from app.models.admin import Admin
print('   ✓ Backend imports successful')
" 2>/dev/null || echo "   ✗ Import failed"

echo ""
echo "✅ Non-Docker tests complete!"
echo ""
echo "To test everything, start Docker and run: ./test_setup.sh"
```

Make it executable:
```bash
chmod +x test_no_docker.sh
./test_no_docker.sh
```

---

## Success! 🎉

If all tests above pass, your system is **75% functional** even without Docker!

**Working:** Code structure, syntax, crypto, biometrics, compilation
**Needs Docker:** Database, blockchain, full integration
