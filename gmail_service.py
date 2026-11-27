import base64
import os
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        return " ".join(self.parts)


def _decode_part(data):
    if not data:
        return ""
    raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    return raw.decode("utf-8", errors="replace")


def _extract_text(payload):
    """Prefer text/plain; fall back to stripping HTML."""
    plain, html = [], []

    def walk(part):
        mime = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")
        if body_data:
            decoded = _decode_part(body_data)
            if mime == "text/plain":
                plain.append(decoded)
            elif mime == "text/html":
                parser = _HTMLText()
                parser.feed(decoded)
                html.append(parser.text())
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return "\n".join(plain or html).strip()


def authenticate_gmail():
    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials/credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "credentials/token.json")
    if not os.path.isfile(credentials_file):
        raise FileNotFoundError(
            f"Gmail OAuth client file not found: {credentials_file}. "
            "Download a Desktop OAuth client JSON from Google Cloud Console."
        )

    creds = None
    if os.path.isfile(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file,
                SCOPES
            )

            print("\nStarting Google OAuth authentication...")

            creds = flow.run_local_server(
                host="localhost",
                port=0,
                open_browser=True,
                access_type="offline",
                prompt="consent",
                timeout_seconds=180
            )

            print("\nGoogle authentication successful!")

        os.makedirs(os.path.dirname(token_file) or ".", exist_ok=True)
        with open(token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        try:
            os.chmod(token_file, 0o600)
        except OSError:
            pass
        

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def fetch_emails(max_results=30):
    """Fetch messages matching the configured Gmail search query."""
    service = authenticate_gmail()
    query = os.getenv("GMAIL_QUERY", "newer_than:2d")
    response = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    emails = []
    for item in response.get("messages", []):
        data = service.users().messages().get(
            userId="me", id=item["id"], format="full"
        ).execute()
        payload = data.get("payload", {})
        headers = {
            h["name"].lower(): h["value"]
            for h in payload.get("headers", [])
        }
        emails.append({
            "id": item["id"],
            "thread_id": data.get("threadId", ""),
            "sender": headers.get("from", ""),
            "subject": headers.get("subject", "(no subject)"),
            "date": headers.get("date", ""),
            "body": _extract_text(payload) or data.get("snippet", ""),
        })
    return emails
