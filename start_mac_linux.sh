#!/bin/bash
# DARKSTARE AI TRADING BRAIN v2.0 - Mac/Linux Launcher

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

echo ""
echo -e "${CYAN}  ============================================================${NC}"
echo -e "${YELLOW}    DARKSTARE AI TRADING BRAIN v2.0${NC}"
echo -e "${CYAN}    Claude + GPT-4o  |  Live Forex, Gold, News, MT5${NC}"
echo -e "${CYAN}  ============================================================${NC}"
echo ""

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python
command -v python3 &>/dev/null || {
    echo -e "${RED}[ERROR] Python 3 not found.${NC}"
    echo "  Mac:   brew install python3"
    echo "  Linux: sudo apt install python3 python3-pip"
    exit 1
}
echo -e "${GREEN}[OK]${NC} $(python3 --version)"

# Install packages
python3 -c "import fastapi,uvicorn,httpx" 2>/dev/null || {
    echo "[..] Installing packages..."
    pip3 install fastapi uvicorn httpx --quiet
    echo -e "${GREEN}[OK]${NC} Packages installed"
}
echo -e "${GREEN}[OK]${NC} All packages ready"

# Get local IP
LOCAL_IP=$(python3 -c "
import socket
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.connect(('8.8.8.8',80))
    print(s.getsockname()[0])
    s.close()
except:
    print('localhost')
" 2>/dev/null)

echo ""
echo -e "${CYAN}  ============================================================${NC}"
echo -e "   Desktop: ${GREEN}http://localhost:8000${NC}"
echo -e "   Mobile:  ${GREEN}http://$LOCAL_IP:8000${NC}"
echo -e "${CYAN}  ============================================================${NC}"
echo ""
echo "  SETUP (first time):"
echo "   1. Click the gear icon (CFG) in the sidebar"
echo "   2. Enter API keys -> SAVE ALL KEYS -> TEST each"
echo "   3. Go to DASH -> click ANALYZE NOW"
echo ""
echo "  MOBILE: Open http://$LOCAL_IP:8000 on your phone"
echo "   iPhone:  Share -> Add to Home Screen"
echo "   Android: Menu -> Add to Home Screen"
echo ""

# Start server
python3 "$DIR/server.py" &
SERVER_PID=$!
sleep 3

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:8000"
else
    xdg-open "http://localhost:8000" 2>/dev/null || true
fi

echo -e "${GREEN}[RUNNING]${NC} Press Ctrl+C to stop the server"
wait $SERVER_PID
