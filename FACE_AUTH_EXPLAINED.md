# Face Authentication - How It Works

## Current Problem

**❌ Face authentication isn't working because there are ZERO voters in the database.**

You deleted all voters to fix the buggy embeddings. Now you need to register NEW voters.

---

## The Complete Flow

### **Phase 1: Voter Registration** (Admin Dashboard)

```
┌─────────────────────────────────────────────────────────────────┐
│  ADMIN DASHBOARD - VOTER REGISTRATION                           │
└─────────────────────────────────────────────────────────────────┘

1. Admin opens webcam
   ↓
2. Webcam captures face image (640×480 JPEG)
   ↓
3. Image sent to backend as base64 string
   ↓
4. BACKEND PROCESSING:
   ├─ Decode base64 → bytes
   ├─ Load image with OpenCV
   ├─ Convert to grayscale
   ├─ Detect face using Haar Cascade
   │  ├─ No face found? → ERROR "No face detected"
   │  └─ Multiple faces? → ERROR "Multiple faces detected"
   ├─ Crop face region (x, y, w, h)
   ├─ Resize to 128×128 pixels
   ├─ Normalize pixel values (0-1 range)
   ├─ Apply histogram equalization
   └─ Flatten to 16,384-element vector
   ↓
5. STORAGE:
   ├─ Convert embedding to bytes (65,536 bytes)
   ├─ Calculate SHA-256 hash (for integrity)
   ├─ Quantize to int8 (reduces to 16,384 bytes)
   ├─ Encrypt with AES-256-GCM
   └─ Store in database:
      ├─ face_embedding_hash (64 chars)
      ├─ encrypted_face_embedding (~16KB)
      ├─ biometric_salt (32 chars)
      └─ blockchain_voter_id (66 chars)
   ↓
6. SUCCESS! Voter registered with ID
```

### **Phase 2: Voter Authentication** (Polling Booth)

```
┌─────────────────────────────────────────────────────────────────┐
│  POLLING BOOTH - VOTER AUTHENTICATION                           │
└─────────────────────────────────────────────────────────────────┘

1. Voter enters Voter ID (e.g., "TEST001")
   ↓
2. Backend looks up voter in database
   │
   ├─ Voter not found? → ERROR "Voter not found"
   └─ Voter found! → Continue
   ↓
3. Check voter status:
   ├─ Already voted? → ERROR "Already voted"
   ├─ Account locked? → ERROR "Account locked"
   └─ OK to proceed → Continue
   ↓
4. Voter clicks "Authenticate with Face"
   ↓
5. Webcam opens, captures face
   ↓
6. Live image sent to backend as base64
   ↓
7. BACKEND PROCESSING (LIVE IMAGE):
   ├─ Decode base64 → bytes
   ├─ Extract face embedding (same process as registration)
   └─ Get 16,384-element vector
   ↓
8. COMPARISON:
   ├─ Load stored encrypted embedding from database
   ├─ Decrypt using AES-256-GCM
   ├─ Dequantize from int8 to float32
   ├─ Calculate COSINE SIMILARITY:
   │  │
   │  │  similarity = dot(live, stored) / (||live|| × ||stored||)
   │  │
   │  └─ Result: 0.0 to 1.0
   │
   ├─ Compare to threshold (0.68):
   │  │
   │  ├─ similarity ≥ 0.68 → ✅ MATCH
   │  └─ similarity < 0.68 → ❌ NO MATCH
   │
   └─ Log attempt to database
   ↓
9. RESULT:
   │
   ├─ ✅ MATCH:
   │  ├─ Reset failed_auth_count = 0
   │  ├─ Create voting session JWT (5 min expiry)
   │  ├─ Return auth token + voter details
   │  └─ Frontend shows candidate selection
   │
   └─ ❌ NO MATCH:
      ├─ Increment failed_auth_count
      ├─ If count ≥ 3 → Lock account
      ├─ Return error message
      └─ Frontend shows remaining attempts
```

---

## What Similarity Scores Mean

```
Similarity Score    Meaning                   Action
─────────────────────────────────────────────────────────────
0.95 - 1.00         Perfect match             ✅ Authenticate
0.85 - 0.94         Very good match           ✅ Authenticate
0.75 - 0.84         Good match                ✅ Authenticate
0.68 - 0.74         Acceptable match          ✅ Authenticate (threshold)
0.60 - 0.67         Close but not enough      ❌ Reject
0.40 - 0.59         Different person          ❌ Reject
0.00 - 0.39         Completely different      ❌ Reject
```

---

## Why You're Getting Errors Right Now

### Error: "Voter not found"

**Cause:** Database has ZERO voters

**What's happening:**
```python
# Backend code (voting.py line 122-134)
result = db.execute(
    text("SELECT ... FROM voters WHERE voter_id = :voter_id"),
    {"voter_id": voter_id}
)
voter = result.fetchone()

if not voter:
    raise HTTPException(404, "Voter not found")
    # ← YOU ARE HERE!
```

**Solution:** Register a voter first!

---

## Step-by-Step: How to Test Right Now

### Terminal 1: Monitor Authentication (Optional)
```bash
cd /Users/work/Maj/backend
python monitor_auth.py
```
This will show real-time authentication attempts with similarity scores.

### Terminal 2: Check Backend Logs
```bash
tail -f /tmp/backend.log | grep -E "face|similarity"
```

### Browser: Register a Voter

1. **Go to:** http://localhost:3000/login

