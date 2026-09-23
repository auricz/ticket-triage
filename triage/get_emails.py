from base64 import b64decode
from os import path, getenv

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

creds = None
if path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            getenv("PATH_TO_SECRET"), SCOPES
        )
        creds = flow.run_local_server(port=0)
    
# Save the credentials for the next run
with open("token.json", "w") as token:
    token.write(creds.to_json())

try:
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])
    
    msg = service.users().messages().get(userId='me', id=messages[0]['id']).execute()

    # Use try-except to avoid any Errors
    try:
        # Get value of 'payload' from dictionary 'txt'
        payload = msg['payload']
        headers = payload['headers']

        # Look for Subject and Sender Email in the headers
        subject = next((d['value'] for d in headers if d['name'] == 'Subject'), None)
        sender_full = next((d['value'] for d in headers if d['name'] == 'From'), None)

        if sender_full:
            sender = sender_full.split('<')[1].replace('>', '')
        else:
            sender = None

        # The Body of the message is in Encrypted format. So, we have to decode it.
        # Get the data and decode it with base 64 decoder.
        parts = payload.get('parts')[0]
        data = parts['body']['data']
        data = data.replace("-","+").replace("_","/")
        decoded_data = b64decode(data)

        # Printing the subject, sender's email and message
        print("Subject: ", subject)
        print("From: ", sender)
        print("Message: ", decoded_data.decode('utf-8'))
        print('\n')

    except Exception as e:
        print(e)


except Exception as e:
    print(f"An error occurred: {e}")