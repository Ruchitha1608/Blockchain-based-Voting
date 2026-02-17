# Troubleshooting Checklist

Quick diagnostic checklist for common issues.

---

## 🔍 System Health Check

Run this checklist whenever something isn't working:

### ✅ Step 1: Verify All Services Running

```bash
# Check Ganache (Terminal 1)
ps aux | grep ganache
# Should show: ganache --networkId 1337 --port 8545

# Check Backend (Terminal 2)
ps aux | grep uvicorn
# Should show: uvicorn app.main:app

# Check Frontend (Terminal 3)
ps aux | grep "npm.*start"
# Should show: npm start (in frontend directory)
```

**If any service is NOT running:**
- Ganache: `ganache --networkId 1337 --port 8545`
- Backend: `cd /Users/work/Maj/backend && source .venv/bin/activate && uvicorn app.main:app --reload`
- Frontend: `cd /Users/work/Maj/frontend && npm start`

---

### ✅ Step 2: Verify Network Connectivity

```bash
# Test Ganache
curl -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
# Expected: {"jsonrpc":"2.0","id":1,"result":"1337"}

# Test Backend
curl http://localhost:8000/api/health
# Expected: HTTP 200 OK

# Test Frontend
curl http://localhost:3000
# Expected: HTML content (React app)
```

**If any test fails:**
- Port already in use? Kill process: `lsof -ti:8545 | xargs kill -9`
- Firewall blocking? Check firewall settings
- Wrong URL? Verify ports in .env files

---

### ✅ Step 3: Verify Blockchain State

```bash
# Check network ID
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}' | grep 1337

# Expected: Should contain "1337"
```

**If network ID is NOT 1337:**
```bash
# STOP Ganache (Ctrl+C)
# START with correct network ID
ganache --networkId 1337 --port 8545

# Redeploy contracts
cd /Users/work/Maj/contracts
npx truffle migrate --reset --network development
```

---

### ✅ Step 4: Verify Contracts Deployed

```bash
cd /Users/work/Maj/contracts
cat build/contracts/ElectionController.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
networks = data.get('networks', {})
print('Deployed networks:', list(networks.keys()))
if '1337' in networks:
    print('✅ Contracts deployed to network 1337')
    print('ElectionController:', networks['1337']['address'])
else:
    print('❌ Contracts NOT deployed to network 1337')
"
```

**If NOT deployed to 1337:**
```bash
cd /Users/work/Maj/contracts
npx truffle migrate --reset --network development
```

---

### ✅ Step 5: Verify Backend Blockchain Connection

```bash
cd /Users/work/Maj/backend
python3 << 'EOF'
import os
os.environ['GANACHE_URL'] = 'http://127.0.0.1:8545'
from app.services.blockchain import blockchain_service

if blockchain_service.connected:
    print("✅ Backend connected to blockchain")
    print(f"   Default account: {blockchain_service.default_account}")

    contracts = {
        "VoterRegistry": blockchain_service.voter_registry,
        "VotingBooth": blockchain_service.voting_booth,
        "ResultsTallier": blockchain_service.results_tallier,
        "ElectionController": blockchain_service.election_controller
    }

    all_loaded = all(contracts.values())
    if all_loaded:
        print("✅ All 4 contracts loaded")
        for name, contract in contracts.items():
            if contract:
                print(f"   {name}: {contract.address}")
    else:
        print("❌ Some contracts not loaded:")
        for name, contract in contracts.items():
            status = "✓" if contract else "✗"
            print(f"   {status} {name}")
else:
    print("❌ Backend NOT connected to blockchain")
    print("   Check if Ganache is running")
EOF
```

**If not connected or contracts not loaded:**
1. Restart Ganache: `ganache --networkId 1337 --port 8545`
2. Restart Backend: `uvicorn app.main:app --reload`
3. If still failing, redeploy contracts

---

## 🐛 Common Issues & Solutions

### Issue 1: "Face recognition service not available"

**Symptoms:**
- Error when registering voter
- Error when authenticating with face

**Diagnosis:**
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check backend logs for DeepFace errors
# Look for "deepface" or "face_recognition" in logs
```

**Solutions:**

**A) DeepFace Models Not Downloaded:**
```bash
# First time running, DeepFace downloads ~100MB models
# Wait for backend to fully start (check logs)
# Should see: "Application startup complete"
```

**B) Missing Dependencies:**
```bash
cd /Users/work/Maj/backend
source .venv/bin/activate
pip install deepface opencv-python-headless
```

**C) Restart Backend:**
```bash
# Ctrl+C to stop
cd /Users/work/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

