from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EmailDraftRequest(BaseModel):
    booking_code: str
    topic: str
    slot_datetime: str
    advisor_email: str = "advisor@company.com"
    additional_notes: str = ""
    meet_link: Optional[str] = None  # Google Meet link from calendar
    calendar_link: Optional[str] = None  # Google Calendar event link


class EmailDraftResponse(BaseModel):
    success: bool
    draft_id: str
    status: str  # DRAFT_REQUIRES_APPROVAL
    message: str
    preview_url: Optional[str] = None
