#!/bin/bash

# RiskShield - Stop Script
# Stops all RiskShield processes

echo "Stopping RiskShield Platform..."
echo ""

# Kill backend processes
echo "Stopping backend..."
PORT=8001
PIDS=$(lsof -ti:$PORT 2>/dev/null)
if [ -n "$PIDS" ]; then
    echo "Found processes on port $PORT: $PIDS"
    kill -9 $PIDS 2>/dev/null
    echo "✓ Backend stopped"
else
    echo "No backend process found"
fi

# Kill frontend processes
echo "Stopping frontend..."
PORT=3000
PIDS=$(lsof -ti:$PORT 2>/dev/null)
if [ -n "$PIDS" ]; then
    echo "Found processes on port $PORT: $PIDS"
    kill -9 $PIDS 2>/dev/null
    echo "✓ Frontend stopped"
else
    echo "No frontend process found"
fi

echo ""
echo "RiskShield stopped."
