from base64 import b64decode
from os import path, getenv
from typing import Iterator

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from email_service import Email, EmailService

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",   # Read emails
    "https://www.googleapis.com/auth/gmail.modify"      # Mark email as read
]

class GmailService(EmailService):

    service = None

    def __init__(self):
        creds = None
        if path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    getenv("PATH_TO_GCP_OAUTH_SECRET"), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def __iter__(self) -> Iterator:
        try:
            if self.service is None:
                raise Exception("Service object is None!")

            results = self.service.users().messages().list(userId='me', q='is:unread').execute()
            messages = results.get('messages', [])

            for msg_id in map(lambda m: m['id'], messages):

                msg = self.service.users().messages().get(userId='me', id=msg_id).execute()

                # Get value of 'payload' from dictionary 'txt'
                payload = msg['payload']
                headers = payload.get('headers', [])

                # Look for Subject and Sender Email in the headers
                subject = next((d['value'] for d in headers if d['name'] == 'Subject'), None)
                sender_full = next((d['value'] for d in headers if d['name'] == 'From'), None)

                if sender_full and '<' in sender_full:
                    sender = sender_full.split('<')[1].replace('>', '')
                else:
                    sender = sender_full

                # The Body of the message is in Base64 format, and may be nested
                # inside multipart/alternative or multipart/mixed parts, or absent
                # entirely (e.g. an attachment-only message). Prefer HTML, fall
                # back to plain text.
                body = self._find_body(payload, 'text/html')
                if body is None:
                    body = self._find_body(payload, 'text/plain')

                yield Email(sender, subject, body, id=msg_id)

        except Exception as e:
            print(f"An error occurred: {e}")

    def mark_as_read(self, email: Email):
        if self.service is None:
            raise Exception("Service object is None!")

        self.service.users().messages().modify(
            userId='me', id=email.id, body={'removeLabelIds': ['UNREAD']}
        ).execute()

    
    def _find_body(self, payload, mime_type='text/html'):
        """Recursively search a Gmail message payload for a part with the given
        MIME type and return its decoded contents, or None if not found.
        Handles both single-part messages and arbitrarily nested multipart
        messages (e.g. multipart/mixed containing multipart/alternative)."""
        if payload.get('mimeType') == mime_type:
            data = payload.get('body', {}).get('data')
            if data:
                data = data.replace("-", "+").replace("_", "/")
                return b64decode(data).decode('utf-8', errors='replace')

        for part in payload.get('parts') or []:
            body = self._find_body(part, mime_type)
            if body is not None:
                return body

        return None
