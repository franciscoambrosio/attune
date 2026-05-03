import base64
from datetime import datetime, timezone, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from attune.models.email import Email

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]
CREDENTIALS_PATH = Path("credentials/credentials.json")
TOKEN_PATH = Path("credentials/token.json")


def _get_credentials() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def _fetch_emails(query: str, max_results: int) -> list[Email]:
    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        full = service.users().messages().get(
            userId="me", messageId=msg["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
        body = _extract_body(full["payload"])

        emails.append(Email(
            id=msg["id"],
            sender=headers.get("From", ""),
            subject=headers.get("Subject", "(no subject)"),
            body=body[:2000],
            timestamp=headers.get("Date", ""),
        ))

    return emails


def fetch_emails_since(after_ts: int, max_results: int = 50) -> list[Email]:
    return _fetch_emails(f"is:unread after:{after_ts}", max_results)


def fetch_emails_since_date(days: int = 30, max_results: int = 100) -> list[Email]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    return _fetch_emails(f"after:{cutoff}", max_results)


def fetch_todays_emails(max_results: int = 50) -> list[Email]:
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    return _fetch_emails(f"after:{today} is:unread", max_results)


def _extract_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return _extract_body(payload["parts"][0])
    data = payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""
