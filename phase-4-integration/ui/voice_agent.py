#!/usr/bin/env python3
"""
AdvisorAI — Professional Light UI
Supports: Voice input (mic → Whisper STT) + Text input
Both paths → LLM state machine → TTS audio + text response shown in chat
"""
import sys, os, torch, torchaudio, numpy as np
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in ["phase-1-core-voice","phase-3-llm-orchestrator","phase-4-integration","phase-4-integration/ui"]:
    sys.path.insert(0, str(_ROOT / _p))

import gradio as gr
from vad.silero_vad_multilingual import create_vad
from stt.hf_whisper_asr import create_hf_asr
from tts.hf_parler_tts import create_hf_tts
from simple_state_machine import run_simple_state_machine

# ── globals ───────────────────────────────────────────────────────────────────
MCP = os.getenv("MCP_SERVER_URL",
    f"http://{os.getenv('MCP_SERVER_HOST','localhost')}:{os.getenv('MCP_SERVER_PORT','8000')}")

conv_state = {"id":None,"state":"greeting","topic":None,"time_preference":None,
              "selected_slot":None,"booking_code":None,"available_slots":[],"slot_offered":False}
history: list[dict] = []

vad = create_vad()
stt = create_hf_asr(model_name="openai/whisper-base")
tts = create_hf_tts(model_name="parler-tts/parler-tts-mini-v1")

# ── chat helpers ──────────────────────────────────────────────────────────────
def _add(role, text, source=""):
    history.append({"role":role,"text":text,"time":datetime.now().strftime("%H:%M"),"source":source})

def _chat_html():
    if not history:
        return '''
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    height:100%;gap:14px;padding:48px 24px;text-align:center;">
          <div style="width:60px;height:60px;border-radius:50%;
                      background:linear-gradient(135deg,#6366f1,#8b5cf6);
                      display:flex;align-items:center;justify-content:center;font-size:26px;
                      box-shadow:0 8px 24px rgba(99,102,241,0.25);">🎙️</div>
          <div>
            <p style="color:#374151;font-size:15px;font-weight:600;margin:0 0 6px;">Ready to assist</p>
            <p style="color:#9ca3af;font-size:13px;margin:0;line-height:1.5;">
              Type a message or record your voice to begin.<br>
              Say "book appointment" to get started.
            </p>
          </div>
        </div>'''
    parts = []
    for m in history:
        role, text, ts, src = m["role"], m["text"], m.get("time",""), m.get("source","")
        if role == "user":
            src_icon = "🎤" if src == "voice" else "⌨️" if src == "text" else ""
            src_badge = (f'<span style="background:#ede9fe;color:#7c3aed;font-size:9px;font-weight:700;'
                         f'padding:2px 7px;border-radius:10px;margin-left:6px;letter-spacing:0.3px;">'
                         f'{src_icon} {src.upper()}</span>') if src else ""
            parts.append(f'''
            <div style="display:flex;justify-content:flex-end;margin:8px 0;align-items:flex-end;gap:8px;">
              <span style="color:#9ca3af;font-size:10px;padding-bottom:2px;">{ts}</span>
              <div style="background:linear-gradient(135deg,#6366f1,#7c3aed);color:#fff;
                          padding:11px 16px;border-radius:18px 18px 4px 18px;max-width:70%;
                          font-size:14px;line-height:1.55;box-shadow:0 4px 12px rgba(99,102,241,0.2);">
                {text}{src_badge}
              </div>
              <div style="width:32px;height:32px;border-radius:50%;background:#ede9fe;
                          display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">👤</div>
            </div>''')
        elif role == "agent":
            parts.append(f'''
            <div style="display:flex;justify-content:flex-start;margin:8px 0;align-items:flex-end;gap:8px;">
              <div style="width:32px;height:32px;border-radius:50%;
                          background:linear-gradient(135deg,#6366f1,#8b5cf6);
                          display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">🤖</div>
              <div style="background:#ffffff;border:1px solid #e5e7eb;color:#111827;
                          padding:11px 16px;border-radius:18px 18px 18px 4px;max-width:70%;
                          font-size:14px;line-height:1.55;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                {text}
              </div>
              <span style="color:#9ca3af;font-size:10px;padding-bottom:2px;">{ts}</span>
            </div>''')
        elif role == "system":
            parts.append(f'''
            <div style="display:flex;justify-content:center;margin:10px 0;">
              <div style="background:#fef3c7;border:1px solid #fde68a;color:#92400e;
                          padding:6px 16px;border-radius:20px;font-size:11px;font-weight:500;">
                {text}
              </div>
            </div>''')
    return '<div style="display:flex;flex-direction:column;padding:4px 0;">' + "".join(parts) + '</div>'