---

### Issue 2: "Blockchain node not connected"

**Symptoms:**
- Cannot start election
- Cannot register voter on blockchain
- Cannot cast vote

**Diagnosis:**
```bash
# Is Ganache running?
curl -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
```

**Solutions:**

**A) Ganache Not Running:**
```bash
ganache --networkId 1337 --port 8545
```

**B) Port 8545 Already in Use:**
```bash
# Kill existing process
lsof -ti:8545 | xargs kill -9

# Start Ganache
ganache --networkId 1337 --port 8545
```

**C) Wrong Network ID:**
```bash
# Check current network ID
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# If not 1337, restart Ganache
ganache --networkId 1337 --port 8545
```

---

### Issue 3: "Results show 0 votes" (but voters voted)

**Symptoms:**
- Votes were cast successfully
- But results page shows 0 votes for all candidates
- Or finalization says "0 votes cast"

**Diagnosis:**
```bash
# Check database for votes
export DB="postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
psql "$DB" -c "SELECT COUNT(*) FROM vote_submissions;"

# Check blockchain transactions
psql "$DB" -c "SELECT COUNT(*) FROM blockchain_txns WHERE tx_type = 'cast_vote';"
```

**Root Cause:**
Network ID mismatch - votes recorded on different blockchain than contracts deployed to.

**Solution:**
```bash
# 1. Check current Ganache network ID
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# 2. Check contract network ID
cd /Users/work/Maj/contracts
cat build/contracts/ElectionController.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Deployed to networks:', list(data.get('networks', {}).keys()))
"

# 3. If they don't match (e.g., contracts on 1337 but Ganache running 5777):

# OPTION A: Restart Ganache with correct network ID
ganache --networkId 1337 --port 8545

# OPTION B: Redeploy contracts to current Ganache
cd /Users/work/Maj/contracts
npx truffle migrate --reset --network development

# 4. Start election over from beginning
# (Previous votes won't be recoverable)
```

---

### Issue 4: "Invalid Date" for election dates

**Symptoms:**
- Election card shows "Start: Invalid Date"
- Election card shows "End: Invalid Date"

**Root Cause:**
Field name mismatch between backend (voting_start_at) and frontend (startDate)

**Solution:**
✅ **Already fixed in latest code!**

Verify you're running latest code:
```bash
cd /Users/work/Maj/frontend
grep "voting_start_at" src/pages/ElectionManager.jsx
# Should show: election.voting_start_at

# If not, update code and restart frontend
npm start
```

---

### Issue 5: Cannot edit election (no button)

**Symptoms:**
- No "Edit Election" button for draft elections
- Or button exists but does nothing

**Root Cause:**
Edit functionality not implemented or API endpoint missing

**Solution:**
✅ **Already fixed in latest code!**

Verify backend endpoint exists:
```bash
curl -X PATCH http://localhost:8000/api/elections/{election-id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'
# Should return 200 OK (or 401 if not authenticated)
```

Verify frontend has edit button:
```bash
cd /Users/work/Maj/frontend
grep "Edit Election" src/pages/ElectionManager.jsx
# Should show button text
```

---

### Issue 6: "Finalize Election" button not appearing

**Symptoms:**
- Closed election successfully
- But no "Finalize Election" button appears

**Root Cause:**
Frontend checking for wrong status value (e.g., "closed" instead of "ended")

**Solution:**
✅ **Already fixed in latest code!**

Verify fix:
```bash
cd /Users/work/Maj/frontend
grep "election.status === 'ended'" src/pages/ElectionManager.jsx
# Should show the condition for finalize button
```

**Workaround:**
Refresh the page after closing election.

---

### Issue 7: Authentication always fails

**Symptoms:**
- Face authentication fails every time
- Or fingerprint authentication fails

**Diagnosis:**

**A) Check if biometric data was stored:**
```bash
export DB="postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
psql "$DB" -c "SELECT voter_id, face_embedding_hash IS NOT NULL as has_face, fingerprint_hash IS NOT NULL as has_fingerprint FROM voters WHERE voter_id = 'V001';"
```

Both should be `t` (true).

**B) Check authentication logs:**
```bash
psql "$DB" -c "SELECT outcome, failure_reason, similarity_score FROM auth_attempts WHERE voter_id IN (SELECT id FROM voters WHERE voter_id = 'V001') ORDER BY attempted_at DESC LIMIT 5;"
```

**Solutions:**

**A) Poor Image Quality:**
- Ensure good lighting
- Face should be clearly visible and front-facing
- No glasses/mask/hat obstructing face
- Retake photo during registration

