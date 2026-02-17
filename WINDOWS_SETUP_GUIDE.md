# Blockchain Voting System - Windows Setup Guide

## 🪟 Windows-Specific Installation Guide

This guide is specifically for setting up the Blockchain Voting System on Windows 10/11.

---

## Prerequisites Installation

### 1. Install Node.js

**Download and Install:**
1. Go to https://nodejs.org/
2. Download the **LTS version** (v18.x or higher)
3. Run the installer (`.msi` file)
4. **Important**: Check "Add to PATH" during installation
5. Restart your terminal after installation

**Verify:**
```powershell
node --version
npm --version
```

### 2. Install Python

**Download and Install:**
1. Go to https://www.python.org/downloads/
2. Download Python 3.11 or higher
3. Run the installer
4. **CRITICAL**: Check "Add Python to PATH" at the bottom of the installer
5. Click "Install Now"

**Verify:**
```powershell
python --version
pip --version
```

**If `python` command doesn't work, try:**
```powershell
python3 --version
py --version
```

### 3. Install Git

**Download and Install:**
1. Go to https://git-scm.com/download/win
2. Download Git for Windows
3. Run the installer
4. Use default settings (recommended)

**Verify:**
```powershell
git --version
```

### 4. Install PostgreSQL (Optional - if not using Neon)

**Download and Install:**
1. Go to https://www.postgresql.org/download/windows/
2. Download PostgreSQL 16
3. Run the installer
4. Remember the password you set for the `postgres` user
5. Default port: 5432

### 5. Install Ganache

**Option A: Ganache CLI (Recommended)**
```powershell
npm install -g ganache
```

**Verify:**
```powershell
ganache --version
```

**Option B: Ganache GUI**
1. Go to https://trufflesuite.com/ganache/
2. Download Ganache for Windows
3. Install and run

---

## Project Setup

### 1. Copy Project Files

Copy the `Maj` folder to your desired location. Example:
```
C:\Users\YourName\Maj\
```

**Open PowerShell in the project directory:**
1. Navigate to `C:\Users\YourName\Maj`
2. Shift + Right-click in the folder
3. Select "Open PowerShell window here"

Or:
```powershell
cd C:\Users\YourName\Maj
```

---

## Backend Setup

### 1. Navigate to Backend
```powershell
cd backend
```

### 2. Create Virtual Environment
```powershell
python -m venv .venv
```

**If `python` doesn't work, try:**
```powershell
python3 -m venv .venv
# OR
py -m venv .venv
```

### 3. Activate Virtual Environment

**PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
.venv\Scripts\activate.bat
```

**You should see `(.venv)` in your prompt**

### 4. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

This will take 2-5 minutes. Wait for it to complete.

### 5. Create .env File

Copy the example:
```powershell
copy .env.example .env
```

**Edit `.env` file** (use Notepad or VS Code):
```powershell
notepad .env
```

### 6. Generate Secrets

**In PowerShell (with virtual environment active):**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Run this 4 times and use the outputs for:
- `JWT_SECRET`
- `VOTING_SESSION_SECRET`
- `BIOMETRIC_SALT_PEPPER`
- `BLOCKCHAIN_PEPPER`

**Example `.env` configuration:**
```env
# Database - Using Neon (Cloud)
DATABASE_URL=postgresql://your_neon_connection_string

# Blockchain - Local Ganache
GANACHE_URL=http://localhost:8545
GANACHE_NETWORK_ID=1337

# Secrets (generate your own!)
JWT_SECRET=YOUR_GENERATED_SECRET_1
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

VOTING_SESSION_SECRET=YOUR_GENERATED_SECRET_2
BIOMETRIC_SALT_PEPPER=YOUR_GENERATED_SECRET_3
BIOMETRIC_ENCRYPTION_KEY=YOUR_GENERATED_SECRET_4
BLOCKCHAIN_PEPPER=YOUR_GENERATED_SECRET_5

# Face Recognition
FACE_MODEL=ArcFace
FACE_THRESHOLD=0.68

# Security
MAX_AUTH_ATTEMPTS=3
SESSION_TIMEOUT_SECONDS=120
LOCKOUT_DURATION_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 7. Verify Backend Setup
```powershell
python -c "from app.database import Base; print('✓ Backend setup OK')"
```

---

## Frontend Setup

### 1. Open New PowerShell Window

Navigate to frontend:
```powershell
cd C:\Users\YourName\Maj\frontend
```

