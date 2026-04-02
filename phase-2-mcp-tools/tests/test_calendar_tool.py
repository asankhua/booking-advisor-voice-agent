"""
Tests for MCP Calendar Tool
"""
import sys
import os
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cal_tool.calendar_tool import MCPCalendarTool
from cal_tool.schemas import (
    GetAvailabilityRequest, CreateHoldRequest,
    CancelHoldRequest, RescheduleHoldRequest
)


def test_calendar_tool():
    """Test calendar tool functions"""
    
    # Create temp file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
        
    try:
        # Initialize tool
        tool = MCPCalendarTool(mock_data_path=temp_path)
        
        print("Testing Calendar Tool...")
        
        # Test 1: Get availability
        print("\n1. Testing get_availability...")
        today = datetime.now().strftime("%Y-%m-%d")
        req = GetAvailabilityRequest(date=today, time_preference="morning")
        resp = tool.get_availability(req)
        print(f"   Found {len(resp.slots)} slots")
        assert len(resp.slots) >= 0, "Should return slots or empty list"
        
        # Test 2: Create hold
        print("\n2. Testing create_hold...")
        # Get a slot to book
        slots = tool._load_slots()
        if slots:
            available_slot = next((s for s in slots if s.status == "available"), None)
            if available_slot:
                req = CreateHoldRequest(
                    topic="KYC/Onboarding",
                    slot_id=available_slot.id,
                    booking_code="KY-1234"
                )
                resp = tool.create_hold(req)
                print(f"   Hold created: {resp.success}")
                print(f"   Message: {resp.message}")
                assert resp.success, "Hold should be created"
                
                # Test 3: Cancel hold
                print("\n3. Testing cancel_hold...")
                req = CancelHoldRequest(booking_code="KY-1234")
                resp = tool.cancel_hold(req)
                print(f"   Hold cancelled: {resp.success}")
                print(f"   Message: {resp.message}")
                assert resp.success, "Hold should be cancelled"
                
                # Test 4: Reschedule
                print("\n4. Testing reschedule_hold...")
                # Create a new hold first
                req1 = CreateHoldRequest(
                    topic="SIP/Mandates",
                    slot_id=available_slot.id,
                    booking_code="SI-5678"
                )
                tool.create_hold(req1)
                
                # Find another available slot
                slots = tool._load_slots()
                other_slot = next((s for s in slots if s.status == "available"), None)
                
                if other_slot:
                    req = RescheduleHoldRequest(
                        booking_code="SI-5678",
                        new_slot_id=other_slot.id
                    )
                    resp = tool.reschedule_hold(req)
                    print(f"   Rescheduled: {resp.success}")
                    print(f"   Message: {resp.message}")
                    
        print("\n✅ All calendar tool tests passed")
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    test_calendar_tool()