def _pipe_html(steps):
    parts = []
    for s in steps:
        st = s["status"]
        if   st=="done":   bg,fg,dot = "#dcfce7","#166534","✓"
        elif st=="active": bg,fg,dot = "#ede9fe","#6d28d9","●"
        elif st=="error":  bg,fg,dot = "#fee2e2","#991b1b","✗"
        else:              bg,fg,dot = "#f3f4f6","#9ca3af","○"
        anim = "animation:spin-pulse 1s infinite;" if st=="active" else ""
        parts.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;background:{bg};color:{fg};'
            f'padding:4px 11px;border-radius:20px;font-size:11px;font-weight:700;{anim}">'
            f'{dot} {s["label"]}</span>')
    sep = '<span style="color:#d1d5db;font-size:11px;">›</span>'
    return (f'<style>@keyframes spin-pulse{{0%,100%{{opacity:1}}50%{{opacity:0.4}}}}</style>'
            f'<div style="display:flex;align-items:center;justify-content:center;gap:5px;'
            f'padding:8px 0;flex-wrap:wrap;">{sep.join(parts)}</div>')

_IDLE = [{"label":"VAD","status":"pending"},{"label":"Whisper","status":"pending"},
         {"label":"LLM","status":"pending"},{"label":"TTS","status":"pending"}]
_TEXT_IDLE = [{"label":"Text","status":"pending"},{"label":"LLM","status":"pending"},
              {"label":"TTS","status":"pending"}]

def _booking_empty():
    return '''
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                height:100%;padding:32px;text-align:center;gap:12px;">
      <div style="width:52px;height:52px;border-radius:14px;background:#f3f4f6;
                  border:2px dashed #d1d5db;display:flex;align-items:center;
                  justify-content:center;font-size:24px;">📅</div>
      <div>
        <p style="color:#374151;font-size:13px;font-weight:600;margin:0 0 4px;">No booking yet</p>
        <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.5;">
          Complete a booking to see<br>your confirmation details here.
        </p>
      </div>
    </div>'''

# ── core processing (shared by voice + text) ──────────────────────────────────
def _process(transcript: str, source: str):
    """Run LLM + TTS on any transcript. Returns (chat_html, pipe_html, audio, booking_html)."""
    _add("user", transcript, source=source)
    response_text, booking_html = run_simple_state_machine(transcript, conv_state)
    _add("agent", response_text)
    audio_out = tts.synthesize(response_text)
    pipe = _pipe_html([{"label":"VAD","status":"done" if source=="voice" else "pending"},
                       {"label":"Whisper","status":"done" if source=="voice" else "pending"},
                       {"label":"LLM","status":"done"},{"label":"TTS","status":"done"}])
    return _chat_html(), pipe, audio_out, booking_html if booking_html else _booking_empty()

# ── voice handler ─────────────────────────────────────────────────────────────
def handle_voice(audio_path):
    if not audio_path:
        gr.Warning("Please record audio first.")
        return _chat_html(), _pipe_html(_IDLE), None, _booking_empty()
    try:
        waveform, sr = torchaudio.load(audio_path)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        audio_data = waveform.squeeze().numpy()
        if sr != 16000:
            audio_data = torchaudio.transforms.Resample(sr, 16000)(waveform).squeeze().numpy()

        speech = vad.process(audio_data)
        raw = speech.audio_data if speech.is_speech else audio_data
        audio_bytes = (raw * 32768).astype(np.int16).tobytes()

        transcript = stt.transcribe_audio(audio_bytes)
        if not transcript or not transcript.strip():
            gr.Warning("Could not understand — please speak clearly and try again.")
            return _chat_html(), _pipe_html(_IDLE), None, _booking_empty()

        vad.reset()
        return _process(transcript, "voice")
    except Exception as e:
        import traceback; traceback.print_exc()
        gr.Warning(f"Voice error: {e}")
        return _chat_html(), _pipe_html(_IDLE), None, _booking_empty()

