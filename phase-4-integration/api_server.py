"""
api_server.py — FastAPI Backend  (port 8001)
Serves the HTML UI + REST endpoints for chat, voice, TTS
"""
import os, sys, json, base64, numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
for _p in ["phase-1-core-voice", "phase-3-llm-orchestrator",
           "phase-4-integration", "phase-4-integration/ui"]:
    sys.path.insert(0, str(ROOT / _p))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── voice pipeline ────────────────────────────────────────────────────────────
from vad.silero_vad_multilingual import create_vad
from simple_state_machine import run_simple_state_machine
from compliance.pii_detector import PIIDetector

import torch, torchaudio

VOICE_PROVIDER = os.getenv("VOICE_PROVIDER", "sarvam").lower()

if VOICE_PROVIDER == "sarvam":
    from stt.sarvam_stt import create_sarvam_stt
    from tts.sarvam_tts import create_sarvam_tts
    stt = create_sarvam_stt()
    tts_engine = create_sarvam_tts()
    print(f"🎙️  Voice provider: Sarvam AI (STT=Saaras v3, TTS=Bulbul v2)")
else:
    from stt.hf_whisper_asr import create_hf_asr
    from tts.hf_parler_tts import create_hf_tts
    stt = create_hf_asr(model_name="openai/whisper-base")
    stt.initial_prompt = "The speaker has an Indian English accent. Financial advisory booking."
    tts_engine = create_hf_tts(model_name="parler-tts/parler-tts-mini-v1")
    print(f"🎙️  Voice provider: Local HF (Whisper + ParlerTTS)")

vad = create_vad()
pii = PIIDetector()

# ── session store ─────────────────────────────────────────────────────────────
sessions: Dict[str, Dict] = {}

def get_session(sid: Optional[str]) -> tuple[str, Dict]:
    if sid and sid in sessions:
        return sid, sessions[sid]
    new_id = f"s_{datetime.now().strftime('%H%M%S%f')}"
    sessions[new_id] = {
        "id": None, "state": "greeting", "topic": None,
        "time_preference": None, "selected_slot": None,
        "booking_code": None, "available_slots": [], "slot_offered": False,
    }
    return new_id, sessions[new_id]

# ── app ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="AdvisorAI API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── models ────────────────────────────────────────────────────────────────────
class ChatReq(BaseModel):
    message: str
    session_id: Optional[str] = None

class AudioReq(BaseModel):
    audio_base64: str
    session_id: Optional[str] = None

# ── helpers ───────────────────────────────────────────────────────────────────

def _run(text: str, state: Dict):
    """Run state machine + TTS. Returns (response_text, booking_html, audio_b64, meet_link, mcp_status)."""
    response_text, booking_html, mcp_status = run_simple_state_machine(text, state)
    audio_bytes = None
    try:
        audio_bytes = tts_engine.synthesize(response_text)
    except Exception as e:
        print(f"TTS error ({VOICE_PROVIDER}): {e}")
    # If Sarvam TTS failed (no key / error), fall back to local Whisper TTS
    if not audio_bytes and VOICE_PROVIDER == "sarvam":
        try:
            from tts.hf_parler_tts import create_hf_tts as _hf_tts
            _fallback = _hf_tts(model_name="parler-tts/parler-tts-mini-v1")
            audio_bytes = _fallback.synthesize(response_text)
        except Exception as e2:
            print(f"TTS fallback error: {e2}")
    audio_b64 = base64.b64encode(audio_bytes).decode() if audio_bytes else ""
    meet_link = state.get("meet_link", "")
    return response_text, booking_html, audio_b64, meet_link, mcp_status

# ── endpoints ─────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/chat")
def chat(req: ChatReq):
    sid, state = get_session(req.session_id)
    if pii.has_pii(req.message):
        msg = "For your security, please don't share personal details on this call."
        audio_bytes = tts_engine.synthesize(msg)
        return {"session_id": sid, "response": msg, "booking_html": "",
                "meet_link": "", "mcp_status": {}, "audio_b64": base64.b64encode(audio_bytes).decode() if audio_bytes else ""}
    resp, booking_html, audio_b64, meet_link, mcp_status = _run(req.message, state)
    return {"session_id": sid, "response": resp,
            "booking_html": booking_html, "audio_b64": audio_b64,
            "meet_link": meet_link, "mcp_status": mcp_status,
            "booking_code": state.get("booking_code")}

