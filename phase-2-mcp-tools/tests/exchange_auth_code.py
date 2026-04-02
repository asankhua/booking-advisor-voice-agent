#!/usr/bin/env python3
"""
Exchange Google OAuth authorization code for token
"""
import json
from google_auth_oauthlib.flow import Flow

# The authorization code from Safari
AUTH_CODE = "4/1Aci98E9sGvKe7oLx56jcBilgpo4OwA16v6XSO4N4eZ-pMw6Aygisv9nTg9w"

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

print("Exchanging authorization code for token...")
print(f"Code: {AUTH_CODE[:20]}...")

flow = Flow.from_client_secrets_file(
    '../config/google-credentials.json',
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

try:
    flow.fetch_token(code=AUTH_CODE)
    creds = flow.credentials

    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    with open('../config/google-token.json', 'w') as f:
        json.dump(token_data, f, indent=2)

    # Also save to phase-2-mcp-tools
    with open('../config/google-token.json', 'w') as f:
        json.dump(token_data, f, indent=2)

    print("\n✅ Token saved successfully!")
    print("\nGranted scopes:")
    for scope in creds.scopes:
        print(f"  ✓ {scope}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nThe code may have expired. Please get a fresh code from Safari.")
