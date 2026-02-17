# Blockchain Voting System - Manual Setup & Operation Guide

Complete step-by-step guide to manually set up and run the blockchain-based voting system.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Starting the System](#starting-the-system)
4. [Creating an Election](#creating-an-election)
5. [Managing Voters](#managing-voters)
6. [Running an Election](#running-an-election)
7. [Viewing Results](#viewing-results)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Node.js**: v18+ and npm
- **Python**: 3.11+
- **PostgreSQL**: 16+ (or Neon cloud database)
- **Ganache**: For local blockchain
- **Git**: For version control

### Install Ganache
```bash
npm install -g ganache
```

---

## Initial Setup

### 1. Database Setup (Neon Cloud)

Your database is already configured:
- **Database URL**: `postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require`
- **Tables**: Already created with schema

### 2. Smart Contracts Setup

```bash
# Navigate to contracts directory
cd /Users/work/Maj/contracts

# Install dependencies (if not already done)
npm install

# Compile contracts
npx truffle compile

# Deploy contracts (only needed once or after contract changes)
npx truffle migrate --network development
```

**Expected Output:**
- VoterRegistry deployed at: `0xe78A0F7E598Cc8b0Bb87894B0F60dD2a88d6a8Ab`
- VotingBooth deployed at: `0x5b1869D9A4C187F2EAa108f3062412ecf0526b24`
- ResultsTallier deployed at: `0xCfEB869F69431e42cdB54A4F4f105C19C080A601`
- ElectionController deployed at: `0x254dffcd3277C0b1660F6d42EFbB754edaBAbC2B`

### 3. Backend Setup

```bash
# Navigate to backend directory
cd /Users/work/Maj/backend

# Create/activate virtual environment (if needed)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd /Users/work/Maj/frontend

# Install dependencies
npm install
```

---

## Starting the System

You need **4 terminal windows** running simultaneously:

### Terminal 1: Ganache (Blockchain)

```bash
# Start Ganache with network ID 1337
ganache --networkId 1337 --port 8545
```

**Keep this running!** You should see:
- Available Accounts (10 addresses)
- Private Keys
- Listening on 127.0.0.1:8545

### Terminal 2: Backend API

```bash
cd /Users/work/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Keep this running!** You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Backend logs will show:
- `blockchain_connected` - Ganache connected
- `contracts_loaded` - All 4 contracts loaded

### Terminal 3: Frontend Development Server

```bash
cd /Users/work/Maj/frontend
npm start
```

**Keep this running!** Browser should auto-open to `http://localhost:3000`

### Terminal 4: Testing/Commands

Keep one terminal free for running commands and tests.

---

## Verifying System Status

### Check Blockchain Connection

```bash
curl -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
```

**Expected**: `{"jsonrpc":"2.0","id":1,"result":"1337"}`

### Check Backend Health

```bash
curl http://localhost:8000/api/health
```

### Check Contracts Loaded

```bash
cd /Users/work/Maj/backend
python3 << 'EOF'
import os
os.environ['GANACHE_URL'] = 'http://127.0.0.1:8545'
from app.services.blockchain import blockchain_service

print(f"Connected: {blockchain_service.connected}")
print(f"VoterRegistry: {'✓' if blockchain_service.voter_registry else '✗'}")
print(f"VotingBooth: {'✓' if blockchain_service.voting_booth else '✗'}")
print(f"ResultsTallier: {'✓' if blockchain_service.results_tallier else '✗'}")
print(f"ElectionController: {'✓' if blockchain_service.election_controller else '✗'}")
EOF
```

All should show ✓

---

## Creating an Election

### 1. Login to Admin Dashboard

1. Open browser: `http://localhost:3000`
2. Login with admin credentials:
   - Username: `super_admin`
   - Password: Your admin password
3. You'll be redirected to `/admin/dashboard`

### 2. Navigate to Election Manager

Click **"Election Manager"** in the sidebar or stat card.

### 3. Create New Election

1. Click **"+ Create Election"** button
2. Fill in details:
   - **Election Name**: e.g., "Muncipal Elections 2026"
   - **Description**: e.g., "Municipal elections for 2026"
   - **Start Date**: Choose date/time for voting to begin
   - **End Date**: Choose date/time for voting to end
3. Click **"Create Election"**

**Status**: Election is now in `draft` status

### 4. Add Constituencies

For each constituency you want:

1. Click **"Add Constituency"** button
2. Enter:
   - **Name**: e.g., "RR01"
   - **Code**: e.g., "RR100"
3. Click **"Add Constituency"**

Repeat for multiple constituencies if needed.

### 5. Add Candidates

For each candidate:

1. Click **"Add Candidate"** button
2. Select:
   - **Constituency**: Choose from dropdown (e.g., RR01)
3. Enter:
   - **Name**: e.g., "REVANTH REDDY"
   - **Party**: e.g., "CONGRESS"
   - **Symbol**: e.g., "HAND"
4. Click **"Add Candidate"**

Repeat for all candidates in all constituencies.

### 6. Edit Election (Optional)

If you need to change dates or details:

1. Click **"Edit Election"** button (only visible for draft elections)
2. Modify any fields
3. Click **"Update Election"** or **"Cancel"**

---

## Managing Voters

### Register Voters

1. Go to **"Voter Registration"** page from dashboard
2. For each voter:

#### **Fill Form:**
```
Voter ID: V001
Full Name: John Doe
Constituency: RR01 (select from dropdown)
```

#### **Capture Biometrics:**
- **Face Photo**:
  1. Click "Capture Face" button
  2. Allow camera access
  3. Position face in frame
  4. Photo will be captured automatically

- **Fingerprint**:
  1. Click "Capture Fingerprint" button
  2. Upload fingerprint image file
  3. Or use fingerprint scanner if available

#### **Submit:**
Click **"Register Voter"** button

**What Happens:**
- Face embedding is generated and encrypted
- Fingerprint is processed and stored
- Voter is registered on blockchain
- `blockchain_voter_id` is generated (keccak256 hash)

### View Registered Voters

1. Go to **"Voter Registration"** page
2. Click **"Voter List"** tab
3. You'll see table with:
   - Voter ID
   - Full Name
   - Constituency
   - Has Voted status
   - Blockchain Voter ID

---

## Running an Election

### 1. Start the Election

**Prerequisites**:
- Election has constituencies ✓
- Election has candidates ✓
- Voters are registered ✓

**Steps:**
1. Go to **"Election Manager"**
2. Find your election (status: `draft`)
3. Click **"Start Election"** button
4. Confirm in dialog

**What Happens:**
- Election status changes to `active`
- Smart contracts are deployed (if not already)
- Contract addresses are stored in database
- Voting is now open!

**Backend logs should show:**
```
election_started
blockchain transaction recorded
```

### 2. Voters Cast Votes

#### **Navigate to Polling Booth:**
Voters go to: `http://localhost:3000/polling-booth`

#### **Authentication Process:**

**Step 1: Face Recognition**
1. Voter ID is entered or selected
2. Click "Authenticate with Face"
3. Camera captures live photo
4. Backend compares with registered face
5. If match (similarity ≥ 0.68):
   - ✅ Authentication successful
   - Auth token issued (5-minute validity)
   - Proceeds to voting

**Step 2: Fallback - Fingerprint** (if face fails)
1. Click "Try Fingerprint"
2. Upload/scan fingerprint
3. Backend compares with registered fingerprint
4. If match:
   - ✅ Authentication successful
   - Auth token issued
   - Proceeds to voting

#### **Voting:**
1. Select your constituency (auto-filled if registered)
2. View candidates with party symbols
3. Select ONE candidate
4. Click **"Cast Vote"** button
5. Confirm vote

**What Happens:**
- Auth token is validated
- Checks if voter already voted (prevents duplicate)
- Vote is submitted to blockchain via ElectionController
- `VoteCast` event is emitted
- Blockchain transaction is recorded
- Voter's `has_voted` flag is set to `true`

**Success Message:** "Vote cast successfully!"

#### **Session Management:**
- Auto-logout after 120 seconds of inactivity
- Token expires after 5 minutes
- Screen resets after vote cast

### 3. Monitor Voting Progress

#### **Admin Dashboard Stats:**
Navigate to dashboard to see real-time:
- Total Elections
- Active Elections
- Registered Voters
- **Total Votes Cast** (updates as voters vote)

#### **Check Database:**
```bash
# Count votes cast
psql "postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require" \
  -c "SELECT COUNT(*) FROM vote_submissions;"

# Check blockchain transactions
psql "postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require" \
  -c "SELECT tx_type, COUNT(*) FROM blockchain_txns GROUP BY tx_type;"
```

### 4. Close the Election

**When voting period ends:**

1. Go to **"Election Manager"**
2. Find your election (status: `active`)
3. Click **"Close Election"** button
4. Confirm in dialog

**What Happens:**
- Calls `ElectionController.closeElection()` on blockchain
- Election status changes from `active` → `ended`
- No more votes can be cast
- Election is ready for finalization

### 5. Finalize the Election

**After closing:**

1. The **"Finalize Election"** button now appears (only for `ended` elections)
2. Click **"Finalize Election"**
3. Confirm in dialog (cannot be undone)

**What Happens:**
- Backend calls `ElectionController.tallyAndFinalize()`
- For each constituency:
  - Counts votes for each candidate
  - Determines winner (candidate with most votes)
  - Detects ties (if multiple candidates have same max votes)
  - Stores results in `ResultsTallier` contract
- Election status changes to `finalized`
- `finalized_at` timestamp is recorded
- Admin who finalized is logged

**This process may take 10-30 seconds** depending on number of constituencies and candidates.

---

## Viewing Results

### Prerequisites
- Election must be **finalized** (not just closed)

### View Results in UI

1. Go to **"Election Manager"**
2. Find your election (status: `finalized`)
3. Click **"View Results"** button

**You'll see:**

#### **Overall Statistics:**
- Total Votes Cast
- Total Constituencies
- Turnout Percentage

#### **Per Constituency:**
- Constituency Name (Code)
- Winner Announcement:
  - 🏆 **Winner: CANDIDATE NAME (PARTY) - X votes**
  - Or ⚠️ **Tie warning** if multiple candidates tied
- **Candidates Table:**
  | Candidate | Party | Votes |
  |-----------|-------|-------|
  | Name 1    | Party | Count |
  | Name 2    | Party | Count |

#### **Overall Chart:**
- Bar chart showing vote distribution
- All candidates across all constituencies
- X-axis: Candidate (Constituency)
- Y-axis: Vote count

### Programmatic Access

#### **API Endpoint:**
```bash
curl -X GET "http://localhost:8000/api/elections/{election_id}/results" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### **Response Structure:**
```json
{
  "election_id": "uuid",
  "election_name": "string",
  "status": "finalized",
  "finalized_at": "2026-02-16T...",
  "total_votes_cast": 100,
  "total_constituencies": 3,
  "turnout_percentage": 85.5,
  "constituencies": [
    {
      "constituency_id": "uuid",
      "constituency_name": "RR01",
      "constituency_code": "RR100",
      "total_votes": 50,
      "is_tied": false,
      "winner": {
        "candidate_id": "uuid",
        "candidate_name": "REVANTH REDDY",
        "party": "CONGRESS",
        "vote_count": 30
      },
      "candidates": [
        {
          "candidate_id": "uuid",
          "candidate_name": "REVANTH REDDY",
          "party": "CONGRESS",
          "vote_count": 30
        },
        {
          "candidate_id": "uuid",
          "candidate_name": "CANDIDATE 2",
          "party": "BJP",
          "vote_count": 20
        }
      ]
    }
  ]
}
```

### Audit Logs

#### **Authentication Attempts:**
Navigate to: `/admin/audit` → **Authentication Logs** tab

View:
- Timestamp
- Voter ID
- Method (face/fingerprint)
- Outcome (success/failure)
- IP Address
- Failure Reason (if failed)
- Similarity Score

**Filters:**
- Date range (start/end)
- Voter ID
- Outcome (success/failure)

**Export:**
Click **"Export to CSV"** to download all logs.

#### **Blockchain Transactions:**
Navigate to: `/admin/audit` → **Blockchain Transactions** tab

View:
- Transaction Hash
- Voter ID (if applicable)
- Timestamp
- Block Number
- Transaction Type

**Search:**
- By Voter ID
- By Transaction Hash

---

## Troubleshooting

### Issue: "Face recognition service not available"

**Cause:** DeepFace model not loaded or backend not running properly

**Solution:**
```bash
# Restart backend
cd /Users/work/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

On first run, DeepFace will download models (~100MB). Wait for:
```
INFO: Application startup complete
```

### Issue: "Blockchain node not connected"

**Cause:** Ganache not running or wrong network ID

**Check:**
```bash
# Is Ganache running?
curl -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
```

**Solution:**
```bash
# Start Ganache with correct network ID
ganache --networkId 1337 --port 8545
```

### Issue: "Results show 0 votes" even though votes were cast

**Cause:** Network ID mismatch - contracts deployed to different Ganache instance

**Verification:**
```bash
# Check current Ganache network ID
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# Should return: {"jsonrpc":"2.0","id":1,"result":"1337"}
```

**Solution:**
```bash
# Option 1: Restart Ganache with network ID 1337
ganache --networkId 1337 --port 8545

# Option 2: Redeploy contracts
cd /Users/work/Maj/contracts
npx truffle migrate --reset --network development

# Then restart election from beginning
```

### Issue: "Invalid Date" showing for election dates

**Cause:** Field name mismatch between backend and frontend

**Solution:** Already fixed! Make sure you're running latest code.

Backend uses: `voting_start_at`, `voting_end_at`
Frontend now correctly reads these fields.

### Issue: Cannot edit election

**Cause:** Edit endpoint not implemented or missing API function

**Solution:** Already fixed! Make sure:
1. Backend has PATCH endpoint at `/api/elections/{id}`
2. Frontend has `updateElection` function imported
3. "Edit Election" button visible for draft elections

### Issue: Authentication always fails

**Possible Causes:**
1. **No face detected in image**
   - Ensure good lighting
   - Face should be clearly visible
   - Try again with better photo

2. **Similarity threshold too strict**
   - Default: 0.68 (68% match required)
   - Lower in code if needed (not recommended for production)

3. **Different person trying to vote**
   - Face must match registered face
   - Try fingerprint fallback

4. **Biometric data not stored correctly**
   - Check database: `SELECT voter_id, face_embedding_hash, fingerprint_hash FROM voters WHERE voter_id = 'V001';`
   - Both should not be NULL

### Issue: Vote submission fails with "Voter already voted"

**Cause:** Database correctly preventing duplicate votes

**This is expected behavior!** Each voter can only vote once.

**To verify:**
```sql
SELECT voter_id, has_voted FROM voters WHERE voter_id = 'V001';
```

### Issue: Finalize button not appearing

**Cause:** Frontend checking wrong status value

**Solution:** Already fixed!
- Backend returns status: `ended`
- Frontend now checks: `election.status === 'ended'`

Refresh the page after closing election.

---

## Quick Reference Commands

### Start Everything
```bash
# Terminal 1
ganache --networkId 1337 --port 8545

# Terminal 2
cd /Users/work/Maj/backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 3
cd /Users/work/Maj/frontend && npm start
```

### Check Status
```bash
# Ganache
curl -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# Backend
curl http://localhost:8000/api/health

# Frontend
# Open http://localhost:3000 in browser
```

### Database Queries
```bash
# Set connection string
export DATABASE_URL="postgresql://neondb_owner:REDACTED@ep-fragrant-night-a59yfwz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Check elections
psql "$DATABASE_URL" -c "SELECT id, name, status FROM elections;"

# Check voters
psql "$DATABASE_URL" -c "SELECT voter_id, full_name, has_voted FROM voters;"

# Check votes
psql "$DATABASE_URL" -c "SELECT COUNT(*) as total_votes FROM vote_submissions;"

# Check blockchain transactions
psql "$DATABASE_URL" -c "SELECT tx_type, COUNT(*) FROM blockchain_txns GROUP BY tx_type;"
```

### Redeploy Contracts
```bash
cd /Users/work/Maj/contracts
npx truffle migrate --reset --network development
```

---

## Complete Election Flow Summary

1. **Setup** (one-time):
   - Install dependencies
   - Deploy contracts
   - Start Ganache, Backend, Frontend

2. **Create Election**:
   - Login as admin
   - Create election with dates
   - Add constituencies
   - Add candidates

3. **Register Voters**:
   - Navigate to Voter Registration
   - For each voter: Enter details, capture face & fingerprint
   - Submit registration

4. **Start Election**:
   - Click "Start Election"
   - Status: draft → active
   - Voting is open

5. **Vote**:
   - Voters go to Polling Booth
   - Authenticate with face (or fingerprint fallback)
   - Select candidate
   - Cast vote

6. **Close Election**:
   - When voting period ends
   - Click "Close Election"
   - Status: active → ended

7. **Finalize**:
   - Click "Finalize Election"
   - Wait for tallying to complete
   - Status: ended → finalized

8. **View Results**:
   - Click "View Results"
   - See winners, vote counts, charts
   - Export audit logs if needed

---

## Security Notes

### In Production, You Must:

1. **Change All Default Passwords**
2. **Use HTTPS** (not HTTP)
3. **Use Real Ethereum Network** (not Ganache)
4. **Secure Private Keys** with HSM or key management service
5. **Enable Rate Limiting** on authentication endpoints
6. **Add CAPTCHA** to prevent bots
7. **Use Professional Biometric Devices** (not webcam)
8. **Regular Security Audits** of smart contracts
9. **Backup Database** every 6 hours
10. **Monitor All Logs** for suspicious activity

### Never Commit to Git:
- `.env` files with secrets
- Private keys
- Database passwords
- API keys
- Biometric data

---

## Support

For issues or questions:
1. Check this documentation first
2. Check troubleshooting section
3. Review backend logs for errors
4. Check Ganache console for transaction errors
5. Verify all 4 services are running

---

**Last Updated:** February 16, 2026
**System Version:** 1.0
**Documentation Version:** 1.0
