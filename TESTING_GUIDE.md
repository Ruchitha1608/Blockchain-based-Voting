# 🧪 Testing Guide - Blockchain Voting System

## ✅ System Status Check

**All services running:**
- ✅ Backend API: http://localhost:8000
- ✅ Frontend: http://localhost:3000
- ✅ Blockchain: Ganache on port 8545
- ✅ Database: Neon DB connected

**API Fixes Applied:**
- ✅ Fixed endpoint URLs (/api prefix)
- ✅ Fixed authentication token names (access_token, refresh_token)
- ✅ Fixed request/response field names (snake_case)
- ✅ Updated axios baseURL to localhost:8000

---

## 🎯 Complete End-to-End Test

### Phase 1: Admin Setup

**Step 1: Open Frontend**
```
URL: http://localhost:3000
```

**Step 2: Navigate to Admin Login**
```
Click "Admin Login" or go to: http://localhost:3000/login
```

**Step 3: Login as Admin**
```
Username: superadmin
Password: Admin@123456
```

**Expected Result:** Redirects to http://localhost:3000/admin (Dashboard)

---

### Phase 2: Create Election

**Step 1: Navigate to Elections**
```
Click "Elections" in sidebar
OR go to: http://localhost:3000/admin/elections
```

**Step 2: Create New Election**
```
Click "Create Election" button

Fill form:
- Name: "2026 General Election"
- Description: "Presidential and parliamentary elections"
- Start Date: 2026-03-01
- End Date: 2026-03-31

Click "Create Election"
```

**Expected Result:** Election appears in the list with status "draft"

---

### Phase 3: Add Constituency

**Step 1: Find Your Election**
```
Locate "2026 General Election" in the elections list
```

**Step 2: Add Constituency**
```
Click "Add Constituency" button

Fill modal:
- Name: "Central District"
- Code: "CENTRAL-01"

Click "Add"
```

**Expected Result:** Success message, constituency added to election

---

### Phase 4: Add Candidates

**Step 1: Add First Candidate**
```
Click "Add Candidate" button

Fill form:
- Name: "Alice Johnson"
- Party: "Progressive Party"
- Age: 45
- Constituency: Select "Central District"
- Image URL: (leave blank or use: https://i.pravatar.cc/150?img=1)

Click "Add Candidate"
```

**Step 2: Add Second Candidate**
```
Click "Add Candidate" again

Fill form:
- Name: "Bob Williams"
- Party: "Democratic Alliance"
- Age: 52
- Constituency: "Central District"
- Image URL: https://i.pravatar.cc/150?img=2

Click "Add Candidate"
```

**Step 3: Add Third Candidate**
```
Add one more candidate:
- Name: "Carol Martinez"
- Party: "Independent"
- Age: 38
- Constituency: "Central District"
- Image URL: https://i.pravatar.cc/150?img=3
```

**Expected Result:** 3 candidates added successfully

---

### Phase 5: Register Test Voter

**Step 1: Navigate to Voter Registration**
```
Click "Voters" in sidebar
OR go to: http://localhost:3000/admin/voters
```

**Step 2: Fill Voter Details**
```
Voter ID: TEST001
Full Name: Jane Doe
Date of Birth: 1990-05-15
Constituency: Select "Central District"
```

**Step 3: Capture Face Image**
```
1. Click "Start Camera" button
2. Allow browser to access webcam (click "Allow")
3. Position your face in the center of the frame
4. Wait for 3-second countdown
5. Camera captures image automatically
6. Review captured image
7. (Optional) Click "Retake" if not satisfied
```

**Step 4: Add Fingerprint (Optional)**
```
Fingerprint Template: (Leave blank for testing or enter dummy data)
```

**Step 5: Register**
```
Click "Register Voter" button
```

**Expected Result:**
- Success message
- Shows blockchain_voter_id (e.g., "0x7a8f3c2e...")
- Form clears for next registration

**⚠️ IMPORTANT:** Remember voter ID "TEST001" - you'll need it for voting!

---

### Phase 6: Start Election

**Step 1: Go Back to Elections**
```
Navigate to: http://localhost:3000/admin/elections
```

**Step 2: Start the Election**
```
Find "2026 General Election"
Click "Start Election" button
Confirm action
Wait for blockchain transaction (~1 second)
```

**Expected Result:**
- Status changes from "draft" to "active"
- Success message appears

---

### Phase 7: Test Voting Flow (Voter)

**Step 1: Open Polling Booth**
```
Open new browser tab or window
Go to: http://localhost:3000
```

**Expected View:** Polling booth interface with "Start Voting" button

**Step 2: Enter Voter ID**
```
Enter Voter ID: TEST001
Click "Next" or "Continue"
```

