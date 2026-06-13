import base64
from datetime import datetime
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.core.config import settings
from app.services.email_parser import parse_bank_email, ParsedTransaction

# Los bancos soportados son mexicanos; convertir el internalDate (UTC) a esta
# zona evita que una compra de las 11pm quede fechada al día siguiente
MX_TZ = ZoneInfo("America/Mexico_City")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BANK_KEYWORDS = ["compra", "cargo", "movimiento", "transacción", '"pago con tarjeta"']


def _decode_body(payload: dict) -> str:
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    if "parts" in payload:
        for part in payload["parts"]:
            text = _decode_body(part)
            if text:
                return text
    return ""


def fetch_new_bank_emails(
    access_token: str,
    refresh_token: str,
    after_timestamp: int | None = None,
    sender_map: dict[str, str] | None = None,
) -> tuple[list[tuple[str, ParsedTransaction]], str | None]:
    """
    Devuelve (lista de (gmail_message_id, ParsedTransaction), access_token_refrescado).
    after_timestamp es epoch en segundos; si es None trae los últimos 30 días.
    El segundo elemento es el access token nuevo si el cliente de Google lo
    refrescó durante la llamada (expiran en 1h), o None si sigue siendo el mismo.
    """
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    service = build("gmail", "v1", credentials=creds)

    query_parts = [f"({' OR '.join(BANK_KEYWORDS)})"]
    if after_timestamp:
        query_parts.append(f"after:{after_timestamp}")
    else:
        query_parts.append("newer_than:30d")

    query = " ".join(query_parts)
    response = service.users().messages().list(userId="me", q=query, maxResults=50).execute()
    messages = response.get("messages", [])

    results = []
    for msg_ref in messages:
        msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}
        sender = headers.get("from", "")
        subject = headers.get("subject", "")
        body = _decode_body(msg["payload"])

        # internalDate: epoch en milisegundos de cuando Gmail recibió el correo
        email_date = None
        if msg.get("internalDate"):
            email_date = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=MX_TZ).date()

        parsed = parse_bank_email(sender, subject, body, email_date, sender_map)
        if parsed:
            results.append((msg_ref["id"], parsed))

    refreshed_token = creds.token if creds.token != access_token else None
    return results, refreshed_token
