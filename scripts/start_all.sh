#!/bin/bash
echo "=== Starting Advisor Voice Agent Servers ==="

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Kill existing processes
echo "Stopping existing processes..."
pkill -9 -f mcp_server.py 2>/dev/null
pkill -9 -f api_server.py 2>/dev/null
sleep 2

# Start MCP Backend
echo "Starting MCP Backend on port 8000..."
cd "$PROJECT_ROOT/phase-2-mcp-tools/server"
python3 mcp_server.py > /tmp/mcp.log 2>&1 &
MCP_PID=$!
echo "MCP Server PID: $MCP_PID"

# Wait for backend
sleep 5

# Start API Frontend
echo "Starting API Frontend on port 8001..."
cd "$PROJECT_ROOT/phase-4-integration"
python3 api_server.py > /tmp/api.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"

# Wait for frontend
sleep 5

# Check status
echo ""
echo "=== Checking Services ==="
echo -n "MCP (8000): "
curl -s http://localhost:8000/health 2>&1 | head -1 || echo "Not responding"

echo -n "API (8001): "
curl -s http://localhost:8001/api/health 2>&1 | head -1 || echo "Not responding"

echo ""
echo "=== Logs ==="
echo "MCP log: /tmp/mcp.log"
echo "API log: /tmp/api.log"
echo ""
echo "To stop: pkill -9 -f 'mcp_server.py|api_server.py'"