**Step 3: Face Authentication**
```
1. System requests webcam access
2. Click "Allow"
3. Position your face in the frame (same person who registered)
4. Click "Capture" or wait for auto-capture
5. System sends image to backend
6. Backend processes face recognition
```

**Expected Result:**
- "Authentication Successful!" message
- Shows session timeout timer (120 seconds)
- Displays candidate selection screen

**If Authentication Fails:**
- Shows "Authentication Failed" with remaining attempts (2 left)
- Option to retry or use fingerprint fallback
- After 3 failed attempts: Account locked (admin must reset)

**Step 4: Select Candidate**
```
View list of 3 candidates:
- Alice Johnson (Progressive Party)
- Bob Williams (Democratic Alliance)
- Carol Martinez (Independent)

Click on a candidate card to select
Selected card shows green border/highlight
```

**Step 5: Cast Vote**
```
Review selected candidate
Click "Cast Vote" button
Confirm your choice
```

**Expected Result:**
- Loading indicator (~1 second)
- "Vote Successfully Cast!" message
- Transaction hash displayed (e.g., "0xabc123...")
- Voter marked as "has_voted" in database
- Vote recorded on blockchain
- Auto-reset after 10 seconds

**Step 6: Verify Vote (Optional)**
```
Copy the transaction hash
Go to admin panel
Navigate to Audit Logs
Search for the transaction hash
Verify vote was recorded
```

---

### Phase 8: View Results (Admin)

**Step 1: Close Election**
```
Go to: http://localhost:3000/admin/elections
Find "2026 General Election"
Click "Close Election"
Confirm action
```

**Expected Result:** Status changes to "closed"

**Step 2: Finalize Results**
```
Click "Finalize Election" button
System calls ResultsTallier smart contract
Tallies all votes from blockchain
Wait for transaction confirmation
```

**Expected Result:**
- Status changes to "finalized"
- Results are calculated and stored

**Step 3: View Results**
```
Click "View Results" button
```

**Expected Result:**
- Bar chart showing vote counts
- Candidate names and parties
- Vote percentages
- Winner highlighted
- Turnout statistics (1 vote from 1 registered voter = 100%)

---

## 🔍 Testing Edge Cases

### Test 1: Double Voting Prevention

**Steps:**
```
1. Complete voting flow for TEST001
2. Try to vote again with same voter ID
```

**Expected Result:**
- "You have already voted" error
- Cannot authenticate again
- Blockchain prevents double voting

### Test 2: Authentication Lockout

**Steps:**
```
1. Register voter TEST002
2. Try to authenticate TEST002 with different face
3. Fail 3 times
```

**Expected Result:**
- Attempt 1: "Authentication failed, 2 attempts remaining"
- Attempt 2: "Authentication failed, 1 attempt remaining"
- Attempt 3: "Account locked due to multiple failed attempts"
- Voter cannot authenticate until admin resets

### Test 3: Session Timeout

**Steps:**
```
1. Authenticate successfully
2. Wait on candidate selection screen
3. Watch countdown timer
```

**Expected Result:**
- Warning at 30 seconds remaining
- At 0 seconds: Session expires
- Redirected back to start
- Must re-authenticate to vote

### Test 4: Fingerprint Fallback

**Steps:**
```
1. Start voting flow
2. Click "Use Fingerprint" instead of face
3. Enter voter ID
4. Provide fingerprint template (if registered)
```

**Expected Result:**
- Fingerprint authentication processed
- Same flow continues if successful

### Test 5: Invalid Voter ID

**Steps:**
```
1. Enter voter ID that doesn't exist: INVALID123
2. Try to authenticate
```

**Expected Result:**
- "Voter not found" error
- Cannot proceed to authentication

---

## 📊 Verification Points

### Backend Logs
```bash
tail -f /tmp/backend.log
```

**Look for:**
- Face authentication attempts
- Vote submissions
- Blockchain transactions
- Error messages

### Frontend Console
```
Press F12 in browser
Go to Console tab
```

**Look for:**
- API call responses
- WebRTC camera status
- React errors (if any)

### Blockchain Verification
```bash
# Check vote count on blockchain
cd /Users/work/Maj/contracts
npx truffle console --network development

# In Truffle console:
const VotingBooth = await artifacts.require("VotingBooth").deployed()
const candidate1Votes = await VotingBooth.getVoteCount("candidate_id_1")
console.log("Votes:", candidate1Votes.toString())
```

### Database Verification
```sql
-- Check auth attempts
SELECT * FROM auth_attempts ORDER BY attempted_at DESC LIMIT 10;

-- Check vote submissions
SELECT * FROM vote_submissions ORDER BY submitted_at DESC LIMIT 10;

-- Check voters who voted
SELECT voter_id, full_name, has_voted FROM voters WHERE has_voted = true;
```

