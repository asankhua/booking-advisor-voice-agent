"""
Tests for MCP Notes Tool
"""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from notes.notes_tool import MCPNotesTool
from notes.schemas import AppendNoteRequest


def test_notes_tool():
    """Test notes tool functions"""
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = f.name
        
    try:
        # Initialize tool
        tool = MCPNotesTool(log_path=temp_path)
        
        print("Testing Notes Tool...")
        
        # Test append
        print("\n1. Testing append_pre_booking_note...")
        req = AppendNoteRequest(
            booking_code="KY-1234",
            topic="KYC/Onboarding",
            slot_datetime="2026-04-15T10:00:00+05:30",
            notes="Customer requested morning slot"
        )
        resp = tool.append_pre_booking_note(req)
        print(f"   Note appended: {resp.success}")
        print(f"   Entry ID: {resp.entry_id}")
        print(f"   Message: {resp.message}")
        assert resp.success, "Note should be appended"
        
        # Test get notes
        print("\n2. Testing get_notes_for_booking...")
        notes = tool.get_notes_for_booking("KY-1234")
        print(f"   Found {len(notes)} notes")
        assert len(notes) >= 1, "Should find the note"
        
        print("\n✅ All notes tool tests passed")
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    test_notes_tool()