@app.post("/api/voice")
def voice(req: AudioReq):
    sid, state = get_session(req.session_id)
    try:
        raw = base64.b64decode(req.audio_base64)
        transcript = ""

        if VOICE_PROVIDER == "sarvam":
            sarvam_key = os.getenv("SARVAM_API_KEY", "")
            if not sarvam_key or sarvam_key == "your_sarvam_api_key_here":
                # No valid key — fall back to local Whisper silently
                transcript = _local_transcribe(raw)
            else:
                import requests as _req
                r = _req.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers={"api-subscription-key": sarvam_key},
                    files={"file": ("audio.webm", raw, "audio/webm")},
                    data={"model": "saaras:v3", "language_code": "en-IN",
                          "with_timestamps": "false"},
                    timeout=30,
                )
                if r.status_code == 200:
                    transcript = r.json().get("transcript", "").strip()
                else:
                    print(f"Sarvam STT error {r.status_code}: {r.text[:200]}")
                    transcript = _local_transcribe(raw)
        else:
            transcript = _local_transcribe(raw)

        transcript = transcript.strip().lstrip("♪").strip()

        if not transcript:
            return {"session_id": sid, "transcript": "", "response": "",
                    "booking_html": "", "audio_b64": "", "error": "no_speech"}

        if pii.has_pii(transcript):
            msg = "For your security, please don't share personal details on this call."
            ab = tts_engine.synthesize(msg)
            return {"session_id": sid, "transcript": transcript, "response": msg,
                    "booking_html": "", "meet_link": "", "mcp_status": {},
                    "audio_b64": base64.b64encode(ab).decode() if ab else ""}

        resp, booking_html, audio_b64, meet_link, mcp_status = _run(transcript, state)
        return {"session_id": sid, "transcript": transcript, "response": resp,
                "booking_html": booking_html, "audio_b64": audio_b64,
                "meet_link": meet_link, "mcp_status": mcp_status,
                "booking_code": state.get("booking_code")}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _local_transcribe(raw: bytes) -> str:
    """Decode webm → numpy → Whisper. Used as fallback when Sarvam key missing."""
    import tempfile, os as _os
    from pydub import AudioSegment
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(raw); tmp_path = tmp.name
    try:
        seg = AudioSegment.from_file(tmp_path)
    finally:
        _os.unlink(tmp_path)
    seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio_data = np.frombuffer(seg.raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    vad.reset()
    # Use the current stt instance if it's Whisper, else use a cached local one
    global _local_stt
    if VOICE_PROVIDER != "sarvam":
        return stt.transcribe(audio_data, language="en")
    if _local_stt is None:
        from stt.hf_whisper_asr import create_hf_asr as _hf
        _local_stt = _hf(model_name="openai/whisper-base")
    return _local_stt.transcribe(audio_data, language="en")

_local_stt = None  # cached fallback Whisper instance

@app.get("/api/provider")
def get_provider():
    return {"provider": VOICE_PROVIDER}

@app.post("/api/provider")
def set_provider(body: dict):
    global VOICE_PROVIDER, stt, tts_engine
    p = body.get("provider", "sarvam").lower()
    if p not in ("sarvam", "local"):
        raise HTTPException(status_code=400, detail="provider must be 'sarvam' or 'local'")
    if p == VOICE_PROVIDER:
        return {"provider": VOICE_PROVIDER, "changed": False}
    VOICE_PROVIDER = p
    if p == "sarvam":
        from stt.sarvam_stt import create_sarvam_stt
        from tts.sarvam_tts import create_sarvam_tts
        stt = create_sarvam_stt()
        tts_engine = create_sarvam_tts()
        print("🔄 Switched to Sarvam AI (STT + TTS)")
    else:
        from stt.hf_whisper_asr import create_hf_asr
        from tts.hf_parler_tts import create_hf_tts
        stt = create_hf_asr(model_name="openai/whisper-base")
        stt.initial_prompt = "The speaker has an Indian English accent. Financial advisory booking."
        tts_engine = create_hf_tts(model_name="parler-tts/parler-tts-mini-v1")
        print("🔄 Switched to Local HF (Whisper + ParlerTTS)")
    return {"provider": VOICE_PROVIDER, "changed": True}

@app.post("/api/reset")
def reset(req: ChatReq):
    sid = req.session_id
    if sid and sid in sessions:
        del sessions[sid]
    new_sid, _ = get_session(None)
    return {"session_id": new_sid}

# ── serve frontend ────────────────────────────────────────────────────────────
UI_DIR = ROOT / "frontend" / "ui_dist"

@app.get("/license")
def license_file():
    license_path = ROOT / "LICENSE"
    if license_path.exists():
        return FileResponse(str(license_path), media_type="text/plain")
    raise HTTPException(status_code=404, detail="LICENSE file not found")

@app.get("/")
def index():
    return FileResponse(str(UI_DIR / "index.html"))

if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8001"))
    print(f"🚀 AdvisorAI API  →  http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
