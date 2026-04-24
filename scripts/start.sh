#!/bin/bash

# RiskShield - Start Script
# Starts both backend and frontend in separate terminals

set -e

echo "Starting RiskShield Platform..."
echo ""

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use osascript to open new terminal windows
    
    echo "Starting Backend..."
    osascript <<END
    tell application "Terminal"
        do script "cd $(pwd)/backend && source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --port 8001"
        activate
    end tell
END
    
    sleep 2
    
    echo "Starting Frontend..."
    osascript <<END
    tell application "Terminal"
        do script "cd $(pwd)/frontend && yarn start"
        activate
    end tell
END
    
else
    # Linux - use gnome-terminal or xterm
    
    if command -v gnome-terminal >/dev/null 2>&1; then
        echo "Starting Backend in new terminal..."
        gnome-terminal -- bash -c "cd $(pwd)/backend && source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --port 8001; exec bash"
        
        sleep 2
        
        echo "Starting Frontend in new terminal..."
        gnome-terminal -- bash -c "cd $(pwd)/frontend && yarn start; exec bash"
        
    elif command -v xterm >/dev/null 2>&1; then
        echo "Starting Backend in new terminal..."
        xterm -hold -e "cd $(pwd)/backend && source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --port 8001" &
        
        sleep 2
        
        echo "Starting Frontend in new terminal..."
        xterm -hold -e "cd $(pwd)/frontend && yarn start" &
        
    else
        echo "Unable to detect terminal emulator."
        echo "Please start manually:"
        echo ""
        echo "Terminal 1: cd backend && source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --port 8001"
        echo "Terminal 2: cd frontend && yarn start"
        exit 1
    fi
fi

echo ""
echo "====================================="
echo "  RiskShield is starting..."
echo "====================================="
echo ""
echo "Backend will be available at: http://localhost:8001"
echo "Frontend will be available at: http://localhost:3000"
echo "API Docs: http://localhost:8001/docs"
echo ""
echo "Demo credentials:"
echo "  LOD1: lod1@bank.com / password123"
echo "  LOD2: lod2@bank.com / password123"
echo ""
echo "Press Ctrl+C in each terminal to stop the services."
