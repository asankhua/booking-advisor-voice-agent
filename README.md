---
title: Booking Advisor Voice Agent
emoji: 🎙️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Advisor Voice Agent

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Groq-FF6B6B.svg?style=flat&logo=groq&logoColor=white" alt="Groq">
  <img src="https://img.shields.io/badge/Sarvam%20AI-4285F4.svg?style=flat" alt="Sarvam AI">
  <img src="https://img.shields.io/badge/Google%20Calendar-EA4335.svg?style=flat&logo=google-calendar&logoColor=white" alt="Google Calendar">
  <img src="https://img.shields.io/badge/Resend-000000.svg?style=flat&logo=resend&logoColor=white" alt="Resend">
</p>

AI-powered voice assistant for financial advisory appointment scheduling with compliance-first architecture.

## Overview

A multilingual voice-based appointment booking system for financial advisors, enabling customers to schedule consultations via natural voice conversations. The system integrates with Google Calendar, generates Meet links, logs to Google Docs, and sends email confirmations—all through a secure, auditable workflow.

## Problem Statement

Traditional appointment booking for financial advisory services involves:
- **Phone tag**: Multiple back-and-forth calls to find suitable slots
- **Language barriers**: Customers struggle with English-only booking systems
- **No-shows**: Lack of automated reminders leads to missed appointments
- **Compliance gaps**: Manual processes lack proper audit trails
- **Scalability issues**: Human operators limit booking capacity during peak hours

## Solution

Advisor Voice Agent automates the entire booking workflow through voice AI:
- **24/7 availability**: Customers book anytime without waiting for business hours
- **Multilingual support**: Conversations in the customer's preferred language
- **Instant confirmation**: Automated calendar invites and email notifications
- **Compliance ready**: All bookings logged to Google Docs for audit
- **Scalable**: Handles multiple concurrent bookings without human intervention

## Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Voice Interface** | Real-time STT/TTS using Sarvam AI | Natural conversation flow, multilingual support |
| **Smart Intent Detection** | Groq LLM classifies intents (book, reschedule, cancel) | Accurate understanding of customer requests |
| **Calendar Integration** | Google Calendar with auto-generated Meet links | Instant scheduling with video meeting setup |
| **Audit Logging** | Google Docs append for compliance | Complete audit trail for regulatory requirements |
| **Email Notifications** | Resend API for confirmations | Automated customer communication |
| **State Management** | Conversation context across turns | Complex multi-turn booking workflows |
| **PII Protection** | Sensitive data redaction in logs | GDPR/privacy compliance |
| **Slot Availability** | Real-time calendar checking | Prevents double-bookings |

## Target Users

| Stakeholder | Benefit |
|-------------|---------|
| **Financial Advisors** | Focus on client meetings instead of scheduling logistics |
| **Advisory Firms** | Reduced admin overhead, better compliance, higher booking rates |
| **Customers** | Book appointments in their language, anytime, without wait |
| **Compliance Teams** | Automatic audit trails, searchable booking logs |

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    GRADIO FRONTEND UI                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              Voice Interface (Gradio)                                │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────────┐  │   │
│  │  │  🎤 Start Call  │  │  🔴 End Call    │  │         Conversation Transcript     │  │   │
│  │  │     Button       │  │     Button      │  │    User → Agent → Booking Confirm   │  │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │ WebSocket / HTTP
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    BACKEND PIPELINE                                        │
│                                                                                             │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│   │   Voice UI   │────▶│  Silero VAD  │────▶│ Sarvam STT   │────▶│   Groq LLM   │       │
│   │   (Gradio)   │     │  (VAD Detection)   │  (Speech-to-Text) │ (Intent/Topic)│       │
│   └──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘       │
│                                                                        │                    │
│                                                                        ▼                    │
│                                                               ┌─────────────────┐          │
│                                                               │  State Machine  │          │
│                                                               │ (4-state flow)  │          │
│                                                               └────────┬────────┘          │
│                                                                        │                    │
│                                                                        ▼                    │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│   │  Sarvam TTS  │◀────│  Response    │◀────│  Booking     │◀────│   MCP Tools  │       │
│   │ (Text-to-Sp) │     │  Generator   │     │  Confirmation│     │   Router     │       │
│   └──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘       │
│                                                                        │                    │
└────────────────────────────────────────────────────────────────────────┼────────────────────┘
                                                                         │
                    ┌────────────────────┬─────────────────────────────┼────────────────────┐
                    ▼                    ▼                             ▼                    ▼
           ┌────────────────┐  ┌────────────────┐          ┌────────────────┐  ┌────────────────┐
           │ Google Calendar │  │  Google Docs   │          │    Resend      │  │  MCP Logger    │
           │  (Calendar API) │  │  (Audit Log)   │          │    (Email)     │  │  (Call Logs)   │
           │ • Create Event  │  │ • Append Note  │          │ • Send Email   │  │ • Track Calls  │
           │ • Generate Meet │  │ • Compliance   │          │ • Confirmation │  │ • Audit Trail  │
           └────────────────┘  └────────────────┘          └────────────────┘  └────────────────┘
