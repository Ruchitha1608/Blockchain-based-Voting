# 🚀 Blockchain Voting System - Fresh Installation Guide

**Complete guide for setting up this project on a new laptop from scratch.**

---

## ⚙️ Prerequisites Installation

### Step 1: Install Required Software

#### **A) Install Homebrew** (Mac/Linux)
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Verify installation
brew --version
```

For **Windows**: Use Git Bash or WSL2 (Windows Subsystem for Linux)

---

#### **B) Install Node.js (v18+)**
```bash
# Using Homebrew (Mac)
brew install node

# OR download from https://nodejs.org (all platforms)

# Verify installation
node --version  # Should be v18 or higher
npm --version
```

---

#### **C) Install Python (3.11+)**
```bash
# Using Homebrew (Mac)
brew install python@3.11

# OR download from https://www.python.org (all platforms)

# Verify installation
python3 --version  # Should be 3.11 or higher
pip3 --version
```

---

#### **D) Install Ganache** (Blockchain)
```bash
# Install globally via npm
npm install -g ganache

# Verify installation
ganache --version
```

---

#### **E) Install Git** (if not already installed)
```bash
# Using Homebrew (Mac)
brew install git

# Verify installation
git --version
```

---

## 📦 Project Setup

### Step 2: Copy Project Files

**Option A: Using Git (if project is in a repository)**
```bash
# Clone the repository
cd ~
git clone <repository-url> Maj
cd Maj
```

**Option B: Copy from USB/Cloud (if sharing directly)**
```bash
# Copy entire Maj folder to home directory
# From USB: cp -r /Volumes/USB/Maj ~/Maj
# From Downloads: cp -r ~/Downloads/Maj ~/Maj

cd ~/Maj
```

**Verify project structure:**
```bash
ls -la
# Should see:
# - backend/
# - frontend/
# - contracts/
# - MANUAL_SETUP_GUIDE.md
# - QUICK_REFERENCE.md
# - etc.
```

---

### Step 3: Set Up Backend

#### **A) Create Python Virtual Environment**
```bash
cd ~/Maj/backend

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate
# On Windows: .venv\Scripts\activate

# You should see (.venv) in your prompt
```

#### **B) Install Python Dependencies**
```bash
# Make sure virtual environment is activated
pip install -r requirements.txt

# This will install:
# - FastAPI
# - SQLAlchemy
# - DeepFace (face recognition)
# - OpenCV
# - Web3.py
# - And ~30 other packages

# Wait 2-5 minutes for installation
```

#### **C) Configure Environment Variables**
```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your settings
nano .env
# OR
open .env  # Opens in default text editor
```

**IMPORTANT: Update these values in `.env`:**

```bash
# Database Configuration
# Option 1: Use Neon (Cloud PostgreSQL - RECOMMENDED)
DATABASE_URL=postgresql://neondb_owner:<PASSWORD>@<HOST>.neon.tech/neondb?sslmode=require

# Option 2: Use Local PostgreSQL (requires PostgreSQL installed)
# DATABASE_URL=postgresql://voting_user:voting_password@localhost:5432/voting_db

# Blockchain Configuration
GANACHE_URL=http://localhost:8545
GANACHE_NETWORK_ID=1337

# JWT Secret (generate new one)
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# Other secrets (auto-generated, can keep defaults)
VOTING_SESSION_SECRET=<generate_random_64_chars>
BIOMETRIC_SALT_PEPPER=<generate_random_32_chars>
BIOMETRIC_ENCRYPTION_KEY=<generate_random_32_chars>
BLOCKCHAIN_PEPPER=<generate_random_32_chars>
```

**Generate secure secrets:**
```bash
# Run this to generate all secrets
python3 << 'EOF'
import secrets
print("JWT_SECRET=" + secrets.token_urlsafe(64))
print("VOTING_SESSION_SECRET=" + secrets.token_urlsafe(64))
print("BIOMETRIC_SALT_PEPPER=" + secrets.token_urlsafe(32))
print("BIOMETRIC_ENCRYPTION_KEY=" + secrets.token_urlsafe(24))
print("BLOCKCHAIN_PEPPER=" + secrets.token_urlsafe(32))
EOF

# Copy these values into your .env file
```

---

### Step 4: Set Up Frontend

```bash
cd ~/Maj/frontend

