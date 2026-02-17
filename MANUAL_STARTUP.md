# Manual Startup Guide - All Services

Complete guide to manually start all services for the Blockchain Voting System.

---

## **Prerequisites**

Before starting, ensure you have:
- ✅ Python 3.11+ installed
- ✅ Node.js 16+ and npm installed
- ✅ Ganache installed (GUI or CLI)
- ✅ PostgreSQL (if using local DB, or Neon for cloud)

---

## **Quick Reference - All Services**

| Service | Port | Command Location | Log Location |
|---------|------|------------------|--------------|
| Backend | 8000 | `/Users/work/Maj/backend` | `/tmp/backend.log` |
| Frontend | 3000 | `/Users/work/Maj/frontend` | `/tmp/frontend.log` |
| Ganache | 8545 | Any directory | Terminal output |
| PostgreSQL | 5432 | System service | System logs |

---

## **Step-by-Step Startup**

### **Step 1: Start Ganache (Blockchain)**

#### **Option A: Ganache CLI**
```bash
# Open a new terminal window
ganache-cli --port 8545 --networkId 1337 --deterministic

# Expected output:
# Ganache CLI v6.x.x
# Available Accounts
# ==================
# (0) 0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1 (100 ETH)
# ...
# Listening on 127.0.0.1:8545
```

**Keep this terminal open!**

#### **Option B: Ganache GUI**
1. Open Ganache application
2. Click "Quickstart" or "New Workspace"
3. Configure:
   - **Port Number:** 8545
   - **Network ID:** 1337
4. Click "Start"

#### **Verify Ganache is Running:**
```bash
curl http://localhost:8545 -X POST \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Should return: {"id":1,"jsonrpc":"2.0","result":"0x..."}
```

---

### **Step 2: Verify Database Connection**

#### **If Using Neon (Cloud PostgreSQL):**
```bash
# Test connection
cd /Users/work/Maj/backend
python -c "
from sqlalchemy import create_engine, text
from app.config import settings
engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connected!')
"
```

#### **If Using Local PostgreSQL:**

**macOS (Homebrew):**
```bash
# Check if PostgreSQL is installed
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@16

# Verify it's running
psql -h localhost -p 5432 -U voting_user -d voting_db -c "SELECT 1;"
```

**Linux (Ubuntu/Debian):**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Check status
sudo systemctl status postgresql

# Verify connection
psql -h localhost -p 5432 -U voting_user -d voting_db -c "SELECT 1;"
```

---

### **Step 3: Start Backend (FastAPI)**

#### **Terminal 2 - Backend**
```bash
# Navigate to backend directory
cd /Users/work/Maj/backend

# Activate virtual environment (if using one)
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install/update dependencies (first time or after changes)
pip install -r requirements.txt

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Will watch for changes in these directories: ['/Users/work/Maj/backend']
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [xxxxx] using WatchFiles
# [timestamp] [info] blockchain_connected url=http://localhost:8545
# [timestamp] [info] contracts_loaded contracts=['VoterRegistry', 'VotingBooth', ...]
# INFO:     Application startup complete.
```

**Keep this terminal open!**

#### **Alternative: Run in Background**
```bash
# Start in background with logging
cd /Users/work/Maj/backend
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

# Check logs
tail -f /tmp/backend.log

# To stop later
lsof -ti:8000 | xargs kill -9
```

#### **Verify Backend is Running:**
```bash
# Check API docs
curl http://localhost:8000/docs | head -20

# Or open in browser:
# http://localhost:8000/docs
```

---

### **Step 4: Start Frontend (React)**

#### **Terminal 3 - Frontend**
```bash
# Navigate to frontend directory
cd /Users/work/Maj/frontend

# Install/update dependencies (first time or after changes)
npm install

# Start the development server
npm start

# Expected output:
# Compiled successfully!
#
# You can now view blockchain-voting-frontend in the browser.
#
#   Local:            http://localhost:3000
#   On Your Network:  http://192.168.x.x:3000
#
# Note that the development build is not optimized.
# To create a production build, use npm run build.
#
# webpack compiled successfully
```

**Keep this terminal open!**

The browser should automatically open to http://localhost:3000

#### **Alternative: Run in Background**
```bash
# Start in background
cd /Users/work/Maj/frontend
nohup npm start > /tmp/frontend.log 2>&1 &

# Check logs
tail -f /tmp/frontend.log

# To stop later
pkill -f "react-scripts start"
```

#### **Verify Frontend is Running:**
```bash
# Check if frontend is accessible
curl http://localhost:3000 | grep "<title>"

