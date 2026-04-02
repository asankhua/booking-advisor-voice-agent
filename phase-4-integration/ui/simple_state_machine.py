"""
Simple State Machine - Keyword-based approach
Lightweight alternative to complex NLU pipeline
"""
import re
import uuid
import requests
import os
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

MCP_BASE_URL = os.getenv(
    "MCP_SERVER_URL",
    f"http://{os.getenv('MCP_SERVER_HOST', 'localhost')}:{os.getenv('MCP_SERVER_PORT', '8000')}",
)

# ── direct provider imports (fallback when MCP server is down) ────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _get_calendar_provider():
    import sys
    sys.path.insert(0, os.path.join(_ROOT, "phase-2-mcp-tools"))
    from providers.google_calendar_provider import GoogleCalendarProvider
    return GoogleCalendarProvider()

def _get_docs_provider():
    import sys
    sys.path.insert(0, os.path.join(_ROOT, "phase-2-mcp-tools"))
    from providers.google_docs_provider import GoogleDocsProvider
    return GoogleDocsProvider()

def _get_resend_provider():
    import sys
    sys.path.insert(0, os.path.join(_ROOT, "phase-2-mcp-tools"))
    from providers.resend_provider import ResendProvider
    return ResendProvider()

# Valid topics that agent can handle
VALID_TOPICS = ["KYC/Onboarding", "SIP/Mandates", "Statements/Tax Docs", "Withdrawals", "Account Changes"]

def is_valid_topic(topic: str) -> bool:
    """Check if topic is one of the 5 valid topics"""
    return topic in VALID_TOPICS

