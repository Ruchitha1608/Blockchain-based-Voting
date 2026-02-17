#!/bin/bash
# Test what works WITHOUT any services running

echo "================================================"
echo "Testing WITHOUT Services (No Docker needed)"
echo "================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${YELLOW}→${NC} $1"; }

# Test 1: Node.js
info "Test 1: Node.js & npm"
if command -v node &> /dev/null; then
    success "Node.js $(node --version)"
    success "npm $(npm --version)"
else
    error "Node.js not found"
fi
echo ""

# Test 2: Python
info "Test 2: Python"
if command -v python3 &> /dev/null; then
    success "Python $(python3 --version)"
else
    error "Python not found"
fi
echo ""

# Test 3: Smart Contracts
info "Test 3: Smart Contract Files"
if [ -f "contracts/contracts/VoterRegistry.sol" ]; then
    success "VoterRegistry.sol found"
else
    error "VoterRegistry.sol missing"
fi

if [ -f "contracts/contracts/VotingBooth.sol" ]; then
    success "VotingBooth.sol found"
else
    error "VotingBooth.sol missing"
fi

if [ -f "contracts/contracts/ResultsTallier.sol" ]; then
    success "ResultsTallier.sol found"
else
    error "ResultsTallier.sol missing"
fi

if [ -f "contracts/contracts/ElectionController.sol" ]; then
    success "ElectionController.sol found"
else
    error "ElectionController.sol missing"
fi
echo ""

# Test 4: Database Schema
info "Test 4: Database Schema"
if [ -f "database/schema.sql" ]; then
    TABLE_COUNT=$(grep -c "CREATE TABLE" database/schema.sql)
    success "schema.sql found ($TABLE_COUNT tables defined)"
else
    error "schema.sql missing"
fi
echo ""

# Test 5: Backend Structure
info "Test 5: Backend Structure"
if [ -f "backend/.env" ]; then
    success ".env file exists"
else
    error ".env file missing - run: python3 generate_env.py"
fi

if [ -f "backend/requirements.txt" ]; then
    PACKAGE_COUNT=$(grep -cv "^#\|^$" backend/requirements.txt)
    success "requirements.txt found (~$PACKAGE_COUNT packages)"
else
    error "requirements.txt missing"
fi

if [ -f "backend/app/main.py" ]; then
    success "main.py found"
else
    error "main.py missing"
fi
echo ""

# Test 6: Backend Models
info "Test 6: Backend Models"
MODEL_COUNT=$(find backend/app/models -name "*.py" -not -name "__*" | wc -l | tr -d ' ')
success "$MODEL_COUNT model files"
echo ""

# Test 7: Backend Services
info "Test 7: Backend Services"
if [ -f "backend/app/services/crypto.py" ]; then
    success "crypto.py found"
fi
if [ -f "backend/app/services/blockchain.py" ]; then
    success "blockchain.py found"
fi
if [ -f "backend/app/services/biometric/face.py" ]; then
    success "face.py found"
fi
if [ -f "backend/app/services/biometric/fingerprint.py" ]; then
    success "fingerprint.py found"
fi
echo ""

# Test 8: Documentation
info "Test 8: Documentation"
DOC_COUNT=$(find . -maxdepth 1 -name "*.md" | wc -l | tr -d ' ')
success "$DOC_COUNT documentation files"
echo ""

echo "================================================"
echo "Summary"
echo "================================================"
echo ""
echo "✅ You can test these WITHOUT any services:"
echo "   1. Smart contract syntax (truffle compile)"
echo "   2. Python code syntax"
echo "   3. Crypto functions (hashing, encryption)"
echo "   4. File structure verification"
echo ""
echo "❌ You NEED services for these:"
echo "   1. Database operations (needs PostgreSQL)"
echo "   2. Blockchain deployment (needs Ganache)"
echo "   3. Full API testing (needs all services)"
echo ""
echo "================================================"
echo "Next Steps"
echo "================================================"
echo ""
echo "1. Test smart contracts:"
echo "   cd contracts && npm install && npx truffle compile"
echo ""
echo "2. Test Python imports:"
echo "   cd backend && python3 -c 'from app.config import settings'"
echo ""
echo "3. When ready, start services:"
echo "   docker-compose up -d"
echo ""
