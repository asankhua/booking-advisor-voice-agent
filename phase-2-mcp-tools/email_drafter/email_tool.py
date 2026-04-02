"""
MCP Email Tool
Drafts advisor notification emails
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .schemas import EmailDraftRequest, EmailDraftResponse

_PHASE2_ROOT = Path(__file__).resolve().parent.parent


def _default_email_drafts_path() -> str:
    return str(_PHASE2_ROOT / "data" / "email_drafts.json")


class MCPEmailTool:
    """
    Email MCP Tool for creating advisor notification drafts
    
    Stores drafts as JSON for mock implementation
    """
    
    def __init__(self, draft_path: Optional[str] = None):
        self.draft_path = draft_path or os.getenv("EMAIL_DRAFT_PATH") or _default_email_drafts_path()
        self._ensure_draft_file()
        
    def _ensure_draft_file(self):
        """Ensure draft JSON file exists"""
        path = Path(self.draft_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump({"drafts": []}, f, indent=2)
                
    def _load_drafts(self) -> Dict[str, Any]:
        """Load existing drafts"""
        with open(self.draft_path, 'r') as f:
            return json.load(f)
            
    def _save_drafts(self, data: Dict[str, Any]):
        """Save drafts to JSON"""
        with open(self.draft_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _generate_email_content(self, request: EmailDraftRequest) -> Dict[str, str]:
        """Generate email subject and body"""
        subject = f"Advisor Q&A — {request.topic} — {request.booking_code} (approval required)"
        
        body = f"""Dear Advisor,

A new tentative pre-booking requires your review before send:

Booking Code: {request.booking_code}
Topic: {request.topic}
Scheduled For: {request.slot_datetime}
Calendar title: Advisor Q&A — {request.topic} — {request.booking_code}
Status: DRAFT — approval gated (do not send until approved)

Please review and confirm this booking in the system.

Additional Notes:
{request.additional_notes or "None"}

---
This is an automated draft from the Voice Agent system.
"""

        return {"subject": subject, "body": body}
        
    def draft_advisor_email(self, request: EmailDraftRequest) -> EmailDraftResponse:
        """
        Create an email draft for advisor notification
        
        Creates an approval-gated draft (milestone: not sent until approved).
        """
        try:
            # Generate email content
            content = self._generate_email_content(request)
            
            # Create draft
            draft_id = f"draft_{request.booking_code}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            draft = {
                "id": draft_id,
                "booking_code": request.booking_code,
                "topic": request.topic,
                "slot_datetime": request.slot_datetime,
                "recipient": request.advisor_email,
                "subject": content["subject"],
                "body": content["body"],
                "status": "DRAFT_REQUIRES_APPROVAL",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "additional_notes": request.additional_notes
            }
            
            # Save draft
            data = self._load_drafts()
            data["drafts"].append(draft)
            self._save_drafts(data)
            
            return EmailDraftResponse(
                success=True,
                draft_id=draft_id,
                status="DRAFT_REQUIRES_APPROVAL",
                message="Email draft created; awaiting approval before send",
                preview_url=f"file://{self.draft_path}"
            )
            
        except Exception as e:
            return EmailDraftResponse(
                success=False,
                draft_id="",
                status="ERROR",
                message=f"Failed to create draft: {str(e)}"
            )
            
    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific draft by ID"""
        data = self._load_drafts()
        for draft in data["drafts"]:
            if draft["id"] == draft_id:
                return draft
        return None
        
    def get_drafts_for_booking(self, booking_code: str) -> list:
        """Get all drafts for a booking code"""
        data = self._load_drafts()
        return [d for d in data["drafts"] if d["booking_code"] == booking_code]


# Factory function
def create_email_tool() -> MCPEmailTool:
    """Create email tool from environment"""
    return MCPEmailTool()
