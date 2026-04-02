"""
MCP Notes Tool
Append-only log for pre-booking notes
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schemas import AppendNoteRequest, AppendNoteResponse

_PHASE2_ROOT = Path(__file__).resolve().parent.parent


def _default_notes_log_path() -> str:
    return str(_PHASE2_ROOT / "data" / "advisor_pre_bookings.txt")


class MCPNotesTool:
    """
    Notes MCP Tool for logging pre-booking advisor notes
    
    Format: timestamp | booking_code | topic | slot_datetime | status
    """
    
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or os.getenv("NOTES_LOG_PATH") or _default_notes_log_path()
        self._ensure_log_file()
        
    def _ensure_log_file(self):
        """Ensure log file exists with header"""
        path = Path(self.log_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write("# Advisor Pre-Bookings Log\n")
                f.write("# Format: timestamp | booking_code | topic | slot_datetime | status | notes\n\n")
                
    def append_pre_booking_note(self, request: AppendNoteRequest) -> AppendNoteResponse:
        """
        Append a pre-booking note to the log
        
        Format: timestamp | booking_code | topic | slot_datetime | status | notes
        """
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            status = "HELD"
            
            # Create log entry
            entry = f"{timestamp} | {request.booking_code} | {request.topic} | {request.slot_datetime} | {status} | {request.notes}\n"
            
            # Append to file
            with open(self.log_path, 'a') as f:
                f.write(entry)
                
            return AppendNoteResponse(
                success=True,
                entry_id=request.booking_code,
                message=f"Note appended for booking {request.booking_code}"
            )
            
        except Exception as e:
            return AppendNoteResponse(
                success=False,
                entry_id="",
                message=f"Failed to append note: {str(e)}"
            )
            
    def get_notes_for_booking(self, booking_code: str) -> list:
        """Retrieve all notes for a specific booking code"""
        notes = []
        
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    if booking_code in line:
                        notes.append(line.strip())
        except FileNotFoundError:
            pass
            
        return notes


# Factory function
def create_notes_tool() -> MCPNotesTool:
    """Create notes tool from environment"""
    return MCPNotesTool()
