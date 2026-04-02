# Booking Advisor Voice Agent — Architecture

**Author:** Ashish Kumar Sankhua  
**Last Updated:** April 2026  
**Status:** Production Ready

---

## Overview

A compliant, AI-powered voice booking assistant for financial advisory appointments. Users speak or type naturally; the system handles the full workflow — intent detection, slot offering, calendar creation, audit logging, and email notification — in under 90 seconds.

---

## Tech Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| STT (default) | Sarvam AI — Saaras v3 | Indian accent, cloud API, ~300ms |
| TTS (default) | Sarvam AI — Bulbul v2 | Indian English voice, ~500ms |
| STT (fallback) | OpenAI Whisper Base (HF) | Offline, 74MB, ~1.5s on CPU |
| TTS (fallback) | ParlerTTS Mini v1 (HF) | Offline, 600MB, ~5s on CPU |
| VAD | Silero VAD | Local, ~20MB, 500ms |
| LLM | Groq — Llama 3.3 70B | Cloud, ~800ms |
| UI | HTML + Tailwind CSS | Vanilla, no framework |
| Backend | FastAPI (port 8001) | Serves UI + REST API |
| MCP Server | FastAPI (port 8000) | Calendar / Notes / Email tools |
| Calendar | Google Calendar API | Real events + Google Meet |
| Notes | Google Docs API | Audit trail |
| Email | Resend API | HTML notifications |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB BROWSER (port 8001)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Booking Advisor Voice Agent  (HTML + Tailwind + JS)     │   │
│  │                                                          │   │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌────────────┐  │   │
│  │  │ 🎤 Voice    │  │ 💬 Conversation  │  │ 📅 Booking │  │   │
│  │  │   Input     │  │    Chat Panel    │  │   Details  │  │   │
│  │  └─────────────┘  └──────────────────┘  └────────────┘  │   │
│  │                                                          │   │
│  │  Pipeline: VAD › Whisper › LLM › TTS › Calendar › Doc › Email │
│  │  Voice Provider Toggle: [Sarvam AI] | [Whisper+Parler]   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP POST /api/voice  /api/chat
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend  api_server.py  :8001               │
│                                                                  │
│  VOICE_PROVIDER=sarvam (default)                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │ Sarvam STT   │   │ Groq LLM     │   │ Sarvam TTS           │ │
│  │ Saaras v3    │──▶│ Llama 3.3 70B│──▶│ Bulbul v2            │ │
│  │ (Indian EN)  │   │ State Machine│   │ (Indian EN voice)    │ │
│  └──────────────┘   └──────┬───────┘   └──────────────────────┘ │
│                            │                                     │
│  VOICE_PROVIDER=local      │                                     │
│  ┌──────────────┐          │ on booking confirm                  │
│  │ Whisper Base │          ▼                                     │
│  │ ParlerTTS    │   ┌──────────────────────────────────────────┐ │
│  └──────────────┘   │  simple_state_machine.py                 │ │
│                     │  4-State Flow:                           │ │
│  VAD (Silero)       │  greeting → topic → time → confirm       │ │
│  PII Detector       └──────────────┬───────────────────────────┘ │
└─────────────────────────────────────┼───────────────────────────┘
                                      │ HTTP POST
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              MCP Server  mcp_server.py  :8000                    │
│                                                                  │
│  POST /calendar/event  ──▶  Google Calendar API (+ Meet link)   │
│  POST /notes/append    ──▶  Google Docs API (audit trail)       │
│  POST /email/draft     ──▶  Resend API (advisor notification)   │
│  GET  /logs/mcp-calls  ──▶  mcp_calls.log                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4-State Conversation Flow

```
State 1: GREETING & DISCLAIMER
  "This call is informational only. Not investment advice.
   No PII will be collected. Which topic: KYC, SIP,
   Statements, Withdrawals, or Account Changes?"
         │
         ▼
State 2: INTENT & TOPIC DETECTION
  Keyword-based detection of 5 topics + 5 intents.
  Investment advice → refused + SEBI link.
         │
         ▼
State 3: TIME PREFERENCE & SLOT OFFERING
  "Morning, afternoon, or evening?"
  → Offers 2 slots in IST
         │
         ▼
State 4: CONFIRMATION & EXECUTION
  Generate booking code (e.g. KYC-4821)
  → POST /calendar/event  (Google Calendar + Meet)
  → POST /notes/append    (Google Docs audit)
  → POST /email/draft     (Resend — approval-gated)
  → Read code + confirm time in IST
```

---

## Voice Provider Toggle

Two providers, hot-swappable at runtime via UI toggle or `.env`:

