#!/usr/bin/env python3
"""
Test Google Calendar integration with booking code generation
Creates a REAL event in Google Calendar
"""
import requests
from datetime import datetime, timedelta

MCP_BASE_URL = "http://localhost:8000"


def test_google_calendar_event():
    """Test creating a real Google Calendar event with Meet"""
    print("=" * 60)
    print("GOOGLE CALENDAR EVENT TEST")
    print("=" * 60)
    
    # Event details
    topic = "KYC/Onboarding"
    booking_code = f"KYC-{datetime.now().strftime('%H%M')}"
    start_time = datetime.now() + timedelta(hours=2)  # 2 hours from now
    
    print(f"\nCreating calendar event:")
    print(f"  Topic: {topic}")
    print(f"  Booking Code: {booking_code}")
    print(f"  Start Time: {start_time.isoformat()}")
    
    # Create event via MCP server
    response = requests.post(
        f"{MCP_BASE_URL}/calendar/event",
        json={
            "topic": topic,
            "booking_code": booking_code,
            "start_time": start_time.isoformat(),
            "duration_minutes": 30,
            "attendee_email": "ashishsankhuapg@gmail.com"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Event created successfully!")
        print(f"  Event ID: {result.get('event_id')}")
        print(f"  Title: {result.get('title')}")
        print(f"  Google Meet Link: {result.get('meet_link')}")
        print(f"  Calendar Link: {result.get('html_link')}")
        
        if result.get('mock'):
            print(f"\n⚠️  WARNING: Event was created in MOCK mode (not real Google Calendar)")
            print(f"   Check MCP server logs for auth issues")
        else:
            print(f"\n✅ REAL event created in Google Calendar!")
            print(f"   Check your calendar at: https://calendar.google.com")
    else:
        print(f"\n❌ Failed to create event: {response.status_code}")
        print(f"   Response: {response.text}")
    
    print(f"\n" + "=" * 60)


if __name__ == "__main__":
    test_google_calendar_event()
