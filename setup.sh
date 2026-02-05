#!/bin/bash

# HackApp - One-Command Startup Script
# Starts all services needed for the demo

set -e  # Exit on error

echo "════════════════════════════════════════════"
echo "🚀 HackApp - Starting All Services"
echo "════════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "✅ Python $(python3 --version) found"
echo ""

# Check if in correct directory
if [ ! -d "hackapp" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install dependencies (if needed)
read -p "📦 Install/update dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing dependencies..."
    pip install -q -r hackapp/agent/requirements.txt
    pip install -q -r hackapp/middleware/requirements.txt
    pip install -q -r hackapp/mock_service/requirements.txt
    echo "✅ Dependencies installed"
    echo ""
fi

# Create logs directory
mkdir -p logs

# Start services in background
echo "🤖 Starting Mock External Service (port 5001)..."
cd hackapp
python3 mock_service/app.py > ../logs/mock_service.log 2>&1 &
MOCK_PID=$!
echo "   PID: $MOCK_PID"

sleep 2

echo "🧠 Starting Middleware API (port 5000)..."
python3 middleware/main.py > ../logs/middleware.log 2>&1 &
MIDDLEWARE_PID=$!
echo "   PID: $MIDDLEWARE_PID"

sleep 2

echo "🖱️  Starting Agent (hotkey listener)..."
python3 agent/main.py > ../logs/agent.log 2>&1 &
AGENT_PID=$!
echo "   PID: $AGENT_PID"

cd ..

sleep 1

echo ""
echo "════════════════════════════════════════════"
echo "✅ All Services Running!"
echo "════════════════════════════════════════════"
echo "   Mock Service:  http://localhost:5001"
echo "   Middleware:    http://localhost:5000"
echo "   Agent:         Listening for hotkeys"
echo ""
echo "📝 Logs are in ./logs/ directory"
echo "🎬 Open DXCare simulator and press CTRL+ALT+V"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo "════════════════════════════════════════════"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $MOCK_PID $MIDDLEWARE_PID $AGENT_PID 2>/dev/null || true
    echo "✅ All services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for any process to exit
wait
