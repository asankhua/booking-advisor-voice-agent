#!/usr/bin/env python3
"""Start all servers for Advisor Voice Agent"""
import subprocess
import os
import time
import signal
import sys

# Get project root (parent of scripts directory)
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def kill_existing():
    """Kill existing server processes"""
    print("Killing existing processes...")
    for proc in ["mcp_server.py", "api_server.py"]:
        try:
            subprocess.run(["pkill", "-9", "-f", proc], capture_output=True)
        except:
            pass
    time.sleep(2)
    print("✅ Processes killed")

def start_mcp():
    """Start MCP backend server"""
    print("\nStarting MCP Backend (port 8000)...")
    mcp_path = os.path.join(BASE_PATH, "phase-2-mcp-tools/server/mcp_server.py")
    log_file = "/tmp/mcp.log"
    
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            ["python3", mcp_path],
            stdout=log,
            stderr=log,
            cwd=os.path.dirname(mcp_path)
        )
    
    print(f"✅ MCP Server started (PID: {process.pid})")
    return process

def start_api():
    """Start API frontend server"""
    print("\nStarting API Frontend (port 8001)...")
    api_path = os.path.join(BASE_PATH, "phase-4-integration/api_server.py")
    log_file = "/tmp/api.log"
    
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            ["python3", api_path],
            stdout=log,
            stderr=log,
            cwd=os.path.dirname(api_path)
        )
    
    print(f"✅ API Server started (PID: {process.pid})")
    return process

def check_health():
    """Check if services are healthy"""
    import urllib.request
    import json
    
    print("\n=== Health Check ===")
    
    # Check MCP
    try:
        req = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
        data = json.loads(req.read())
        print(f"✅ MCP (8000): {data.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ MCP (8000): Not responding ({e})")
    
    # Check API
    try:
        req = urllib.request.urlopen("http://localhost:8001/api/health", timeout=5)
        data = json.loads(req.read())
        print(f"✅ API (8001): {data.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ API (8001): Not responding ({e})")

def show_logs():
    """Show recent log entries"""
    print("\n=== Recent Logs ===")
    
    for name, log_file in [("MCP", "/tmp/mcp.log"), ("API", "/tmp/api.log")]:
        print(f"\n{name} Log (last 10 lines):")
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"  {line.rstrip()}")
        except:
            print("  No log available")

def main():
    print("="*50)
    print("ADVISOR VOICE AGENT - SERVER STARTUP")
    print("="*50)
    
    kill_existing()
    
    mcp_proc = start_mcp()
    time.sleep(5)
    
    api_proc = start_api()
    time.sleep(5)
    
    check_health()
    show_logs()
    
    print("\n" + "="*50)
    print("SERVERS STARTED!")
    print("="*50)
    print("\nAccess URLs:")
    print("  Frontend: http://localhost:8001")
    print("  Backend:  http://localhost:8000")
    print("\nTo stop:")
    print(f"  kill {mcp_proc.pid} {api_proc.pid}")
    print("  or: pkill -9 -f 'mcp_server.py|api_server.py'")
    print("\nView logs:")
    print("  tail -f /tmp/mcp.log")
    print("  tail -f /tmp/api.log")

if __name__ == "__main__":
    main()
