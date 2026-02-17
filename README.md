# Blockchain-Based Voting System with Biometric Authentication

A secure, transparent, and tamper-proof electronic voting system that combines blockchain technology with biometric authentication (face recognition and fingerprint) to ensure voter identity verification and vote immutability.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-blue)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.19-orange)](https://soliditylang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [System Requirements](#-system-requirements)
- [Project Structure](#-project-structure)
- [Ports & Services](#-ports--services)
- [Installation Guide](#-installation-guide)
  - [Step 1: Prerequisites](#step-1-install-prerequisites)
  - [Step 2: Clone Repository](#step-2-clone-repository)
  - [Step 3: Backend Setup](#step-3-backend-setup)
  - [Step 4: Frontend Setup](#step-4-frontend-setup)
  - [Step 5: Database Setup](#step-5-database-setup)
  - [Step 6: Blockchain Setup](#step-6-blockchain-setup)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Complete Application Flow](#-complete-application-flow)
- [Demo Walkthrough](#-demo-walkthrough)
- [API Documentation](#-api-documentation)
- [Security Features](#-security-features)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Contributing](#-contributing)

---

## 🎯 Overview

This system implements all 41 functional requirements for a complete blockchain-based voting platform with:

- **✅ Biometric Authentication**: Face recognition (primary) and fingerprint (fallback)
- **✅ Blockchain Integration**: Immutable vote storage on Ethereum-compatible blockchain
- **✅ Smart Contracts**: Solidity contracts for voter registration, voting, and tallying
- **✅ Admin Portal**: Web interface for election management
- **✅ Polling Booth**: Public interface for voter authentication and voting
- **✅ Audit Trail**: Complete transparency with append-only logs
- **✅ Security**: AES-256 encryption, SHA-256 hashing, JWT authentication

---

## ✨ Features

### **🔐 Voter Registration Module (FR 1)**
✅ Admin-authorized voter registration
✅ Voter details capture (ID, name, age, constituency)
✅ Face image capture & embedding extraction (OpenCV, 128×128)
✅ Fingerprint capture & template processing (Gabor filters + minutiae)
✅ AES-256-GCM encryption for biometric data
✅ SHA-256 hashing for integrity verification
✅ Duplicate prevention (unique voter IDs)
✅ Blockchain voter ID linking (Keccak256)

### **🔍 Voter Authentication Module (FR 2)**
✅ Face recognition (68% similarity threshold)
✅ Live face comparison with stored embeddings
✅ Fingerprint fallback authentication (75% threshold)
✅ Voter details display after authentication
✅ Multiple authentication attempt tracking
✅ Account lockout (3 failed attempts → 30-minute lockout)

### **✅ Voter Verification & Confirmation (FR 3)**
✅ Display authenticated voter details
✅ Explicit identity confirmation required
✅ Authentication event logging (append-only)

### **🗳️ Voting Interface Module (FR 4)**
✅ Constituency-based candidate display
✅ Single candidate selection
✅ Final confirmation prompt
✅ Vote modification prevention

### **⛓️ Blockchain Vote Recording Module (FR 5)**
✅ Vote recording on Ganache blockchain
✅ Smart contract immutable storage
✅ One vote per voter enforcement
✅ Vote anonymity (hashed voter IDs)
✅ Voter marked as "voted"
✅ Double voting prevention

### **📜 Smart Contract Management (FR 6)**
✅ Voter eligibility verification contract
✅ Vote recording contract
✅ Election result tallying contract
✅ Access control (authorized officials only)
✅ Election lifecycle control (start/end times)

### **📊 Audit & Transparency Module (FR 7)**
✅ Immutable authentication logs
✅ Vote submission timestamp logs
✅ Officials can verify vote counts
✅ Public auditability without voter identity

### **👨‍💼 Admin & Election Management Module (FR 8)**
✅ Create and manage elections
✅ Add candidates
✅ Configure voting periods
✅ Role-based access control (4 admin roles)
✅ Real-time and post-election reports

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                         │
├────────────────────────────┬────────────────────────────────────┤
│   Admin Portal (React)     │   Polling Booth (React)            │
│   Port: 3000               │   Port: 3000                       │
│   - Admin Login            │   - Voter Authentication           │
│   - Voter Registration     │   - Face/Fingerprint Capture       │
│   - Election Management    │   - Vote Casting                   │
│   - Audit Logs             │   - Result Display                 │
└────────────┬───────────────┴────────────┬───────────────────────┘
             │                            │
             │      HTTP REST API         │
             │      (Port 8000)           │
             │                            │
┌────────────┴────────────────────────────┴───────────────────────┐
│                    BACKEND (FastAPI)                            │
│                    Port: 8000                                   │
├─────────────────────────────────────────────────────────────────┤
│  📡 Routers           🔧 Services              🛡️ Middleware     │
│  ├─ auth.py          ├─ biometric/            ├─ JWT Auth       │
│  ├─ voters.py        │  ├─ face.py            ├─ RBAC           │
│  ├─ voting.py        │  └─ fingerprint.py     ├─ CORS           │
│  ├─ elections.py     ├─ blockchain.py         └─ Error Handler  │
│  └─ candidates.py    └─ crypto.py                               │
└──────┬─────────────────────────┬──────────────────┬─────────────┘
       │                         │                  │
   ┌───┴────────┐         ┌──────┴──────┐    ┌─────┴─────────┐
   │ PostgreSQL │         │   Ganache   │    │    Smart      │
   │  Database  │         │ Blockchain  │    │  Contracts    │
   │ Port: 5432 │         │ Port: 8545  │    │  (Solidity)   │
   │ (or Neon)  │         │             │    │  - Registry   │
   └────────────┘         └─────────────┘    │  - Booth      │
                                             │  - Tallier    │
                                             │  - Controller │
                                             └───────────────┘
```

---

## 💻 Technology Stack

### **Frontend**
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18.2 |
| Routing | React Router | v6 |
| HTTP Client | Axios | 1.6+ |
| Styling | CSS3 | Custom |
| Build Tool | Create React App | 5.0+ |

### **Backend**
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.104+ |
| Language | Python | 3.11+ |
| Web Server | Uvicorn | 0.24+ |
| ORM | SQLAlchemy | 2.0+ |
| Auth | JWT (PyJWT) | 2.8+ |
| Password Hash | Argon2 | Latest |

### **Biometric Processing**
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Face Recognition | OpenCV 4.8+ | HOG + Face Detection |
| Face Features | NumPy | Embedding extraction (128×128) |
| Fingerprint | OpenCV | Gabor filters + Minutiae |
| Image Processing | PIL/Pillow | Image manipulation |

### **Blockchain**
| Component | Technology | Version |
|-----------|-----------|---------|
| Platform | Ethereum | Compatible |
| Development | Ganache | Latest |
| Contracts | Solidity | 0.8.19 |
| Web3 Library | Web3.py | 6.0+ |

### **Database**
| Component | Technology | Version |
|-----------|-----------|---------|
| DBMS | PostgreSQL | 16+ |
| Cloud Option | Neon | Serverless |
| Pool Manager | SQLAlchemy | Built-in |

### **Security**
| Feature | Technology |
|---------|-----------|
| Biometric Encryption | AES-256-GCM |
| Biometric Hashing | SHA-256 |
| Blockchain IDs | Keccak256 |
| Passwords | Argon2id |

---

## 🔧 System Requirements

### **Hardware Requirements**
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Dual-core 2.0GHz | Quad-core 2.5GHz+ |
| RAM | 4GB | 8GB+ |
| Storage | 2GB free | 5GB+ free |
| Webcam | 720p | 1080p |
| Fingerprint Scanner | Optional | USB scanner |

### **Software Requirements**

#### **Required**
- **Operating System**:
  - macOS 10.15+ (Catalina or later)
  - Ubuntu 20.04+ / Debian 11+
  - Windows 10+ (with WSL2)

- **Python**: 3.11 or 3.12
- **Node.js**: 16.0+
- **npm**: 7.0+
- **Git**: 2.0+

#### **Optional**
- **PostgreSQL**: 16+ (if using local DB instead of Neon)
- **Docker**: For containerized deployment
- **Ganache GUI**: For visual blockchain management

### **Browser Compatibility**
- ✅ Chrome 90+ (Recommended)
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

---

## 📁 Project Structure

```
/Users/work/Maj/                        # Project root
│
├── 📂 backend/                         # Backend (FastAPI) - Port 8000
│   ├── 📂 app/
│   │   ├── 📂 routers/                # API Endpoints
│   │   │   ├── auth.py               # Admin authentication
│   │   │   ├── voters.py             # Voter registration (FR 1)
│   │   │   ├── voting.py             # Authentication & voting (FR 2, 4, 5)
│   │   │   ├── elections.py          # Election management (FR 8)
│   │   │   └── candidates.py         # Candidate management (FR 8)
│   │   │
│   │   ├── 📂 services/               # Business Logic
│   │   │   ├── 📂 biometric/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── face.py          # OpenCV face recognition (FR 1.3, 2.2)
│   │   │   │   └── fingerprint.py   # Fingerprint processing (FR 1.4, 2.6)
│   │   │   ├── blockchain.py        # Web3 integration (FR 5, 6)
│   │   │   └── crypto.py            # Encryption & hashing (FR 1.6)
│   │   │
│   │   ├── 📂 middleware/             # Middleware
│   │   │   └── auth.py              # JWT auth, RBAC (FR 8.3)
│   │   │
│   │   ├── 📂 models/                 # SQLAlchemy ORM
│   │   │   ├── voter.py
│   │   │   ├── election.py
│   │   │   └── admin.py
│   │   │
│   │   ├── 📂 schemas/                # Pydantic Validation
│   │   │   ├── voter.py
│   │   │   ├── election.py
│   │   │   └── auth.py
│   │   │
│   │   ├── config.py                 # Settings (Pydantic)
│   │   ├── database.py               # DB connection pool
│   │   └── main.py                   # FastAPI app entry
│   │
│   ├── requirements.txt               # Python dependencies
│   ├── .env                          # Environment variables
│   ├── check_voters.py               # Utility: List all voters
│   ├── diagnose_embedding.py         # Utility: Debug face embeddings
│   └── delete_voter.py               # Utility: Remove voter
│
├── 📂 frontend/                        # Frontend (React) - Port 3000
│   ├── 📂 public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── 📂 src/
│   │   ├── 📂 pages/
│   │   │   ├── Login.jsx            # Admin login
│   │   │   ├── AdminDashboard.jsx   # Admin home (FR 8)
│   │   │   ├── VoterRegistration.jsx # Register voters (FR 1)
│   │   │   ├── ElectionManager.jsx  # Manage elections (FR 8)
│   │   │   ├── PollingBooth.jsx     # Voter auth & voting (FR 2, 3, 4)
│   │   │   └── AuditViewer.jsx      # View audit logs (FR 7)
│   │   │
│   │   ├── 📂 services/
│   │   │   └── api.js               # Axios API client
│   │   │
│   │   ├── App.jsx                  # Main app component
│   │   ├── App.css                  # Global styles
│   │   └── index.js                 # React entry point
│   │
│   ├── package.json                  # npm dependencies
│   ├── .env                          # Frontend config
│   └── package-lock.json
│
├── 📂 blockchain/                      # Smart Contracts
│   ├── 📂 contracts/
│   │   ├── ElectionController.sol   # Election lifecycle (FR 6.3)
│   │   ├── VoterRegistry.sol        # Voter eligibility (FR 6.1)
│   │   ├── VotingBooth.sol          # Vote recording (FR 5.1, 6.1)
│   │   └── ResultsTallier.sol       # Vote tallying (FR 6.1)
│   │
│   ├── 📂 build/                     # Compiled contracts (JSON ABI)
│   │   └── contracts/
│   │       ├── ElectionController.json
│   │       ├── VoterRegistry.json
│   │       ├── VotingBooth.json
│   │       └── ResultsTallier.json
│   │
│   └── 📂 migrations/                # Deployment scripts
│       └── 2_deploy_contracts.js
│
├── 📂 database/                        # Database Schema
│   ├── schema.sql                   # Full PostgreSQL schema
│   │                                # - 9 tables
│   │                                # - Triggers
│   │                                # - Constraints
│   │                                # - Indexes
│   └── 📂 migrations/
│       └── 001_make_fingerprint_optional.sql
│
├── 📂 docs/                           # Documentation
│   ├── DEMO_GUIDE.md               # 30-minute full demo
│   ├── START_DEMO.md               # 5-minute quick start
│   ├── MANUAL_STARTUP.md           # Service startup guide
│   └── REQUIREMENTS_AUDIT.md       # All 41 requirements ✅
│
├── 📜 Scripts
│   ├── start_all.sh                 # Start all services
│   ├── stop_all.sh                  # Stop all services
│   └── check_status.sh              # Verify services
│
└── 📄 README.md                       # This file
```

---

## 🌐 Ports & Services

| Service | Port | URL | Purpose | Status Check |
|---------|------|-----|---------|--------------|
| **Frontend** | 3000 | http://localhost:3000 | React web UI | `curl http://localhost:3000` |
| **Backend** | 8000 | http://localhost:8000 | FastAPI REST API | `curl http://localhost:8000/docs` |
| **API Docs** | 8000 | http://localhost:8000/docs | Swagger UI | Opens in browser |
| **Ganache** | 8545 | http://localhost:8545 | Blockchain RPC | `curl -X POST http://localhost:8545 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'` |
| **PostgreSQL** | 5432 | localhost:5432 | Database | `psql -h localhost -p 5432 -U voting_user -d voting_db` |

**Firewall Rules (if needed):**
```bash
# Allow incoming on these ports
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # Backend
sudo ufw allow 8545/tcp  # Ganache (if external access needed)
```

---

## 📥 Installation Guide

### **Step 1: Install Prerequisites**

#### **macOS**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Node.js
brew install node@18

# Verify installations
python3.11 --version  # Should show 3.11.x
node --version        # Should show 18.x or higher
npm --version         # Should show 9.x or higher
```

#### **Ubuntu/Debian**
```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
python3.11 --version
node --version
npm --version
```

#### **Windows** (Using WSL2 - Recommended)
```bash
# Install WSL2 (PowerShell as Administrator)
wsl --install

# Inside WSL2, follow Ubuntu/Debian instructions above
```

---

### **Step 2: Clone Repository**

```bash
# Navigate to your workspace
cd ~

# Clone the repository
git clone <repository-url> Maj
cd Maj

# Or if already cloned
cd /Users/work/Maj
```

---

### **Step 3: Backend Setup**

```bash
# Navigate to backend directory
cd /Users/work/Maj/backend

# Create Python virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate     # macOS/Linux
# OR
venv\Scripts\activate        # Windows

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "
import fastapi
import sqlalchemy
import cv2
import web3
print('✅ All backend dependencies installed successfully!')
"
```

**Backend Dependencies (requirements.txt):**
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]
passlib[argon2]
python-multipart
web3>=6.0.0
opencv-python>=4.8.0
numpy>=1.24.0
Pillow>=10.0.0
structlog>=23.0.0
```

---

### **Step 4: Frontend Setup**

```bash
# Navigate to frontend directory
cd /Users/work/Maj/frontend

# Install npm dependencies
npm install

# Verify installation
npm list react react-router-dom axios
```

**Frontend Dependencies (package.json):**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.18.0",
    "axios": "^1.6.0"
  }
}
```

---

### **Step 5: Database Setup**

#### **Option A: Use Neon (Cloud - Recommended, No Installation)**

Database is pre-configured in `.env` file. No local installation needed!

**Verify connection:**
```bash
cd /Users/work/Maj/backend
source venv/bin/activate

python -c "
from sqlalchemy import create_engine, text
from app.config import settings
engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connected successfully!')
"
```

#### **Option B: Install PostgreSQL Locally**

**macOS:**
```bash
# Install PostgreSQL 16
brew install postgresql@16

# Start PostgreSQL service
brew services start postgresql@16

# Create database and user
createdb voting_db
psql voting_db -c "CREATE USER voting_user WITH PASSWORD 'voting_password';"
psql voting_db -c "GRANT ALL PRIVILEGES ON DATABASE voting_db TO voting_user;"

# Import schema
psql -U voting_user -d voting_db -f /Users/work/Maj/database/schema.sql

# Update .env to use local database
# DATABASE_URL=postgresql://voting_user:voting_password@localhost:5432/voting_db
```

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt install postgresql-16

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE voting_db;"
sudo -u postgres psql -c "CREATE USER voting_user WITH PASSWORD 'voting_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE voting_db TO voting_user;"

# Import schema
sudo -u postgres psql -U voting_user -d voting_db -f database/schema.sql
```

---

### **Step 6: Blockchain Setup (Ganache)**

#### **Option A: Ganache CLI (Recommended)**

```bash
# Install globally
npm install -g ganache-cli

# Verify installation
ganache-cli --version

# Start Ganache (keep running)
ganache-cli --port 8545 --networkId 1337 --deterministic

# Expected output:
# Ganache CLI v6.x.x
# Available Accounts
# ==================
# (0) 0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1 (100 ETH)
# ...
# Listening on 127.0.0.1:8545
```

#### **Option B: Ganache GUI**

1. Download from: https://trufflesuite.com/ganache/
2. Install the application
3. Open Ganache
4. Click "New Workspace"
5. Configure:
   - **Server**: Hostname: `127.0.0.1`, Port: `8545`
   - **Chain**: Network ID: `1337`
6. Click "Save & Restart"

---

## ⚙️ Configuration

### **Backend Environment Variables**

Edit `/Users/work/Maj/backend/.env`:

```bash
# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# Neon Cloud PostgreSQL (Default - No installation needed)
DATABASE_URL=postgresql://neondb_owner:npg_VMlKaojFt12Z@ep-winter-frog-aiibm9k9-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Local PostgreSQL (Uncomment if using local database)
# DATABASE_URL=postgresql://voting_user:voting_password@localhost:5432/voting_db

# ============================================================================
# BLOCKCHAIN CONFIGURATION
# ============================================================================
GANACHE_URL=http://localhost:8545
GANACHE_NETWORK_ID=1337

# ============================================================================
# JWT AUTHENTICATION
# ============================================================================
JWT_SECRET=your-secret-key-minimum-32-characters-long-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================================================
# VOTING SESSION
# ============================================================================
VOTING_SESSION_SECRET=your-voting-session-secret-change-in-production

# ============================================================================
# BIOMETRIC SECURITY
# ============================================================================
BIOMETRIC_SALT_PEPPER=your-biometric-pepper-change-in-production
BIOMETRIC_ENCRYPTION_KEY=exactly-32-characters-for-aes!!  # MUST BE 32 CHARS
FACE_MODEL=ArcFace
FACE_THRESHOLD=0.68              # 68% similarity required
FINGERPRINT_SDK=opencv
FINGERPRINT_THRESHOLD=0.75       # 75% similarity required

# ============================================================================
# BLOCKCHAIN PEPPER
# ============================================================================
BLOCKCHAIN_PEPPER=your-blockchain-pepper-change-in-production

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
MAX_AUTH_ATTEMPTS=3              # Failed attempts before lockout
SESSION_TIMEOUT_SECONDS=120      # 2 minutes
LOCKOUT_DURATION_MINUTES=30      # Account lockout duration

# ============================================================================
# REDIS (Optional - for session management)
# ============================================================================
REDIS_URL=redis://localhost:6379/0

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                  # json or text

# ============================================================================
# CORS (Add additional origins as needed)
# ============================================================================
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### **Frontend Environment Variables**

Edit `/Users/work/Maj/frontend/.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
```

---

## 🚀 Running the Application

### **Quick Start (All Services at Once)**

```bash
# From project root
cd /Users/work/Maj

# Make scripts executable (first time only)
chmod +x start_all.sh stop_all.sh check_status.sh

# Start all services
./start_all.sh

# Wait 10-15 seconds for services to start...

# Check status
./check_status.sh

# Expected output:
# ✅ Backend (FastAPI):    http://localhost:8000 - RUNNING
# ✅ Frontend (React):     http://localhost:3000 - RUNNING
# ✅ Blockchain (Ganache): http://localhost:8545 - RUNNING
# ✅ Database (PostgreSQL): CONNECTED

# When done, stop all services
./stop_all.sh
```

---

### **Manual Startup (Detailed Control)**

**Terminal 1: Ganache (Blockchain)**
```bash
ganache-cli --port 8545 --networkId 1337 --deterministic
```
**✅ Keep this terminal open!**

**Terminal 2: Backend (FastAPI)**
```bash
cd /Users/work/Maj/backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# [timestamp] [info] blockchain_connected url=http://localhost:8545
# [timestamp] [info] contracts_loaded
# INFO:     Application startup complete.
```
**✅ Keep this terminal open!**

**Terminal 3: Frontend (React)**
```bash
cd /Users/work/Maj/frontend
npm start

# Expected output:
# Compiled successfully!
# You can now view blockchain-voting-frontend in the browser.
#   Local:            http://localhost:3000
```
**✅ Browser will open automatically!**

---

## 🎬 Complete Application Flow

### **📋 Overview of Complete Workflow**

```
Phase 1: Admin Setup → Phase 2: Voter Registration → Phase 3: Election Start →
Phase 4: Voting → Phase 5: Results & Audit
```

### **Phase 1: Admin Setup (5 minutes)**

#### **1.1 Admin Login**
1. Open: http://localhost:3000/login
2. Credentials:
   - Username: `superadmin`
   - Password: `Admin@123456`
3. Click "Login"
4. **✅ Result**: Redirected to Admin Dashboard

#### **1.2 Create Election**
1. Click "Create Election"
2. Fill form:
   - Name: `2026 General Election`
   - Description: `National parliamentary election`
   - Start Date: Tomorrow 9:00 AM
   - End Date: Tomorrow 6:00 PM
3. Click "Create"
4. **✅ Result**: Election created with status "draft"

#### **1.3 Add Constituencies**
1. Go to "Manage Constituencies"
2. Add Constituency 1:
   - Name: `Hyderabad Central`
   - Code: `HYD`
   - On-Chain ID: `0`
3. Add Constituency 2:
   - Name: `Delhi North`
   - Code: `DEL`
   - On-Chain ID: `1`
4. **✅ Result**: 2 constituencies created

#### **1.4 Add Candidates**
**For Hyderabad Central:**
1. Name: `Rajesh Kumar`, Party: `Progressive Party`, ID: `0`
2. Name: `Priya Sharma`, Party: `Democratic Alliance`, ID: `1`

**For Delhi North:**
3. Name: `Amit Singh`, Party: `Progressive Party`, ID: `2`
4. Name: `Neha Gupta`, Party: `Democratic Alliance`, ID: `3`

**✅ Result**: 4 candidates added

---

### **Phase 2: Voter Registration (10 minutes)**

#### **2.1 Register First Voter**
1. Go to: http://localhost:3000/admin/voters
2. Click "Register New Voter"
3. Fill details:
   ```
   Voter ID: DEMO001
   Full Name: John Doe
   Date of Birth: 1995-01-15
   Age: (auto-calculated: 31)
   Address: 123 Main St, Hyderabad
   Constituency: Hyderabad Central (HYD)
   ```

4. **Capture Face:**
   - Click "Capture Face"
   - Allow webcam access
   - Position face (well-lit, centered, clear)
   - Click "Take Photo"
   - **✅ Preview**: Photo appears clearly

5. **Fingerprint (Optional):**
   - If you have scanner: Click "Capture Fingerprint"
   - If no scanner: Leave empty (it's optional)

6. Click "Register Voter"

7. **✅ Expected Result:**
   ```json
   {
     "message": "Voter registered successfully",
     "voter_id": "DEMO001",
     "blockchain_voter_id": "0x..."
   }
   ```

#### **2.2 Verify Registration**
```bash
cd /Users/work/Maj/backend
python check_voters.py

# Expected output:
# ✅ Found 1 registered voter(s):
# Voter ID: DEMO001
# Name: John Doe
# Constituency: Hyderabad Central
# Face: Yes
# Fingerprint: No
# Voted: No
```

#### **2.3 Verify Face Embedding Quality**
```bash
python diagnose_embedding.py DEMO001

# Expected output:
# ✅ CORRECT SIZE! Face embedding is properly formatted.
#    Decrypted data size: 16384 bytes
#    Expected size: 16384 bytes
```

#### **2.4 Register More Voters**
Repeat steps 2.1-2.3 for:
- `DEMO002` (Jane Smith, Delhi North)
- `DEMO003` (Optional: Additional voter)

---

### **Phase 3: Election Activation (3 minutes)**

#### **3.1 Deploy to Blockchain**
1. Admin Dashboard → "Elections"
2. Find "2026 General Election"
3. Click "Deploy to Blockchain"
4. Wait 30-60 seconds
5. **✅ Result**:
   ```
   Smart contracts deployed:
   - ElectionController: 0x254dff...
   - VoterRegistry: 0xe78A0F...
   - VotingBooth: 0x5b1869...
   - ResultsTallier: 0xCfEB86...
   ```

#### **3.2 Start Election**
1. Click "Start Election"
2. Confirm action
3. **✅ Result**: Status changes to "active"

---

### **Phase 4: Voting Process (5 minutes per voter)**

#### **4.1 Voter Authentication (Face Recognition)**
1. **Open NEW BROWSER TAB**: http://localhost:3000
2. Enter Voter ID: `DEMO001`
3. Click "Verify Identity"

4. **Face Authentication:**
   - Webcam activates automatically
   - **⚠️ IMPORTANT**: Use the SAME person who registered
   - Position face clearly (same lighting as registration)
   - Click "Authenticate"

5. **✅ Success Response:**
   ```
   Face authentication successful!
   Similarity: 0.72 (threshold: 0.68)
   Welcome, John Doe
   Constituency: Hyderabad Central
   ```

6. **❌ Failure Response (if different person):**
   ```
   Face authentication failed. 2 attempt(s) remaining.
   [Button: Try Fingerprint Authentication]
   ```

#### **4.2 Fingerprint Fallback (If Face Fails)**
1. Click "Try Fingerprint Authentication"
2. Scan fingerprint or upload fingerprint image
3. Click "Authenticate"
4. **✅ Success**: Proceeds to voting

#### **4.3 Cast Vote**
1. After successful authentication:
   - You see: "Candidates for Hyderabad Central"
   - Options:
     - ⚪ Rajesh Kumar (Progressive Party)
     - ⚪ Priya Sharma (Democratic Alliance)

2. Select one candidate (radio button)
3. Click "Cast Vote"
4. Confirm: "Yes, Cast My Vote"

5. **✅ Success:**
   ```
   Vote cast successfully!
   Transaction Hash: 0x...
   Thank you for voting!
   ```

#### **4.4 Test Double Voting Prevention**
1. Refresh page or try to vote again with `DEMO001`
2. **✅ Expected:**
   ```
   ❌ You have already cast your vote in this election.
   ```

**Backend Log:**
```
vote_cast: voter_id=DEMO001, candidate_id=0
blockchain_transaction: tx_hash=0x...
voter_marked_as_voted: voter_id=DEMO001, has_voted=true
```

---

### **Phase 5: Results & Audit (5 minutes)**

#### **5.1 Cast Additional Votes**
Repeat Phase 4 with:
- `DEMO002` (vote for different candidate in Delhi North)

#### **5.2 Close Election**
1. Admin Dashboard → Elections
2. Click "Close Election"
3. **✅ Result**: Status = "ended"

#### **5.3 Tally Results**
1. Click "Tally Results"
2. **✅ Blockchain Results:**
   ```
   Hyderabad Central:
     Rajesh Kumar: 1 vote
     Priya Sharma: 0 votes

   Delhi North:
     Amit Singh: 1 vote
     Neha Gupta: 0 votes

   Total Votes Cast: 2
   Turnout: 100% (2/2 registered voters)
   ```

#### **5.4 View Audit Logs**
```bash
cd /Users/work/Maj/backend
python check_auth_attempts.py

# Output:
# Time                 Voter ID  Method      Outcome   Similarity  Reason
# 2026-02-15 16:30:00  DEMO001   face        success   0.7200      N/A
# 2026-02-15 16:35:00  DEMO002   face        success   0.7100      N/A
```

#### **5.5 Verify Blockchain Records**
```bash
cd backend
python -c "
from app.services.blockchain import blockchain_service
booth = blockchain_service.voting_booth_contract
results = booth.functions.getResults().call()
print('Blockchain Vote Counts:', results)
"

# Output: [1, 0, 1, 0]  (Candidate IDs: 0, 1, 2, 3)
```

---

## 📚 API Documentation

### **Interactive API Docs**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### **Key API Endpoints**

#### **Authentication**
```http
POST   /api/auth/login              # Admin login
POST   /api/auth/refresh            # Refresh JWT token
GET    /api/auth/me                 # Get current user info
```

#### **Voter Management**
```http
POST   /api/voters/register         # Register new voter (FR 1)
GET    /api/voters                  # List all voters
GET    /api/voters/{voter_id}       # Get voter details
DELETE /api/voters/{voter_id}       # Delete voter (admin only)
```

#### **Voting**
```http
POST   /api/voting/authenticate/face              # Face auth (FR 2.2)
POST   /api/voting/authenticate/fingerprint       # Fingerprint auth (FR 2.6)
POST   /api/voting/cast-vote                      # Cast vote (FR 5.1)
GET    /api/voting/candidates/{constituency_id}   # Get candidates (FR 4.1)
```

#### **Election Management**
```http
POST   /api/elections                  # Create election (FR 8.1)
GET    /api/elections                  # List all elections
GET    /api/elections/{id}             # Get election details
PUT    /api/elections/{id}/start       # Start election (FR 6.3)
PUT    /api/elections/{id}/close       # Close election (FR 6.3)
GET    /api/elections/{id}/stats       # Get real-time stats (FR 8.4)
GET    /api/elections/{id}/results     # Get final results (FR 7.3)
```

---

## 🔒 Security Features

### **✅ All Security Requirements Implemented**

#### **Biometric Security (FR 1.6)**
- ✅ AES-256-GCM encryption for face embeddings
- ✅ AES-256-GCM encryption for fingerprint templates
- ✅ SHA-256 hashing for integrity verification
- ✅ Unique salt per voter
- ✅ System-wide pepper for additional security
- ✅ No raw biometric data stored

#### **Authentication Security (FR 2.8)**
- ✅ JWT tokens with 30-minute expiry
- ✅ 5-minute voting session tokens (one-time use)
- ✅ Argon2id password hashing (admin accounts)
- ✅ 3 failed attempts → 30-minute lockout
- ✅ IP address logging for audit
- ✅ Session token invalidation after vote

#### **Blockchain Anonymity (FR 5.4)**
- ✅ Voter ID hashed with Keccak256
- ✅ No link between blockchain ID and voter identity
- ✅ Vote events contain no voter information
- ✅ Public blockchain audit without identity exposure

#### **Database Security (FR 7.1-7.2)**
- ✅ Append-only audit tables (PostgreSQL rules)
- ✅ Foreign key constraints
- ✅ NOT NULL on critical fields
- ✅ CHECK constraints for validation
- ✅ SSL/TLS connection (Neon cloud)

---

## 🐛 Troubleshooting

### **Problem: Face Authentication Always Fails (Similarity = 0.0)**

**Diagnosis:**
```bash
cd /Users/work/Maj/backend
python diagnose_embedding.py DEMO001
```

**If shows wrong size (e.g., 23920 bytes):**
```bash
# Voter was registered with old buggy code
# Solution: Delete and re-register
python delete_voter.py DEMO001

# Then re-register via UI with correct code
```

**If shows correct size (16384 bytes):**
- ✅ Embedding is correct
- ❌ Issue: Different person during authentication
- **Solution**: Use SAME person for both registration and auth
- **Tips**:
  - Same lighting conditions
  - Face centered
  - Same distance from camera
  - Remove glasses if registered without them

---

### **Problem: Port Already in Use**

```bash
# Backend (Port 8000)
lsof -ti:8000 | xargs kill -9

# Frontend (Port 3000)
pkill -f "react-scripts start"

# Ganache (Port 8545)
pkill -f "ganache-cli"

# Then restart services
./start_all.sh
```

---

### **Problem: Database Connection Failed**

**For Neon (Cloud):**
```bash
# Check internet connection
ping -c 3 google.com

# Verify DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL

# Test connection
cd backend
python -c "
from app.config import settings
print(settings.DATABASE_URL)
"
```

**For Local PostgreSQL:**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@16

# Test connection
psql -h localhost -p 5432 -U voting_user -d voting_db -c "SELECT 1;"
```

---

### **Problem: Ganache Not Installed**

```bash
# Install Ganache CLI globally
npm install -g ganache-cli

# Verify installation
ganache-cli --version

# Start Ganache
ganache-cli --port 8545 --networkId 1337 --deterministic
```

---

### **Problem: Backend Won't Start**

```bash
# Check Python version
python3.11 --version  # Must be 3.11+

# Check if virtual environment is activated
which python  # Should show path with "venv"

# Reinstall dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Check for import errors
python -c "from app.main import app; print('✅ App loads')"

# Check logs
tail -50 /tmp/backend.log
```

---

### **Problem: Frontend Build Errors**

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Check Node version
node --version  # Must be 16.0+

# Start with verbose logging
npm start --verbose
```

---

## ❓ FAQ

**Q: Do I need a physical fingerprint scanner?**
A: No, fingerprint is optional. Face recognition alone is sufficient. You can test by uploading fingerprint images.

**Q: Can I run this without Ganache/blockchain?**
A: Yes! The system will skip blockchain operations and store votes only in the database (for testing).

**Q: How do I reset the database?**
A: Re-run the schema: `psql -U voting_user -d voting_db -f database/schema.sql`

**Q: How do I change admin password?**
A: Login as superadmin → Settings → Change Password

**Q: Can I deploy this to production?**
A: Yes, but requires:
- Use DeepFace instead of OpenCV for accuracy
- Deploy to real Ethereum network
- Set up SSL/TLS
- Use production database with backups
- Security audit required

**Q: What browsers are supported?**
A: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

**Q: How many voters can the system handle?**
A: Development: 1000+, Production (with optimization): 100,000+

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

**Code Style:**
- Python: PEP 8, use Black formatter
- JavaScript: Airbnb style, use Prettier
- Solidity: Follow Solidity style guide

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 📞 Support

- **Documentation**: Check `docs/` folder
- **Issues**: Create GitHub issue
- **Email**: support@votingsystem.com

---

## ✅ Quick Start Checklist

- [ ] Install Python 3.11+
- [ ] Install Node.js 16+
- [ ] Install Ganache CLI
- [ ] Clone repository
- [ ] Backend: `pip install -r requirements.txt`
- [ ] Frontend: `npm install`
- [ ] Configure `.env` files
- [ ] Start Ganache: `ganache-cli --port 8545 --networkId 1337`
- [ ] Start Backend: `uvicorn app.main:app --reload`
- [ ] Start Frontend: `npm start`
- [ ] Open http://localhost:3000/login
- [ ] Login: `superadmin` / `Admin@123456`
- [ ] Register voter with face capture
- [ ] Test voting flow

---

## 🎯 Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Complete | All 41 requirements satisfied |
| Frontend UI | ✅ Complete | React 18, responsive design |
| Smart Contracts | ✅ Complete | 4 contracts deployed |
| Database Schema | ✅ Complete | 9 tables with constraints |
| Face Recognition | ✅ Working | OpenCV (128×128 embeddings) |
| Fingerprint Auth | ✅ Working | OpenCV processing pipeline |
| Blockchain Integration | ✅ Working | Ganache (dev), Ethereum ready |
| Documentation | ✅ Complete | All guides available |
| Testing | ⚠️ Manual | Automated tests pending |
| Production Deploy | ⏳ Pending | SSL, real network needed |

**Version**: 1.0.0
**Last Updated**: 2026-02-15
**Requirements Satisfied**: 41/41 ✅

---

**🗳️ Built with ❤️ for secure and transparent elections**

**🚀 Ready to deploy? Check [DEMO_GUIDE.md](docs/DEMO_GUIDE.md) for complete walkthrough!**
