#!/usr/bin/env python3
"""
Test Google Docs append functionality
"""
import requests
from datetime import datetime, timedelta

MCP_BASE_URL = "http://localhost:8000"


def test_google_docs_append():
    """Test appending booking note to Google Doc"""
    print("=" * 60)
    print("GOOGLE DOCS APPEND TEST")
    print("=" * 60)
    
    booking_code = f"KYC-{datetime.now().strftime('%H%M%S')}"
    slot_time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    
    print(f"\nAppending note to Google Doc:")
    print(f"  Booking Code: {booking_code}")
    print(f"  Topic: KYC/Onboarding")
    print(f"  Slot: {slot_time}")
    
    response = requests.post(
        f"{MCP_BASE_URL}/notes/append",
        json={
            "booking_code": booking_code,
            "topic": "KYC/Onboarding",
            "slot_datetime": slot_time,
            "notes": "Test booking via API",
            "meet_link": "https://meet.google.com/abc-defg-hij"  # Real Meet link
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Note appended successfully!")
        print(f"  Success: {result.get('success')}")
        print(f"  Entry ID: {result.get('entry_id')}")
        print(f"  Message: {result.get('message')}")
    else:
        print(f"\n❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    print(f"\n" + "=" * 60)
    print(f"Google Doc: https://docs.google.com/document/d/1-30O5QtOh0wC2t3cALaQADAGqJB6WFtMGD-huNLHPu4/edit")
    print("=" * 60)


if __name__ == "__main__":
    test_google_docs_append()
