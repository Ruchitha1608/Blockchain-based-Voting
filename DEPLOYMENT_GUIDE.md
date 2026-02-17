# Blockchain Voting System - Production Deployment Guide

## 🚀 Deployment Stack

- **Frontend**: Vercel (React app)
- **Backend**: Render.com (FastAPI)
- **Database**: Neon PostgreSQL (already configured)
- **Blockchain**: Sepolia Testnet (Ethereum)

**Total Cost**: $0/month (Free tiers)

---

## 📋 Prerequisites

Before deploying, ensure you have:

- ✅ GitHub account (for code hosting)
- ✅ Vercel account (sign up at vercel.com)
- ✅ Render account (sign up at render.com)
- ✅ Infura or Alchemy account (for Sepolia testnet)
- ✅ Neon database (you already have this)
- ✅ Git installed locally
- ✅ Code pushed to GitHub (you already did this)

---

## Part 1: Deploy Smart Contracts to Sepolia Testnet

### Step 1.1: Get Infura API Key

1. Go to https://infura.io
2. Sign up for free account
3. Create new project: "Voting System"
4. Copy your **Project ID** (API key)
5. Save it - you'll need it later

**Alternative**: Use Alchemy (https://alchemy.com) instead

### Step 1.2: Get Sepolia Test ETH

1. Go to https://sepoliafaucet.com
2. Enter your wallet address
3. Get free test ETH (needed for deploying contracts)

**Your deployer address** (from Ganache):
- Check: `contracts/migrations/` files
- Or create new wallet with MetaMask

### Step 1.3: Update Truffle Configuration

Edit `contracts/truffle-config.js`:

```javascript
require('dotenv').config();
const HDWalletProvider = require('@truffle/hdwallet-provider');

module.exports = {
  networks: {
    // Local development
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "1337",
    },

    // Sepolia testnet (PRODUCTION)
    sepolia: {
      provider: () => new HDWalletProvider(
        process.env.DEPLOYER_PRIVATE_KEY,
        `https://sepolia.infura.io/v3/${process.env.INFURA_API_KEY}`
      ),
      network_id: 11155111,
      gas: 5500000,
      confirmations: 2,
      timeoutBlocks: 200,
      skipDryRun: true
    }
  },

  compilers: {
    solc: {
      version: "0.8.19",
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        }
      }
    }
  }
};
```

### Step 1.4: Install HDWallet Provider

```bash
cd contracts
npm install @truffle/hdwallet-provider dotenv
```

### Step 1.5: Create Contracts .env File

Create `contracts/.env`:

```env
INFURA_API_KEY=your_infura_project_id_here
DEPLOYER_PRIVATE_KEY=your_wallet_private_key_here
```

**⚠️ CRITICAL**: Never commit this file to Git!

Add to `contracts/.gitignore`:
```
.env
```

### Step 1.6: Deploy to Sepolia

```bash
cd contracts
npx truffle migrate --network sepolia
```

**Save the contract addresses!** You'll need them for backend configuration.

Example output:
```
VoterRegistry:      0xABCD...1234
VotingBooth:        0xEFGH...5678
ResultsTallier:     0xIJKL...9012
ElectionController: 0xMNOP...3456
```

---

## Part 2: Deploy Backend to Render.com

### Step 2.1: Create render.yaml

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: blockchain-voting-backend
    env: python
    region: oregon
    plan: free
    buildCommand: |
      cd backend
      pip install -r requirements.txt
    startCommand: |
      cd backend
      uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: GANACHE_URL
        value: https://sepolia.infura.io/v3/YOUR_INFURA_KEY
      - key: GANACHE_NETWORK_ID
        value: "11155111"
      - key: JWT_SECRET
        generateValue: true
      - key: VOTING_SESSION_SECRET
        generateValue: true
      - key: BIOMETRIC_SALT_PEPPER
        generateValue: true
      - key: BLOCKCHAIN_PEPPER
        generateValue: true
      - key: FACE_MODEL
        value: ArcFace
      - key: FACE_THRESHOLD
        value: "0.68"
      - key: MAX_AUTH_ATTEMPTS
        value: "3"
      - key: SESSION_TIMEOUT_SECONDS
        value: "120"
      - key: LOCKOUT_DURATION_MINUTES
        value: "30"
      - key: LOG_LEVEL
        value: INFO
      - key: LOG_FORMAT
        value: json
```

### Step 2.2: Update Backend for Production

Create `backend/deployed_contracts.json`:

```json
{
  "VoterRegistry": "0xYOUR_VOTER_REGISTRY_ADDRESS",
  "VotingBooth": "0xYOUR_VOTING_BOOTH_ADDRESS",
  "ResultsTallier": "0xYOUR_RESULTS_TALLIER_ADDRESS",
  "ElectionController": "0xYOUR_ELECTION_CONTROLLER_ADDRESS",
  "network_id": "11155111"
}
```

