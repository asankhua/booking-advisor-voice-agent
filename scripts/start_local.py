#!/usr/bin/env python3
"""
start_local.py - Launch all services for local testing
Connects Phase 1 (Voice), Phase 2 (MCP), Phase 3 (LLM), Phase 4 (API) with Frontend UI
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def log(msg, color=Colors.BLUE):
    print(f"{color}[LAUNCHER] {msg}{Colors.END}")

def main():
    log("Starting Advisor Voice Agent - Local Development Mode", Colors.GREEN)
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    processes = []
    
    try:
        # 1. Start FastAPI Backend (Phase 4 Integration)
        log("Starting FastAPI Backend (Port 8001)...")
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "phase-4-integration.api_server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        processes.append(("API Server", api_process, "http://localhost:8001"))
        time.sleep(3)  # Wait for API to start
        
        # 2. Serve Frontend UI (Simple HTTP server on port 8000)
        log("Starting Frontend UI (Port 8000)...")
        frontend_path = project_root / "frontend" / "ui_dist"
        ui_process = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8000"],
            cwd=frontend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        processes.append(("Frontend UI", ui_process, "http://localhost:8000"))
        time.sleep(2)
        
        # 3. Optional: Start Gradio UI (Port 7860)
        log("Starting Gradio UI (Port 7860)...")
        gradio_process = subprocess.Popen(
            [sys.executable, "frontend/full_ui.py"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        processes.append(("Gradio UI", gradio_process, "http://localhost:7860"))
        
        print("\n" + "=" * 60)
        log("ALL SERVICES STARTED!", Colors.GREEN)
        print("=" * 60)
        print(f"\n{Colors.YELLOW}🌐 LOCAL TESTING URLs:{Colors.END}")
        print(f"   • Main UI:       http://localhost:8000")
        print(f"   • API Docs:      http://localhost:8001/docs")
        print(f"   • API Health:    http://localhost:8001/api/health")
        print(f"   • Gradio UI:     http://localhost:7860")
        print(f"\n{Colors.YELLOW}📁 Phase Connections:{Colors.END}")
        print(f"   • Phase 1 (Voice):  Whisper + ParlerTTS + SileroVAD")
        print(f"   • Phase 2 (MCP):    Google Calendar + Docs + Resend Email")
        print(f"   • Phase 3 (LLM):    Groq API (llama-3.3-70b)")
        print(f"   • Phase 4 (API):    FastAPI on port 8001")
        print(f"   • Frontend:         HTML/CSS/Tailwind on port 8000")
        print(f"\n{Colors.YELLOW}⚡ Quick Test:{Colors.END}")
        print(f"   1. Open http://localhost:8000 in your browser")
        print(f"   2. Click the microphone to record audio")
        print(f"   3. Or type a message and send")
        print(f"   4. Check http://localhost:8001/api/health for status")
        print("\n" + "=" * 60)
        log("Press Ctrl+C to stop all services", Colors.RED)
        print("=" * 60)
        
        # Monitor processes
        while True:
            for name, proc, url in processes:
                ret = proc.poll()
                if ret is not None and ret != 0:
                    log(f"{name} exited with code {ret}!", Colors.RED)
                    stdout, stderr = proc.communicate()
                    if stderr:
                        print(f"Error: {stderr.decode()[:500]}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n")
        log("Shutting down all services...", Colors.YELLOW)
        
        for name, proc, url in processes:
            log(f"Stopping {name}...")
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                else:
                    proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        
        log("All services stopped. Goodbye!", Colors.GREEN)

if __name__ == "__main__":
    main()