# Install Node.js dependencies
npm install

# This will install:
# - React
# - React Router
# - Axios
# - Recharts
# - And ~200 other packages

# Wait 2-5 minutes for installation
```

#### **Configure Frontend Environment** (optional)
```bash
# Create .env file if needed
cat > .env << 'EOF'
REACT_APP_API_URL=http://localhost:8000
EOF
```

---

### Step 5: Set Up Smart Contracts

```bash
cd ~/Maj/contracts

# Install dependencies
npm install

# This will install:
# - Truffle
# - Web3.js
# - OpenZeppelin Contracts
# - And ~50 other packages

# Compile contracts
npx truffle compile

# You should see:
# > Compiling ./contracts/VoterRegistry.sol
# > Compiling ./contracts/VotingBooth.sol
# > Compiling ./contracts/ResultsTallier.sol
# > Compiling ./contracts/ElectionController.sol
# > Artifacts written to build/contracts
# > Compiled successfully
```

---

### Step 6: Database Setup

#### **Option A: Using Neon (Cloud - RECOMMENDED)**

1. **Create Neon Account**:
   - Go to: https://neon.tech
   - Sign up (free tier available)
   - Create new project: "Voting System"

2. **Get Connection String**:
   - Copy connection string from Neon dashboard
   - Format: `postgresql://user:password@host.neon.tech/neondb?sslmode=require`

3. **Update Backend .env**:
   ```bash
   cd ~/Maj/backend
   nano .env
   # Update DATABASE_URL with your Neon connection string
   ```

4. **Run Database Migration**:
   ```bash
   # The schema is in database/schema.sql
   # Connect to Neon and run it:

   # Option 1: Using psql
   psql "YOUR_NEON_CONNECTION_STRING" -f ../database/schema.sql

   # Option 2: Copy schema.sql contents and paste in Neon SQL editor
   # https://console.neon.tech → Your Project → SQL Editor
   ```

#### **Option B: Local PostgreSQL** (Advanced)

```bash
# Install PostgreSQL
brew install postgresql@16

# Start PostgreSQL service
brew services start postgresql@16

# Create database and user
psql postgres << 'EOF'
CREATE USER voting_user WITH PASSWORD 'voting_password';
CREATE DATABASE voting_db OWNER voting_user;
GRANT ALL PRIVILEGES ON DATABASE voting_db TO voting_user;
\q
EOF

# Run schema
psql -U voting_user -d voting_db -f ~/Maj/database/schema.sql

# Update .env
cd ~/Maj/backend
nano .env
# Set: DATABASE_URL=postgresql://voting_user:voting_password@localhost:5432/voting_db
```

---

## 🎬 Starting the System

### Step 7: Start All Services

You need **4 terminal windows** open simultaneously:

#### **Terminal 1: Start Ganache (Blockchain)**
```bash
ganache --networkId 1337 --port 8545

# Should show:
# ganache v7.9.2
# Available Accounts
# ==================
# (0) 0x... (100 ETH)
# (1) 0x... (100 ETH)
# ...
# Listening on 127.0.0.1:8545
```

**Leave this running!**

---

#### **Terminal 2: Deploy Smart Contracts**

```bash
cd ~/Maj/contracts

# Deploy to Ganache
npx truffle migrate --network development

# Should show:
# 1_deploy_registry.js
#   Deploying 'VoterRegistry'
#   > contract address: 0x...
#
# 2_deploy_booth.js
#   Deploying 'VotingBooth'
#   > contract address: 0x...
#
# 3_deploy_tallier.js
#   Deploying 'ResultsTallier'
#   > contract address: 0x...
#
# 4_deploy_controller.js
#   Deploying 'ElectionController'
#   > contract address: 0x...
```

**After deployment completes, start backend in this terminal:**
```bash
cd ~/Maj/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Should show:
# INFO: Uvicorn running on http://0.0.0.0:8000
# INFO: Application startup complete
#
# Backend logs:
# blockchain_connected url=http://127.0.0.1:8545
# default_account_set account=0x...
# contracts_loaded contracts=['VoterRegistry', 'VotingBooth', 'ResultsTallier', 'ElectionController']
```

**Leave this running!**

---

#### **Terminal 3: Start Frontend**