| | Sarvam AI (default) | Local HuggingFace |
|--|---------------------|-------------------|
| STT | Saaras v3 | Whisper Base |
| TTS | Bulbul v2 | ParlerTTS Mini |
| Latency | ~800ms total | ~6-8s on CPU |
| Accent | Indian English native | Prompt-guided |
| Requires | `SARVAM_API_KEY` | No API key |
| Audio format | webm/opus direct | pydub decode |

Switch via:
- UI footer toggle (live, no restart)
- `.env`: `VOICE_PROVIDER=sarvam` or `VOICE_PROVIDER=local`
- API: `POST /api/provider {"provider": "sarvam"}`

---

## MCP Tools

| Tool | Endpoint | Provider | Output |
|------|----------|----------|--------|
| Calendar | `POST /calendar/event` | Google Calendar API | Event + Meet link |
| Notes | `POST /notes/append` | Google Docs API | Audit entry |
| Email | `POST /email/draft` | Resend API | Approval-gated email |
| Availability | `POST /calendar/availability` | Mock / Google Cal | 2 slots |
| Hold | `POST /calendar/hold` | Mock | Tentative hold |

---

## Pipeline Status (UI)

The UI shows a real-time progress bar with 7 steps:

```
VAD › Whisper › LLM › TTS › Calendar › Doc › Email
 ●       ●       ●     ●       ●          ●      ●
gray   amber   amber  amber   green     green  green
(idle) (active)(done) (done)  (done)    (done) (done)
```

- **Amber** = active/processing
- **Green** = done successfully  
- **Red** = error

---

## Security & Compliance

| Control | Implementation |
|---------|----------------|
| PII detection | Regex: phone, email, PAN, Aadhaar, account numbers |
| PII response | Immediate interruption, redirect to secure channel |
| Disclaimer | Hardcoded in State 1, every session |
| Investment advice | Intent classifier → refusal + SEBI link |
| Audit trail | Every booking logged to Google Docs with timestamp |
| Email approval | `DRAFT_REQUIRES_APPROVAL` — not auto-sent |
| Booking code | Format `XXX-NNNN` (e.g. `KYC-4821`) |

---

## Folder Structure

```
.
├── start.py                           # Unified launcher
├── requirements.txt
├── .env / .env.example
├── frontend/ui_dist/index.html        # Web UI
├── phase-1-core-voice/
│   ├── stt/sarvam_stt.py              # Sarvam STT (default)
│   ├── stt/hf_whisper_asr.py          # Whisper (fallback)
│   ├── tts/sarvam_tts.py              # Sarvam TTS (default)
│   ├── tts/hf_parler_tts.py           # ParlerTTS (fallback)
│   └── vad/silero_vad_multilingual.py
├── phase-2-mcp-tools/
│   ├── server/mcp_server.py           # MCP server :8000
│   └── providers/                     # Google Cal, Docs, Resend
├── phase-3-llm-orchestrator/
│   ├── core/orchestrator.py
│   └── nlu/intent_classifier.py
└── phase-4-integration/
    ├── api_server.py                  # Main backend :8001
    ├── compliance/pii_detector.py
    └── ui/simple_state_machine.py     # 4-state flow
```

---

## Running

```bash
python start.py
# MCP Server  → http://localhost:8000
# Voice Agent → http://localhost:8001
```

To switch voice provider without restart — use the toggle in the UI footer.

---

## Deployment

### Local

```bash
pip install -r requirements.txt      # also: brew install ffmpeg
cp .env.example .env                 # fill in API keys
python start.py                      # starts MCP :8000 + API :8001
```

### Hugging Face Spaces (Docker)

Single container runs both servers:
- MCP server starts on `:8000` (internal)
- FastAPI + UI serves on `:7860` (HF default port)

```
docker build -t advisor-voice-agent .
docker run -p 7860:7860 \
  -e GROQ_API_KEY=... \
  -e SARVAM_API_KEY=... \
  -e GOOGLE_CLIENT_ID=... \
  -e GOOGLE_CLIENT_SECRET=... \
  -e GOOGLE_REFRESH_TOKEN=... \
  -e GOOGLE_CALENDAR_ID=... \
  -e GOOGLE_DOC_ID=... \
  -e RESEND_API_KEY=... \
  advisor-voice-agent
```

Set all secrets in HF Space Settings → Repository secrets.

### GitHub → HF Auto-Sync

`.github/workflows/sync-to-huggingface.yml` — pushes to HF on every `main` commit.  
Requires `HF_TOKEN` in GitHub repo secrets.

---

## Security Notes

- `.env` is in `.gitignore` — never committed
- `config/google-credentials.json` and `config/google-token.json` are in `.gitignore`
- All secrets loaded via `os.getenv()` — no hardcoded values in code
- Rotate keys if accidentally exposed
