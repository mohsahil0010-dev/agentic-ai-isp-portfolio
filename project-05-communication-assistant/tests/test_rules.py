from models import (
    CommunicationChannel,
    EventType,
    ISPEvent,
    Priority,
)
from rules import evaluate_communication_rules


def test_outage_is_critical_and_uses_both_channels():
    event = ISPEvent(
        event_type=EventType.NETWORK_OUTAGE,
        email="customer@example.com",
        area="Model Town",
        details="Internet service is unavailable.",
    )

    result = evaluate_communication_rules(event)

    assert result.should_communicate is True
    assert result.priority == Priority.CRITICAL
    assert result.channel == CommunicationChannel.BOTH


def test_outage_falls_back_when_email_is_missing():
    event = ISPEvent(
        event_type=EventType.NETWORK_OUTAGE,
        area="Model Town",
        details="Internet service is unavailable.",
    )

    result = evaluate_communication_rules(event)

    assert result.channel == CommunicationChannel.NOTIFICATION


def test_critical_weak_signal():
    event = ISPEvent(
        event_type=EventType.WEAK_SIGNAL,
        email="customer@example.com",
        rx_power_dbm=-30.2,
        details="Optical signal is critically weak.",
    )

    result = evaluate_communication_rules(event)

    assert result.priority == Priority.CRITICAL
    assert result.channel == CommunicationChannel.BOTH


def test_acceptable_signal_requires_no_message():
    event = ISPEvent(
        event_type=EventType.WEAK_SIGNAL,
        rx_power_dbm=-24.0,
        details="Optical signal was checked.",
    )

    result = evaluate_communication_rules(event)

    assert result.should_communicate is False
    assert result.channel == CommunicationChannel.NONE


def test_large_payment_due_has_high_priority():
    event = ISPEvent(
        event_type=EventType.PAYMENT_DUE,
        email="customer@example.com",
        amount_due=5000,
        details="Monthly internet payment is due.",
    )

    result = evaluate_communication_rules(event)

    assert result.priority == Priority.HIGH
    assert result.channel == CommunicationChannel.EMAIL


def test_maintenance_uses_medium_priority():
    event = ISPEvent(
        event_type=EventType.SCHEDULED_MAINTENANCE,
        email="customer@example.com",
        area="Layyah",
        details="Fiber maintenance is scheduled.",
    )

    result = evaluate_communication_rules(event)

    assert result.priority == Priority.MEDIUM
    assert result.channel == CommunicationChannel.BOTH


def test_service_restored_uses_notification():
    event = ISPEvent(
        event_type=EventType.SERVICE_RESTORED,
        area="Model Town",
        details="Internet service has been restored.",
    )

    result = evaluate_communication_rules(event)

    assert result.priority == Priority.LOW
    assert result.channel == CommunicationChannel.NOTIFICATION