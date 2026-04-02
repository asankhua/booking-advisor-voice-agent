from pydantic import BaseModel
from typing import Optional
from datetime import datetime


def default_hold_title(topic: str, booking_code: str) -> str:
    return f"Advisor Q&A — {topic} — {booking_code}"


class SlotHoldInfo(BaseModel):
    booking_code: str
    topic: str
    held_at: datetime
    # Milestone calendar title: Advisor Q&A — {Topic} — {Code}
    hold_title: Optional[str] = None
    
    
class Slot(BaseModel):
    id: str
    datetime: datetime
    duration_minutes: int
    status: str  # available, held, cancelled
    hold_info: Optional[SlotHoldInfo] = None
    

class GetAvailabilityRequest(BaseModel):
    date: str  # YYYY-MM-DD
    time_preference: Optional[str] = None  # morning, afternoon, evening
    
    
class GetAvailabilityResponse(BaseModel):
    slots: list[Slot]
    

class CreateHoldRequest(BaseModel):
    topic: str
    slot_id: str
    booking_code: str
    
    
class CreateHoldResponse(BaseModel):
    success: bool
    hold_id: str
    message: str
    slot_datetime: Optional[str] = None  # ISO, for downstream notes/email
    hold_title: Optional[str] = None
    

class CancelHoldRequest(BaseModel):
    booking_code: str
    
    
class CancelHoldResponse(BaseModel):
    success: bool
    message: str
    

class RescheduleHoldRequest(BaseModel):
    booking_code: str
    new_slot_id: str
    
    
class RescheduleHoldResponse(BaseModel):
    success: bool
    new_hold_id: str
    message: str