```bash
cd ~/Maj/frontend
npm start

# Should show:
# Compiled successfully!
#
# You can now view frontend in the browser.
#
#   Local:            http://localhost:3000
#   On Your Network:  http://192.168.x.x:3000
```

**Browser should auto-open to http://localhost:3000**

**Leave this running!**

---

#### **Terminal 4: Free for Commands**

Keep this terminal free for running database queries, git commands, etc.

---

## ✅ Verification

### Step 8: Verify Everything Works

#### **A) Check Ganache**
```bash
curl -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# Expected output:
# {"jsonrpc":"2.0","id":1,"result":"1337"}
```

#### **B) Check Backend**
```bash
curl http://localhost:8000/api/health

# Expected output:
# {"status":"healthy","database":"connected"}
```

#### **C) Check Frontend**
Open browser: http://localhost:3000

You should see the **Login page**.

---

### Step 9: Create Admin User

The admin user needs to be created manually in the database:

```bash
# Run this Python script
cd ~/Maj/backend
source .venv/bin/activate

python3 << 'EOF'
import os
os.environ['DATABASE_URL'] = 'YOUR_DATABASE_URL_HERE'  # Update this!

from app.database import SessionLocal
from app.models.admin import Admin, AdminRole
from app.services.crypto import hash_password
import uuid

db = SessionLocal()

# Check if admin exists
existing = db.query(Admin).filter(Admin.username == 'super_admin').first()

if existing:
    print("❌ Admin 'super_admin' already exists!")
else:
    # Create admin
    admin = Admin(
        id=uuid.uuid4(),
        username='super_admin',
        password_hash=hash_password('Admin@123'),  # CHANGE THIS PASSWORD!
        full_name='Super Administrator',
        role=AdminRole.SUPER_ADMIN.value,
        is_active=True
    )

    db.add(admin)
    db.commit()

    print("✅ Admin user created successfully!")
    print(f"   Username: super_admin")
    print(f"   Password: Admin@123")
    print(f"   Role: {AdminRole.SUPER_ADMIN.value}")
    print("")
    print("⚠️  IMPORTANT: Change this password immediately after first login!")

db.close()
EOF
```

**Or using SQL directly:**

```bash
# Connect to your database
psql "YOUR_DATABASE_URL"

# Run this SQL (password hash for 'Admin@123'):
INSERT INTO admins (id, username, password_hash, full_name, role, is_active, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'super_admin',
  '$argon2id$v=19$m=65536,t=3,p=4$...',  -- Use hash from Python script
  'Super Administrator',
  'super_admin',
  true,
  NOW(),
  NOW()
);
```

---

## 🎯 First Login

### Step 10: Test the System

1. **Open Browser**: http://localhost:3000
2. **Login**:
   - Username: `super_admin`
   - Password: `Admin@123` (or whatever you set)
3. **You should see**: Admin Dashboard

**Congratulations! 🎉 System is running!**

---

## 📝 Quick Test Checklist

Run through this checklist to ensure everything works:

- [ ] Can login to admin dashboard
- [ ] Can create a new election
- [ ] Can add constituency
- [ ] Can add candidate
- [ ] Can edit election details
- [ ] Can navigate to Voter Registration
- [ ] Can capture face photo (camera permission)
- [ ] Can register a voter
- [ ] Backend shows no errors
- [ ] All 4 terminals are running

If ALL checks pass: ✅ **System fully operational!**

---

## 🔧 Configuration Files Summary

Your friend needs these files configured:

### **Backend** (`~/Maj/backend/.env`):
```bash
DATABASE_URL=postgresql://...  # From Neon or local PostgreSQL
GANACHE_URL=http://localhost:8545
GANACHE_NETWORK_ID=1337
JWT_SECRET=<64-char-random-string>
VOTING_SESSION_SECRET=<64-char-random-string>
BIOMETRIC_SALT_PEPPER=<32-char-random-string>
BIOMETRIC_ENCRYPTION_KEY=<24-char-random-string>
BLOCKCHAIN_PEPPER=<32-char-random-string>
```

### **Frontend** (`~/Maj/frontend/.env`):
```bash
REACT_APP_API_URL=http://localhost:8000
```

### **Contracts** (`~/Maj/contracts/truffle-config.js`):
Already configured, but verify:
```javascript
networks: {
  development: {
    host: "127.0.0.1",
    port: 8545,
    network_id: "1337"
  }
}
```

---

