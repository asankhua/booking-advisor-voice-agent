#!/usr/bin/env python3
"""
Google Calendar OAuth Token Generator
Run this to get your refresh token for Google Calendar API
"""

import json
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

def check_credentials():
    """Check if credentials file is valid"""
    try:
        with open('config/google-credentials.json', 'r') as f:
            creds = json.load(f)
        
        print("=" * 60)
        print("CREDENTIALS CHECK")
        print("=" * 60)
        
        # Check for 'installed' key (Desktop app)
        if 'installed' in creds:
            print("✓ Client type: Desktop app (correct)")
            client = creds['installed']
        elif 'web' in creds:
            print("✗ ERROR: Client type is 'Web application'")
            print("  Fix: Create new OAuth client with 'Desktop app' type")
            return False
        else:
            print("✗ Unknown client type")
            return False
        
        # Check redirect URIs
        redirect_uris = client.get('redirect_uris', [])
        if 'http://localhost' in redirect_uris:
            print("✓ Redirect URIs configured")
        else:
            print("✗ Missing http://localhost in redirect_uris")
            print(f"  Found: {redirect_uris}")
        
        print(f"✓ Client ID: {client.get('client_id', 'MISSING')[:20]}...")
        print(f"✓ Project: {client.get('project_id', 'MISSING')}")
        
        return True
        
    except FileNotFoundError:
        print("✗ config/google-credentials.json not found!")
        print("  Download from Google Cloud Console → APIs & Services → Credentials")
        return False
    except json.JSONDecodeError:
        print("✗ Invalid JSON in credentials file")
        return False

def main():
    if not check_credentials():
        print("\n" + "=" * 60)
        print("FIX REQUIRED:")
        print("=" * 60)
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Click 'Create Credentials' → 'OAuth client ID'")
        print("3. Select 'Desktop app' as Application type")
        print("4. Name: 'Voice Agent Desktop'")
        print("5. Click 'Create' and download the JSON")
        print("6. Replace config/google-credentials.json with the new file")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("STARTING OAUTH FLOW")
    print("=" * 60)
    
    # Create the flow using the client secrets file
    flow = InstalledAppFlow.from_client_secrets_file(
        'config/google-credentials.json', 
        SCOPES
    )
    
    try:
        # Run the OAuth flow with fixed port
        creds = flow.run_local_server(port=8085, open_browser=False)
        print("Browser opened. Waiting for authorization...")
        print(f"If not opened, visit: {flow.authorization_url()[0]}")
        
        # Save the credentials to a JSON file
        token_path = 'config/google-token.json'
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        with open(token_path, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("\n" + "=" * 60)
        print(" SUCCESS!")
        print("=" * 60)
        print(f"Token saved to: {token_path}")
        print("\nYou can now use Google Calendar in your voice agent!")
        print("=" * 60)
    
    except Exception as e:
        print("\n" + "=" * 60)
        print(" ERROR OCCURRED DURING OAUTH FLOW")
        print("=" * 60)
        print(f"Error: {e}")
        print("=" * 60)
    print("=" * 60)

if __name__ == '__main__':
    main()
