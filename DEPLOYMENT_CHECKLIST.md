# Deployment Checklist

## 🎯 Quick Deployment Steps

### Step 1: Prepare Blockchain (Sepolia)

- [ ] Sign up at https://infura.io
- [ ] Create project and get API key
- [ ] Get Sepolia test ETH from https://sepoliafaucet.com
- [ ] Install dependencies:
  ```bash
  cd contracts
  npm install @truffle/hdwallet-provider dotenv
  ```
- [ ] Create `contracts/.env`:
  ```env
  INFURA_API_KEY=your_key_here
  DEPLOYER_PRIVATE_KEY=your_wallet_private_key
  ```
- [ ] Deploy contracts:
  ```bash
  npx truffle migrate --network sepolia
  ```
- [ ] **Save contract addresses!**

### Step 2: Deploy Backend (Render.com)

- [ ] Sign up at https://render.com
- [ ] Connect GitHub account
- [ ] New Web Service → Select repository
- [ ] Configure:
  - Name: `blockchain-voting-backend`
  - Root Directory: `backend`
  - Environment: `Python 3`
  - Build: `pip install -r requirements.txt`
  - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables:
  - `DATABASE_URL` → Your Neon connection string
  - `GANACHE_URL` → `https://sepolia.infura.io/v3/YOUR_KEY`
  - `GANACHE_NETWORK_ID` → `11155111`
  - All other vars from `backend/.env`
- [ ] Deploy (wait 5-10 min)
- [ ] Copy backend URL

### Step 3: Deploy Frontend (Vercel)

- [ ] Sign up at https://vercel.com
- [ ] Connect GitHub account
- [ ] New Project → Import repository
- [ ] Configure:
  - Framework: `Create React App`
  - Root Directory: `frontend`
  - Build Command: `npm run build`
  - Output Directory: `build`
- [ ] Add environment variable:
  - `REACT_APP_API_URL` → Your Render backend URL
- [ ] Deploy (wait 2-3 min)
- [ ] Copy frontend URL

### Step 4: Configure CORS

- [ ] Edit `backend/app/main.py`
- [ ] Add your Vercel URL to `allow_origins`
- [ ] Commit and push (Render auto-redeploys)

### Step 5: Test Everything

- [ ] Backend health: `curl YOUR_BACKEND_URL/api/health`
- [ ] Frontend loads
- [ ] Can login
- [ ] Can create election
- [ ] Can register voter
- [ ] Can cast vote
- [ ] Results show correctly

### Step 6: Create Admin User

- [ ] Connect to Neon database
- [ ] Run admin user creation SQL
- [ ] Test login

---

## 📝 What You'll Need

### Accounts to Create:
- [ ] Infura.io (free)
- [ ] Render.com (free)
- [ ] Vercel.com (free)

### Information to Save:
- [ ] Infura API key
- [ ] Sepolia contract addresses
- [ ] Render backend URL
- [ ] Vercel frontend URL

### Secrets to Generate:
- [ ] JWT_SECRET
- [ ] VOTING_SESSION_SECRET
- [ ] BIOMETRIC_SALT_PEPPER
- [ ] BLOCKCHAIN_PEPPER

---

## ⚡ Quick Commands

```bash
# 1. Deploy contracts
cd contracts
npx truffle migrate --network sepolia

# 2. Commit deployment files
git add .
git commit -m "Add deployment configuration"
git push origin main

# 3. Check deployment status
# Render: https://dashboard.render.com
# Vercel: https://vercel.com/dashboard
```

---

## 🔗 Important URLs

- **Infura Dashboard**: https://infura.io/dashboard
- **Sepolia Faucet**: https://sepoliafaucet.com
- **Render Dashboard**: https://dashboard.render.com
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Neon Dashboard**: https://console.neon.tech

---

## ⏱️ Estimated Time

- Step 1 (Blockchain): 20-30 minutes
- Step 2 (Backend): 15-20 minutes
- Step 3 (Frontend): 10-15 minutes
- Step 4-6 (Config & Test): 15-20 minutes

**Total**: 60-90 minutes

---

## 🆘 Need Help?

See detailed instructions in `DEPLOYMENT_GUIDE.md`
