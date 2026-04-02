#!/usr/bin/env python3
"""
Google Calendar OAuth - Console Version (No Browser)
This bypasses the 400 error by using console-based auth
"""

import json
import sys

def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        print("=" * 60)
        print("Google Calendar OAuth - Console Mode")
        print("=" * 60)
        print("\nThis will provide a URL to open in your browser.")
        print("After authorizing, you'll paste the code back here.\n")
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        flow = InstalledAppFlow.from_client_secrets_file(
            'config/google-credentials.json',
            SCOPES
        )
        
        # Use console-based auth (no local server needed)
        creds = flow.run_console()
        
        # Save token
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        with open('config/google-token.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print("Token saved to: config/google-token.json")
        print("\nYour Google Calendar integration is now ready!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. config/google-credentials.json exists")
        print("2. You've enabled Google Calendar API")
        print("3. Your OAuth consent screen has test users added")
        sys.exit(1)

if __name__ == '__main__':
    main()
