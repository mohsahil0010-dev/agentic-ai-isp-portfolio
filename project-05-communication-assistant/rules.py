from dataclasses import asdict, dataclass
from typing import Any

from models import (
    CommunicationChannel,
    EventType,
    ISPEvent,
    Priority,
)


@dataclass(frozen=True)
class RuleDecision:
    """Deterministic result produced before the AI agent runs."""

    should_communicate: bool
    channel: CommunicationChannel
    priority: Priority
    audience: str
    reason: str
    instructions: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def get_audience(event: ISPEvent) -> str:
    """Build a human-readable communication audience."""

    if event.customer_name and event.customer_id:
        return (
            f"{event.customer_name} "
            f"(Customer ID: {event.customer_id})"
        )

    if event.customer_id:
        return f"Customer ID: {event.customer_id}"

    if event.area:
        return f"Customers in {event.area}"

    return "Affected ISP customers"


def select_available_channel(
    preferred_channel: CommunicationChannel,
    event: ISPEvent,
) -> CommunicationChannel:
    """Fall back to an app notification when email is unavailable."""

    if preferred_channel in {
        CommunicationChannel.EMAIL,
        CommunicationChannel.BOTH,
    } and not event.email:
        return CommunicationChannel.NOTIFICATION

    return preferred_channel


def evaluate_communication_rules(
    event: ISPEvent,
) -> RuleDecision:
    """Evaluate defined ISP conditions before AI message generation."""

    audience = get_audience(event)

    if event.event_type == EventType.NETWORK_OUTAGE:
        channel = select_available_channel(
            CommunicationChannel.BOTH,
            event,
        )

        return RuleDecision(
            should_communicate=True,
            channel=channel,
            priority=Priority.CRITICAL,
            audience=audience,
            reason="A network outage requires immediate communication.",
            instructions=(
                "Inform customers about the outage, apologize for the "
                "disruption, mention the affected area when available, "
                "and state that the technical team is working on it."
            ),
        )

    if event.event_type == EventType.WEAK_SIGNAL:
        signal = event.rx_power_dbm

        if signal is not None and signal <= -30:
            priority = Priority.CRITICAL
            channel = select_available_channel(
                CommunicationChannel.BOTH,
                event,
            )
            reason = "RX power is critically weak."
            instructions = (
                "Warn the customer about a critical optical signal and "
                "state that urgent technical inspection is required."
            )

        elif signal is not None and signal <= -28:
            priority = Priority.HIGH
            channel = select_available_channel(
                CommunicationChannel.BOTH,
                event,
            )
            reason = "RX power is below the safe operating level."
            instructions = (
                "Warn the customer about weak optical signal and advise "
                "that a technician will inspect the fiber connection."
            )

        elif signal is not None and signal <= -25:
            priority = Priority.MEDIUM
            channel = CommunicationChannel.NOTIFICATION
            reason = "RX power requires monitoring."
            instructions = (
                "Prepare a monitoring notification for the technical team."
            )

        else:
            return RuleDecision(
                should_communicate=False,
                channel=CommunicationChannel.NONE,
                priority=Priority.LOW,
                audience=audience,
                reason="RX power is within the acceptable range.",
                instructions="Do not send a customer communication.",
            )

        return RuleDecision(
            should_communicate=True,
            channel=channel,
            priority=priority,
            audience=audience,
            reason=reason,
            instructions=instructions,
        )

    if event.event_type == EventType.PAYMENT_DUE:
        channel = select_available_channel(
            CommunicationChannel.EMAIL,
            event,
        )

        priority = (
            Priority.HIGH
            if event.amount_due is not None
            and event.amount_due >= 5_000
            else Priority.MEDIUM
        )

        return RuleDecision(
            should_communicate=True,
            channel=channel,
            priority=priority,
            audience=audience,
            reason="The customer's internet payment is due.",
            instructions=(
                "Prepare a polite payment reminder containing the amount, "
                "due date, customer ID, and package when available."
            ),
        )

    if event.event_type == EventType.SCHEDULED_MAINTENANCE:
        channel = select_available_channel(
            CommunicationChannel.BOTH,
            event,
        )

        return RuleDecision(
            should_communicate=True,
            channel=channel,
            priority=Priority.MEDIUM,
            audience=audience,
            reason="Customers should be notified before maintenance.",
            instructions=(
                "Explain the maintenance schedule, possible service "
                "interruption, affected area, and expected completion."
            ),
        )

    if event.event_type == EventType.SERVICE_RESTORED:
        return RuleDecision(
            should_communicate=True,
            channel=CommunicationChannel.NOTIFICATION,
            priority=Priority.LOW,
            audience=audience,
            reason="Customers should know that service is restored.",
            instructions=(
                "Confirm that internet service has been restored and "
                "thank customers for their patience."
            ),
        )

    return RuleDecision(
        should_communicate=True,
        channel=select_available_channel(
            CommunicationChannel.EMAIL,
            event,
        ),
        priority=Priority.LOW,
        audience=audience,
        reason="The event contains a general customer notice.",
        instructions=(
            "Prepare a short, clear, and professional ISP announcement."
        ),
    )