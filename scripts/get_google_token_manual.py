#!/usr/bin/env python3
"""
Google Calendar OAuth - Manual Code Exchange
Most reliable method for OAuth when browser redirects fail
"""

import json
import sys

def main():
    try:
        from google_auth_oauthlib.flow import Flow
        
        print("=" * 70)
        print("GOOGLE CALENDAR OAUTH - MANUAL AUTHORIZATION")
        print("=" * 70)
        print("\nStep 1: Open this URL in Safari (copy & paste):\n")
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        # Create flow
        flow = Flow.from_client_secrets_file(
            'config/google-credentials.json',
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Manual redirect (out-of-band)
        )
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen
        )
        
        print(auth_url)
        print("\n" + "=" * 70)
        print("Step 2: Sign in and authorize access")
        print("Step 3: Google will show an authorization code")
        print("Step 4: Copy that code and paste it below\n")
        print("=" * 70)
        
        # Get code from user
        code = input("Paste authorization code here: ").strip()
        
        if not code:
            print("❌ No code provided. Exiting.")
            sys.exit(1)
        
        print("\nExchanging code for token...")
        
        # Exchange code for token
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save token
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes)
        }
        
        with open('config/google-token.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Token saved to config/google-token.json")
        print("=" * 70)
        print("\nYour Google Calendar integration is now ready!")
        print("You can now use the voice agent with real calendar data.")
        
    except FileNotFoundError:
        print("❌ config/google-credentials.json not found!")
        print("Download from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure in Google Cloud Console:")
        print("1. Google Calendar API is enabled")
        print("2. OAuth consent screen is configured")
        print("3. Your email is added as a test user")
        print("4. OAuth client is 'Desktop app' type (not Web)")
        sys.exit(1)

if __name__ == '__main__':
    main()
