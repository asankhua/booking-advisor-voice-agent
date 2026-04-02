from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Load .env from project root using find_dotenv (searches up directories)
from dotenv import load_dotenv, find_dotenv
env_path = find_dotenv(filename='.env', raise_error_if_not_found=False)
if env_path:
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    # Fallback to manual path resolution
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded .env from fallback: {env_path}")
    else:
        print(f"⚠️ .env file not found")

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get project root for logs
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Setup logging with absolute path
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'mcp_calls.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from cal_tool.calendar_tool import create_calendar_tool
from cal_tool.schemas import (
    GetAvailabilityRequest, GetAvailabilityResponse,
    CreateHoldRequest, CreateHoldResponse,
    CancelHoldRequest, CancelHoldResponse,
    RescheduleHoldRequest, RescheduleHoldResponse
)
from notes.notes_tool import create_notes_tool
from notes.schemas import AppendNoteRequest, AppendNoteResponse
from email_drafter.email_tool import create_email_tool
from email_drafter.schemas import EmailDraftRequest, EmailDraftResponse

# Import Google Calendar Provider for real events
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from google_calendar_provider import GoogleCalendarProvider
from google_docs_provider import GoogleDocsProvider
from resend_provider import ResendProvider


class CreateEventRequest(BaseModel):
    topic: str
    booking_code: str
    start_time: datetime
    duration_minutes: int = 30
    attendee_email: Optional[str] = None


class CreateEventResponse(BaseModel):
    success: bool
    event_id: Optional[str] = None
    meet_link: Optional[str] = None
    html_link: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


