"""
Google Calendar Provider with Google Meet Integration
Creates actual calendar events with Meet conference data
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

class GoogleCalendarProvider:
    """
    Real Google Calendar API integration with Google Meet
    """
    
    def __init__(self):
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.credentials_path = self._resolve_path(os.getenv('GOOGLE_CREDENTIALS_PATH'))
        self.token_path = self._resolve_path(os.getenv('GOOGLE_TOKEN_PATH'))
        self.service = None
        self._init_service()
    
    def _resolve_path(self, path):
        """Resolve relative paths from project root"""
        if not path:
            return None
        if os.path.isabs(path):
            return path
        # Try project root (3 levels up from providers file: providers/ -> mcp-tools/ -> project root)
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / path
        if full_path.exists():
            return str(full_path)
        # Also try project root directly (without config/ prefix)
        alt_path = project_root / Path(path).name
        if alt_path.exists():
            return str(alt_path)
        # Fallback to current working directory
        return path
    
    def _init_service(self):
        """Initialize Google Calendar API service"""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            # Try loading from token file first
            if self.token_path and os.path.exists(self.token_path):
                with open(self.token_path, 'r') as f:
                    token_data = json.load(f)
                
                creds = Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/calendar'])
                )
            else:
                # Fallback to environment variables
                client_id = os.getenv('GOOGLE_CLIENT_ID')
                client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
                
                if not client_id or not client_secret:
                    raise ValueError("No Google credentials found. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars or provide token file.")
                
                creds = Credentials(
                    token=None,
                    refresh_token=os.getenv('GOOGLE_REFRESH_TOKEN'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
            
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar API initialized")
            
        except Exception as e:
            print(f"⚠️  Google Calendar init failed (using mock): {e}")
            self.service = None
    
    def create_event_with_meet(self, topic: str, booking_code: str, 
                               start_time: datetime, duration_minutes: int = 30,
                               attendee_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Create Google Calendar event with Google Meet
        
        Event title format: "Advisor Q&A — {Topic} — {Code}"
        """
        if not self.service:
            # Mock response for testing
            return {
                "success": True,
                "event_id": f"mock_{booking_code}",
                "meet_link": f"https://meet.google.com/mock-{booking_code.lower().replace('-', '')}",
                "html_link": f"https://calendar.google.com/calendar/event?eid=mock",
                "mock": True
            }
        
        try:
            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Event title: "Advisor Q&A — {Topic} — {Code}"
            event_title = f"Advisor Q&A — {topic} — {booking_code}"
            
            # Create event body
            event_body = {
                'summary': event_title,
                'description': f'Booking Code: {booking_code}\nTopic: {topic}\n\nJoin the meeting via Google Meet.',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                # Add Google Meet conference
                'conferenceData': {
                    'createRequest': {
                        'requestId': booking_code,
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                # Add attendee if provided
                'attendees': [],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},  # 30 min before
                    ],
                },
            }
            
            # Add attendee if provided
            if attendee_email:
                event_body['attendees'].append({'email': attendee_email})
            
            # Create the event
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body,
                conferenceDataVersion=1  # Required for Meet
            ).execute()
            
            # Extract Meet link
            meet_link = event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
            html_link = event.get('htmlLink', '')
            
            print(f"✅ Calendar event created: {event_title}")
            print(f"✅ Google Meet link: {meet_link}")
            
            return {
                "success": True,
                "event_id": event['id'],
                "meet_link": meet_link,
                "html_link": html_link,
                "title": event_title,
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to create calendar event: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event"""
        if not self.service:
            return True  # Mock success
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            print(f"❌ Failed to delete event: {e}")
            return False

# Factory function
def create_google_calendar_provider():
    return GoogleCalendarProvider()