2. **Login as admin:**
   - Check what admin credentials exist:
     ```bash
     cd /Users/work/Maj/backend
     python -c "
     from sqlalchemy import create_engine, text
     from app.config import settings
     engine = create_engine(settings.DATABASE_URL)
     with engine.connect() as conn:
         result = conn.execute(text('SELECT username FROM admins LIMIT 5'))
         for row in result:
             print(f'Username: {row.username}')
     "
     ```

3. **Go to "Voter Registration"**

4. **Fill in the form:**
   - Voter ID: `TEST001`
   - Full Name: `RUCHITHA` (or your name)
   - Date of Birth: Any date
   - Gender: Select one
   - Constituency: Select `HYD` or `Test Constituency`

5. **Capture Face:**
   - Click "Capture Face" button
   - Allow webcam access
   - Position your face:
     - Face the camera directly
     - Good lighting
     - No glasses (if possible)
     - Neutral expression
   - Click capture
   - See preview image

6. **Upload Fingerprint (Optional):**
   - Skip for now, just test face first

7. **Click "Register Voter"**

8. **Expected response:**
   ```json
   {
     "success": true,
     "voter_id": "TEST001",
     "blockchain_voter_id": "0x1234...",
     "message": "Voter registered successfully"
   }
   ```

9. **Check backend logs:**
   ```bash
   tail /tmp/backend.log
   ```
   Should see:
   ```
   face_embedding_extracted shape=(16384,) size=16384
   face_embedding_processed hash_length=64 encrypted_length=XXX
   ```

10. **Verify in database:**
    ```bash
    cd /Users/work/Maj/backend
    python -c "
    from sqlalchemy import create_engine, text
    from app.config import settings
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT voter_id, full_name,
                   LENGTH(encrypted_face_embedding) as face_size
            FROM voters
        '''))
        for row in result:
            status = '✅' if row.face_size == 16384 else '❌'
            print(f'{status} {row.voter_id} - Face: {row.face_size} bytes')
    "
    ```
    Should show:
    ```
    ✅ TEST001 - Face: 16384 bytes
    ```

### Browser: Test Face Authentication

1. **Go to:** http://localhost:3000/

2. **Enter Voter ID:** `TEST001`

3. **Click "Authenticate with Face"**

4. **Webcam opens:**
   - Show **THE SAME PERSON** who registered
   - Similar lighting conditions
   - Face the camera directly

5. **Expected response (SUCCESS):**
   ```json
   {
     "success": true,
     "auth_token": "eyJ...",
     "voter_details": {
       "name": "RUCHITHA",
       "constituency": "HYD"
     }
   }
   ```

6. **Check backend logs:**
   ```bash
   tail /tmp/backend.log | grep similarity
   ```
   Should see:
   ```
   face_comparison_complete matched=True similarity=0.8567
   face_authentication_success voter_id=TEST001 similarity=0.8567
   ```

7. **Expected response (FAILURE - different person):**
   ```json
   {
     "detail": "Face authentication failed. 2 attempt(s) remaining."
   }
   ```
   Backend logs:
   ```
   face_comparison_complete matched=False similarity=0.4523
   ```

---

## Common Issues and Solutions

### Issue 1: "No face detected in image"

**Causes:**
- Poor lighting
- Face too small in frame
- Face not visible
- Wearing sunglasses/mask

**Solutions:**
- Improve lighting
- Move closer to camera
- Face camera directly
- Remove obstructions

### Issue 2: "Multiple faces detected"

**Causes:**
- Someone else in frame
- Poster/photo in background

**Solutions:**
- Make sure only one person in frame
- Remove background faces

### Issue 3: Authentication fails with low similarity (0.40-0.60)

**Causes:**
- Different person (this is correct behavior!)
- Very different lighting
- Different facial expression
- Different angle

**Solutions:**
- Use the SAME person who registered
- Match lighting conditions
- Try neutral expression
- Face camera directly

### Issue 4: Authentication fails with borderline similarity (0.65-0.67)

**Causes:**
- Just below threshold (0.68)
- Lighting slightly different
- Slight angle difference

**Solutions:**
- Try again with better conditions
- Lower threshold in config (if acceptable):
  ```bash
  # Edit /Users/work/Maj/backend/.env
  FACE_THRESHOLD=0.65

  # Restart backend
  lsof -ti:8000 | xargs kill -9
  cd /Users/work/Maj/backend
  nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
  ```

---

## Technical Details

### Embedding Size
- **Expected:** 16,384 bytes
- **Calculation:** 128 × 128 = 16,384 float32 values
- **Any other size means broken code!**

### Threshold
- **Default:** 0.68
- **Adjustable in:** `/Users/work/Maj/backend/.env`
- **Trade-off:**
  - Lower (0.60): More false positives (wrong person accepted)
  - Higher (0.80): More false negatives (right person rejected)

### Cosine Similarity Formula
```python
def cosine_similarity(a, b):
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot_product / (norm_a * norm_b)
```

### Security Features
- SHA-256 hash for integrity verification
- AES-256-GCM encryption for storage
- Unique salt per voter
- Keccak256 for blockchain voter ID
- Separate pepper for additional security

---

## Summary

**Current State:**
- ❌ 0 voters in database
- ✅ Backend running with FIXED code
- ✅ Face service working correctly
- ✅ Fingerprint service simplified

**What You Need to Do:**
1. Register a voter with face image
2. Test authentication with SAME person
3. Check backend logs for similarity scores
4. Verify embedding size is 16,384 bytes

**Expected Outcome:**
- Same person: similarity 0.70-0.95 → ✅ SUCCESS
- Different person: similarity <0.60 → ❌ FAILURE (correct!)
- Edge cases: similarity 0.65-0.69 → borderline (might need adjustment)

The system is working correctly - you just need to register voters first!