Update `backend/app/services/blockchain.py` to read from this file in production.

### Step 2.3: Deploy to Render

1. **Go to**: https://render.com
2. **Sign in** with GitHub
3. **New** → **Web Service**
4. **Connect** your GitHub repository: `Blockchain-based-Voting`
5. **Configure**:
   - Name: `blockchain-voting-backend`
   - Root Directory: `backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Add Environment Variables**:
   - Click "Environment" tab
   - Add all variables from `.env`:
     - `DATABASE_URL`: Your Neon connection string
     - `GANACHE_URL`: `https://sepolia.infura.io/v3/YOUR_INFURA_KEY`
     - `GANACHE_NETWORK_ID`: `11155111`
     - `JWT_SECRET`: (generate new)
     - `VOTING_SESSION_SECRET`: (generate new)
     - etc.
7. **Create Web Service**
8. Wait for deployment (5-10 minutes)
9. **Copy your backend URL**: `https://blockchain-voting-backend.onrender.com`

**Note**: Free tier spins down after 15 minutes of inactivity. First request after may be slow (30s).

---

## Part 3: Deploy Frontend to Vercel

### Step 3.1: Update Frontend Environment

Create `frontend/.env.production`:

```env
REACT_APP_API_URL=https://blockchain-voting-backend.onrender.com
```

### Step 3.2: Add Vercel Configuration

Create `vercel.json` in project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ],
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/build",
  "framework": "create-react-app"
}
```

### Step 3.3: Update package.json

Add to `frontend/package.json`:

```json
{
  "scripts": {
    "build": "react-scripts build",
    "vercel-build": "react-scripts build"
  }
}
```

### Step 3.4: Deploy to Vercel

**Option A: Vercel CLI**
```bash
npm install -g vercel
cd /Users/work/Maj
vercel
```

**Option B: Vercel Dashboard** (Recommended)

1. **Go to**: https://vercel.com
2. **Sign in** with GitHub
3. **New Project**
4. **Import** your repository: `Blockchain-based-Voting`
5. **Configure**:
   - Framework Preset: `Create React App`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`
6. **Environment Variables**:
   - Add `REACT_APP_API_URL`: `https://blockchain-voting-backend.onrender.com`
7. **Deploy**
8. Wait 2-3 minutes
9. **Your app is live!** `https://blockchain-voting.vercel.app`

---

## Part 4: Configure CORS

### Update Backend CORS Settings

Edit `backend/app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://blockchain-voting.vercel.app",  # Your Vercel domain
        "https://*.vercel.app",  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Commit and push** → Render will auto-redeploy.

---

## Part 5: Set Up Database Schema

Your Neon database is already set up, but verify the schema:

```bash
# Connect to Neon
psql "YOUR_NEON_CONNECTION_STRING"

# Run schema if needed
\i database/schema.sql

# Create admin user
INSERT INTO admins (id, username, password_hash, full_name, role, is_active)
VALUES (
  gen_random_uuid(),
  'super_admin',
  'YOUR_HASHED_PASSWORD',
  'Super Administrator',
  'super_admin',
  true
);
```

---

## Part 6: Final Configuration

### Update Smart Contract Addresses

In `backend/deployed_contracts.json`:
```json
{
  "VoterRegistry": "0x...",
  "VotingBooth": "0x...",
  "ResultsTallier": "0x...",
  "ElectionController": "0x...",
  "network_id": "11155111"
}
```

Push to GitHub → Backend auto-redeploys on Render.

---

## Part 7: Testing Production Deployment

### 7.1 Test Backend

```bash
# Health check
curl https://blockchain-voting-backend.onrender.com/api/health

# Should return: {"status":"healthy"}
```

### 7.2 Test Frontend

1. Open: `https://blockchain-voting.vercel.app`
2. Should see login page
3. Try logging in with admin credentials

### 7.3 Test Blockchain Connection

Check backend logs on Render:
- Should see "Blockchain connected"
- Should see contract addresses loaded

---

## Part 8: Environment Variables Reference

### Backend (Render.com)

```env
# Database
DATABASE_URL=postgresql://...neon.tech/neondb

# Blockchain (Sepolia)
GANACHE_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
GANACHE_NETWORK_ID=11155111

# Security (Generate new for production!)
JWT_SECRET=<generate-new>
VOTING_SESSION_SECRET=<generate-new>
BIOMETRIC_SALT_PEPPER=<generate-new>
BLOCKCHAIN_PEPPER=<generate-new>

# Face Recognition
FACE_MODEL=ArcFace
FACE_THRESHOLD=0.68

# Security Settings
MAX_AUTH_ATTEMPTS=3
SESSION_TIMEOUT_SECONDS=120
LOCKOUT_DURATION_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Frontend (Vercel)

```env
REACT_APP_API_URL=https://blockchain-voting-backend.onrender.com
```

---

## Part 9: Continuous Deployment

Both Vercel and Render automatically deploy when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Automatic deployments:
# ✅ Vercel rebuilds frontend (2-3 min)
# ✅ Render rebuilds backend (5-10 min)
```

