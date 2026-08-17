import pytest

import communication_tools
from communication_tools import (
    CommunicationToolError,
    send_email,
    send_notification,
)


def disable_history_writing(monkeypatch):
    saved_records = []

    monkeypatch.setattr(
        communication_tools,
        "save_record",
        saved_records.append,
    )

    return saved_records


def test_email_is_simulated(monkeypatch):
    monkeypatch.setenv(
        "COMMUNICATION_MODE",
        "simulation",
    )

    saved_records = disable_history_writing(
        monkeypatch
    )

    result = send_email(
        recipient="customer@example.com",
        subject="Payment Reminder",
        message="Your payment of Rs 2200 is due.",
        event_type="payment_due",
        priority="medium",
    )

    assert result["status"] == "simulated"
    assert result["channel"] == "email"
    assert result["tool_name"] == "send_email"
    assert len(saved_records) == 1


def test_notification_is_simulated(monkeypatch):
    monkeypatch.setenv(
        "COMMUNICATION_MODE",
        "simulation",
    )

    saved_records = disable_history_writing(
        monkeypatch
    )

    result = send_notification(
        recipient="80105",
        subject="Service Restored",
        message="Your internet service is restored.",
        event_type="service_restored",
        priority="low",
    )

    assert result["status"] == "simulated"
    assert result["channel"] == "notification"
    assert result["tool_name"] == "send_notification"
    assert len(saved_records) == 1


def test_invalid_priority_is_rejected(monkeypatch):
    disable_history_writing(monkeypatch)

    with pytest.raises(
        CommunicationToolError,
        match="Invalid",
    ):
        send_email(
            recipient="customer@example.com",
            subject="Test",
            message="Test message",
            event_type="payment_due",
            priority="urgent",
        )


def test_live_email_fails_safely_without_smtp(
    monkeypatch,
):
    monkeypatch.setenv(
        "COMMUNICATION_MODE",
        "live",
    )

    monkeypatch.delenv(
        "SMTP_HOST",
        raising=False,
    )
    monkeypatch.delenv(
        "SMTP_USERNAME",
        raising=False,
    )
    monkeypatch.delenv(
        "SMTP_PASSWORD",
        raising=False,
    )
    monkeypatch.delenv(
        "SMTP_FROM_EMAIL",
        raising=False,
    )

    disable_history_writing(monkeypatch)

    result = send_email(
        recipient="customer@example.com",
        subject="Test Email",
        message="Test message",
        event_type="general_notice",
        priority="low",
    )

    assert result["status"] == "failed"
    assert "SMTP settings" in result["details"]