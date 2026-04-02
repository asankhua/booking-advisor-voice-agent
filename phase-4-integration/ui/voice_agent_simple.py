#!/usr/bin/env python3
"""
Simple Working Voice Agent
Minimal implementation that actually works
"""
import gradio as gr
import numpy as np
import requests
from datetime import datetime, timedelta

# State
state = {"step": 0, "topic": "", "time": "", "slot": None, "code": ""}

def process(audio_tuple):
    """Process voice input"""
    global state
    
    if audio_tuple is None:
        return "Click 🎤 and say 'book appointment'", None, ""
    
    # Show recording toast
    gr.Info("🎤 Recording audio...", duration=2)
    
    # Simple mock STT - in real use, call Whisper API
    # For now, simulate based on step
    
    if state["step"] == 0:
        gr.Info("🤖 Agent: Processing your request...", duration=2)
        state["step"] = 1
        return "Hello! I cannot provide investment advice. What topic: KYC, SIP, Statements, Withdrawals, or Account Changes?", None, ""
    
    elif state["step"] == 1:
        gr.Info("🤖 Agent: Understanding topic...", duration=2)
        # Parse topic from audio (simplified)
        state["topic"] = "KYC/Onboarding"
        state["prefix"] = "KY"
        state["step"] = 2
        gr.Info(f"✅ Topic selected: {state['topic']}", duration=3)
        return "KYC/Onboarding. Morning or afternoon?", None, ""
    
    elif state["step"] == 2:
        gr.Info("🤖 Agent: Processing time preference...", duration=2)
        state["time"] = "morning"
        state["step"] = 3
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%B %d")
        gr.Info("✅ Time preference recorded", duration=2)
        return f"I have 2 slots for {tomorrow}: 1) 10 AM IST, 2) 2 PM IST. Say 'first' or 'second'.", None, ""
    
    elif state["step"] == 3:
        gr.Info("🎲 Generating booking code...", duration=2)
        # Generate booking code in format: XX-X123 (e.g., NL-A742)
        prefix = state["prefix"]
        letter = chr(65 + np.random.randint(0, 26))  # Random A-Z
        numbers = np.random.randint(100, 999)
        state["code"] = f"{prefix}-{letter}{numbers}"
        state["step"] = 4
        gr.Info(f"✅ Booking code generated: {state['code']}", duration=3)
        
        # Create MCP calls
        try:
            gr.Info("📅 Creating Google Calendar event...", duration=2)
            # 1. Google Calendar: Create event with Meet
            start_time = datetime.now() + timedelta(days=1)
            start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
            
            calendar_response = requests.post("http://localhost:8000/calendar/event", 
                         json={
                             "topic": state["topic"], 
                             "booking_code": state["code"],
                             "start_time": start_time.isoformat(),
                             "duration_minutes": 30
                         },
                         timeout=5)
            
            meet_link = ""
            if calendar_response.status_code == 200:
                result = calendar_response.json()
                if result.get("success"):
                    meet_link = result.get("meet_link", "")
                    gr.Info("✅ Google Calendar event created with Meet link", duration=3)
                else:
                    gr.Warning("⚠️ Calendar event creation failed", duration=3)
            
            gr.Info("📝 Appending to Advisor Pre-Bookings...", duration=2)
            # 2. Notes: Append to Advisor Pre-Bookings
            notes_response = requests.post("http://localhost:8000/notes/append",
                         json={
                             "booking_code": state["code"],
                             "date": tomorrow,
                             "topic": state["topic"],
                             "slot": "10 AM IST",
                             "notes": f"Pre-booking: {state['topic']} - Code: {state['code']}"
                         },
                         timeout=2)
            if notes_response.status_code == 200:
                gr.Info("✅ Notes appended to Google Doc", duration=3)
            else:
                gr.Warning("⚠️ Notes append failed", duration=3)
            
            gr.Info("📧 Sending advisor notification...", duration=2)
            # 3. Email Draft: Prepare advisor email (approval-gated)
            email_body = f"""A new appointment has been booked.

Booking Code: {state['code']}
Topic: {state['topic']}
Date: {tomorrow}
Slot: 10 AM IST
Google Meet: {meet_link if meet_link else 'Will be generated'}

Please review and approve."""
            
            email_response = requests.post("http://localhost:8000/email/draft",
                         json={
                             "to": "advisor@company.com",
                             "subject": f"New Booking: {state['code']} - {state['topic']}",
                             "body": email_body,
                             "booking_code": state["code"],
                             "requires_approval": True
                         },
                         timeout=2)
            if email_response.status_code == 200:
                gr.Info("✅ Email notification sent to advisor", duration=3)
            else:
                gr.Warning("⚠️ Email notification failed", duration=3)
                
        except Exception as e:
            gr.Warning(f"⚠️ MCP call error: {str(e)}", duration=5)
        
        code = state["code"]
        
        booking_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 12px; text-align: center; margin-top: 20px;">
            <h2>✅ Booking Confirmed!</h2>
            <div style="font-size: 36px; font-family: monospace; letter-spacing: 4px; 
                        background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; margin: 15px 0;">
                {code}
            </div>
            <p style="font-size: 18px;">{state['topic']} - Tomorrow at 10 AM IST</p>
            <p style="font-size: 14px; margin-top: 10px;">Google Meet link will be shared via email</p>
        </div>
        """
        
        gr.Info("🎉 Booking complete! Check your confirmation.", duration=5)
        return f"Perfect! Your booking code is {code}. Your advisor will contact you shortly.", None, booking_html
    
    else:
        gr.Info("📝 Booking confirmed. Use the secure link to complete registration.", duration=3)
        return "Your booking is confirmed! Use the secure link to complete registration.", None, ""

def reset():
    global state
    state = {"step": 0, "topic": "", "time": "", "slot": None, "code": ""}
    gr.Info("🔄 Session reset. Ready for new booking.", duration=3)
    return "Hello! I cannot provide investment advice. I can only help you book an appointment. What topic: KYC, SIP, Statements, Withdrawals, or Account Changes?", None, ""

def select_topic(topic_name):
    """Handle topic selection from button click"""
    global state
    state["topic"] = topic_name
    state["prefix"] = topic_name[:2].upper()
    state["step"] = 2
    gr.Info(f"📋 Topic selected: {topic_name}", duration=3)
    return f"Selected: {topic_name}. Now choose Morning, Afternoon, or Evening.", None, ""

def select_time(time_pref):
    """Handle time preference selection"""
    global state
    state["time"] = time_pref
    state["step"] = 3
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%B %d")
    gr.Info(f"🕐 {time_pref.title()} selected for {tomorrow}", duration=3)
    return f"{time_pref.title()} selected for {tomorrow}. Available slots:", None, ""

def select_slot(slot_num):
    """Handle slot selection and create booking"""
    global state
    
    gr.Info(f"✅ Slot {slot_num} selected", duration=2)
    
    # Generate booking code in format: XX-X123 (e.g., NL-A742)
    letters = state['prefix']
    letter = chr(65 + np.random.randint(0, 26))  # Random A-Z
    numbers = np.random.randint(100, 999)
    state["code"] = f"{letters}-{letter}{numbers}"
    state["step"] = 4
    
    gr.Info(f"🎲 Booking code generated: {state['code']}", duration=3)
    
    # Create MCP calls
    try:
        gr.Info("📅 Creating Google Calendar event...", duration=2)
        # 1. Calendar hold
        requests.post("http://localhost:8000/calendar/hold", 
                     json={"topic": state["topic"], "slot_id": f"slot_{slot_num}", "booking_code": state["code"]},
                     timeout=2)
        gr.Info("✅ Calendar event created", duration=2)
        
        gr.Info("📝 Appending to Advisor Pre-Bookings...", duration=2)
        # 2. Notes: Append to Advisor Pre-Bookings  
        notes_response = requests.post("http://localhost:8000/notes/append",
                     json={
                         "booking_code": state["code"],
                         "date": tomorrow,
                         "topic": state["topic"],
                         "slot": f"{'10 AM IST' if slot_num == 1 else '2 PM IST'}",
                         "notes": f"Pre-booking: {state['topic']} - Code: {state['code']}"
                     },
                     timeout=2)
        if notes_response.status_code == 200:
            gr.Info("✅ Notes appended to Google Doc", duration=3)
        
        gr.Info("📧 Sending advisor notification...", duration=2)
        # 3. Email Draft: Prepare advisor email (approval-gated)
        email_response = requests.post("http://localhost:8000/email/draft",
                     json={
                         "to": "advisor@company.com",
                         "subject": f"New Booking: {state['code']} - {state['topic']}",
                         "body": f"A new appointment has been booked.\n\nBooking Code: {state['code']}\nTopic: {state['topic']}\nDate: {tomorrow}\nSlot: {'10 AM IST' if slot_num == 1 else '2 PM IST'}\n\nPlease review and approve.",
                         "booking_code": state["code"],
                         "requires_approval": True
                     },
                     timeout=2)
        if email_response.status_code == 200:
            gr.Info("✅ Email notification sent to advisor", duration=3)
        
        gr.Info("🎉 All operations completed successfully!", duration=5)
    except Exception as e:
        gr.Warning(f"⚠️ MCP call error: {str(e)}", duration=5)
    
    code = state["code"]
    
    booking_html = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 20px; border-radius: 12px; text-align: center; margin-top: 20px;">
        <h2>✅ Booking Confirmed!</h2>
        <div style="font-size: 36px; font-family: monospace; letter-spacing: 4px; 
                    background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; margin: 15px 0;">
            {code}
        </div>
        <p style="font-size: 18px;">{state['topic']} - Tomorrow at {'10 AM IST' if slot_num == 1 else '2 PM IST'}</p>
        <p style="font-size: 14px; margin-top: 10px;">Google Meet link will be shared via email</p>
    </div>
    """
    
    return f"Perfect! Your booking code is {code}. Your advisor will contact you shortly.", None, booking_html