## 🚨 Common Issues During Setup

### Issue: "command not found: ganache"
```bash
# Install globally
npm install -g ganache

# Or use npx
npx ganache --networkId 1337 --port 8545
```

### Issue: "ModuleNotFoundError: No module named 'deepface'"
```bash
# Virtual environment not activated
cd ~/Maj/backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "EADDRINUSE: Port 3000 already in use"
```bash
# Kill process using port
lsof -ti:3000 | xargs kill -9

# Then restart
npm start
```

### Issue: "Cannot connect to database"
```bash
# Verify DATABASE_URL in .env
# Verify database exists
# Verify internet connection (if using Neon)
# Check firewall settings
```

### Issue: "Contracts not deployed"
```bash
# Make sure Ganache is running FIRST
# Then deploy contracts
cd ~/Maj/contracts
npx truffle migrate --reset --network development
```

---

## 📚 What to Share with Your Friend

### **Files to Copy:**
```
Maj/
├── backend/            (entire folder)
├── frontend/           (entire folder)
├── contracts/          (entire folder)
├── database/           (entire folder)
├── MANUAL_SETUP_GUIDE.md
├── QUICK_REFERENCE.md
├── TROUBLESHOOTING_CHECKLIST.md
├── NEW_MACHINE_SETUP.md  (this file)
└── README.md
```

### **What NOT to copy:**
```
.venv/                  (recreate on new machine)
node_modules/           (reinstall with npm install)
build/                  (regenerate with truffle compile)
.env                    (contains your secrets, create fresh)
__pycache__/            (Python cache, regenerate)
.pytest_cache/          (test cache, regenerate)
```

### **Instructions for Your Friend:**

1. **Give them this file**: `NEW_MACHINE_SETUP.md`
2. **Tell them**:
   - Follow each step in order
   - Don't skip prerequisites
   - Read error messages carefully
   - Each terminal window must stay open
3. **Help them create**:
   - Neon database account (or set up local PostgreSQL)
   - Generate new secrets for `.env`
   - Create first admin user

---

## 🎓 Learning Resources

If your friend wants to understand the system better:

- **Main Guide**: `MANUAL_SETUP_GUIDE.md` - Full system documentation
- **Quick Commands**: `QUICK_REFERENCE.md` - Common operations
- **Debugging**: `TROUBLESHOOTING_CHECKLIST.md` - Fix issues
- **API Docs**: http://localhost:8000/docs (after starting backend)

---

## 📞 Getting Help

If stuck, check in this order:

1. ✅ **Verify Prerequisites**: All software installed?
2. ✅ **Check Logs**: What errors in terminal?
3. ✅ **Read Docs**: `TROUBLESHOOTING_CHECKLIST.md`
4. ✅ **Test Components**: Ganache? Backend? Frontend?
5. ✅ **Start Fresh**: Redo from Step 7 (Starting System)

---

## 🔐 Security Reminders

Before going to production:

- [ ] Change default admin password
- [ ] Generate new JWT secrets
- [ ] Use HTTPS (not HTTP)
- [ ] Use real Ethereum network (not Ganache)
- [ ] Enable firewall
- [ ] Regular database backups
- [ ] Update all dependencies
- [ ] Security audit of smart contracts

---

## ✨ Final Checklist

Before considering setup complete:

- [ ] All 4 terminals running without errors
- [ ] Can login to admin dashboard
- [ ] Can create and manage elections
- [ ] Can register voters with biometrics
- [ ] Can start election
- [ ] Can authenticate and vote
- [ ] Can close and finalize election
- [ ] Can view results with vote counts
- [ ] Audit logs are being recorded
- [ ] No errors in any terminal

---

**Setup Time Estimate:**
- Prerequisites: 30-60 minutes (if starting fresh)
- Project Setup: 15-20 minutes
- Database Setup: 10-15 minutes
- First Launch: 5-10 minutes

**Total: 1-2 hours for complete fresh installation**

---

**System Requirements:**
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 5GB free space
- **CPU**: Any modern processor
- **OS**: macOS, Linux, or Windows (with WSL2)
- **Internet**: Required for downloading packages and Neon database

---

**Last Updated**: February 16, 2026
**For Project Version**: 1.0
**Tested On**: macOS (Apple Silicon & Intel), Ubuntu 22.04, Windows 11 (WSL2)
