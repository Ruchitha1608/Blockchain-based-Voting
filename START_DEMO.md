# Quick Start - Demo in 5 Minutes

Follow these exact steps to start your demo:

---

## **Step 1: Verify All Services (30 seconds)**

```bash
# Check if backend is running
curl http://localhost:8000/docs
# Should show FastAPI Swagger UI

# Check if frontend is running
curl http://localhost:3000
# Should show React app

# Check if Ganache is running
curl http://localhost:8545 -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
# Should return block number
```

**All working?** → Continue to Step 2
**Something not working?** → See "Start Services" below

---

## **Step 2: Login as Admin (10 seconds)**

1. Open browser: **http://localhost:3000/admin/login**
2. Login:
   - Username: `superadmin`
   - Password: `Admin@123456`

---

## **Step 3: Check Existing Data (20 seconds)**

Open terminal:
```bash
cd /Users/work/Maj/backend
python check_voters.py
```

**If you see TEST001, TEST002:**
- These have BROKEN face embeddings (old code)
- **Skip them** - Register new voters (DEMO001, DEMO002)

**If you see DEMO001, DEMO002:**
- Check if they have correct embeddings:
  ```bash
  python diagnose_embedding.py DEMO001
  ```
- If shows "✅ CORRECT SIZE" → **You're ready to vote!** Go to Step 5

**If no voters:**
- Continue to Step 4

---

## **Step 4: Register Test Voter (2 minutes)**

1. Go to: **http://localhost:3000/admin/voters**
2. Click **"Register New Voter"**
3. Fill in:
   ```
   Voter ID: DEMO001
   Full Name: John Doe
   Date of Birth: 1995-01-15
   Constituency: HYD (or whichever exists)
   ```
4. **Capture Face:**
   - Allow webcam
   - Position your face (well-lit, centered)
   - Click "Take Photo"
5. **Skip fingerprint** (or upload if you have scanner)
6. Click **"Register Voter"**

**Expected:** ✅ "Voter registered successfully"

**Verify it worked:**
```bash
python diagnose_embedding.py DEMO001
```
**Should show:** ✅ CORRECT SIZE! (16384 bytes)

---

## **Step 5: Start Election (1 minute)**

1. Go to Admin Dashboard
2. Find your election
3. If status is "draft":
   - Click **"Deploy to Blockchain"** (wait 30 sec)
   - Click **"Start Election"**
4. Status should be **"active"** ✅

---

## **Step 6: Test Voting (1 minute)**

1. Open **NEW TAB**: **http://localhost:3000**
2. Enter Voter ID: `DEMO001`
3. Click **"Verify Identity"**
4. **Authenticate with face:**
   - Use SAME PERSON who registered
   - Same lighting conditions
   - Click "Authenticate"

**Expected:** ✅ "Face authentication successful!"

5. Select a candidate
6. Click **"Cast Vote"**

**Expected:** ✅ "Vote cast successfully!"

---

## **🎉 Demo Complete!**

You've just demonstrated:
- ✅ Admin election management
- ✅ Voter registration with face biometrics
- ✅ Face recognition authentication
- ✅ Blockchain vote recording
- ✅ Double voting prevention

---

## **If Services Not Running:**

### Start Backend:
```bash
cd /Users/work/Maj/backend
pkill -f uvicorn  # Kill old processes
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend:
```bash
cd /Users/work/Maj/frontend
npm start
```

### Start Ganache:
```bash
ganache-cli --port 8545 --networkId 1337
# OR open Ganache GUI app
```

---

## **Quick Troubleshooting:**

### "Face authentication failed" with similarity 0.0:
```bash
python diagnose_embedding.py DEMO001
```
- If shows wrong size → Delete and re-register
- If correct size → Use SAME person for auth

### "No active election available":
- Go to Admin Dashboard
- Click "Start Election"

### "Voter not found":
- Check voter ID is EXACT match (case-sensitive)
- Run `python check_voters.py` to see all voters

---

## **Full Demo Guide:**

For complete step-by-step with screenshots and troubleshooting, see:
**[DEMO_GUIDE.md](DEMO_GUIDE.md)**

For technical details and requirements audit, see:
**[REQUIREMENTS_AUDIT.md](REQUIREMENTS_AUDIT.md)**
