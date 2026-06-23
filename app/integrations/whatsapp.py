import os
import requests
from typing import Any, Dict, Optional

TWILIO_ACCOUNT_SID = os.getenv("AC0b297bffe04ee95fcb2eb0462115f6f7")
TWILIO_AUTH_TOKEN = os.getenv("1166b6c160836f1e6909da4c7c31d14b")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO", "+919754844785")
TWILIO_API_URL = os.getenv(
    "TWILIO_API_URL",
    "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
)


def is_whatsapp_enabled() -> bool:
    return bool(
        TWILIO_ACCOUNT_SID
        and TWILIO_AUTH_TOKEN
        and TWILIO_WHATSAPP_FROM
        and TWILIO_WHATSAPP_TO
    )


def send_whatsapp_message(
    body: str,
    to: Optional[str] = None,
    from_: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a WhatsApp message using Twilio Sandbox credentials from env vars."""
    if not is_whatsapp_enabled():
        return {
            "status": "disabled",
            "reason": "Missing Twilio environment variables",
        }

    to = to or TWILIO_WHATSAPP_TO
    from_ = from_ or TWILIO_WHATSAPP_FROM
    url = TWILIO_API_URL.format(sid=TWILIO_ACCOUNT_SID)

    payload = {
        "From": f"whatsapp:{from_}",
        "To": f"whatsapp:{to}",
        "Body": body,
    }
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    response = requests.post(url, data=payload, auth=auth, timeout=10)
    response.raise_for_status()
    return response.json()


def notify_search(query: str, source: str, answer: str) -> Dict[str, Any]:
    """Send a WhatsApp notification for every search request."""
    if not is_whatsapp_enabled():
        return {"status": "disabled"}

    message = (
        f"[{source.upper()}] New search request:\n"
        f"Query: {query}\n\n"
        f"Answer preview:\n{answer.strip()[:400]}"
    )

    return send_whatsapp_message(body=message)