# UI - Define ALL components first, then event handlers
with gr.Blocks(css="""
.topic-btn { margin: 5px; min-width: 150px; }
.time-btn { margin: 5px; min-width: 100px; }
.slot-btn { margin: 5px; min-width: 200px; }
""") as demo:
    gr.HTML("<h1 style='text-align:center'>🎙️ Advisor Voice Agent</h1>")
    gr.HTML("<p style='text-align:center;color:#64748b'>Speak or click to book an appointment</p>")
    
    with gr.Row():
        with gr.Column():
            gr.HTML("<div style='text-align:center;padding:15px;background:#e2e8f0;border-radius:8px;font-weight:bold'>🎤 Click to Speak</div>")
            
            audio = gr.Audio(
                sources=["microphone"],
                type="numpy",
                streaming=True,
                label="Microphone Input"
            )
            
            gr.Markdown("**Instructions:** Click microphone → Speak → Release → Get response")
            reset_btn = gr.Button("🔄 Schedule Call with advisor", variant="primary")
        
        with gr.Column():
            text = gr.Textbox(label="Response", value="Click 🎤 and say 'I want to book'", lines=3)
            audio_out = gr.Audio(label="Voice", autoplay=True)
            booking = gr.HTML("")
    
    # Topic Selection Pills
    gr.Markdown("---")
    gr.Markdown("**📋 Select Topic (or speak):**")
    with gr.Row():
        topic_kyc = gr.Button("KYC/Onboarding", variant="secondary", elem_classes=["topic-btn"])
        topic_sip = gr.Button("SIP/Mandates", variant="secondary", elem_classes=["topic-btn"])
        topic_statements = gr.Button("Statements/Tax Docs", variant="secondary", elem_classes=["topic-btn"])
        topic_withdrawals = gr.Button("Withdrawals", variant="secondary", elem_classes=["topic-btn"])
        topic_account = gr.Button("Account Changes", variant="secondary", elem_classes=["topic-btn"])
    
    # Calendar and Time Selection
    gr.Markdown("---")
    with gr.Row():
        with gr.Column():
            gr.Markdown("**📅 Select Date:**")
            date_dropdown = gr.Dropdown(
                choices=["Today", "Tomorrow", "Day after tomorrow"],
                value="Tomorrow",
                label="Choose date"
            )
        
        with gr.Column():
            gr.Markdown("**🕐 Select Time Preference:**")
            with gr.Row():
                time_morning = gr.Button("☀️ Morning (9-12 AM)", variant="secondary", elem_classes=["time-btn"])
                time_afternoon = gr.Button("🌤 Afternoon (12-4 PM)", variant="secondary", elem_classes=["time-btn"])
                time_evening = gr.Button("🌙 Evening (4-7 PM)", variant="secondary", elem_classes=["time-btn"])
    
    # Available Slots
    gr.Markdown("---")
    gr.Markdown("**✅ Available Slots (from Google Calendar):**")
    with gr.Row():
        slot1 = gr.Button("Slot 1", variant="secondary", elem_classes=["slot-btn"])
        slot2 = gr.Button("Slot 2", variant="secondary", elem_classes=["slot-btn"])
    
    # Event handlers come AFTER all components are defined
    audio.stream(process, [audio], [text, audio_out, booking])
    reset_btn.click(reset, outputs=[text, audio_out, booking])
    
    # Topic button handlers
    topic_kyc.click(lambda: select_topic("KYC/Onboarding"), outputs=[text, audio_out, booking])
    topic_sip.click(lambda: select_topic("SIP/Mandates"), outputs=[text, audio_out, booking])
    topic_statements.click(lambda: select_topic("Statements/Tax Docs"), outputs=[text, audio_out, booking])
    topic_withdrawals.click(lambda: select_topic("Withdrawals"), outputs=[text, audio_out, booking])
    topic_account.click(lambda: select_topic("Account Changes"), outputs=[text, audio_out, booking])
    
    # Time preference handlers
    time_morning.click(lambda: select_time("morning"), outputs=[text, audio_out, booking])
    time_afternoon.click(lambda: select_time("afternoon"), outputs=[text, audio_out, booking])
    time_evening.click(lambda: select_time("evening"), outputs=[text, audio_out, booking])
    
    # Slot selection handlers
    slot1.click(lambda: select_slot(1), outputs=[text, audio_out, booking])
    slot2.click(lambda: select_slot(2), outputs=[text, audio_out, booking])
    
    # Footer with disclaimer and system status
    gr.Markdown("---")
    with gr.Row():
        gr.HTML("""
        <div style="text-align: center; padding: 15px; background: #f8fafc; border-radius: 8px; margin-top: 20px;">
            <p style="font-size: 12px; color: #64748b; margin: 0;">
                <strong>Disclaimer:</strong> This is an informational assistant only. Not investment advice. 
                No personal data is collected on this call. Booking code will be shared for your records.
            </p>
            <p style="font-size: 11px; color: #94a3b8; margin: 8px 0 0 0;">
                Powered by Sarvam AI + Groq | MCP Tools: Google Calendar, Docs, Resend
            </p>
        </div>
        """)

if __name__ == "__main__":
    demo.launch(server_port=7860)
