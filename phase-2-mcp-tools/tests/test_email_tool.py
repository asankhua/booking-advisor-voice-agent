"""
Tests for MCP Email Tool
"""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from email_drafter.email_tool import MCPEmailTool
from email_drafter.schemas import EmailDraftRequest


def test_email_tool():
    """Test email tool functions"""
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
        
    try:
        # Initialize tool
        tool = MCPEmailTool(draft_path=temp_path)
        
        print("Testing Email Tool...")
        
        # Test draft creation
        print("\n1. Testing draft_advisor_email...")
        req = EmailDraftRequest(
            booking_code="KY-1234",
            topic="KYC/Onboarding",
            slot_datetime="2026-04-15T10:00:00+05:30",
            advisor_email="advisor@test.com",
            additional_notes="Customer prefers Hindi conversation"
        )
        resp = tool.draft_advisor_email(req)
        print(f"   Draft created: {resp.success}")
        print(f"   Draft ID: {resp.draft_id}")
        print(f"   Status: {resp.status}")
        print(f"   Message: {resp.message}")
        assert resp.success, "Draft should be created"
        assert resp.status == "DRAFT_REQUIRES_APPROVAL", "Milestone: approval-gated draft"
        
        # Test get drafts
        print("\n2. Testing get_drafts_for_booking...")
        drafts = tool.get_drafts_for_booking("KY-1234")
        print(f"   Found {len(drafts)} drafts")
        assert len(drafts) >= 1, "Should find the draft"
        
        print("\n✅ All email tool tests passed")
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    test_email_tool()
