#!/usr/bin/env python3
"""
Send email with calendar details
"""
import requests
from datetime import datetime, timedelta

MCP_BASE_URL = "http://localhost:8000"


def send_email_with_calendar():
    """Send email notification with calendar event details"""
    print("=" * 60)
    print("SEND EMAIL WITH CALENDAR DETAILS")
    print("=" * 60)
    
    # First create a calendar event
    topic = "KYC/Onboarding"
    booking_code = f"KYC-{datetime.now().strftime('%H%M%S')}"
    start_time = datetime.now() + timedelta(hours=2)
    slot_time = start_time.strftime("%Y-%m-%d %H:%M")
    
    print(f"\n[1/2] Creating Calendar Event...")
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
            meet_link = cal_result.get('meet_link')
            calendar_link = cal_result.get('html_link')
            print(f"   ✅ Event created: {cal_result.get('event_id')}")
            print(f"   ✅ Meet: {meet_link}")
        else:
            print(f"   ❌ Calendar failed: {cal_result.get('error')}")
            meet_link = None
            calendar_link = None
    else:
        print(f"   ❌ Calendar failed: {cal_response.status_code}")
        meet_link = None
        calendar_link = None
    
    # Now send email with calendar details
    print(f"\n[2/2] Sending Email with Calendar Details...")
    
    # Build email content with calendar details
    additional_notes = f"""
📅 MEETING DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Booking Code: {booking_code}
Topic: {topic}
Date & Time: {slot_time}
Duration: 30 minutes

🔗 GOOGLE MEET:
{meet_link or 'N/A'}

📆 CALENDAR LINK:
{calendar_link or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please join the meeting on time.
    """.strip()
    
    email_response = requests.post(
        f"{MCP_BASE_URL}/email/draft",
        json={
            "booking_code": booking_code,
            "topic": topic,
            "slot_datetime": slot_time,
            "advisor_email": "ashishsankhuapg@gmail.com",
            "meet_link": meet_link,  # Real Meet link from calendar
            "calendar_link": calendar_link,  # Real Calendar link
            "additional_notes": additional_notes
        }
    )
    
    if email_response.status_code == 200:
        result = email_response.json()
        print(f"\n✅ Email Status:")
        print(f"   Success: {result.get('success')}")
        print(f"   Draft ID: {result.get('draft_id')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('success'):
            print(f"\n📧 Check your email at: https://resend.com/emails")
            print(f"   OR check inbox: ashishsankhuapg@gmail.com")
        else:
            print(f"\n❌ Error: {result.get('error')}")
    else:
        print(f"\n❌ Email request failed: {email_response.status_code}")
        print(f"   Response: {email_response.text}")
    
    print(f"\n" + "=" * 60)
    print(f"Booking Code: {booking_code}")
    print(f"Subject: Advisor Q&A — {topic} — {booking_code}")
    print("=" * 60)


if __name__ == "__main__":
    send_email_with_calendar()
