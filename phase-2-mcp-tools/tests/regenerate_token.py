#!/usr/bin/env python3
"""
Regenerate Google OAuth Token with correct scopes for Calendar + Docs
Run this to get a new token with all required permissions
"""
import os
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes needed for all features
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

def regenerate_token():
    """Generate new OAuth token with all required scopes"""
    print("=" * 60)
    print("REGENERATING GOOGLE OAUTH TOKEN")
    print("=" * 60)
    print("\nRequired scopes:")
    for scope in SCOPES:
        print(f"  - {scope}")
    
    creds_path = '../config/google-credentials.json'
    token_path = '../config/google-token.json'
    
    if not os.path.exists(creds_path):
        print(f"\n❌ Credentials file not found: {creds_path}")
        print("   Download it from Google Cloud Console")
        return
    
    print(f"\n🔄 Starting OAuth flow...")
    print(f"   A browser window will open for authentication")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the token
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
        
        print(f"\n✅ Token saved to: {token_path}")
        print(f"\nGranted scopes:")
        for scope in creds.scopes:
            print(f"  ✓ {scope}")
        
        # Also update token in phase-2-mcp-tools
        mcp_token_path = '../config/google-token.json'
        if os.path.exists('../config'):
            with open(mcp_token_path, 'w') as f:
                json.dump(token_data, f, indent=2)
            print(f"\n✅ Token also saved to: {mcp_token_path}")
        
        print("\n" + "=" * 60)
        print("TOKEN REGENERATION COMPLETE")
        print("=" * 60)
        print("\n📝 Restart the MCP server to use the new token:")
        print("   pkill -f mcp_server")
        print("   python3 phase-2-mcp-tools/server/mcp_server.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    regenerate_token()
