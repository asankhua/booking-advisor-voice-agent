"""
Google Docs Provider for Notes
Appends booking details to a Google Doc
"""
import os
import json
from typing import Dict, Any
from datetime import datetime

class GoogleDocsProvider:
    """
    Real Google Docs API integration
    Appends booking entries to a shared Google Doc
    """
    
    def __init__(self):
        self.doc_id = os.getenv('GOOGLE_DOC_ID')
        self.token_path = os.getenv('GOOGLE_TOKEN_PATH', 'config/google-token.json')
        self.service = None
        self._init_service()
    
    def _init_service(self):
        """Initialize Google Docs API service"""
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
                    scopes=token_data.get('scopes', [
                        'https://www.googleapis.com/auth/documents',
                        'https://www.googleapis.com/auth/drive.file'
                    ])
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
                    scopes=[
                        'https://www.googleapis.com/auth/documents',
                        'https://www.googleapis.com/auth/drive.file'
                    ]
                )
            
            self.service = build('docs', 'v1', credentials=creds)
            print("✅ Google Docs API initialized")
            
        except Exception as e:
            print(f"⚠️  Google Docs init failed (using mock): {e}")
            self.service = None
    
    def append_booking(self, booking_code: str, date: str, topic: str, 
                       slot: str, notes: str = "", meet_link: str = None,
                       mcp_status: str = "SUCCESS") -> Dict[str, Any]:
        """
        Append booking entry to Google Doc with timestamp, MCP status, and meet link
        """
        if not self.service or not self.doc_id:
            # Mock response for testing
            return {
                "success": True,
                "doc_id": self.doc_id or "mock_doc",
                "mock": True,
                "message": f"Mock: Appended {booking_code} to document"
            }
        
        try:
            # Get current document to find end
            doc = self.service.documents().get(documentId=self.doc_id).execute()
            content = doc.get('body', {}).get('content', [])
            
            # Find end of document
            end_index = 1
            for element in content:
                if 'endIndex' in element:
                    end_index = max(end_index, element['endIndex'])
            
            # Format entry with timestamp, MCP status, and meet link
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry_text = f"\n\n{'='*50}\n"
            entry_text += f"📅 BOOKING: {booking_code}\n"
            entry_text += f"⏰ Timestamp: {timestamp}\n"
            entry_text += f"📊 MCP Status: {mcp_status}\n"
            entry_text += f"📋 Topic: {topic}\n"
            entry_text += f"📆 Date: {date}\n"
            entry_text += f"🕐 Slot: {slot}\n"
            if meet_link:
                entry_text += f"🔗 Meet Link: {meet_link}\n"
            if notes:
                entry_text += f"📝 Notes: {notes}\n"
            entry_text += f"{'='*50}\n"
            
            # Append to document
            requests = [{
                'insertText': {
                    'location': {
                        'index': end_index - 1  # Insert before final newline
                    },
                    'text': entry_text
                }
            }]
            
            result = self.service.documents().batchUpdate(
                documentId=self.doc_id,
                body={'requests': requests}
            ).execute()
            
            print(f"✅ Appended booking {booking_code} to Google Doc")
            
            return {
                "success": True,
                "doc_id": self.doc_id,
                "revision_id": result.get('writeControl', {}).get('requiredRevisionId')
            }
            
        except Exception as e:
            print(f"❌ Failed to append to Google Doc: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Factory function
def create_google_docs_provider():
    return GoogleDocsProvider()
