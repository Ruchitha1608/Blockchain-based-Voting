#!/bin/bash

echo "============================================================"
echo "SYSTEM STATUS CHECK"
echo "============================================================"

# Check Backend
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend (FastAPI):    http://localhost:8000 - RUNNING"
else
    echo "❌ Backend:              NOT RUNNING"
fi

# Check Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend (React):     http://localhost:3000 - RUNNING"
else
    echo "❌ Frontend:             NOT RUNNING"
fi

# Check Ganache
GANACHE_CHECK=$(curl -s http://localhost:8545 -X POST \
    -H "Content-Type: application/json" \
    --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' 2>/dev/null)

if echo "$GANACHE_CHECK" | grep -q "result"; then
    BLOCK=$(echo "$GANACHE_CHECK" | grep -o '"result":"0x[0-9a-f]*"' | cut -d'"' -f4)
    BLOCK_DEC=$((16#${BLOCK:2}))
    echo "✅ Blockchain (Ganache): http://localhost:8545 - RUNNING (Block #$BLOCK_DEC)"
else
    echo "❌ Blockchain:           NOT RUNNING"
fi

# Check Database
cd /Users/work/Maj/backend
DB_CHECK=$(python -c "
from sqlalchemy import create_engine, text
from app.config import settings
try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('CONNECTED')
except:
    print('FAILED')
" 2>/dev/null)

if [ "$DB_CHECK" = "CONNECTED" ]; then
    echo "✅ Database (PostgreSQL): CONNECTED"
else
    echo "❌ Database:             NOT CONNECTED"
fi

echo "============================================================"
