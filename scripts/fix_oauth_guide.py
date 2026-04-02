#!/usr/bin/env python3
"""
Quick fix guide for Google OAuth 400 error
"""

print("""
╔══════════════════════════════════════════════════════════════════╗
║  FIX GOOGLE OAUTH 400 ERROR - STEP BY STEP                       ║
╚══════════════════════════════════════════════════════════════════╝

The 400 error means your OAuth consent screen is not configured.
Follow these exact steps:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: Go to OAuth Consent Screen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Open: https://console.cloud.google.com/apis/credentials/consent
2. Select your project: "advisor-voice-agent"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: Configure App Information (if not done)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you see "CONFIGURE CONSENT SCREEN" button, click it:

App Information:
- App name: Voice Agent Calendar
- User support email: YOUR_EMAIL@gmail.com
- Developer contact information: YOUR_EMAIL@gmail.com

Click "SAVE AND CONTINUE"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: Scopes (skip for now)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Click "SAVE AND CONTINUE" (no scopes needed for basic calendar)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: Test Users (CRITICAL - This fixes the 400 error)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Find "Test users" section
2. Click "ADD USERS"
3. Enter: ashishsankhuapg@gmail.com
4. Click "ADD"
5. Click "SAVE AND CONTINUE"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Click "BACK TO DASHBOARD"
2. Look for "PUBLISHING STATUS"
3. If it says "Testing", that's OK for now
4. DO NOT click "PUBLISH APP" yet (not needed for testing)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6: Try Auth Again
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After completing above, run:

    python3 scripts/get_google_token.py

Then click the URL it provides.

The 400 error should be fixed now!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALTERNATIVE: If still getting errors
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Check if you need to:

1. Enable the API (if not done):
   https://console.cloud.google.com/apis/library/calendar.googleapis.com
   Click "ENABLE"

2. Wait 5-10 minutes after changes (Google takes time to propagate)

3. Try incognito/private browser window

4. Or use this simpler auth flow:
   
   python3 -c "
   from google_auth_oauthlib.flow import InstalledAppFlow
   flow = InstalledAppFlow.from_client_secrets_file(
       'config/google-credentials.json',
       ['https://www.googleapis.com/auth/calendar']
   )
   creds = flow.run_console()  # Uses console instead of browser
   import json
   with open('config/google-token.json', 'w') as f:
       json.dump({'token': creds.token, 'refresh_token': creds.refresh_token,
                  'token_uri': creds.token_uri, 'client_id': creds.client_id,
                  'client_secret': creds.client_secret, 'scopes': creds.scopes}, f)
   print('Token saved!')
   "

""")
