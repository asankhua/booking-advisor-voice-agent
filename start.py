#!/usr/bin/env python3
"""
start.py — Unified launcher
Starts:
  1. MCP Server  (Phase 2) → http://localhost:8000
  2. Voice Agent (Phase 4) → http://localhost:7861
"""
import os, sys, time, signal, subprocess, socket, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; C = "\033[96m"; B = "\033[1m"; X = "\033[0m"
def info(m):  print(f"{G}[INFO]{X}  {m}", flush=True)
def warn(m):  print(f"{Y}[WARN]{X}  {m}", flush=True)
def err(m):   print(f"{R}[ERR]{X}   {m}", flush=True)

# ── env ──────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    info(".env loaded")
except Exception:
    warn("python-dotenv not found, skipping .env load")

# ── process registry ─────────────────────────────────────────────────────────
procs: list[subprocess.Popen] = []

def _cleanup(*_):
    print(f"\n{Y}Stopping servers...{X}", flush=True)
    for p in procs:
        try: p.terminate()
        except: pass
    for p in procs:
        try: p.wait(timeout=5)
        except: p.kill()
    print(f"{G}Done.{X}", flush=True)
    sys.exit(0)

signal.signal(signal.SIGINT,  _cleanup)
signal.signal(signal.SIGTERM, _cleanup)

def _stream(proc, tag):
    def _r():
        for line in proc.stdout:
            print(f"  {C}[{tag}]{X} {line}", end="", flush=True)
    threading.Thread(target=_r, daemon=True).start()

def _wait_port(port, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(1)
    return False

def launch(name, cmd, cwd, extra_env=None):
    env = {**os.environ, **(extra_env or {})}
    p = subprocess.Popen(cmd, cwd=str(cwd), env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    procs.append(p)
    _stream(p, name)
    info(f"{name} started (pid={p.pid})")
    return p

# ── main ─────────────────────────────────────────────────────────────────────
print(f"\n{B}{'='*56}{X}")
print(f"{B}  AdvisorAI — Full Stack Launcher{X}")
print(f"{B}{'='*56}{X}\n")

# 1. MCP Server
info("Starting MCP Server on :8000 ...")
mcp = launch(
    "MCP",
    [sys.executable, "-m", "uvicorn", "server.mcp_server:app",
     "--host", "0.0.0.0", "--port", "8000"],
    ROOT / "phase-2-mcp-tools",
)
if _wait_port(8000, timeout=30):
    info(f"MCP Server ready  →  {C}http://localhost:8000{X}")
    info(f"API Docs          →  {C}http://localhost:8000/docs{X}")
else:
    warn("MCP Server slow to start — continuing anyway")

# 2. FastAPI UI server (serves HTML frontend + voice/chat API)
info("Starting AdvisorAI API server on :8001  (model load may take ~60s) ...")
ui = launch(
    "UI",
    [sys.executable, str(ROOT / "phase-4-integration" / "api_server.py")],
    ROOT,
    extra_env={"API_PORT": "8001"},
)
if _wait_port(8001, timeout=180):
    info(f"AdvisorAI UI ready →  {C}http://localhost:8001{X}")
else:
    warn("UI server taking longer than expected — models still loading, check logs above")

print(f"\n{B}{'='*56}{X}")
print(f"{G}{B}  Services:{X}")
print(f"  🔧 MCP Server  →  {C}http://localhost:8000{X}")
print(f"  📖 MCP Docs    →  {C}http://localhost:8000/docs{X}")
print(f"  🎙️  AdvisorAI   →  {C}http://localhost:8001{X}  ← open this")
print(f"{B}{'='*56}{X}")
print(f"\n{Y}Ctrl+C to stop.{X}\n")

# keep-alive
while True:
    time.sleep(3)
    for p, name in [(mcp, "MCP"), (ui, "UI")]:
        if p.poll() is not None:
            warn(f"{name} process exited (code {p.returncode}) — check logs above")