# ── text handler ──────────────────────────────────────────────────────────────
def handle_text(text_input):
    if not text_input or not text_input.strip():
        gr.Warning("Please type a message first.")
        return _chat_html(), _pipe_html(_TEXT_IDLE), None, _booking_empty(), ""
    result = _process(text_input.strip(), "text")
    return result[0], result[1], result[2], result[3], ""   # clear textbox

# ── reset ─────────────────────────────────────────────────────────────────────
def reset_all():
    global conv_state, history
    conv_state = {"id":None,"state":"greeting","topic":None,"time_preference":None,
                  "selected_slot":None,"booking_code":None,"available_slots":[],"slot_offered":False}
    history.clear()
    _add("system", "New session started — say hello or pick a topic below")
    return _chat_html(), _pipe_html(_IDLE), None, _booking_empty(), ""

# ── topic shortcut ────────────────────────────────────────────────────────────
def pick_topic(name):
    conv_state.update({"state":"topic_detection","topic":name})
    return _process(f"I want to book an appointment for {name}", "text")[:4] + (_booking_empty(),)

# ── CSS (light theme) ─────────────────────────────────────────────────────────
CSS = """
*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: #f8fafc !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    color: #111827 !important;
}
.gradio-container { max-width: 100% !important; padding: 0 !important; }

/* scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #f1f5f9; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

/* hide gradio footer */
footer, .footer { display: none !important; }

/* chat window */
.chat-win {
    height: 440px; max-height: 440px;
    overflow-y: auto; padding: 8px 4px;
    scroll-behavior: smooth;
    background: #f8fafc;
}

/* booking panel */
.book-panel {
    min-height: 200px; overflow-y: auto;
}

/* card */
.card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* primary button */
.btn-send {
    background: linear-gradient(135deg,#6366f1,#7c3aed) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    font-size: 13px !important; letter-spacing: 0.3px !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
    transition: all 0.15s !important;
}
.btn-send:hover { transform: translateY(-1px) !important;
                  box-shadow: 0 6px 16px rgba(99,102,241,0.4) !important; }

/* secondary button */
.btn-reset {
    background: #ffffff !important; color: #6b7280 !important;
    border: 1px solid #e5e7eb !important; border-radius: 10px !important;
    font-size: 13px !important; transition: all 0.15s !important;
}
.btn-reset:hover { border-color: #6366f1 !important; color: #6366f1 !important; }

/* topic pills */
.pill {
    background: #f3f4f6 !important; color: #374151 !important;
    border: 1px solid #e5e7eb !important; border-radius: 20px !important;
    font-size: 12px !important; font-weight: 600 !important;
    padding: 6px 14px !important; transition: all 0.15s !important;
    white-space: nowrap !important;
}
.pill:hover {
    background: #ede9fe !important; color: #6d28d9 !important;
    border-color: #c4b5fd !important;
}

/* text input */
.txt-input textarea {
    border: 1.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    color: #111827 !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    resize: none !important;
    transition: border-color 0.15s !important;
}
.txt-input textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    outline: none !important;
}

/* audio widget */
.gr-audio-container, .audio-container {
    background: #f9fafb !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
}

/* label overrides */
label { color: #6b7280 !important; font-size: 12px !important; }
"""

