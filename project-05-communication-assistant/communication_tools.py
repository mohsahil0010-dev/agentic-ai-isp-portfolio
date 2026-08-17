import os
import smtplib
from email.message import EmailMessage
from typing import Any

from dotenv import load_dotenv

from history import save_record
from models import (
    CommunicationChannel,
    CommunicationRecord,
    DeliveryStatus,
    EventType,
    Priority,
)


class CommunicationToolError(Exception):
    """Raised when a communication tool receives invalid input."""


def get_mode() -> str:
    load_dotenv()
    return os.getenv(
        "COMMUNICATION_MODE",
        "simulation",
    ).lower()


def send_email(
    recipient: str,
    subject: str,
    message: str,
    event_type: str,
    priority: str,
) -> dict[str, Any]:
    """Send or safely simulate an ISP customer email."""

    try:
        selected_event = EventType(event_type)
        selected_priority = Priority(priority)
    except ValueError as exc:
        raise CommunicationToolError(
            f"Invalid email tool input: {exc}"
        ) from exc

    mode = get_mode()
    status = DeliveryStatus.SIMULATED
    details = "Email safely simulated; no real email was sent."

    if mode == "live":
        load_dotenv()

        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = (
            os.getenv("SMTP_FROM_EMAIL")
            or smtp_username
        )

        required_settings = [
            smtp_host,
            smtp_username,
            smtp_password,
            from_email,
        ]

        if not all(required_settings):
            status = DeliveryStatus.FAILED
            details = (
                "Live email mode is enabled, but SMTP settings "
                "are incomplete."
            )
        else:
            try:
                email_message = EmailMessage()
                email_message["From"] = from_email
                email_message["To"] = recipient
                email_message["Subject"] = subject
                email_message.set_content(message)

                with smtplib.SMTP(
                    smtp_host,
                    smtp_port,
                    timeout=20,
                ) as smtp:
                    smtp.starttls()
                    smtp.login(
                        smtp_username,
                        smtp_password,
                    )
                    smtp.send_message(email_message)

                status = DeliveryStatus.SENT
                details = "Email sent through the configured SMTP server."

            except Exception as exc:
                status = DeliveryStatus.FAILED
                details = f"SMTP email failed: {exc}"

    record = CommunicationRecord(
        event_type=selected_event,
        channel=CommunicationChannel.EMAIL,
        priority=selected_priority,
        recipient=recipient,
        subject=subject,
        message=message,
        status=status,
        tool_name="send_email",
        details=details,
    )

    save_record(record)
    return record.model_dump(mode="json")


def send_notification(
    recipient: str,
    subject: str,
    message: str,
    event_type: str,
    priority: str,
) -> dict[str, Any]:
    """Create an internal ISP customer or technical notification."""

    try:
        selected_event = EventType(event_type)
        selected_priority = Priority(priority)
    except ValueError as exc:
        raise CommunicationToolError(
            f"Invalid notification tool input: {exc}"
        ) from exc

    mode = get_mode()

    status = (
        DeliveryStatus.SIMULATED
        if mode == "simulation"
        else DeliveryStatus.SENT
    )

    details = (
        "Notification safely simulated."
        if mode == "simulation"
        else "Internal notification recorded as sent."
    )

    record = CommunicationRecord(
        event_type=selected_event,
        channel=CommunicationChannel.NOTIFICATION,
        priority=selected_priority,
        recipient=recipient,
        subject=subject,
        message=message,
        status=status,
        tool_name="send_notification",
        details=details,
    )

    save_record(record)
    return record.model_dump(mode="json")


COMMUNICATION_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send or simulate an email to an ISP customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Customer email address.",
                    },
                    "subject": {
                        "type": "string",
                    },
                    "message": {
                        "type": "string",
                    },
                    "event_type": {
                        "type": "string",
                        "enum": [
                            item.value
                            for item in EventType
                        ],
                    },
                    "priority": {
                        "type": "string",
                        "enum": [
                            item.value
                            for item in Priority
                        ],
                    },
                },
                "required": [
                    "recipient",
                    "subject",
                    "message",
                    "event_type",
                    "priority",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": (
                "Create an ISP customer or technical notification."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": (
                            "Customer ID, customer name, area, "
                            "or technical team."
                        ),
                    },
                    "subject": {
                        "type": "string",
                    },
                    "message": {
                        "type": "string",
                    },
                    "event_type": {
                        "type": "string",
                        "enum": [
                            item.value
                            for item in EventType
                        ],
                    },
                    "priority": {
                        "type": "string",
                        "enum": [
                            item.value
                            for item in Priority
                        ],
                    },
                },
                "required": [
                    "recipient",
                    "subject",
                    "message",
                    "event_type",
                    "priority",
                ],
                "additionalProperties": False,
            },
        },
    },
]


COMMUNICATION_TOOL_FUNCTIONS = {
    "send_email": send_email,
    "send_notification": send_notification,
}