### 2. Install Dependencies
```powershell
npm install
```

This will take 2-5 minutes.

### 3. Create .env File
```powershell
echo REACT_APP_API_URL=http://localhost:8000 > .env
```

Or manually create `.env` file:
```env
REACT_APP_API_URL=http://localhost:8000
```

---

## Smart Contracts Setup

### 1. Open New PowerShell Window

Navigate to contracts:
```powershell
cd C:\Users\YourName\Maj\contracts
```

### 2. Install Dependencies
```powershell
npm install
```

### 3. Compile Contracts
```powershell
npx truffle compile
```

Should show: "Compiled successfully"

---

## Database Setup

### Option A: Neon (Cloud - Recommended for Windows)

**Advantages:**
- No local PostgreSQL installation needed
- Always accessible
- Automatic backups

**Steps:**
1. Go to https://neon.tech
2. Sign up for free account
3. Create new project: "Voting System"
4. Copy the connection string
5. Update `backend\.env`:
   ```env
   DATABASE_URL=postgresql://your_neon_user:password@your_neon_host/neondb?sslmode=require
   ```

**Run Database Schema:**

You'll need `psql` command-line tool. Two options:

**Option 1: Use Neon SQL Editor (Easy)**
1. Go to your Neon project dashboard
2. Click "SQL Editor"
3. Copy entire contents of `database\schema.sql`
4. Paste and run in SQL Editor

**Option 2: Install psql on Windows**
```powershell
# Install PostgreSQL (includes psql)
# Then run:
psql "your_neon_connection_string" -f database\schema.sql
```

### Option B: Local PostgreSQL

**If you installed PostgreSQL earlier:**

1. **Open SQL Shell (psql)** from Start Menu

2. **Create Database:**
```sql
CREATE DATABASE voting_db;
CREATE USER voting_user WITH PASSWORD 'voting_password';
GRANT ALL PRIVILEGES ON DATABASE voting_db TO voting_user;
```

3. **Exit and reconnect as voting_user:**
```powershell
psql -U voting_user -d voting_db
```

4. **Run Schema:**
```sql
\i 'C:/Users/YourName/Maj/database/schema.sql'
```

**Note:** Use forward slashes `/` in the path, not backslashes!

5. **Update `backend\.env`:**
```env
DATABASE_URL=postgresql://voting_user:voting_password@localhost:5432/voting_db
```

---

## Create Admin User

### Method 1: Python Script (Recommended)

Create `create_admin.py` in backend folder:

```python
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.admin import Admin, AdminRole
from app.services.crypto import hash_password
import uuid

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        existing = db.query(Admin).filter(Admin.username == "super_admin").first()
        if existing:
            print("❌ Admin user already exists")
            return

        # Create admin
        admin = Admin(
            id=uuid.uuid4(),
            username="super_admin",
            password_hash=hash_password("Admin@123"),
            full_name="Super Administrator",
            role=AdminRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created successfully!")
        print("   Username: super_admin")
        print("   Password: Admin@123")
        print("   ⚠️  Change this password after first login!")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
```

**Run the script:**
```powershell
cd backend
.venv\Scripts\Activate.ps1
python create_admin.py
```

### Method 2: Direct SQL

Run this in your database:

```sql
INSERT INTO admins (id, username, password_hash, full_name, role, is_active)
VALUES (
    gen_random_uuid(),
    'super_admin',
    'YOUR_HASHED_PASSWORD',  -- Generate using Python script
    'Super Administrator',
    'super_admin',
    true
);
```

---

## Starting the System

You need **3 PowerShell windows** open simultaneously.

### PowerShell 1: Ganache

```powershell
ganache --networkId 1337 --port 8545
```

**Should show:**
- "Listening on 127.0.0.1:8545"
- List of 10 accounts with private keys

**Leave this running!**

### PowerShell 2: Backend

```powershell
cd C:\Users\YourName\Maj\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Should show:**
- "Application startup complete"
- "Uvicorn running on http://0.0.0.0:8000"

**Leave this running!**

### PowerShell 3: Frontend

```powershell
cd C:\Users\YourName\Maj\frontend
npm start
```

**Should:**
- Open browser automatically to http://localhost:3000
- Show "Compiled successfully!"

**Leave this running!**

### PowerShell 4: Deploy Contracts (One-time)

**Before starting backend, deploy contracts:**

```powershell
cd C:\Users\YourName\Maj\contracts
npx truffle migrate --network development
```

**Should show:**
- 4 contract addresses
- Network ID: 1337

**Important:** Run this AFTER starting Ganache but BEFORE starting backend!

---

## Verification

### 1. Test Ganache

**PowerShell:**
```powershell
curl -X POST http://127.0.0.1:8545 `
  -H "Content-Type: application/json" `
  -Body '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
```

