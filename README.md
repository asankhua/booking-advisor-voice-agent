---
title: Booking Advisor Voice Agent
emoji: 🎙️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 🎙️ Booking Advisor Voice Agent

AI-powered voice booking assistant for financial advisory appointments.  
Speak or type naturally — the AI schedules your consultation, creates a Google Calendar event with Meet link, logs an audit trail to Google Docs, and sends a confirmation email — all in under 90 seconds.

---

## Live URL

```
http://localhost:8001
```

---

## Deployment

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt
# Also install ffmpeg: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)

# 2. Configure environment
cp .env.example .env
# Edit .env — add your API keys

# 3. Start both servers
python start.py
```

### Hugging Face Spaces (Docker)

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select **Docker** as SDK
3. Add these secrets in Space Settings → Repository secrets:
   ```
   GROQ_API_KEY
   SARVAM_API_KEY
   GOOGLE_CLIENT_ID
   GOOGLE_CLIENT_SECRET
   GOOGLE_REFRESH_TOKEN
   GOOGLE_CALENDAR_ID
   GOOGLE_DOC_ID
   RESEND_API_KEY
   RESEND_FROM_EMAIL
   ```
4. Push code — GitHub Actions auto-syncs to HF on every push to `main`

The app runs on port **7860** (HF Spaces default). MCP server starts internally on port 8000.

### GitHub → HuggingFace Auto-Sync

Add `HF_TOKEN` to GitHub repo secrets (Settings → Secrets → Actions).  
Every push to `main` triggers `.github/workflows/sync-to-huggingface.yml`.

---

| Service | URL |
|---------|-----|
| Voice Agent UI | http://localhost:8001 |
| MCP Server | http://localhost:8000 |
| MCP API Docs | http://localhost:8000/docs |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| STT (default) | Sarvam AI — Saaras v3 | Indian accent speech recognition |
| TTS (default) | Sarvam AI — Bulbul v2 | Indian English voice synthesis |
| STT (fallback) | OpenAI Whisper Base (HF) | Offline speech recognition |
| TTS (fallback) | ParlerTTS Mini v1 (HF) | Offline text-to-speech |
| VAD | Silero VAD | Voice activity detection |
| LLM | Groq — Llama 3.3 70B | Intent classification, state management |
| UI | Vanilla HTML + Tailwind CSS | Professional light-theme web interface |
| Backend | FastAPI (port 8001) | REST API, serves UI, voice/chat endpoints |
| MCP Server | FastAPI (port 8000) | Calendar, Notes, Email tool endpoints |
| Calendar | Google Calendar API | Creates events with Google Meet links |
| Notes | Google Docs API | Audit trail logging |
| Email | Resend API | Advisor notification emails |

---

## Voice Provider Toggle

Switch between Sarvam AI (cloud, Indian accent) and local HuggingFace models without restarting — use the toggle in the UI footer, or set in `.env`:

```bash
VOICE_PROVIDER=sarvam   # default — Sarvam AI (fast, Indian accent)
VOICE_PROVIDER=local    # HuggingFace Whisper + ParlerTTS (offline)
```

---

## Supported Topics

- KYC / Onboarding
- SIP / Mandates
- Statements / Tax Docs
- Withdrawals
- Account Changes / Nominee

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq LLM API key |
| `SARVAM_API_KEY` | ✅ (if VOICE_PROVIDER=sarvam) | Sarvam AI key — get free at console.sarvam.ai |
| `VOICE_PROVIDER` | ❌ | `sarvam` (default) or `local` |
| `GOOGLE_CLIENT_ID` | ✅ | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth client secret |
| `GOOGLE_CALENDAR_ID` | ✅ | Target calendar ID |
| `GOOGLE_DOC_ID` | ✅ | Google Doc ID for audit trail |
| `RESEND_API_KEY` | ✅ | Resend email API key |
| `MCP_SERVER_PORT` | ❌ | Default: 8000 |
| `API_PORT` | ❌ | Default: 8001 |

---

## Project Structure

```
.
├── start.py                          # Unified launcher (MCP + UI)
├── requirements.txt
├── .env / .env.example
├── frontend/ui_dist/index.html       # Professional web UI (Tailwind)
├── phase-1-core-voice/
│   ├── stt/
│   │   ├── sarvam_stt.py             # Sarvam Saaras v3 STT
│   │   ├── hf_whisper_asr.py         # HuggingFace Whisper (fallback)
│   │   └── mock_stt.py               # Mock for testing
│   ├── tts/
│   │   ├── sarvam_tts.py             # Sarvam Bulbul v2 TTS
│   │   └── hf_parler_tts.py          # ParlerTTS (fallback)
│   └── vad/
│       └── silero_vad_multilingual.py
├── phase-2-mcp-tools/
│   ├── server/mcp_server.py          # MCP FastAPI server (port 8000)
│   ├── providers/
│   │   ├── google_calendar_provider.py
│   │   ├── google_docs_provider.py
│   │   └── resend_provider.py
│   ├── cal_tool/                     # Calendar MCP tool
│   ├── notes/                        # Notes MCP tool
│   └── email_drafter/                # Email MCP tool
├── phase-3-llm-orchestrator/
│   ├── core/orchestrator.py          # LLM orchestration
│   ├── nlu/intent_classifier.py      # 5-intent classifier
│   └── nlu/topic_router.py           # 5-topic router
└── phase-4-integration/
    ├── api_server.py                 # Main FastAPI backend (port 8001)
    ├── compliance/pii_detector.py    # Real-time PII detection
    ├── handlers/waitlist_handler.py
    └── ui/simple_state_machine.py    # 4-state booking flow
```

---

## Compliance

- No PII collected on voice call (real-time detection + interruption)
- Mandatory disclaimer at session start
- Investment advice refused with SEBI educational link
- All bookings logged to Google Docs audit trail
- Email drafts require advisor approval before sending

---

## License

MIT — see [LICENSE](LICENSE)