---

## Part 10: Monitoring & Logs

### Render Logs
- Dashboard → Your Service → Logs
- Real-time log streaming

### Vercel Logs
- Dashboard → Your Project → Deployments → Logs
- See build and runtime logs

### Neon Database
- Dashboard → Monitoring
- Query performance, connections

---

## Part 11: Custom Domain (Optional)

### Vercel (Frontend)
1. Dashboard → Project → Settings → Domains
2. Add your domain: `voting.yourdomain.com`
3. Update DNS records (provided by Vercel)
4. SSL certificate auto-configured

### Render (Backend)
1. Dashboard → Service → Settings → Custom Domains
2. Add: `api.yourdomain.com`
3. Update DNS with CNAME
4. Free SSL included

---

## Part 12: Cost Breakdown

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Vercel** | ✅ Free | 100GB bandwidth/month, Unlimited sites |
| **Render** | ✅ Free | 750 hours/month, Sleeps after 15min inactivity |
| **Neon** | ✅ Free | 3GB storage, 0.5 CPU |
| **Infura** | ✅ Free | 100k requests/day |

**Total**: $0/month for moderate usage

---

## Part 13: Production Checklist

Before going live:

- [ ] Smart contracts deployed to Sepolia
- [ ] Contract addresses saved and configured
- [ ] Backend deployed to Render
- [ ] Frontend deployed to Vercel
- [ ] Environment variables set correctly
- [ ] CORS configured
- [ ] Database schema initialized
- [ ] Admin user created
- [ ] Health checks passing
- [ ] Can login to admin dashboard
- [ ] Can create election
- [ ] Can register voter
- [ ] Can cast vote
- [ ] Results display correctly
- [ ] Audit logs working
- [ ] All secrets rotated (new JWT keys, etc.)

---

## Part 14: Troubleshooting

### Backend not connecting to Sepolia

**Check:**
- Infura API key is correct
- Network ID is `11155111`
- Contract addresses are from Sepolia deployment
- Deployer has Sepolia ETH

### Frontend can't connect to Backend

**Check:**
- `REACT_APP_API_URL` is correct
- CORS is configured with Vercel domain
- Backend is running (Render may be sleeping)

### Render service sleeping

**Solution:**
- Upgrade to paid plan ($7/mo)
- Or use cron-job.org to ping every 14 minutes
- Or accept 30s cold start

### Database connection issues

**Check:**
- Neon connection string is correct
- SSL mode is `require`
- Database is not paused (free tier)

---

## Part 15: Security Best Practices

1. **Rotate all secrets** for production
2. **Never commit** `.env` files
3. **Use different keys** than development
4. **Enable 2FA** on Vercel, Render, GitHub
5. **Monitor logs** for suspicious activity
6. **Keep dependencies updated**
7. **Use HTTPS only** (automatic on Vercel/Render)

---

## Part 16: Scaling (Future)

When you outgrow free tier:

**Render**:
- Upgrade to $7/mo (no sleep)
- Or $25/mo (better performance)

**Vercel**:
- $20/mo Pro (more bandwidth)

**Blockchain**:
- Move to mainnet (costs real ETH)
- Or keep on Sepolia (free forever)

**Database**:
- Neon Pro: $19/mo (more storage/compute)
- Or migrate to AWS RDS

---

## Quick Commands

### Deploy Contracts to Sepolia
```bash
cd contracts
npx truffle migrate --network sepolia
```

### Update Backend
```bash
git add backend/
git commit -m "Update backend"
git push origin main
# Render auto-deploys
```

### Update Frontend
```bash
git add frontend/
git commit -m "Update frontend"
git push origin main
# Vercel auto-deploys
```

### View Logs
```bash
# Render: Dashboard → Logs
# Vercel: Dashboard → Deployments → Logs
```

---

## Support & Resources

- **Vercel Docs**: https://vercel.com/docs
- **Render Docs**: https://render.com/docs
- **Truffle Sepolia**: https://trufflesuite.com/docs/truffle/reference/configuration/#networks
- **Infura**: https://docs.infura.io
- **Sepolia Faucet**: https://sepoliafaucet.com

---

**Deployment Time Estimate**: 1-2 hours for first deployment

**Congratulations!** 🎉 Your blockchain voting system is now live on the internet!

**Next Steps**:
1. Share your URL: `https://blockchain-voting.vercel.app`
2. Monitor usage and logs
3. Gather feedback
4. Iterate and improve

---

**Version**: 1.0
**Last Updated**: February 17, 2026
**Platform**: Vercel + Render + Neon + Sepolia
