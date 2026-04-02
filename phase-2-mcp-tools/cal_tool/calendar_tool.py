"""
MCP Calendar Tool
Manages advisor slot availability, holds, and rescheduling
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

_PHASE2_ROOT = Path(__file__).resolve().parent.parent


def _default_calendar_json_path() -> str:
    return str(_PHASE2_ROOT / "data" / "calendar_mock.json")


from .schemas import (
    Slot, SlotHoldInfo, GetAvailabilityRequest, GetAvailabilityResponse,
    CreateHoldRequest, CreateHoldResponse, CancelHoldRequest, CancelHoldResponse,
    RescheduleHoldRequest, RescheduleHoldResponse, default_hold_title,
)


class MCPCalendarTool:
    """
    Calendar MCP Tool for managing advisor appointment slots
    
    Functions:
    - get_availability: Returns available slots for a date
    - create_hold: Places a tentative hold on a slot
    - cancel_hold: Releases a hold
    - reschedule_hold: Moves hold to new slot
    """
    
    def __init__(self, mock_data_path: Optional[str] = None):
        self.data_path = mock_data_path or os.getenv("CALENDAR_MOCK_PATH") or _default_calendar_json_path()
        self._ensure_data_file()
        
    def _ensure_data_file(self):
        """Ensure mock data file exists with valid JSON (empty files are repopulated)."""
        path = Path(self.data_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.stat().st_size == 0:
            self._create_default_slots()
            
    def _load_slots(self) -> List[Slot]:
        """Load slots from JSON"""
        with open(self.data_path, 'r') as f:
            data = json.load(f)
            
        slots = []
        for slot_data in data['slots']:
            hold_info = None
            if slot_data.get('hold_info'):
                hi = slot_data['hold_info'].copy()
                if 'hold_title' not in hi or hi.get('hold_title') is None:
                    hi['hold_title'] = default_hold_title(hi['topic'], hi['booking_code'])
                hold_info = SlotHoldInfo(**hi)
            
            slot = Slot(
                id=slot_data['id'],
                datetime=datetime.fromisoformat(slot_data['datetime']),
                duration_minutes=slot_data['duration_minutes'],
                status=slot_data['status'],
                hold_info=hold_info
            )
            slots.append(slot)
            
        return slots
        
    def _save_slots(self, slots: List[Slot]):
        """Save slots to JSON"""
        data = {
            "version": "1.0",
            "timezone": "Asia/Kolkata",
            "slots": []
        }
        
        for slot in slots:
            slot_dict = {
                "id": slot.id,
                "datetime": slot.datetime.isoformat(),
                "duration_minutes": slot.duration_minutes,
                "status": slot.status,
                "hold_info": None
            }
            
            if slot.hold_info:
                slot_dict["hold_info"] = {
                    "booking_code": slot.hold_info.booking_code,
                    "topic": slot.hold_info.topic,
                    "held_at": slot.hold_info.held_at.isoformat(),
                    "hold_title": slot.hold_info.hold_title
                    or default_hold_title(slot.hold_info.topic, slot.hold_info.booking_code),
                }
                
            data["slots"].append(slot_dict)
            
        with open(self.data_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _create_default_slots(self):
        """Create default 10 slots across 5 days"""
        from datetime import datetime, timedelta
        
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        slots = []
        
        for day_offset in range(5):
            date = base_date + timedelta(days=day_offset)
            
            # Morning slot (10 AM)
            morning = date.replace(hour=10, minute=0)
            slots.append({
                "id": f"slot_{len(slots)+1:03d}",
                "datetime": morning.isoformat() + "+05:30",
                "duration_minutes": 30,
                "status": "available",
                "hold_info": None
            })
            
            # Afternoon slot (2 PM)
            afternoon = date.replace(hour=14, minute=0)
            slots.append({
                "id": f"slot_{len(slots)+1:03d}",
                "datetime": afternoon.isoformat() + "+05:30",
                "duration_minutes": 30,
                "status": "available",
                "hold_info": None
            })
            
        data = {
            "version": "1.0",
            "timezone": "Asia/Kolkata",
            "slots": slots
        }
        
        with open(self.data_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_availability(self, request: GetAvailabilityRequest) -> GetAvailabilityResponse:
        """Get available slots for a specific date"""
        slots = self._load_slots()
        
        # Filter by date (avoid datetime.strptime: local package name `calendar` shadows stdlib `calendar`)
        if request.date:
            y, m, d = (int(x) for x in request.date.split("-"))
            target_date = datetime(y, m, d).date()
            slots = [s for s in slots if s.datetime.date() == target_date]
            
        # Filter by time preference
        if request.time_preference:
            if request.time_preference.lower() == "morning":
                slots = [s for s in slots if s.datetime.hour < 12]
            elif request.time_preference.lower() == "afternoon":
                slots = [s for s in slots if 12 <= s.datetime.hour < 17]
            elif request.time_preference.lower() == "evening":
                slots = [s for s in slots if s.datetime.hour >= 17]
                
        # Only return available slots
        available_slots = [s for s in slots if s.status == "available"]
        
        # Return max 2 slots as per requirement
        return GetAvailabilityResponse(slots=available_slots[:2])
        
    def create_hold(self, request: CreateHoldRequest) -> CreateHoldResponse:
        """Place a tentative hold on a slot"""
        slots = self._load_slots()
        
        # Find the slot
        slot = next((s for s in slots if s.id == request.slot_id), None)
        if not slot:
            return CreateHoldResponse(
                success=False,
                hold_id="",
                message=f"Slot {request.slot_id} not found"
            )
            
        if slot.status != "available":
            return CreateHoldResponse(
                success=False,
                hold_id="",
                message=f"Slot {request.slot_id} is not available (status: {slot.status})"
            )
            
        # Create hold (milestone title: Advisor Q&A — {Topic} — {Code})
        title = default_hold_title(request.topic, request.booking_code)
        slot.status = "held"
        slot.hold_info = SlotHoldInfo(
            booking_code=request.booking_code,
            topic=request.topic,
            held_at=datetime.now(),
            hold_title=title,
        )
        
        self._save_slots(slots)
        
        return CreateHoldResponse(
            success=True,
            hold_id=request.booking_code,
            message=f"Hold created for {request.topic} on {slot.datetime}",
            slot_datetime=slot.datetime.isoformat(),
            hold_title=title,
        )
        
    def cancel_hold(self, request: CancelHoldRequest) -> CancelHoldResponse:
        """Cancel an existing hold"""
        slots = self._load_slots()
        
        # Find slot with this booking code
        slot = next(
            (s for s in slots if s.hold_info and s.hold_info.booking_code == request.booking_code),
            None
        )
        
        if not slot:
            return CancelHoldResponse(
                success=False,
                message=f"No hold found with code {request.booking_code}"
            )
            
        # Release hold
        slot.status = "available"
        slot.hold_info = None
        
        self._save_slots(slots)
        
        return CancelHoldResponse(
            success=True,
            message=f"Hold {request.booking_code} cancelled successfully"
        )
        
    def reschedule_hold(self, request: RescheduleHoldRequest) -> RescheduleHoldResponse:
        """Reschedule a hold to a new slot"""
        slots = self._load_slots()
        
        # Find current hold
        current_slot = next(
            (s for s in slots if s.hold_info and s.hold_info.booking_code == request.booking_code),
            None
        )
        
        if not current_slot:
            return RescheduleHoldResponse(
                success=False,
                new_hold_id="",
                message=f"No hold found with code {request.booking_code}"
            )
            
        # Find new slot
        new_slot = next((s for s in slots if s.id == request.new_slot_id), None)
        if not new_slot:
            return RescheduleHoldResponse(
                success=False,
                new_hold_id="",
                message=f"New slot {request.new_slot_id} not found"
            )
            
        if new_slot.status != "available":
            return RescheduleHoldResponse(
                success=False,
                new_hold_id="",
                message=f"New slot {request.new_slot_id} is not available"
            )
            
        # Transfer hold info to new slot
        hold_info = current_slot.hold_info
        current_slot.status = "available"
        current_slot.hold_info = None
        
        new_slot.status = "held"
        new_slot.hold_info = hold_info
        
        self._save_slots(slots)
        
        return RescheduleHoldResponse(
            success=True,
            new_hold_id=request.booking_code,
            message=f"Rescheduled to {new_slot.datetime}"
        )


# Factory function
def create_calendar_tool() -> MCPCalendarTool:
    """Create calendar tool from environment"""
    return MCPCalendarTool()
