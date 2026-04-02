#!/usr/bin/env python3
"""
Exchange authorization code for Google OAuth token
"""
import json
from google_auth_oauthlib.flow import Flow

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

AUTH_CODE = "4/1Aci98E96TNKseAvml67dO3OE-O0rJYW_VVTim9c-Ctq0gyg02hXXpSm6AUE"

print("Exchanging authorization code for token...")

flow = Flow.from_client_secrets_file(
    'config/google-credentials.json',
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

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

with open('config/google-token.json', 'w') as f:
    json.dump(token_data, f, indent=2)

print("\n✅ Token saved successfully!")
print("\nGranted scopes:")
for scope in creds.scopes:
    print(f"  ✓ {scope}")

# Also save to phase-2-mcp-tools
with open('phase-2-mcp-tools/config/google-token.json', 'w') as f:
    json.dump(token_data, f, indent=2)
print("\n✅ Token also saved to phase-2-mcp-tools/config/")
