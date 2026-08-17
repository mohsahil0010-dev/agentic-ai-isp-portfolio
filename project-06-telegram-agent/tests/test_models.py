import json
from pathlib import Path

from models import (
    BotRequest,
    BotResponse,
    Customer,
    CustomerStatus,
    IntentType,
    OutageStatus,
    TicketPriority,
    TicketStatus,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_first_customer() -> dict:
    customers_path = DATA_DIR / "customers.json"

    with customers_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        customers = json.load(file)

    return customers[0]


def test_customer_model_accepts_sample_customer() -> None:
    customer_data = load_first_customer()
    customer = Customer.model_validate(customer_data)

    assert customer.customer_id == "80102"
    assert customer.name == "Hamza Khan"
    assert customer.area == "Model Town"
    assert customer.status == CustomerStatus.ACTIVE


def test_customer_id_is_normalized() -> None:
    customer_data = load_first_customer()
    customer_data["customer_id"] = " 80 102 "

    customer = Customer.model_validate(customer_data)

    assert customer.customer_id == "80102"


def test_bot_request_model() -> None:
    request = BotRequest(
        message="Check the internet outage in Model Town.",
        chat_id="test-chat-001",
        username="Test User",
    )

    assert request.message == (
        "Check the internet outage in Model Town."
    )
    assert request.chat_id == "test-chat-001"
    assert request.username == "Test User"


def test_bot_response_model() -> None:
    response = BotResponse(
        success=True,
        intent=IntentType.OUTAGE_CHECK,
        response="An active outage was found.",
        tools_used=["check_outage"],
    )

    assert response.success is True
    assert response.intent == IntentType.OUTAGE_CHECK
    assert response.tools_used == ["check_outage"]


def test_enum_values() -> None:
    assert CustomerStatus.ACTIVE.value == "active"
    assert OutageStatus.ACTIVE.value == "active"
    assert TicketPriority.HIGH.value == "high"
    assert TicketStatus.OPEN.value == "open"
    assert IntentType.OUTAGE_CHECK.value == "outage_check"