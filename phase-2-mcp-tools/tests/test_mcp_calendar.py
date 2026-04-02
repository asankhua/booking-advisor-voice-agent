#!/usr/bin/env python3
"""
Test script for MCP Calendar Tool with booking code generation
Tests: get_availability, create_hold, cancel_hold
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add paths for imports
_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT / "phase-2-mcp-tools"))
sys.path.insert(0, str(_REPO_ROOT))

from cal_tool.calendar_tool import MCPCalendarTool
from cal_tool.schemas import (
    GetAvailabilityRequest, CreateHoldRequest, CancelHoldRequest
)


def generate_booking_code(topic: str) -> str:
    """Generate a booking code from topic prefix + random number"""
    import random
    topic_prefix = topic.replace("/", "-").replace(" ", "-")[:3].upper()
    random_num = random.randint(1000, 9999)
    return f"{topic_prefix}-{random_num}"


def test_mcp_calendar():
    """Test MCP calendar functionality with booking code generation"""
    print("=" * 60)
    print("MCP CALENDAR TOOL TEST")
    print("=" * 60)
    
    # Initialize tool
    tool = MCPCalendarTool()
    print(f"\n✓ Calendar tool initialized")
    print(f"  Data path: {tool.data_path}")
    
    # Test 1: Get availability for today
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n1. Testing get_availability for {today}")
    
    req = GetAvailabilityRequest(date=today, time_preference=None)
    resp = tool.get_availability(req)
    
    print(f"   Found {len(resp.slots)} available slots:")
    for slot in resp.slots:
        print(f"   - {slot.id}: {slot.datetime.strftime('%Y-%m-%d %H:%M')} ({slot.status})")
    
    if not resp.slots:
        print("   ⚠ No slots available for today, checking tomorrow...")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        req = GetAvailabilityRequest(date=tomorrow, time_preference=None)
        resp = tool.get_availability(req)
        print(f"   Found {len(resp.slots)} slots for tomorrow")
        for slot in resp.slots:
            print(f"   - {slot.id}: {slot.datetime.strftime('%Y-%m-%d %H:%M')}")
    
    # Test 2: Create hold with booking code
    if resp.slots:
        test_slot = resp.slots[0]
        print(f"\n2. Testing create_hold on slot {test_slot.id}")
        
        topic = "KYC/Onboarding"
        booking_code = generate_booking_code(topic)
        print(f"   Generated booking code: {booking_code}")
        
        hold_req = CreateHoldRequest(
            topic=topic,
            slot_id=test_slot.id,
            booking_code=booking_code
        )
        hold_resp = tool.create_hold(hold_req)
        
        if hold_resp.success:
            print(f"   ✓ Hold created successfully!")
            print(f"   - Hold ID: {hold_resp.hold_id}")
            print(f"   - Title: {hold_resp.hold_title}")
            print(f"   - Slot datetime: {hold_resp.slot_datetime}")
            print(f"   - Message: {hold_resp.message}")
        else:
            print(f"   ✗ Hold failed: {hold_resp.message}")
            return
        
        # Test 3: Verify slot is now held
        print(f"\n3. Verifying slot is now 'held' status")
        check_req = GetAvailabilityRequest(date=test_slot.datetime.strftime("%Y-%m-%d"))
        check_resp = tool.get_availability(check_req)
        
        held_slots = [s for s in check_resp.slots if s.status == "held"]
        print(f"   Found {len(held_slots)} held slots")
        for slot in held_slots:
            if slot.hold_info:
                print(f"   - {slot.id}: {slot.hold_info.booking_code} ({slot.hold_info.topic})")
        
        # Test 4: Cancel the hold
        print(f"\n4. Testing cancel_hold for {booking_code}")
        cancel_req = CancelHoldRequest(booking_code=booking_code)
        cancel_resp = tool.cancel_hold(cancel_req)
        
        if cancel_resp.success:
            print(f"   ✓ Cancelled successfully: {cancel_resp.message}")
        else:
            print(f"   ✗ Cancel failed: {cancel_resp.message}")
        
        # Test 5: Verify slot is available again
        print(f"\n5. Verifying slot is 'available' again")
        final_req = GetAvailabilityRequest(date=test_slot.datetime.strftime("%Y-%m-%d"))
        final_resp = tool.get_availability(final_req)
        
        available_slots = [s for s in final_resp.slots if s.status == "available"]
        held_slots = [s for s in final_resp.slots if s.status == "held"]
        
        print(f"   Available slots: {len(available_slots)}")
        print(f"   Held slots: {len(held_slots)}")
        
        if test_slot.id in [s.id for s in available_slots]:
            print(f"   ✓ Slot {test_slot.id} is now available again")
    else:
        print("   ⚠ No slots to test with")
    
    print(f"\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_mcp_calendar()