app = FastAPI(
    title="MCP Server",
    description="Model Context Protocol Server for Voice Agent",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tools
calendar_tool = create_calendar_tool()
notes_tool = create_notes_tool()
email_tool = create_email_tool()

# Initialize Google Calendar for real event creation
google_calendar = GoogleCalendarProvider()

# Initialize Google Docs for real notes
google_docs = GoogleDocsProvider()

# Initialize Resend for real email sending
resend = ResendProvider()


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# Calendar endpoints
@app.post("/calendar/availability", response_model=GetAvailabilityResponse)
def get_availability(request: GetAvailabilityRequest):
    return calendar_tool.get_availability(request)


@app.post("/calendar/hold", response_model=CreateHoldResponse)
def create_hold(request: CreateHoldRequest):
    logger.info(f"[MCP_CALL] calendar/hold - START - booking_code={request.booking_code}, topic={request.topic}")
    result = calendar_tool.create_hold(request)
    if result.success:
        logger.info(f"[MCP_CALL] calendar/hold - SUCCESS - booking_code={request.booking_code}")
    else:
        logger.error(f"[MCP_CALL] calendar/hold - FAILED - booking_code={request.booking_code}")
    return result


@app.post("/calendar/hold/cancel", response_model=CancelHoldResponse)
def cancel_hold(request: CancelHoldRequest):
    logger.info(f"[MCP_CALL] calendar/hold/cancel - START - booking_code={request.booking_code}")
    result = calendar_tool.cancel_hold(request)
    if result.success:
        logger.info(f"[MCP_CALL] calendar/hold/cancel - SUCCESS - booking_code={request.booking_code}")
    else:
        logger.error(f"[MCP_CALL] calendar/hold/cancel - FAILED - booking_code={request.booking_code}")
    return result


@app.post("/calendar/hold/reschedule", response_model=RescheduleHoldResponse)
def reschedule_hold(request: RescheduleHoldRequest):
    logger.info(f"[MCP_CALL] calendar/hold/reschedule - START - booking_code={request.booking_code}")
    result = calendar_tool.reschedule_hold(request)
    if result.success:
        logger.info(f"[MCP_CALL] calendar/hold/reschedule - SUCCESS - booking_code={request.booking_code}")
    else:
        logger.error(f"[MCP_CALL] calendar/hold/reschedule - FAILED - booking_code={request.booking_code}")
    return result


# Google Calendar - Create real event with Google Meet
@app.post("/calendar/event", response_model=CreateEventResponse)
def create_calendar_event(request: CreateEventRequest):
    """Create Google Calendar event with Google Meet"""
    logger.info(f"[MCP_CALL] calendar/event - START - booking_code={request.booking_code}, topic={request.topic}")
    
    result = google_calendar.create_event_with_meet(
        topic=request.topic,
        booking_code=request.booking_code,
        start_time=request.start_time,
        duration_minutes=request.duration_minutes,
        attendee_email=request.attendee_email
    )
    
    if result.get("success"):
        logger.info(f"[MCP_CALL] calendar/event - SUCCESS - booking_code={request.booking_code}, topic={request.topic}")
        return CreateEventResponse(
            success=True,
            event_id=result.get("event_id"),
            meet_link=result.get("meet_link"),
            html_link=result.get("html_link"),
            title=result.get("title")
        )
    else:
        logger.error(f"[MCP_CALL] calendar/event - FAILED - booking_code={request.booking_code}, error={result.get('error')}")
        return CreateEventResponse(
            success=False,
            error=result.get("error", "Unknown error")
        )


# Notes endpoints
@app.post("/notes/append", response_model=AppendNoteResponse)
def append_note(request: AppendNoteRequest):
    logger.info(f"[MCP_CALL] notes/append - START - booking_code={request.booking_code}")
    
    # Use Google Docs for real note storage
    if os.getenv('NOTES_PROVIDER') == 'googledocs':
        result = google_docs.append_booking(
            booking_code=request.booking_code,
            date=request.slot_datetime[:10],  # Extract date part from slot_datetime
            topic=request.topic,
            slot=request.slot_datetime,  # Use full slot_datetime
            notes=request.notes,
            meet_link=getattr(request, 'meet_link', None),  # Pass meet_link if available
            mcp_status="SUCCESS"  # Log MCP status
        )
        if result.get("success"):
            logger.info(f"[MCP_CALL] notes/append - SUCCESS - booking_code={request.booking_code}, topic={request.topic}")
            return AppendNoteResponse(
                success=True,
                entry_id=result.get("doc_id", ""),  # Map doc_id to entry_id
                message="Note appended to Google Doc"
            )
        else:
            logger.error(f"[MCP_CALL] notes/append - FAILED - booking_code={request.booking_code}, error={result.get('error')}")
            return AppendNoteResponse(
                success=False,
                entry_id="",
                message=result.get("error", "Failed to append to Google Doc")
            )
    else:
        # Fallback to original notes tool
        result = notes_tool.append_pre_booking_note(request)
        if result.success:
            logger.info(f"[MCP_CALL] notes/append - SUCCESS (mock) - booking_code={request.booking_code}")
        else:
            logger.error(f"[MCP_CALL] notes/append - FAILED (mock) - booking_code={request.booking_code}")
        return result


# Email endpoints - using Resend for real email delivery
@app.post("/email/draft", response_model=EmailDraftResponse)
def draft_email(request: EmailDraftRequest):
    logger.info(f"[MCP_CALL] email/draft - START - booking_code={request.booking_code}, topic={request.topic}")
    
    # Use Resend for real email sending
    if os.getenv('EMAIL_PROVIDER') == 'resend':
        result = resend.send_booking_notification(
            to_email=request.advisor_email,
            booking_code=request.booking_code,
            topic=request.topic,
            slot=request.slot_datetime,
            meet_link=getattr(request, 'meet_link', None),
            calendar_link=getattr(request, 'calendar_link', None),  # Pass calendar link
            doc_link=os.getenv('GOOGLE_DOC_LINK', 'https://docs.google.com/document/d/1-30O5QtOh0wC2t3cALaQADAGqJB6WFtMGD-huNLHPu4/edit?tab=t.0'),
            additional_notes=request.additional_notes
        )
        if result.get("success"):
            logger.info(f"[MCP_CALL] email/draft - SUCCESS - booking_code={request.booking_code}, topic={request.topic}")
            return EmailDraftResponse(
                success=True,
                draft_id=result.get("email_id", ""),  # Map email_id to draft_id
                status="SENT",
                message="Email sent via Resend"
            )
        else:
            logger.error(f"[MCP_CALL] email/draft - FAILED - booking_code={request.booking_code}, error={result.get('error')}")
            return EmailDraftResponse(
                success=False,
                error=result.get("error", "Failed to send email")
            )
    else:
        # Fallback to original email tool
        result = email_tool.draft_advisor_email(request)
        if result.success:
            logger.info(f"[MCP_CALL] email/draft - SUCCESS (mock) - booking_code={request.booking_code}")
        else:
            logger.error(f"[MCP_CALL] email/draft - FAILED (mock) - booking_code={request.booking_code}")
        return result


@app.get("/email/drafts/{booking_code}")
def get_drafts_for_booking(booking_code: str):
    logger.info(f"[MCP_CALL] email/drafts - GET - booking_code={booking_code}")
    drafts = email_tool.get_drafts_for_booking(booking_code)
    return {"booking_code": booking_code, "drafts": drafts}


@app.get("/logs/mcp-calls")
def get_mcp_call_logs(lines: int = 100):
    """View recent MCP call logs"""
    try:
        log_file = os.path.join(LOGS_DIR, 'mcp_calls.log')
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return {
                "total_lines": len(all_lines),
                "showing_last": min(lines, len(all_lines)),
                "logs": all_lines[-lines:] if all_lines else []
            }
    except FileNotFoundError:
        return {"error": "Log file not found", "logs": []}


def start_server():
    host = os.getenv("MCP_SERVER_HOST", "localhost")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
