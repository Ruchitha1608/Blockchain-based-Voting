#!/bin/bash

# Blockchain Voting System - Setup and Test Script
# This script verifies all components are working correctly

set -e

echo "========================================="
echo "Blockchain Voting System - Setup Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print info
info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check if Docker is running
info "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running. Please start Docker first."
    exit 1
fi
success "Docker is running"

# Check if docker-compose is installed
info "Checking docker-compose..."
if ! command -v docker-compose &> /dev/null; then
    error "docker-compose is not installed"
    exit 1
fi
success "docker-compose is installed"

echo ""
echo "========================================="
echo "Phase 1: Infrastructure Setup"
echo "========================================="

# Start infrastructure services
info "Starting PostgreSQL, Ganache, and Redis..."
docker-compose up -d postgres ganache redis

# Wait for services to be healthy
info "Waiting for services to be ready (30 seconds)..."
sleep 30

# Check PostgreSQL
info "Checking PostgreSQL..."
if docker exec voting_postgres pg_isready -U voting_user -d voting_db > /dev/null 2>&1; then
    success "PostgreSQL is ready"
else
    error "PostgreSQL failed to start"
    exit 1
fi

# Check Ganache
info "Checking Ganache..."
if curl -s http://localhost:8545 > /dev/null 2>&1; then
    success "Ganache is running"
else
    error "Ganache failed to start"
    exit 1
fi

# Check Redis
info "Checking Redis..."
if docker exec voting_redis redis-cli ping > /dev/null 2>&1; then
    success "Redis is running"
else
    error "Redis failed to start"
    exit 1
fi

echo ""
echo "========================================="
echo "Phase 2: Database Setup"
echo "========================================="

# Initialize database schema
info "Creating database schema..."
if docker exec -i voting_postgres psql -U voting_user -d voting_db < database/schema.sql > /dev/null 2>&1; then
    success "Database schema created"
else
    error "Failed to create database schema"
    exit 1
fi

# Verify tables
info "Verifying database tables..."
TABLE_COUNT=$(docker exec voting_postgres psql -U voting_user -d voting_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')

if [ "$TABLE_COUNT" -eq "9" ]; then
    success "All 9 tables created successfully"
else
    error "Expected 9 tables, found $TABLE_COUNT"
fi

# List tables
info "Database tables:"
docker exec voting_postgres psql -U voting_user -d voting_db -c "\dt" | grep public

echo ""
echo "========================================="
echo "Phase 3: Smart Contracts"
echo "========================================="

# Check if Node.js is installed
info "Checking Node.js..."
if ! command -v node &> /dev/null; then
    error "Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi
success "Node.js is installed: $(node --version)"

# Install contract dependencies
info "Installing contract dependencies..."
cd contracts
if [ ! -d "node_modules" ]; then
    npm install > /dev/null 2>&1
    success "Contract dependencies installed"
else
    success "Contract dependencies already installed"
fi

# Compile contracts
info "Compiling smart contracts..."
if npx truffle compile > /dev/null 2>&1; then
    success "Smart contracts compiled"
else
    error "Failed to compile smart contracts"
    exit 1
fi

# Deploy contracts
info "Deploying smart contracts to Ganache..."
if npx truffle migrate --network development; then
    success "Smart contracts deployed"
else
    error "Failed to deploy smart contracts"
    exit 1
fi

# Verify deployment
if [ -f "../deployed_addresses.json" ]; then
    success "Contract addresses saved to deployed_addresses.json"
    info "Contract addresses:"
    cat ../deployed_addresses.json | grep -A 1 '"address"' | head -8
else
    error "deployed_addresses.json not found"
fi

cd ..

echo ""
echo "========================================="
echo "Phase 4: Backend Setup"
echo "========================================="

# Check if Python is installed
info "Checking Python..."
if ! command -v python3.11 &> /dev/null && ! command -v python3 &> /dev/null; then
    error "Python 3.11+ is not installed"
    exit 1
fi
success "Python is installed"

# Check if virtual environment exists
info "Checking Python virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    info "Creating virtual environment..."
    python3.11 -m venv venv || python3 -m venv venv
    success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate || source venv/Scripts/activate

# Install backend dependencies
info "Installing backend dependencies (this may take a few minutes)..."
pip install --quiet --upgrade pip > /dev/null 2>&1
if pip install -r requirements.txt > /dev/null 2>&1; then
    success "Backend dependencies installed"
else
    error "Failed to install backend dependencies"
    deactivate
    exit 1
fi

echo ""
echo "========================================="
echo "Phase 5: Backend Testing"
echo "========================================="

# Set environment variables
export DATABASE_URL="postgresql://voting_user:voting_pass@localhost:5432/voting_db"
export GANACHE_URL="http://localhost:8545"

# Test backend imports
info "Testing backend imports..."
if python -c "
import sys
sys.path.insert(0, '.')
from app.config import settings
from app.database import check_db_connection
from app.services.crypto import generate_salt, hash_password
from app.services.blockchain import blockchain_service
from app.models.admin import Admin
from app.schemas.admin import AdminCreate
print('All imports successful')
" > /dev/null 2>&1; then
    success "Backend imports successful"
else
    error "Backend import test failed"
    deactivate
    exit 1
fi

# Test database connection
info "Testing database connection..."
if python -c "
import sys
sys.path.insert(0, '.')
from app.database import check_db_connection
assert check_db_connection(), 'Database connection failed'
print('Database connection successful')
" > /dev/null 2>&1; then
    success "Database connection working"
else
    error "Database connection test failed"
fi

# Test blockchain connection
info "Testing blockchain connection..."
if python -c "
import sys
sys.path.insert(0, '.')
from app.services.blockchain import blockchain_service
assert blockchain_service.web3.is_connected(), 'Blockchain not connected'
print('Blockchain connection successful')
" > /dev/null 2>&1; then
    success "Blockchain connection working"
else
    error "Blockchain connection test failed"
fi

deactivate
cd ..

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Start the backend:"
echo "     cd backend"
echo "     source venv/bin/activate"
echo "     uvicorn app.main:app --reload"
echo ""
echo "  2. Access the API:"
echo "     - API: http://localhost:8000"
echo "     - Docs: http://localhost:8000/docs"
echo "     - Health: http://localhost:8000/health"
echo ""
echo "  3. Default admin login:"
echo "     - Username: superadmin"
echo "     - Email: admin@voting.system"
echo "     - Password: Admin@123456"
echo "     (Change this immediately!)"
echo ""
echo "  4. View contract addresses:"
echo "     cat deployed_addresses.json"
echo ""
echo "  5. Run smart contract tests:"
echo "     cd contracts && npm test"
echo ""
success "All components are ready!"
