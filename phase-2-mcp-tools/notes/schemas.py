from pydantic import BaseModel
from datetime import datetime


class AppendNoteRequest(BaseModel):
    booking_code: str
    topic: str
    slot_datetime: str
    notes: str = ""
    meet_link: str = None


class AppendNoteResponse(BaseModel):
    success: bool
    entry_id: str
    message: str
