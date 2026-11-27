
import os
import logging

from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()

logger = logging.getLogger("jobalert.whatsapp")


def get_twilio_client():
    """Create and validate the Twilio client."""

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        raise ValueError(
            "TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN is missing in .env"
        )

    if not account_sid.startswith("AC"):
        raise ValueError("Invalid Twilio Account SID format")

    return Client(account_sid, auth_token)


def format_notification(data):
    """Format a job opportunity as a WhatsApp message."""

    skills = ", ".join(data.get("skills") or []) or "Not specified"

    bullets = data.get("bullets") or []
    bullet_text = "\n".join(f"• {item}" for item in bullets)

    message = (
        "🚀 JOB / INTERNSHIP ALERT\n\n"
        f"🏢 Company: {data.get('company', 'Not specified')}\n"
        f"💼 Role: {data.get('role', 'Not specified')}\n"
        f"📌 Category: {data.get('category', 'Not specified')}\n"
        f"📍 Location: {data.get('location', 'Not specified')}\n"
        f"💰 Stipend/Salary: {data.get('stipend_or_salary', 'Not specified')}\n"
        f"⏳ Duration: {data.get('duration', 'Not specified')}\n"
        f"🎓 Eligibility: {data.get('eligibility', 'Not specified')}\n"
        f"📅 Deadline: {data.get('deadline', 'Not specified')}\n"
        f"🧠 Skills: {skills}\n\n"
        f"📝 Summary:\n{data.get('summary', 'Not specified')}\n\n"
    )

    if bullet_text:
        message += f"⭐ Highlights:\n{bullet_text}\n\n"

    application_link = data.get("application_link", "Not specified")

    if application_link != "Not specified":
        message += f"🔗 Apply here:\n{application_link}\n"

    # Twilio WhatsApp message body limit.
    if len(message) > 1500:
        message = message[:1450] + "\n\n[Message shortened]"

    return message.strip()


def send_notification(data):
    """
    Send a WhatsApp notification using Twilio.

    Returns the Twilio message SID after successful submission.
    """

    client = get_twilio_client()

    whatsapp_from = os.getenv("WHATSAPP_FROM")
    whatsapp_to = os.getenv("WHATSAPP_TO")

    if not whatsapp_from or not whatsapp_to:
        raise ValueError(
            "WHATSAPP_FROM or WHATSAPP_TO is missing in .env"
        )

    if not whatsapp_from.startswith("whatsapp:+"):
        raise ValueError(
            "WHATSAPP_FROM must use format whatsapp:+14155238886"
        )

    if not whatsapp_to.startswith("whatsapp:+"):
        raise ValueError(
            "WHATSAPP_TO must use format whatsapp:+919876543210"
        )

    message_body = format_notification(data)

    try:
        message = client.messages.create(
            from_=whatsapp_from,
            to=whatsapp_to,
            body=message_body,
        )

        logger.info(
            "WhatsApp message submitted successfully. SID=%s Status=%s",
            message.sid,
            message.status,
        )

        return message.sid

    except TwilioRestException:
        logger.exception("Twilio rejected the WhatsApp message")
        raise