---

## 🐛 Common Issues & Solutions

### Issue: "Cannot access webcam"

**Causes:**
- Browser didn't request permission
- Permission denied by user
- Camera in use by another app
- HTTPS required (some browsers)

**Solutions:**
1. Check browser site settings
2. Reload page and click "Allow"
3. Close other apps using camera
4. Use Chrome/Firefox (better WebRTC support)
5. For production: Use HTTPS

### Issue: "Face authentication keeps failing"

**Causes:**
- Different lighting conditions
- Different person
- Glasses/hat added/removed
- Low-quality image

**Solutions:**
1. Use same lighting as registration
2. Same person must authenticate
3. Remove/add glasses to match registration
4. Ensure good webcam quality
5. Try fingerprint fallback

### Issue: "404 Not Found on API calls"

**Status:** ✅ FIXED
- Updated all endpoint URLs
- Added /api prefix
- Fixed token names

### Issue: "JWT token expired"

**Cause:** Access token expires after 30 minutes

**Solution:**
- Frontend auto-refreshes with refresh_token
- If refresh fails: Redirects to login
- Just login again

### Issue: "Vote transaction failed"

**Causes:**
- Ganache not running
- Smart contract error
- Out of gas
- Already voted

**Solutions:**
1. Check Ganache is running: `ps aux | grep ganache`
2. Check backend logs for errors
3. Verify voter hasn't already voted
4. Restart Ganache if needed

---

## ✅ Test Checklist

### Frontend Tests
- [ ] Polling booth loads at /
- [ ] Admin login works
- [ ] Admin dashboard shows stats
- [ ] Create election works
- [ ] Add constituency works
- [ ] Add candidate works
- [ ] Voter registration with webcam works
- [ ] Start election works
- [ ] Face authentication works
- [ ] Vote casting works
- [ ] Results visualization works
- [ ] Audit logs display
- [ ] Session timeout works
- [ ] Logout works

### Backend Tests
- [ ] Health endpoint returns healthy
- [ ] Login returns JWT tokens
- [ ] Token refresh works
- [ ] Face authentication endpoint works
- [ ] Vote casting records to blockchain
- [ ] Results tallying works
- [ ] Audit logs queryable
- [ ] CORS allows frontend requests

### Blockchain Tests
- [ ] Ganache running with 10 accounts
- [ ] All 4 contracts deployed
- [ ] Voter registration on chain works
- [ ] Vote submission on chain works
- [ ] Results tallier works
- [ ] Transaction history accessible

### Security Tests
- [ ] Biometric data encrypted
- [ ] Voter anonymity maintained on blockchain
- [ ] Cannot vote twice
- [ ] Account lockout after 3 failures
- [ ] Session timeout enforced
- [ ] Protected routes require JWT

---

## 📈 Performance Metrics

**Target Metrics:**

| Operation | Target Time | Acceptable Range |
|-----------|-------------|------------------|
| Page load | < 2s | < 3s |
| Login | < 500ms | < 1s |
| Face auth | < 500ms | < 1.5s |
| Vote casting | < 1s | < 2s |
| Results load | < 300ms | < 1s |

**Measure with:**
- Browser DevTools → Network tab
- Backend logs (timestamps)
- React DevTools Profiler

---

## 🎉 Success Criteria

**System is working if:**

✅ Admin can login and access dashboard
✅ Admin can create and manage elections
✅ Admin can register voters with webcam
✅ Admin can add candidates
✅ Admin can start/close/finalize elections
✅ Voter can authenticate with face
✅ Voter can cast vote on blockchain
✅ Vote is recorded and verifiable
✅ Results display correctly
✅ Audit logs show all activity
✅ No double voting possible
✅ Session timeout works
✅ All security features active

---

## 🚀 Next Steps After Testing

Once testing is successful:

1. **Create more test data:**
   - Multiple constituencies
   - More candidates
   - More voters

2. **Test edge cases:**
   - Ties in voting
   - Large number of voters
   - Multiple simultaneous votes
   - Network interruptions

3. **Performance testing:**
   - Load testing with 100+ voters
   - Stress testing API endpoints
   - Blockchain transaction throughput

4. **Security review:**
   - Penetration testing
   - Vulnerability scanning
   - Code review

5. **Production preparation:**
   - Change default passwords
   - Deploy to production blockchain
   - Set up monitoring
   - Configure backups

---

**Ready to test?** Start at: http://localhost:3000

**Questions?** Check [COMPLETE_SYSTEM_GUIDE.md](./COMPLETE_SYSTEM_GUIDE.md)

🧪 **Happy testing!** 🧪