**B) Threshold Too Strict:**
Default threshold: 0.68 (68% similarity required)

To adjust (in backend code):
```python
# app/services/biometric/face.py
SIMILARITY_THRESHOLD = 0.60  # Lower to 60% (less strict)
```

**C) Wrong Person Trying to Vote:**
Face must match registered face. This is expected security!
- Use fingerprint fallback
- Or re-register with correct face

**D) DeepFace Model Issues:**
```bash
# Restart backend to reload models
cd /Users/work/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

---

### Issue 8: Vote submission fails with "Voter already voted"

**Symptoms:**
- Error: "Voter has already cast a vote"
- Cannot vote again

**Root Cause:**
✅ **This is EXPECTED behavior!** Each voter can only vote once.

**Verification:**
```bash
export DB="postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
psql "$DB" -c "SELECT voter_id, has_voted FROM voters WHERE voter_id = 'V001';"
```

If `has_voted = t`, voter already voted.

**Solution:**
None needed - this prevents duplicate voting (security feature).

To test multiple votes, register multiple voters with different voter IDs.

---

### Issue 9: Frontend won't load (white screen)

**Symptoms:**
- Browser shows white/blank screen
- Or "Cannot GET /"

**Diagnosis:**
```bash
# Check if frontend dev server is running
curl http://localhost:3000
# Should return HTML

# Check browser console (F12) for errors
```

**Solutions:**

**A) Frontend Not Running:**
```bash
cd /Users/work/Maj/frontend
npm start
```

**B) Node Modules Missing:**
```bash
cd /Users/work/Maj/frontend
npm install
npm start
```

**C) Port 3000 Already in Use:**
```bash
# Kill existing process
lsof -ti:3000 | xargs kill -9

# Restart
npm start
```

**D) Build Errors:**
Check terminal for compile errors. Fix syntax errors in React code.

---

### Issue 10: Database connection errors

**Symptoms:**
- "Connection refused"
- "Could not connect to database"

**Diagnosis:**
Your database is on Neon (cloud), so connection errors are rare.

Check connection string:
```bash
echo $DATABASE_URL
# Should show: postgresql://neondb_owner:...@ep-fragrant-night...
```

**Solutions:**

**A) Internet Connection:**
Verify you have internet access (Neon is cloud-hosted).

**B) Connection String Missing:**
```bash
# Set in backend .env file
cd /Users/work/Maj/backend
echo 'DATABASE_URL=postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require' >> .env

# Restart backend
uvicorn app.main:app --reload
```

**C) Neon Database Paused:**
Neon free tier pauses inactive databases. Just retry - it auto-resumes.

---

## 🔄 Nuclear Option: Complete Reset

If nothing else works, start fresh:

```bash
# 1. Stop all services (Ctrl+C in all terminals)

# 2. Kill any lingering processes
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:8545 | xargs kill -9

# 3. Clear Ganache data (fresh blockchain)
rm -rf ~/.ganache

# 4. Restart Ganache
ganache --networkId 1337 --port 8545

# 5. Redeploy contracts
cd /Users/work/Maj/contracts
npx truffle migrate --reset --network development

# 6. Restart backend
cd /Users/work/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload

# 7. Restart frontend
cd /Users/work/Maj/frontend
npm start

# 8. In database, optionally reset elections
# (Keep this as last resort - loses all data!)
export DB="postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
psql "$DB" -c "TRUNCATE elections, constituencies, candidates, voters, vote_submissions, auth_attempts, blockchain_txns, audit_logs RESTART IDENTITY CASCADE;"
```

---

## 📞 Getting Help

If you're still stuck after trying everything:

1. **Check Backend Logs:**
   Look for errors in terminal running backend

2. **Check Browser Console (F12):**
   Look for JavaScript errors

3. **Check Ganache Terminal:**
   Look for transaction failures

4. **Review This Checklist:**
   Did you follow all steps?

5. **Check Documentation:**
   - `MANUAL_SETUP_GUIDE.md` - Full setup guide
   - `QUICK_REFERENCE.md` - Quick commands

---

## 📋 Pre-Flight Checklist

Before running an election, verify:

- [ ] Ganache running on port 8545
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Network ID is 1337
- [ ] All 4 contracts deployed
- [ ] Backend connected to blockchain
- [ ] Database accessible
- [ ] Can login to admin dashboard
- [ ] Can create/edit elections
- [ ] Can register voters
- [ ] Face recognition working
- [ ] Can authenticate and vote
- [ ] Can view audit logs

If ALL checks pass: ✅ **System is ready!**

---

**Last Updated:** February 16, 2026