```

**Data Flow:**
1. **Voice Input** → Customer speaks to Gradio UI
2. **VAD** → Silero detects voice activity
3. **STT** → Sarvam AI converts speech to text
4. **LLM** → Groq classifies intent (book/reschedule/cancel)
5. **State Machine** → 4-state conversation flow (greet → topic → slots → confirm)
6. **MCP Router** → Executes appropriate tool (calendar/docs/email)
7. **TTS** → Sarvam AI speaks response back to customer
8. **Confirmation** → Booking code + Meet link shared

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **STT/TTS** | Sarvam AI | Speech recognition and synthesis |
| **VAD** | Silero | Voice activity detection |
| **LLM** | Groq (Llama 3.3 70B) | Intent classification, state management |
| **UI** | Gradio | Voice chat interface |
| **APIs** | Google Calendar, Docs, Resend | Calendar, audit logs, email |
| **Server** | FastAPI (MCP) | Tool calling protocol server |
| **Orchestration** | Custom Python | State machine, intent routing |


### Prerequisites

- Python 3.10+
- API keys for: Sarvam AI, Groq, Resend
- Google Cloud OAuth credentials

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/asankhua/advisor-appointment--voiceagent.git
cd advisor-appointment--voiceagent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Step 1: Start MCP Server (Backend)
cd phase-2-mcp-tools
python3 -m server.mcp_server

# Step 2: Start Voice Agent Frontend (new terminal)
cd ..
python3 app.py
```

### Local URLs

After starting both services:

- **Frontend UI**: http://127.0.0.1:7860
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Required Environment Variables

```bash
# === Phase 1: Voice AI ===
SARVAM_API_KEY=your_sarvam_key
GROQ_API_KEY=your_groq_key

# === Phase 2: Integrations ===
GOOGLE_CLIENT_ID=your_oauth_client_id
GOOGLE_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost

# === Phase 3: Email Service ===
RESEND_API_KEY=your_resend_key
RESEND_FROM_EMAIL=noreply@yourdomain.com

# === Phase 4: Configuration ===
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
GRADIO_SERVER_PORT=7860
```

### Google OAuth Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing

2. **Enable APIs**
   - Google Calendar API
   - Google Docs API

3. **Create OAuth Credentials**
   - Go to APIs & Services → Credentials
   - Create OAuth 2.0 Client ID
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost`

4. **Download Credentials**
   - Save as `config/google-credentials.json` (gitignored)

### Testing Checklist

- [ ] MCP server running on port 8000
- [ ] Frontend accessible on http://127.0.0.1:7860
- [ ] API keys configured in `.env`
- [ ] Google OAuth credentials set up
- [ ] Test voice recording and speech recognition
- [ ] Test appointment booking flow
- [ ] Verify email confirmations

## Project Structure

```
advisor-voice-agent/
├── phase-1-core-voice/          # Voice interface, STT/TTS, VAD
│   ├── core/
│   │   ├── stt_sarvam.py        # Speech-to-text
│   │   ├── tts_sarvam.py        # Text-to-speech
│   │   └── vad_silero.py        # Voice activity detection
│   └── ui/
│       └── voice_chat.py        # Gradio interface
│
├── phase-2-mcp-tools/           # API integrations via MCP
│   ├── server/
│   │   └── mcp_server.py        # FastAPI MCP server
│   └── providers/
│       ├── google_calendar.py   # Calendar operations
│       ├── google_docs.py       # Audit logging
│       └── email_resend.py      # Email notifications
│
├── phase-3-llm-orchestrator/    # Intent routing & state mgmt
│   ├── core/
│   │   ├── orchestrator.py      # Main orchestration logic
│   │   └── intent_classifier.py # Groq-based intent detection
│   └── state/
│       └── booking_state.py     # Conversation state machine
│
└── .env.example                 # Environment template
```


## Security & Compliance

- **OAuth 2.0**: Secure Google API authentication
- **Environment variables**: No secrets in code
- **PII redaction**: Sensitive data masked in logs
- **Audit trail**: Every booking logged to Google Docs
- **Gitignore**: All credential files excluded from repository

## Documentation

- `ARCHITECTURE.md` - Detailed system design and component interactions
- `CASE_STUDY.md` - Business metrics and ROI analysis

## Deployment Options

| Platform | Best For | Setup |
|----------|----------|-------|
| **Render** | Quick MVP | One-click deploy from GitHub |
| **Google Cloud Run** | Production scale | Pay-per-use, auto-scaling |
| **Railway** | Simplicity | Auto-detects Python services |

## Working Commits

| Environment | Commit | Status | Notes |
|-------------|--------|--------|-------|
| **Production** | `7634ee1` | ✅ Ready | Environment variable based, secure for deployment |

## License

MIT License - See LICENSE file for details

## Support

For setup issues or questions:
- Review `ARCHITECTURE.md` for system details
- Open an issue in the repository
