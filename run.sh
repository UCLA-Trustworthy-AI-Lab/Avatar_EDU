#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}Starting Avatar EDU servers...${NC}"

# Function to kill servers on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down servers...${NC}"
    kill $FLASK_PID $NEXTJS_PID 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Start Flask backend server
echo -e "${GREEN}Starting Flask server on http://localhost:5001...${NC}"
cd "$SCRIPT_DIR"
uv run python run.py &
FLASK_PID=$!

# Give Flask time to start
sleep 2

# Start Next.js frontend server
echo -e "${GREEN}Starting HeyGen Avatar server on http://localhost:3000...${NC}"
cd "$SCRIPT_DIR/InteractiveAvatarNextJSDemo"
npm run dev &
NEXTJS_PID=$!

echo -e "${BLUE}Both servers are starting...${NC}"
echo -e "${GREEN}Flask server: http://localhost:5001${NC}"
echo -e "${GREEN}HeyGen Avatar: http://localhost:3000${NC}"
echo -e "${BLUE}Press Ctrl+C to stop both servers${NC}"

# Wait for both processes
wait $FLASK_PID $NEXTJS_PID
