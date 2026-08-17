import pytest
from pydantic import ValidationError

from models import EventType, ISPEvent


def test_customer_id_is_cleaned():
    event = ISPEvent(
        event_type=EventType.GENERAL_NOTICE,
        customer_id=" 80 105 ",
        details="General customer notice.",
    )

    assert event.customer_id == "80105"


def test_pakistan_phone_number_is_normalized():
    event = ISPEvent(
        event_type=EventType.GENERAL_NOTICE,
        phone_number="+92 300-1234567",
        details="General customer notice.",
    )

    assert event.phone_number == "03001234567"


def test_payment_due_requires_amount():
    with pytest.raises(
        ValidationError,
        match="amount_due",
    ):
        ISPEvent(
            event_type=EventType.PAYMENT_DUE,
            details="Monthly payment is due.",
        )


def test_weak_signal_requires_rx_power():
    with pytest.raises(
        ValidationError,
        match="rx_power_dbm",
    ):
        ISPEvent(
            event_type=EventType.WEAK_SIGNAL,
            details="Optical signal is weak.",
        )


def test_invalid_email_is_rejected():
    with pytest.raises(ValidationError):
        ISPEvent(
            event_type=EventType.GENERAL_NOTICE,
            email="not-an-email",
            details="General customer notice.",
        )