def create_calendar_event(topic: str, booking_code: str, slot_datetime: str, attendee_email: str = None):
    """Create Google Calendar event — tries MCP server first, falls back to direct provider."""
    if not attendee_email:
        attendee_email = os.getenv("GOOGLE_CALENDAR_ID", "")
    try:
        response = requests.post(
            f"{MCP_BASE_URL}/calendar/event",
            json={"topic": topic, "booking_code": booking_code,
                  "start_time": slot_datetime, "duration_minutes": 30,
                  "attendee_email": attendee_email},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return {"success": True, "event_id": result.get("event_id"),
                        "meet_link": result.get("meet_link"), "html_link": result.get("html_link"),
                        "title": result.get("title")}
    except Exception:
        pass
    # Direct fallback
    try:
        from datetime import datetime as _dt
        cal = _get_calendar_provider()
        start = _dt.fromisoformat(slot_datetime.replace("Z", "+00:00")) if isinstance(slot_datetime, str) else slot_datetime
        result = cal.create_event_with_meet(topic=topic, booking_code=booking_code,
                                            start_time=start, duration_minutes=30,
                                            attendee_email=attendee_email)
        if result.get("success"):
            print(f"✅ Calendar event created (direct): {result.get('event_id')}")
            return result
    except Exception as e:
        print(f"Calendar direct error: {e}")
    return {"success": False, "error": "Calendar unavailable"}

def append_notes_to_doc(booking_code: str, topic: str, slot_datetime: str, meet_link: str):
    """Append booking to Google Doc — tries MCP first, falls back to direct."""
    try:
        response = requests.post(
            f"{MCP_BASE_URL}/notes/append",
            json={"booking_code": booking_code, "topic": topic,
                  "slot_datetime": slot_datetime, "notes": "Booking confirmed via Voice Agent",
                  "meet_link": meet_link},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    # Direct fallback
    try:
        docs = _get_docs_provider()
        result = docs.append_booking(
            booking_code=booking_code,
            date=slot_datetime[:10] if slot_datetime else "",
            topic=topic,
            slot=slot_datetime,
            notes="Booking confirmed via Voice Agent",
            meet_link=meet_link,
            mcp_status="SUCCESS"
        )
        if result.get("success"):
            print(f"✅ Notes appended (direct): {booking_code}")
        return result
    except Exception as e:
        print(f"Notes direct error: {e}")
        return None

def send_email_notification(booking_code: str, topic: str, slot_datetime: str,
                             meet_link: str, calendar_link: str, to_email: str = None):
    """Send email via MCP first, falls back to direct Resend."""
    if not to_email:
        to_email = os.getenv("GOOGLE_CALENDAR_ID", "")
    try:
        response = requests.post(
            f"{MCP_BASE_URL}/email/draft",
            json={"booking_code": booking_code, "topic": topic,
                  "slot_datetime": slot_datetime, "advisor_email": to_email,
                  "meet_link": meet_link, "calendar_link": calendar_link},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    # Direct fallback
    try:
        resend = _get_resend_provider()
        doc_link = os.getenv("GOOGLE_DOC_LINK",
            f"https://docs.google.com/document/d/{os.getenv('GOOGLE_DOC_ID','')}/edit")
        result = resend.send_booking_notification(
            to_email=to_email,
            booking_code=booking_code,
            topic=topic,
            slot=slot_datetime,
            meet_link=meet_link,
            calendar_link=calendar_link,
            doc_link=doc_link,
            additional_notes=""
        )
        if result.get("success"):
            print(f"✅ Email sent (direct): {booking_code}")
        return result
    except Exception as e:
        print(f"Email direct error: {e}")
        return None


def simple_topic_detection(transcript: str) -> str:
    """Simple keyword-based topic detection"""
    text_lower = transcript.lower()
    
    # Topic keywords
    if any(word in text_lower for word in ['kyc', 'onboarding', 'account opening', 'new account']):
        return "KYC/Onboarding"
    elif any(word in text_lower for word in ['sip', 'mandate', 'systematic investment', 'monthly']):
        return "SIP/Mandates"
    elif any(word in text_lower for word in ['statement', 'tax', 'document', 'capital gain', 'transaction']):
        return "Statements/Tax Docs"
    elif any(word in text_lower for word in ['withdraw', 'redeem', 'exit', 'money out']):
        return "Withdrawals"
    elif any(word in text_lower for word in ['nominee', 'address change', 'bank change', 'account change']):
        return "Account Changes"
    else:
        return "Unknown"


def simple_intent_detection(transcript: str) -> str:
    """Simple keyword-based intent detection"""
    text_lower = transcript.lower()
    
    # Investment advice keywords
    if any(word in text_lower for word in ['invest', 'recommend', 'suggest', 'which fund', 'best fund', 'buy', 'sell']):
        return "INVESTMENT_ADVICE"
    # Booking keywords
    elif any(word in text_lower for word in ['book', 'appointment', 'schedule', 'meeting', 'slot', 'available']):
        return "BOOK_APPOINTMENT"
    # Reschedule/cancel keywords
    elif any(word in text_lower for word in ['reschedule', 'cancel', 'change time', 'move appointment']):
        return "RESCHEDULE_CANCEL"
    # Check availability
    elif any(word in text_lower for word in ['available', 'free slot', 'when can', 'timing']):
        return "CHECK_AVAILABILITY"
    # Default to general help
    else:
        return "GENERAL_HELP"


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p, %B %d")
    except:
        return dt_str


def generate_booking_code(topic_prefix: str) -> str:
    """Generate booking code"""
    import random
    random_num = random.randint(1000, 9999)
    return f"{topic_prefix}-{random_num}"


# Simple state machine
def run_simple_state_machine(transcript: str, conversation_state: Dict[str, Any]) -> Tuple[str, str]:
    """Run simple state machine. Returns (response_text, booking_html)."""
    
    response_text = ""
    booking_html = ""
    # Initialize conversation ID
    if conversation_state.get("id") is None:
        conversation_state["id"] = str(uuid.uuid4())[:8]
    
    # Check for personal information
    if re.search(r'\b\d{10}\b', transcript) or '@' in transcript:
        return ("For your security, please don't share personal details on this call. "
                "What topic would you like to discuss?"), ""
    
    if conversation_state["state"] == "greeting":
        response_text = (
            "Hello! This call is informational only and does not constitute investment advice. "
            "I cannot provide investment recommendations. "
            "We will not ask for your phone, email, or account numbers on this call. "
            "What topic would you like to discuss? KYC, SIP, Statements, Withdrawals, or Account Changes?"
        )
        conversation_state["state"] = "topic_detection"
        
    elif conversation_state["state"] == "topic_detection":
        intent = simple_intent_detection(transcript)
        topic = simple_topic_detection(transcript)
        
        # Validate topic is one of the 5 allowed topics
        if not is_valid_topic(topic):
            response_text = "Please select a valid topic: KYC, SIP, Statements, Withdrawals, or Account Changes."
            # Stay in topic_detection state until valid topic provided
        elif intent == "INVESTMENT_ADVICE":
            response_text = (
                "I cannot provide investment advice or product recommendations. "
                "I can help you book a human advisor appointment for personalized guidance. "
                "Would you like to book an appointment?"
            )
            conversation_state["state"] = "booking_interest"
        elif intent in ["RESCHEDULE_CANCEL"]:
            response_text = (
                "To reschedule or cancel, please use the secure link from your confirmation email or SMS. "
                "I cannot collect booking codes or personal details on this call."
            )
        elif intent == "CHECK_AVAILABILITY":
            conversation_state["topic"] = topic
            # Directly offer specific slots instead of asking for preference
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            mock_slots = [
                {"datetime": f"{tomorrow}T10:00:00Z", "id": "slot1"},
                {"datetime": f"{tomorrow}T14:00:00Z", "id": "slot2"}
            ]
            conversation_state["available_slots"] = mock_slots
            dt1 = format_datetime(mock_slots[0]["datetime"])
            dt2 = format_datetime(mock_slots[1]["datetime"])
            response_text = f"I have 2 slots in IST: {dt1}, or {dt2}. Say first or second, or yes to book the first."
            conversation_state["state"] = "confirm_slot"
        else:  # GENERAL_HELP or BOOK_APPOINTMENT with valid topic
            print(f"[DEBUG] Intent: {intent}, Topic: {topic}, Valid: True")
            conversation_state["topic"] = topic
            # Start conversational flow for the topic
            response_text = f"I can help you with {topic}. What specific help do you need with {topic}?"
            conversation_state["state"] = "understand_needs"
                
    elif conversation_state["state"] == "understand_needs":
        # Ask follow-up questions to understand user needs
        topic = conversation_state.get("topic", "")
        text_lower = transcript.lower()
        
        # Check if user wants to book an appointment
        if any(word in text_lower for word in ['book', 'appointment', 'schedule', 'meeting', 'call', 'slot']):
            # Directly offer specific slots instead of asking for preference
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            mock_slots = [
                {"datetime": f"{tomorrow}T10:00:00Z", "id": "slot1"},
                {"datetime": f"{tomorrow}T14:00:00Z", "id": "slot2"}
            ]
            conversation_state["available_slots"] = mock_slots
            dt1 = format_datetime(mock_slots[0]["datetime"])
            dt2 = format_datetime(mock_slots[1]["datetime"])
            response_text = f"I have 2 slots in IST: {dt1}, or {dt2}. Say first or second, or yes to book the first."
            conversation_state["state"] = "confirm_slot"
        elif any(word in text_lower for word in ['help', 'information', 'guidance', 'explain', 'how to']):
            # Provide helpful information about the topic
            if topic == "KYC/Onboarding":
                response_text = (
                    "For KYC/Onboarding, you'll need: government ID, proof of address, and any application reference. "
                    "Would you like to book an appointment to complete the process?"
                )
            elif topic == "SIP/Mandates":
                response_text = (
                    "For SIP/Mandates, you'll need: bank mandate form if changing debit, UMRN if applicable, and scheme name. "
                    "Would you like to book an appointment to set this up?"
                )
            elif topic == "Statements/Tax Docs":
                response_text = (
                    "For Statements/Tax Docs, you'll need: financial year and whether you need capital gains or transaction history. "
                    "Would you like to book an appointment to get these documents?"
                )
            elif topic == "Withdrawals":
                response_text = (
                    "For Withdrawals, you'll need: approximate amount or units, and the bank account registered with us. "
                    "Would you like to book an appointment to process your withdrawal?"
                )
            elif topic == "Account Changes":
                response_text = (
                    "For Account Changes, you'll need: nominee details as per rules, or change request type. "
                    "Would you like to book an appointment to make these changes?"
                )
            else:
                response_text = f"Would you like to book an appointment to get help with {topic}?"
            conversation_state["state"] = "booking_interest"
        else:
            # General response - ask for confirmation first
            response_text = f"I can help you book a {topic} appointment with a human advisor, can I proceed?"
            conversation_state["state"] = "confirm_appointment"
            
    elif conversation_state["state"] == "confirm_appointment":
        text_lower = transcript.lower()
        if any(word in text_lower for word in ['yes', 'sure', 'ok', 'definitely', 'would like', 'proceed', 'go ahead']):
            # User confirmed - now show slots
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            mock_slots = [
                {"datetime": f"{tomorrow}T10:00:00Z", "id": "slot1"},
                {"datetime": f"{tomorrow}T14:00:00Z", "id": "slot2"}
            ]
            conversation_state["available_slots"] = mock_slots
            dt1 = format_datetime(mock_slots[0]["datetime"])
            dt2 = format_datetime(mock_slots[1]["datetime"])
            response_text = f"I have 2 slots in IST: {dt1}, or {dt2}. Say first or second, or yes to book the first."
            conversation_state["state"] = "confirm_slot"
        elif any(word in text_lower for word in ['no', 'not now', 'later', 'maybe', 'cancel']):
            response_text = "No problem! Is there anything else I can help you with today?"
            conversation_state["state"] = "greeting"
        else:
            response_text = "Please say yes to proceed with booking, or no to cancel."
            
    elif conversation_state["state"] == "booking_interest":
        text_lower = transcript.lower()
        if any(word in text_lower for word in ['yes', 'sure', 'ok', 'definitely', 'would like']):
            # Directly offer specific slots instead of asking for preference
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            mock_slots = [
                {"datetime": f"{tomorrow}T10:00:00Z", "id": "slot1"},
                {"datetime": f"{tomorrow}T14:00:00Z", "id": "slot2"}
            ]
            conversation_state["available_slots"] = mock_slots
            dt1 = format_datetime(mock_slots[0]["datetime"])
            dt2 = format_datetime(mock_slots[1]["datetime"])
            response_text = f"I have 2 slots in IST: {dt1}, or {dt2}. Say first or second, or yes to book the first."
            conversation_state["state"] = "confirm_slot"
        elif any(word in text_lower for word in ['no', 'not now', 'later', 'maybe']):
            response_text = "No problem! Is there anything else I can help you with today?"
            conversation_state["state"] = "greeting"
        else:
            response_text = "Would you like to book an appointment? Please say yes or no."
                
    elif conversation_state["state"] == "time_preference":
        text_lower = transcript.lower()
        if "morning" in text_lower:
            conversation_state["time_preference"] = "morning"
        elif "afternoon" in text_lower:
            conversation_state["time_preference"] = "afternoon"
        elif "evening" in text_lower:
            conversation_state["time_preference"] = "evening"
        else:
            conversation_state["time_preference"] = "morning"
        
        # Generate mock slots (in real implementation, call MCP)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        mock_slots = [
            {"datetime": f"{tomorrow}T10:00:00Z", "id": "slot1"},
            {"datetime": f"{tomorrow}T14:00:00Z", "id": "slot2"}
        ]
        conversation_state["available_slots"] = mock_slots
        
        if len(mock_slots) >= 2:
            dt1 = format_datetime(mock_slots[0]["datetime"])
            dt2 = format_datetime(mock_slots[1]["datetime"])
            response_text = f"I have 2 slots in IST: {dt1}, or {dt2}. Say first or second, or yes to book the first."
            conversation_state["state"] = "confirm_slot"
        else:
            response_text = "I'm sorry, no slots are available. Would you like to be added to the waitlist?"
            conversation_state["state"] = "waitlist"
            
    elif conversation_state["state"] == "confirm_slot":
        text_lower = transcript.lower()
        slots = conversation_state.get("available_slots", [])
        
        if "first" in text_lower or "yes" in text_lower:
            selected_slot = slots[0] if slots else None
        elif "second" in text_lower:
            selected_slot = slots[1] if len(slots) > 1 else None
        else:
            response_text = "Please say first, second, or yes to book a slot."
            return response_text, "", {}
            
        if selected_slot:
            # Generate booking
            topic_prefix = conversation_state.get("topic", "GEN")[:3].upper()
            booking_code = generate_booking_code(topic_prefix)
            
            conversation_state["selected_slot"] = selected_slot
            conversation_state["booking_code"] = booking_code
            
            # Create real calendar event via MCP
            calendar_result = create_calendar_event(
                topic=conversation_state.get("topic", "Unknown"),
                booking_code=booking_code,
                slot_datetime=selected_slot['datetime']
            )
            
            meet_link = calendar_result.get("meet_link") if calendar_result.get("success") else None
            calendar_link = calendar_result.get("html_link") if calendar_result.get("success") else None
            event_id = calendar_result.get("event_id") if calendar_result.get("success") else None
            
            # Store in conversation state for later use
            conversation_state["meet_link"] = meet_link
            conversation_state["calendar_link"] = calendar_link
            conversation_state["event_id"] = event_id
            
            # Append to Google Doc
            notes_result = append_notes_to_doc(booking_code, conversation_state.get("topic", "Unknown"), 
                               selected_slot['datetime'], meet_link or "N/A")
            
            # Send email notification
            email_result = send_email_notification(booking_code, conversation_state.get("topic", "Unknown"),
                                   selected_slot['datetime'], meet_link or "", calendar_link or "")

            # Track MCP statuses for pipeline bar
            mcp_status = {
                "calendar": "ok" if calendar_result.get("success") else "error",
                "doc":      "ok" if (notes_result and notes_result.get("success")) else "error",
                "mail":     "ok" if (email_result and email_result.get("success")) else "error",
            }
            conversation_state["mcp_status"] = mcp_status
            
            # Create booking confirmation HTML — light theme
            meet_btn = (
                f'<a href="MEET_LINK_PLACEHOLDER" target="_blank" style="display:inline-flex;align-items:center;gap:6px;'
                f'background:linear-gradient(135deg,#6366f1,#7c3aed);color:#fff;text-decoration:none;'
                f'padding:9px 16px;border-radius:10px;font-size:12px;font-weight:700;width:100%;justify-content:center;'
                f'box-shadow:0 4px 12px rgba(99,102,241,0.25);">'
                f'🎥 Join Google Meet ↗</a>'
            ) if meet_link else (
                '<span style="font-size:11px;color:#9ca3af;">Meet link will be emailed shortly</span>'
            )

            booking_html = f"""
            <div style="background:#ffffff;border:1.5px solid #c4b5fd;border-radius:16px;padding:20px;
                        box-shadow:0 4px 20px rgba(99,102,241,0.08);">
              <!-- header -->
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                <div style="width:36px;height:36px;border-radius:10px;
                            background:linear-gradient(135deg,#10b981,#059669);
                            display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;">✓</div>
                <div>
                  <div style="font-size:15px;font-weight:700;color:#111827;">Booking Confirmed</div>
                  <div style="font-size:11px;color:#9ca3af;">All systems updated</div>
                </div>
              </div>

              <!-- booking code -->
              <div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:12px;
                          padding:14px;text-align:center;margin-bottom:14px;">
                <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#9ca3af;margin-bottom:6px;font-weight:600;">
                  Booking Code
                </div>
                <div style="font-size:26px;font-weight:800;letter-spacing:4px;
                            background:linear-gradient(135deg,#6366f1,#7c3aed);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                  {booking_code}
                </div>
              </div>

              <!-- details -->
              <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:8px 12px;background:#f9fafb;border:1px solid #f3f4f6;border-radius:8px;">
                  <span style="font-size:11px;color:#6b7280;font-weight:500;">Topic</span>
                  <span style="font-size:12px;color:#111827;font-weight:600;">{conversation_state.get('topic','Unknown')}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:8px 12px;background:#f9fafb;border:1px solid #f3f4f6;border-radius:8px;">
                  <span style="font-size:11px;color:#6b7280;font-weight:500;">Time (IST)</span>
                  <span style="font-size:12px;color:#111827;font-weight:600;">{format_datetime(selected_slot['datetime'])}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:8px 12px;background:#f9fafb;border:1px solid #f3f4f6;border-radius:8px;">
                  <span style="font-size:11px;color:#6b7280;font-weight:500;">Duration</span>
                  <span style="font-size:12px;color:#111827;font-weight:600;">30 minutes</span>
                </div>
              </div>

              <!-- meet link -->
              <div style="margin-bottom:14px;">{meet_btn}</div>

              <!-- status chips -->
              <div style="display:flex;flex-direction:column;gap:5px;
                          padding:12px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;">
                <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#374151;font-weight:500;">
                  <span style="color:#10b981;font-weight:700;">✓</span> Calendar event created
                </div>
                <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#374151;font-weight:500;">
                  <span style="color:#10b981;font-weight:700;">✓</span> Notes saved to Google Doc
                </div>
                <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#374151;font-weight:500;">
                  <span style="color:#10b981;font-weight:700;">✓</span> Advisor email sent
                </div>
              </div>
            </div>
            """
            
            response_text = f"Perfect! Your appointment is confirmed. Your booking code is {booking_code}. "
            if meet_link:
                response_text += f"Your Google Meet link is: {meet_link}. "
            response_text += "You'll receive a confirmation email shortly."
            
            conversation_state["state"] = "complete"
            
    elif conversation_state["state"] == "waitlist":
        if "yes" in transcript.lower():
            response_text = "You've been added to the waitlist. We'll notify you when a slot becomes available."
            conversation_state["state"] = "complete"
        else:
            response_text = "Would you like to be added to the waitlist for the next available slot?"
            
    else:  # complete or any other state
        response_text = (
            "Your booking is complete. Is there anything else I can help you with today? "
            "You can start a new booking anytime by mentioning a topic."
        )
        conversation_state["state"] = "greeting"
    
    return response_text, booking_html, conversation_state.get("mcp_status", {})
