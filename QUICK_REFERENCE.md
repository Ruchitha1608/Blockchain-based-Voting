# Blockchain Voting System - Quick Reference Card

**Platform Support**: Mac, Linux, Windows

> **Windows Users**: See [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) for detailed Windows-specific setup instructions.

---

## 🚀 Start System

### Mac/Linux (4 Terminals)

```bash
# Terminal 1: Ganache
ganache --networkId 1337 --port 8545

# Terminal 2: Backend
cd ~/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3: Frontend
cd ~/Maj/frontend
npm start

# Terminal 4: Free for commands
```

### Windows (3 PowerShell Windows)

```powershell
# PowerShell 1: Ganache
ganache --networkId 1337 --port 8545

# PowerShell 2: Backend
cd C:\Users\YourName\Maj\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# PowerShell 3: Frontend
cd C:\Users\YourName\Maj\frontend
npm start
```

---

## 📊 System Status Checks

```bash
# Ganache (should return network ID 1337)
curl -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# Backend (should return 200 OK)
curl http://localhost:8000/api/health

# Frontend (open in browser)
http://localhost:3000
```

---

## 🗳️ Election Workflow

### 1️⃣ Create Election
```
1. Login → Admin Dashboard
2. Election Manager → "+ Create Election"
3. Fill: Name, Description, Start/End Dates
4. Add Constituency (Name, Code)
5. Add Candidates (Name, Party, Symbol)
```

### 2️⃣ Register Voters
```
1. Voter Registration page
2. Enter: Voter ID, Name, Constituency
3. Capture Face (webcam)
4. Capture Fingerprint (upload)
5. Submit → Voter registered on blockchain
```

### 3️⃣ Start Election
```
Election Manager → "Start Election" button
Status: draft → active
```

### 4️⃣ Vote
```
Polling Booth page:
1. Authenticate with Face (or Fingerprint)
2. Select Candidate
3. Cast Vote → Recorded on blockchain
```

### 5️⃣ Close & Finalize
```
1. Close Election (Status: active → ended)
2. Finalize Election (Tallies votes)
3. View Results (Shows winners, charts)
```

---

## 🔧 Common Commands

### Redeploy Contracts

**Mac/Linux:**
```bash
cd ~/Maj/contracts
npx truffle migrate --reset --network development
```

**Windows:**
```powershell
cd C:\Users\YourName\Maj\contracts
npx truffle migrate --reset --network development
```

### Database Queries (Using Neon)

**Mac/Linux:**
```bash
export DB="postgresql://your_neon_connection_string"

# List elections
psql "$DB" -c "SELECT id, name, status FROM elections;"

# Count votes
psql "$DB" -c "SELECT COUNT(*) FROM vote_submissions;"

# Check voters
psql "$DB" -c "SELECT voter_id, full_name, has_voted FROM voters;"
```

**Windows:**
```powershell
$DB="postgresql://your_neon_connection_string"

# List elections
psql "$DB" -c "SELECT id, name, status FROM elections;"

# Count votes
psql "$DB" -c "SELECT COUNT(*) FROM vote_submissions;"

# Check voters
psql "$DB" -c "SELECT voter_id, full_name, has_voted FROM voters;"
```

**Or use Neon SQL Editor** (easiest for Windows):
1. Go to your Neon dashboard
2. Click "SQL Editor"
3. Run queries directly

### View Blockchain Transactions

```sql
SELECT tx_type, tx_hash, block_number, status
FROM blockchain_txns
ORDER BY recorded_at DESC
LIMIT 10;
```

---

## ⚠️ Quick Fixes

### Face Recognition Not Working

**Mac/Linux:**
```bash
# Restart backend (loads DeepFace models)
cd ~/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Windows:**
```powershell
# Restart backend (loads DeepFace models)
cd C:\Users\YourName\Maj\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Blockchain Not Connected

**All platforms:**
```bash
# Ensure Ganache running with correct network ID
ganache --networkId 1337 --port 8545
```

### Results Show 0 Votes

**Mac/Linux:**
```bash
# Verify network ID matches
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}' | grep 1337

# If wrong, redeploy contracts and start over
cd ~/Maj/contracts
npx truffle migrate --reset
```

**Windows:**
```powershell
# Verify network ID matches
curl -X POST http://127.0.0.1:8545 `
  -H "Content-Type: application/json" `
  -Body '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# If wrong, redeploy contracts and start over
cd C:\Users\YourName\Maj\contracts
npx truffle migrate --reset
```

### Port Already in Use

**Mac/Linux:**
```bash
# Kill process on port 8545 (Ganache)
lsof -ti:8545 | xargs kill -9

# Kill process on port 8000 (Backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000 (Frontend)
lsof -ti:3000 | xargs kill -9
```

**Windows:**
```powershell
# Find and kill process on port 8545 (Ganache)
netstat -ano | findstr :8545
taskkill /PID <PID> /F

# Find and kill process on port 8000 (Backend)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Find and kill process on port 3000 (Frontend)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

## 📱 URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:3000/admin/dashboard
- **Polling Booth**: http://localhost:3000/polling-booth
- **Audit Viewer**: http://localhost:3000/admin/audit

---

## 🔑 Default Admin Credentials

```
Username: super_admin
Password: [Your admin password]
```

---

## 📦 Smart Contract Addresses (Network 1337)

```
VoterRegistry:      0xe78A0F7E598Cc8b0Bb87894B0F60dD2a88d6a8Ab
VotingBooth:        0x5b1869D9A4C187F2EAa108f3062412ecf0526b24
ResultsTallier:     0xCfEB869F69431e42cdB54A4F4f105C19C080A601
ElectionController: 0x254dffcd3277C0b1660F6d42EFbB754edaBAbC2B
```

---

## 🎯 Election Status Flow

```
draft → active → ended → finalized
  ↓       ↓        ↓         ↓
Edit    Vote    Close    Results
        Open   Voting   Available
```

---

## 📊 Key Metrics Dashboard

- **Total Elections**: All created elections
- **Active Elections**: Currently accepting votes
- **Registered Voters**: Total voters in system
- **Total Votes Cast**: Votes recorded on blockchain

---

## 🐛 Debug Logs

### Backend Logs
```bash
# Watch backend logs
tail -f /path/to/backend.log

# Or run with verbose logging
uvicorn app.main:app --reload --log-level debug
```

### Ganache Logs
```bash
# Ganache terminal shows:
- eth_sendRawTransaction (vote submissions)
- eth_call (reading contract state)
- Block confirmations
```

---

## 🎓 Documentation

### Setup Guides
- **Mac/Linux**: [NEW_MACHINE_SETUP.md](NEW_MACHINE_SETUP.md) + [SETUP_CHECKLIST.txt](SETUP_CHECKLIST.txt)
- **Windows**: [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) + [WINDOWS_SETUP_CHECKLIST.txt](WINDOWS_SETUP_CHECKLIST.txt)

### Operation
- **Manual**: [MANUAL_SETUP_GUIDE.md](MANUAL_SETUP_GUIDE.md) - Complete operational guide
- **Troubleshooting**: [TROUBLESHOOTING_CHECKLIST.md](TROUBLESHOOTING_CHECKLIST.md) - Debug guide

---

**Quick Start in 3 Steps:**
1. Start all 3 services (Ganache, Backend, Frontend)
2. Create election + Register voters
3. Start → Vote → Close → Finalize → Results ✅

---

**Platform Notes:**
- **Mac/Linux**: Use `bash` or `zsh` terminal
- **Windows**: Use PowerShell (recommended) or Command Prompt
- **Windows (Alternative)**: Use WSL2 and follow Mac/Linux instructions
