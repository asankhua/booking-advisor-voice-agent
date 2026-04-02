"""
Waitlist Handler for Voice Agent
Manages waitlist when no slots available
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

_PHASE4_ROOT = Path(__file__).resolve().parent.parent


def _default_waitlist_path() -> str:
    return str(_PHASE4_ROOT / "data" / "waitlist.json")


@dataclass
class WaitlistEntry:
    id: str
    topic: str
    time_preference: str
    created_at: str
    status: str  # PENDING, NOTIFIED, CONVERTED
    contact_method: str = "phone"  # Future: actual contact info collected post-call


class WaitlistHandler:
    """
    Manages waitlist for users when no slots available
    
    Functions:
    - Add to waitlist
    - Get waitlist entries
    - Mark as notified when slots available
    """
    
    def __init__(self, waitlist_path: Optional[str] = None):
        self.waitlist_path = waitlist_path or os.getenv("WAITLIST_PATH") or _default_waitlist_path()
        self._ensure_file()
        
    def _ensure_file(self):
        """Ensure waitlist file exists"""
        path = Path(self.waitlist_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump({"entries": []}, f)
                
    def _load_entries(self) -> List[Dict]:
        """Load waitlist entries"""
        with open(self.waitlist_path, 'r') as f:
            data = json.load(f)
        return data.get("entries", [])
        
    def _save_entries(self, entries: List[Dict]):
        """Save waitlist entries"""
        with open(self.waitlist_path, 'w') as f:
            json.dump({"entries": entries}, f, indent=2)
            
    def add_to_waitlist(
        self,
        topic: str,
        time_preference: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Add user to waitlist
        
        Returns:
            Entry details with ID
        """
        entries = self._load_entries()
        
        entry_id = f"wl_{conversation_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        new_entry = {
            "id": entry_id,
            "topic": topic,
            "time_preference": time_preference,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "PENDING",
            "contact_method": "phone"
        }
        
        entries.append(new_entry)
        self._save_entries(entries)
        
        return {
            "success": True,
            "entry_id": entry_id,
            "message": f"Added to waitlist for {topic}. We'll notify you when slots open up."
        }
        
    def get_waitlist(self, status: Optional[str] = None) -> List[Dict]:
        """Get waitlist entries, optionally filtered by status"""
        entries = self._load_entries()
        
        if status:
            entries = [e for e in entries if e["status"] == status]
            
        return entries
        
    def mark_notified(self, entry_id: str) -> bool:
        """Mark entry as notified (when slot becomes available)"""
        entries = self._load_entries()
        
        for entry in entries:
            if entry["id"] == entry_id:
                entry["status"] = "NOTIFIED"
                self._save_entries(entries)
                return True
                
        return False
        
    def mark_converted(self, entry_id: str, booking_code: str) -> bool:
        """Mark entry as converted to booking"""
        entries = self._load_entries()
        
        for entry in entries:
            if entry["id"] == entry_id:
                entry["status"] = "CONVERTED"
                entry["booking_code"] = booking_code
                self._save_entries(entries)
                return True
                
        return False
        
    def get_position(self, entry_id: str) -> int:
        """Get waitlist position for entry"""
        entries = self._load_entries()
        
        pending = [e for e in entries if e["status"] == "PENDING"]
        
        for i, entry in enumerate(pending):
            if entry["id"] == entry_id:
                return i + 1
                
        return -1
        
    def get_waitlist_message(self, topic: str) -> str:
        """Generate waitlist offer message"""
        return (
            f"I don't see any available slots for {topic} at the moment. "
            "Would you like me to add you to the waitlist? I'll notify you as soon as a slot opens up."
        )


# Convenience function
def create_waitlist_handler() -> WaitlistHandler:
    """Factory function"""
    return WaitlistHandler()
