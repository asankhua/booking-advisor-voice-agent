#!/bin/bash
# Start backend and frontend servers

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Killing existing processes..."
pkill -9 -f mcp_server.py 2>/dev/null
pkill -9 -f api_server.py 2>/dev/null
sleep 2

echo "Starting MCP backend server..."
cd "$PROJECT_ROOT/phase-2-mcp-tools/server"
python3 mcp_server.py > /tmp/mcp.log 2>&1 &
sleep 5

echo "Starting API frontend server..."
cd "$PROJECT_ROOT/phase-4-integration"
python3 api_server.py > /tmp/api.log 2>&1 &
sleep 5

echo "Checking services..."
sleep 3
curl -s http://localhost:8000/health 2>&1 | head -1
curl -s http://localhost:8001/api/health 2>&1 | head -1

echo "Servers started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8001"