# Or open in browser:
# http://localhost:3000
```

---

## **Step 5: Verify All Services**

### **Complete System Check**
```bash
cd /Users/work/Maj/backend

# Run system check script
python << 'EOF'
import requests
import json

print("=" * 60)
print("SYSTEM STATUS CHECK")
print("=" * 60)

# Check Backend
try:
    response = requests.get("http://localhost:8000/docs", timeout=2)
    if response.status_code == 200:
        print("✅ Backend (FastAPI):    http://localhost:8000 - RUNNING")
    else:
        print(f"⚠️  Backend:              Status {response.status_code}")
except Exception as e:
    print(f"❌ Backend:              NOT RUNNING ({str(e)[:50]})")

# Check Frontend
try:
    response = requests.get("http://localhost:3000", timeout=2)
    if response.status_code == 200:
        print("✅ Frontend (React):     http://localhost:3000 - RUNNING")
    else:
        print(f"⚠️  Frontend:             Status {response.status_code}")
except Exception as e:
    print(f"❌ Frontend:             NOT RUNNING ({str(e)[:50]})")

# Check Ganache
try:
    response = requests.post(
        "http://localhost:8545",
        json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1},
        timeout=2
    )
    if response.status_code == 200:
        result = response.json()
        block = int(result['result'], 16)
        print(f"✅ Blockchain (Ganache): http://localhost:8545 - RUNNING (Block #{block})")
    else:
        print(f"⚠️  Blockchain:           Status {response.status_code}")
except Exception as e:
    print(f"❌ Blockchain:           NOT RUNNING ({str(e)[:50]})")

# Check Database
try:
    from sqlalchemy import create_engine, text
    from app.config import settings
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Database (PostgreSQL): CONNECTED")
except Exception as e:
    print(f"❌ Database:             NOT CONNECTED ({str(e)[:50]})")

print("=" * 60)
EOF
```

**Expected Output:**
```
============================================================
SYSTEM STATUS CHECK
============================================================
✅ Backend (FastAPI):    http://localhost:8000 - RUNNING
✅ Frontend (React):     http://localhost:3000 - RUNNING
✅ Blockchain (Ganache): http://localhost:8545 - RUNNING (Block #5)
✅ Database (PostgreSQL): CONNECTED
============================================================
```

---

## **Quick Start Script (All at Once)**

### **Create a startup script:**
```bash
cat > /Users/work/Maj/start_all.sh << 'EOF'
#!/bin/bash

echo "Starting Blockchain Voting System..."
echo "===================================="

# Change to project directory
cd /Users/work/Maj

# Kill existing processes
echo "Stopping existing services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null
pkill -f "ganache-cli" 2>/dev/null

sleep 2

# Start Ganache
echo "Starting Ganache..."
ganache-cli --port 8545 --networkId 1337 --deterministic > /tmp/ganache.log 2>&1 &
sleep 3

# Start Backend
echo "Starting Backend..."
cd backend
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5

# Start Frontend
echo "Starting Frontend..."
cd ../frontend
nohup npm start > /tmp/frontend.log 2>&1 &
sleep 10

echo ""
echo "✅ All services started!"
echo ""
echo "Access URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  Backend:   tail -f /tmp/backend.log"
echo "  Frontend:  tail -f /tmp/frontend.log"
echo "  Ganache:   tail -f /tmp/ganache.log"
echo ""
EOF

# Make it executable
chmod +x /Users/work/Maj/start_all.sh
```

### **Run the script:**
```bash
/Users/work/Maj/start_all.sh
```

---

## **Stopping Services**

### **Stop All Services:**
```bash
# Stop Backend
lsof -ti:8000 | xargs kill -9

# Stop Frontend
pkill -f "react-scripts start"

# Stop Ganache
pkill -f "ganache-cli"

# Or use the stop script:
cat > /Users/work/Maj/stop_all.sh << 'EOF'
#!/bin/bash
echo "Stopping all services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null
pkill -f "ganache-cli" 2>/dev/null
echo "✅ All services stopped"
EOF

chmod +x /Users/work/Maj/stop_all.sh
/Users/work/Maj/stop_all.sh
```

---

## **Troubleshooting**

### **Problem: Port Already in Use**

**Backend (Port 8000):**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill it
lsof -ti:8000 | xargs kill -9

# Restart backend
cd /Users/work/Maj/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Port 3000):**
```bash
# Kill React process
pkill -f "react-scripts start"

# Restart frontend
cd /Users/work/Maj/frontend
npm start
```

**Ganache (Port 8545):**
```bash
# Kill Ganache
pkill -f "ganache-cli"

