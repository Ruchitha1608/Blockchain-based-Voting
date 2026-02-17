#!/bin/bash

echo "Stopping Blockchain Voting System..."
echo "===================================="

# Stop Backend
echo "Stopping Backend..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Stop Frontend
echo "Stopping Frontend..."
pkill -f "react-scripts start" 2>/dev/null

# Stop Ganache
echo "Stopping Ganache..."
pkill -f "ganache-cli" 2>/dev/null

sleep 2

echo ""
echo "✅ All services stopped"
echo ""