**Expected:** `{"jsonrpc":"2.0","id":1,"result":"1337"}`

### 2. Test Backend

**PowerShell:**
```powershell
curl http://localhost:8000/api/health
```

**Expected:** `{"status":"healthy"}`

### 3. Test Frontend

Open browser: http://localhost:3000

**Should see:** Login page

### 4. Test Login

- Username: `super_admin`
- Password: `Admin@123`

**Should see:** Admin Dashboard

---

## Troubleshooting

### "Python not found"

**Fix:**
```powershell
# Find Python installation
where python
where py

# Use the correct one
py -m venv .venv
```

### "Activate.ps1 cannot be loaded"

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Port 8545 already in use"

**Fix:**
```powershell
# Find process using port
netstat -ano | findstr :8545

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### "Port 8000 already in use"

**Fix:**
```powershell
# Find and kill
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "Port 3000 already in use"

**Fix:**
```powershell
# Find and kill
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### "npm ERR! code ENOENT"

**Fix:**
```powershell
# Delete node_modules and reinstall
rmdir /s node_modules
del package-lock.json
npm install
```

### "uvicorn: command not found"

**Fix:**
```powershell
# Make sure virtual environment is activated
.venv\Scripts\Activate.ps1

# Reinstall uvicorn
pip install uvicorn
```

### "Cannot connect to database"

**For Neon:**
- Check internet connection
- Verify connection string in `.env`
- Neon may pause free tier databases - just retry

**For Local PostgreSQL:**
- Check if PostgreSQL service is running:
  ```powershell
  # In Services (services.msc), look for "postgresql-x64-16"
  # Or restart from command line
  net start postgresql-x64-16
  ```

---

## Windows-Specific Notes

### File Paths
- Use `\` for file paths in Windows commands
- Use `/` for file paths in PostgreSQL commands
- Use `/` in `.env` file paths

### Virtual Environment
- Activation script is `.venv\Scripts\Activate.ps1` (PowerShell)
- Or `.venv\Scripts\activate.bat` (Command Prompt)
- NOT `source .venv/bin/activate` (that's for Linux/Mac)

### Line Endings
If you get errors about line endings:
```powershell
git config --global core.autocrlf true
```

### Firewall
Windows Firewall may block ports. If services can't connect:
1. Search for "Windows Defender Firewall"
2. Click "Advanced settings"
3. Add inbound rules for ports 3000, 8000, 8545

---

## Quick Start Summary

**One-time setup:**
1. Install prerequisites (Node.js, Python, Git, Ganache)
2. Copy project files
3. Setup backend (virtual env, pip install, .env)
4. Setup frontend (npm install, .env)
5. Setup contracts (npm install, compile)
6. Setup database (Neon or local)
7. Create admin user
8. Deploy contracts

**Every time you run the system:**
1. Start Ganache: `ganache --networkId 1337 --port 8545`
2. Start Backend: `cd backend`, activate venv, `uvicorn app.main:app --reload`
3. Start Frontend: `cd frontend`, `npm start`
4. Open http://localhost:3000

---

## Alternative: WSL2 (Windows Subsystem for Linux)

If you're comfortable with Linux, you can use WSL2 and follow the macOS/Linux guide instead.

**Install WSL2:**
```powershell
wsl --install
```

Then follow the Linux setup instructions from `NEW_MACHINE_SETUP.md`.

---

## System Requirements

- **OS**: Windows 10/11
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 5GB free space
- **CPU**: Any modern processor
- **Internet**: Required for Neon database and package downloads

---

## Next Steps

1. Follow this guide step-by-step
2. Use `SETUP_CHECKLIST.txt` to track progress
3. If issues arise, check `TROUBLESHOOTING_CHECKLIST.md`
4. Once running, see `MANUAL_SETUP_GUIDE.md` for how to use the system

---

**Estimated Setup Time**: 1-2 hours

**Version**: 1.0
**Last Updated**: February 16, 2026
**Tested On**: Windows 10, Windows 11