# Restart
ganache-cli --port 8545 --networkId 1337
```

---

### **Problem: Backend Won't Start**

**Check Python version:**
```bash
python --version
# Should be 3.11 or higher
```

**Check dependencies:**
```bash
cd /Users/work/Maj/backend
pip install -r requirements.txt
```

**Check database connection:**
```bash
python -c "from app.config import settings; print(settings.DATABASE_URL)"
```

**Check logs:**
```bash
tail -50 /tmp/backend.log
```

---

### **Problem: Frontend Won't Start**

**Check Node version:**
```bash
node --version
# Should be 16.0 or higher
```

**Clear cache and reinstall:**
```bash
cd /Users/work/Maj/frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

**Check logs:**
```bash
tail -50 /tmp/frontend.log
```

---

### **Problem: Database Connection Failed**

**For Neon (Cloud):**
```bash
# Test connection
curl -I https://ep-winter-frog-aiibm9k9-pooler.c-4.us-east-1.aws.neon.tech

# Check .env file
cat /Users/work/Maj/backend/.env | grep DATABASE_URL
```

**For Local PostgreSQL:**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start it
brew services start postgresql@16

# Test connection
psql -h localhost -p 5432 -U voting_user -d voting_db
```

---

### **Problem: Ganache Not Responding**

**Restart Ganache:**
```bash
pkill -f ganache-cli
ganache-cli --port 8545 --networkId 1337 --deterministic
```

**Use Ganache GUI instead:**
- Open Ganache app
- Create new workspace
- Set port to 8545
- Set network ID to 1337

---

## **Environment Variables**

### **Backend (.env file location):**
```bash
/Users/work/Maj/backend/.env
```

**Key variables:**
```bash
# Database
DATABASE_URL=postgresql://neondb_owner:npg_VMlKaojFt12Z@ep-winter-frog-aiibm9k9-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Blockchain
GANACHE_URL=http://localhost:8545
GANACHE_NETWORK_ID=1337

# Security (auto-generated, don't change)
JWT_SECRET=...
BIOMETRIC_ENCRYPTION_KEY=...
```

---

## **Development Mode vs Production**

### **Development (Current Setup):**
- Backend with `--reload` (auto-restart on code changes)
- Frontend with `npm start` (hot reload)
- Ganache CLI (deterministic accounts)

### **Production Setup:**
```bash
# Backend
cd /Users/work/Maj/backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Frontend
cd /Users/work/Maj/frontend
npm run build
# Serve the build folder with nginx or similar
```

---

## **Useful Commands**

### **Check what's running:**
```bash
# Check all ports
lsof -i :8000,3000,8545

# Check specific service
ps aux | grep uvicorn
ps aux | grep react-scripts
ps aux | grep ganache
```

### **View logs:**
```bash
# Backend
tail -f /tmp/backend.log

# Frontend
tail -f /tmp/frontend.log

# Ganache
tail -f /tmp/ganache.log
```

### **Quick restart:**
```bash
# Restart backend only
lsof -ti:8000 | xargs kill -9 && \
cd /Users/work/Maj/backend && \
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

# Restart frontend only
pkill -f "react-scripts start" && \
cd /Users/work/Maj/frontend && \
nohup npm start > /tmp/frontend.log 2>&1 &
```

---

## **Terminal Layout Recommendation**

For manual development, use 3 terminals:

```
┌─────────────────────────┬─────────────────────────┐
│   Terminal 1: Ganache   │  Terminal 2: Backend    │
│   (Blockchain)          │  (FastAPI)              │
│                         │                         │
│   ganache-cli ...       │  uvicorn app.main:app   │
│                         │                         │
├─────────────────────────┴─────────────────────────┤
│           Terminal 3: Frontend                    │
│           (React)                                 │
│                                                   │
│           npm start                               │
└───────────────────────────────────────────────────┘
```

---

## **Summary**

### **Startup Order:**
1. **Ganache** (port 8545) - Must start FIRST
2. **Database** - Verify connection
3. **Backend** (port 8000) - Connects to Ganache & DB
4. **Frontend** (port 3000) - Connects to Backend

### **Verification:**
- Open http://localhost:3000 - Should load React app
- Open http://localhost:8000/docs - Should show API docs
- Run system check script - All green checkmarks

### **Quick Commands:**
```bash
# Start all
/Users/work/Maj/start_all.sh

# Stop all
/Users/work/Maj/stop_all.sh

# Check status
cd /Users/work/Maj/backend && python check_voters.py
```

---

**Now you can start all services manually and have full control over each component!**