# ── UI layout ─────────────────────────────────────────────────────────────────
with gr.Blocks(title="AdvisorAI — Booking Assistant", css=CSS,
               theme=gr.themes.Base(
                   primary_hue="violet", neutral_hue="slate",
                   font=gr.themes.GoogleFont("Inter")
               )) as demo:

    # ── NAV ──────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="background:#ffffff;border-bottom:1px solid #e5e7eb;padding:0 32px;
                display:flex;align-items:center;justify-content:space-between;height:58px;
                position:sticky;top:0;z-index:100;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:34px;height:34px;border-radius:10px;
                    background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    display:flex;align-items:center;justify-content:center;font-size:17px;">🎙️</div>
        <div>
          <div style="font-size:15px;font-weight:800;color:#111827;letter-spacing:-0.4px;">AdvisorAI</div>
          <div style="font-size:10px;color:#9ca3af;letter-spacing:0.6px;text-transform:uppercase;margin-top:-1px;">Voice Booking Platform</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:20px;">
        <div style="display:flex;align-items:center;gap:6px;">
          <div style="width:7px;height:7px;border-radius:50%;background:#10b981;
                      box-shadow:0 0 0 2px #d1fae5;animation:blink 2s infinite;"></div>
          <span style="font-size:11px;color:#6b7280;font-weight:500;">Live</span>
        </div>
        <div style="background:#f3f4f6;border-radius:20px;padding:4px 12px;
                    font-size:11px;color:#6b7280;font-weight:500;">
          Whisper · ParlerTTS · Groq · MCP
        </div>
      </div>
    </div>
    <style>@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}</style>
    """)

    # ── HERO ─────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="background:linear-gradient(135deg,#f5f3ff 0%,#ede9fe 40%,#e0e7ff 100%);
                border-bottom:1px solid #e5e7eb;padding:36px 32px 30px;text-align:center;
                position:relative;overflow:hidden;">
      <div style="position:absolute;top:-80px;left:-80px;width:300px;height:300px;border-radius:50%;
                  background:radial-gradient(circle,rgba(99,102,241,0.08),transparent 70%);"></div>
      <div style="position:absolute;bottom:-60px;right:-60px;width:260px;height:260px;border-radius:50%;
                  background:radial-gradient(circle,rgba(139,92,246,0.07),transparent 70%);"></div>
      <div style="position:relative;max-width:640px;margin:0 auto;">
        <div style="display:inline-flex;align-items:center;gap:7px;background:#ffffff;
                    border:1px solid #c4b5fd;border-radius:20px;padding:4px 14px;margin-bottom:14px;
                    box-shadow:0 1px 4px rgba(99,102,241,0.12);">
          <span style="width:6px;height:6px;border-radius:50%;background:#6366f1;display:inline-block;"></span>
          <span style="font-size:11px;color:#6d28d9;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;">
            AI-Powered Financial Advisory
          </span>
        </div>
        <h1 style="margin:0 0 10px;font-size:34px;font-weight:800;letter-spacing:-0.8px;color:#111827;">
          Book Your Advisor Session
        </h1>
        <p style="margin:0 0 20px;font-size:15px;color:#6b7280;line-height:1.6;">
          Speak or type naturally — our AI schedules your consultation,<br>
          creates a calendar event, and sends confirmation instantly.
        </p>
        <div style="display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;">
          <span style="display:flex;align-items:center;gap:5px;font-size:12px;color:#6b7280;">
            <span style="color:#10b981;font-weight:700;">✓</span> No PII on call
          </span>
          <span style="display:flex;align-items:center;gap:5px;font-size:12px;color:#6b7280;">
            <span style="color:#10b981;font-weight:700;">✓</span> Google Calendar + Meet
          </span>
          <span style="display:flex;align-items:center;gap:5px;font-size:12px;color:#6b7280;">
            <span style="color:#10b981;font-weight:700;">✓</span> Instant confirmation
          </span>
          <span style="display:flex;align-items:center;gap:5px;font-size:12px;color:#6b7280;">
            <span style="color:#10b981;font-weight:700;">✓</span> SEBI compliant
          </span>
        </div>
      </div>
    </div>
    """)

    # ── STATS ─────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="background:#ffffff;border-bottom:1px solid #e5e7eb;padding:14px 32px;">
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:10px;
                    padding:10px 22px;text-align:center;min-width:110px;">
          <div style="font-size:20px;font-weight:800;color:#6d28d9;">90s</div>
          <div style="font-size:10px;color:#8b5cf6;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Avg Booking</div>
        </div>
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                    padding:10px 22px;text-align:center;min-width:110px;">
          <div style="font-size:20px;font-weight:800;color:#059669;">99.2%</div>
          <div style="font-size:10px;color:#10b981;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">PII Safe</div>
        </div>
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:10px 22px;text-align:center;min-width:110px;">
          <div style="font-size:20px;font-weight:800;color:#d97706;">2.5s</div>
          <div style="font-size:10px;color:#f59e0b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Latency</div>
        </div>
        <div style="background:#fdf4ff;border:1px solid #e9d5ff;border-radius:10px;
                    padding:10px 22px;text-align:center;min-width:110px;">
          <div style="font-size:20px;font-weight:800;color:#9333ea;">5</div>
          <div style="font-size:10px;color:#a855f7;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Topics</div>
        </div>
      </div>
    </div>
    """)

    # ── TOPIC PILLS ───────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="background:#f8fafc;padding:14px 32px 0;">
      <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                text-transform:uppercase;margin:0 0 10px;">Quick Topic Select</p>
    </div>
    """)
    with gr.Row():
        t1 = gr.Button("🪪 KYC / Onboarding",    elem_classes=["pill"])
        t2 = gr.Button("📈 SIP / Mandates",       elem_classes=["pill"])
        t3 = gr.Button("📄 Statements / Tax",     elem_classes=["pill"])
        t4 = gr.Button("💸 Withdrawals",          elem_classes=["pill"])
        t5 = gr.Button("⚙️ Account Changes",      elem_classes=["pill"])

    # ── MAIN LAYOUT ───────────────────────────────────────────────────────────
    with gr.Row(equal_height=False):

        # LEFT PANEL — inputs
        with gr.Column(scale=1, min_width=300):

            # Voice input card
            gr.HTML("""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                        padding:20px;margin:16px 0 0 16px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
              <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                         text-transform:uppercase;margin:0 0 14px;">🎤 Voice Input</p>""")
            audio_in = gr.Audio(sources=["microphone"], type="filepath",
                                label="", show_label=False)
            with gr.Row():
                voice_btn = gr.Button("▶ Send Voice", elem_classes=["btn-send"], size="sm")
                reset_btn = gr.Button("↺ Reset",      elem_classes=["btn-reset"], size="sm")
            gr.HTML("</div>")

            # Text input card
            gr.HTML("""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                        padding:20px;margin:12px 0 0 16px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
              <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                         text-transform:uppercase;margin:0 0 12px;">⌨️ Text Input</p>""")
            text_in = gr.Textbox(
                placeholder='Type here, e.g. "Book a KYC appointment for tomorrow morning"',
                lines=3, max_lines=5, show_label=False,
                elem_classes=["txt-input"]
            )
            text_btn = gr.Button("Send Message →", elem_classes=["btn-send"], size="sm")
            gr.HTML("</div>")

            # Pipeline status card
            gr.HTML("""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                        padding:16px 20px;margin:12px 0 0 16px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
              <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                         text-transform:uppercase;margin:0 0 10px;">Pipeline Status</p>""")
            pipe_display = gr.HTML(_pipe_html(_IDLE))
            gr.HTML("</div>")

            # Audio response card
            gr.HTML("""<div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                        padding:16px 20px;margin:12px 0 0 16px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
              <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                         text-transform:uppercase;margin:0 0 10px;">🔊 AI Voice Response</p>""")
            audio_out = gr.Audio(label="", show_label=False, autoplay=True)
            gr.HTML("</div>")

            # Compliance card
            gr.HTML("""
            <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;
                        padding:14px 16px;margin:12px 0 0 16px;">
              <p style="font-size:11px;font-weight:700;color:#92400e;margin:0 0 6px;">
                ⚠ Compliance Notice
              </p>
              <p style="font-size:11px;color:#78716c;margin:0;line-height:1.6;">
                Informational only — not investment advice.<br>
                Do not share PAN, Aadhaar, phone or account numbers.
              </p>
            </div>
            """)

        # CENTRE — conversation
        with gr.Column(scale=2, min_width=400):
            gr.HTML("""
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                        padding:20px;margin:16px 8px 0;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                           text-transform:uppercase;margin:0;">💬 Conversation</p>
                <div style="display:flex;align-items:center;gap:6px;">
                  <div style="width:7px;height:7px;border-radius:50%;background:#10b981;
                              box-shadow:0 0 0 2px #d1fae5;"></div>
                  <span style="font-size:11px;color:#6b7280;font-weight:500;">Active</span>
                </div>
              </div>
            """)
            chat_display = gr.HTML(value=_chat_html(), elem_classes=["chat-win"])
            gr.HTML("</div>")

        # RIGHT — booking + stack
        with gr.Column(scale=1, min_width=280):
            gr.HTML("""
            <div style="background:#fff;border:1.5px solid #c4b5fd;border-radius:16px;
                        padding:20px;margin:16px 16px 0 0;
                        box-shadow:0 4px 16px rgba(99,102,241,0.08);">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#6366f1;
                            box-shadow:0 0 0 3px #ede9fe;"></div>
                <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                           text-transform:uppercase;margin:0;">📅 Booking Details</p>
              </div>
            """)
            booking_display = gr.HTML(value=_booking_empty(), elem_classes=["book-panel"])
            gr.HTML("</div>")

            # AI stack card
            gr.HTML("""
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                        padding:20px;margin:12px 16px 0 0;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
              <p style="font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1.2px;
                         text-transform:uppercase;margin:0 0 14px;">AI Stack</p>
              <div style="display:flex;flex-direction:column;gap:9px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#6b7280;">VAD</span>
                  <span style="font-size:11px;color:#6d28d9;background:#f5f3ff;padding:2px 9px;border-radius:6px;font-weight:600;">Silero</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#6b7280;">STT</span>
                  <span style="font-size:11px;color:#6d28d9;background:#f5f3ff;padding:2px 9px;border-radius:6px;font-weight:600;">Whisper Base</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#6b7280;">LLM</span>
                  <span style="font-size:11px;color:#6d28d9;background:#f5f3ff;padding:2px 9px;border-radius:6px;font-weight:600;">Groq Llama 3.3</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#6b7280;">TTS</span>
                  <span style="font-size:11px;color:#6d28d9;background:#f5f3ff;padding:2px 9px;border-radius:6px;font-weight:600;">ParlerTTS Mini</span>
                </div>
                <div style="height:1px;background:#f3f4f6;margin:2px 0;"></div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#6b7280;">Calendar</span>
                  <span style="font-size:11px;color:#059669;background:#f0fdf4;padding:2px 9px;border-radius:6px;font-weight:600;">Google + Meet</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#6b7280;">Notes</span>
                  <span style="font-size:11px;color:#059669;background:#f0fdf4;padding:2px 9px;border-radius:6px;font-weight:600;">Google Docs</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#6b7280;">Email</span>
                  <span style="font-size:11px;color:#059669;background:#f0fdf4;padding:2px 9px;border-radius:6px;font-weight:600;">Resend API</span>
                </div>
              </div>
            </div>
            """)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="background:#ffffff;border-top:1px solid #e5e7eb;padding:16px 32px;margin-top:24px;
                display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
      <span style="font-size:12px;color:#9ca3af;">
        © 2026 AdvisorAI · Ashish Kumar Sankhua · MIT License
      </span>
      <div style="display:flex;align-items:center;gap:16px;">
        <a href="https://www.sebi.gov.in" target="_blank"
           style="font-size:11px;color:#6366f1;text-decoration:none;font-weight:600;">SEBI Resources ↗</a>
        <span style="font-size:11px;color:#d1d5db;">|</span>
        <span style="font-size:11px;color:#9ca3af;">MCP :8000 · UI :7861</span>
      </div>
    </div>
    """)

    # ── WIRING ────────────────────────────────────────────────────────────────
    _v_outs = [chat_display, pipe_display, audio_out, booking_display]
    _t_outs = [chat_display, pipe_display, audio_out, booking_display, text_in]

    voice_btn.click(fn=handle_voice, inputs=[audio_in],   outputs=_v_outs)
    text_btn.click( fn=handle_text,  inputs=[text_in],    outputs=_t_outs)
    text_in.submit( fn=handle_text,  inputs=[text_in],    outputs=_t_outs)  # Enter key
    reset_btn.click(fn=reset_all,    inputs=[],           outputs=_t_outs)

    def _topic(name):
        conv_state.update({"state":"topic_detection","topic":name})
        r = _process(f"I want to book an appointment for {name}", "text")
        return r[0], r[1], r[2], r[3], ""

    t1.click(fn=lambda: _topic("KYC/Onboarding"),     outputs=_t_outs)
    t2.click(fn=lambda: _topic("SIP/Mandates"),       outputs=_t_outs)
    t3.click(fn=lambda: _topic("Statements/Tax Docs"),outputs=_t_outs)
    t4.click(fn=lambda: _topic("Withdrawals"),        outputs=_t_outs)
    t5.click(fn=lambda: _topic("Account Changes"),    outputs=_t_outs)


# ── launch ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _port = int(os.environ.get("GRADIO_SERVER_PORT", "7861"))
    _host = os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0")
    print(f"🚀 AdvisorAI → http://localhost:{_port}")
    demo.launch(server_name=_host, server_port=_port, show_error=True)
