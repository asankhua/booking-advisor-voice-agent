#!/usr/bin/env python3
"""
Test Google Docs append and Email notification functionality
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
            "slot_datetime": slot_time,  # Changed from date+slot to slot_datetime
            "notes": "Test booking via API"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Note appended successfully!")
        print(f"  Success: {result.get('success')}")
        print(f"  Doc ID: {result.get('doc_id')}")
        print(f"  Message: {result.get('message')}")
        
        if not result.get('success'):
            print(f"\n❌ Error: {result.get('error')}")
    else:
        print(f"\n❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    return booking_code


def test_email_notification(booking_code):
    """Test sending email notification"""
    print(f"\n" + "=" * 60)
    print("EMAIL NOTIFICATION TEST")
    print("=" * 60)
    
    slot_time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    meet_link = "https://meet.google.com/test-meet-link"
    
    print(f"\nSending email notification:")
    print(f"  To: ashishsankhuapg@gmail.com")
    print(f"  Booking Code: {booking_code}")
    print(f"  Topic: KYC/Onboarding")
    print(f"  Slot: {slot_time}")
    
    response = requests.post(
        f"{MCP_BASE_URL}/email/draft",
        json={
            "booking_code": booking_code,
            "topic": "KYC/Onboarding",
            "slot_datetime": slot_time,  # Changed from slot to slot_datetime
            "advisor_email": "ashishsankhuapg@gmail.com",  # Changed from to to advisor_email
            "additional_notes": f"Meet Link: {meet_link}"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Email sent successfully!")
        print(f"  Success: {result.get('success')}")
        print(f"  Draft ID: {result.get('draft_id')}")
        print(f"  Message: {result.get('message')}")
        
        if not result.get('success'):
            print(f"\n❌ Error: {result.get('error')}")
    else:
        print(f"\n❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")


def test_full_flow():
    """Test complete flow: Calendar → Docs → Email"""
    print("=" * 60)
    print("COMPLETE FLOW TEST: Calendar + Docs + Email")
    print("=" * 60)
    
    # Step 1: Create Calendar Event
    topic = "KYC/Onboarding"
    booking_code = f"KYC-{datetime.now().strftime('%H%M%S')}"
    start_time = datetime.now() + timedelta(hours=2)
    slot_time = start_time.strftime("%Y-%m-%d %H:%M")
    
    print(f"\n[1/3] Creating Calendar Event...")
    cal_response = requests.post(
        f"{MCP_BASE_URL}/calendar/event",
        json={
            "topic": topic,
            "booking_code": booking_code,
            "start_time": start_time.isoformat(),
            "duration_minutes": 30,
            "attendee_email": "ashishsankhuapg@gmail.com"
        }
    )
    
    if cal_response.status_code == 200:
        cal_result = cal_response.json()
        if cal_result.get('success'):
            print(f"   ✅ Calendar event created: {cal_result.get('event_id')}")
            meet_link = cal_result.get('meet_link')
            print(f"   ✅ Meet link: {meet_link}")
        else:
            print(f"   ❌ Calendar failed: {cal_result.get('error')}")
            meet_link = None
    else:
        print(f"   ❌ Calendar request failed: {cal_response.status_code}")
        meet_link = None
    
    # Step 2: Append to Google Doc
    print(f"\n[2/3] Appending to Google Doc...")
    doc_response = requests.post(
        f"{MCP_BASE_URL}/notes/append",
        json={
            "booking_code": booking_code,
            "topic": topic,
            "slot_datetime": slot_time,
            "notes": f"Google Meet: {meet_link or 'N/A'}"
        }
    )
    
    if doc_response.status_code == 200:
        doc_result = doc_response.json()
        if doc_result.get('success'):
            print(f"   ✅ Note appended: {doc_result.get('message')}")
        else:
            print(f"   ❌ Docs failed: {doc_result.get('error')}")
    else:
        print(f"   ❌ Docs request failed: {doc_response.status_code}")
    
    # Step 3: Send Email
    print(f"\n[3/3] Sending Email Notification...")
    email_response = requests.post(
        f"{MCP_BASE_URL}/email/draft",
        json={
            "booking_code": booking_code,
            "topic": topic,
            "slot_datetime": slot_time,
            "advisor_email": "ashishsankhuapg@gmail.com",
            "additional_notes": f"Meet Link: {meet_link}"
        }
    )
    
    if email_response.status_code == 200:
        email_result = email_response.json()
        if email_result.get('success'):
            print(f"   ✅ Email sent: {email_result.get('message')}")
            print(f"   📧 Check your email at: https://resend.com/emails")
        else:
            print(f"   ❌ Email failed: {email_result.get('error')}")
    else:
        print(f"   ❌ Email request failed: {email_response.status_code}")
    
    print(f"\n" + "=" * 60)
    print(f"Booking Code: {booking_code}")
    print(f"Google Doc: https://docs.google.com/document/d/1-30O5QtOh0wC2t3cALaQADAGqJB6WFtMGD-huNLHPu4/edit")
    print("=" * 60)


if __name__ == "__main__":
    # Run individual tests
    # test_google_docs_append()
    # test_email_notification("TEST-1234")
    
    # Run full flow test
    test_full_flow()
