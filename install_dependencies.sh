#!/bin/bash
################################################################################
# HackApp - Dependency Installation Script
# Installs all required dependencies for the HackApp project
################################################################################

set -e  # Exit on error

echo "=================================="
echo "🚀 HackApp Dependency Installer"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${YELLOW}⚠️  Warning: This script is designed for Linux/WSL${NC}"
    echo "   You may need to install dependencies manually on other systems"
    echo ""
fi

# 1. System Dependencies
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y portaudio19-dev python3-dev python3-pip
    echo -e "${GREEN}✅ System dependencies installed${NC}"
else
    echo -e "${RED}❌ apt-get not found. Please install portaudio19-dev manually${NC}"
fi
echo ""

# 2. Python Dependencies
echo -e "${YELLOW}🐍 Installing Python dependencies...${NC}"

# Check if we should use --break-system-packages
PIP_FLAGS=""
if [[ -f /etc/os-release ]] && grep -q "debian\|ubuntu" /etc/os-release; then
    PIP_FLAGS="--break-system-packages"
fi

# Install agent dependencies
echo "   📱 Agent dependencies..."
pip install -r hackapp/agent/requirements.txt $PIP_FLAGS

# Install middleware dependencies
echo "   🖥️  Middleware dependencies..."
pip install -r hackapp/middleware/requirements.txt $PIP_FLAGS

# Install mock service dependencies
echo "   🧪 Mock service dependencies..."
pip install -r hackapp/mock_service/requirements.txt $PIP_FLAGS

echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# 3. Optional Dependencies
echo -e "${YELLOW}📚 Installing optional dependencies...${NC}"
pip install pytesseract pillow openpyxl pandas $PIP_FLAGS 2>/dev/null && \
    echo -e "${GREEN}✅ Optional dependencies installed${NC}" || \
    echo -e "${YELLOW}⚠️  Some optional dependencies failed (non-critical)${NC}"
echo ""

# 4. Environment Setup
echo -e "${YELLOW}⚙️  Setting up environment...${NC}"
if [[ ! -f hackapp/.env ]]; then
    cat > hackapp/.env << 'EOF'
# Groq API Configuration
# Get your API key from: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Middleware Configuration
MIDDLEWARE_URL=http://localhost:5000
MIDDLEWARE_TOKEN=hackathon_demo_token
EOF
    echo -e "${GREEN}✅ Created .env file (remember to add your GROQ_API_KEY)${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists (skipping)${NC}"
fi
echo ""

# 5. Verification
echo -e "${YELLOW}🔍 Verifying installation...${NC}"

# Test Python imports
python3 -c "import pynput; import pyautogui; import fastapi; import flask" 2>/dev/null && \
    echo -e "${GREEN}✅ Core packages verified${NC}" || \
    echo -e "${RED}❌ Some packages failed to import${NC}"

# Test PortAudio
python3 -c "import sounddevice" 2>/dev/null && \
    echo -e "${GREEN}✅ Audio support verified${NC}" || \
    echo -e "${RED}❌ PortAudio not working (sounddevice import failed)${NC}"

echo ""
echo "=================================="
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo "=================================="
echo ""
echo "📝 Next steps:"
echo "   1. Add your GROQ_API_KEY to hackapp/.env"
echo "   2. Start services: ./setup.sh"
echo "   3. Check DEPENDENCIES.txt for troubleshooting"
echo ""
