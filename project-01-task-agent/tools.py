import csv
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parent / "data"


def read_csv_file(filename: str) -> list[dict[str, str]]:
    """Read a CSV file from the project's data directory."""

    file_path = DATA_DIRECTORY / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def lookup_customer(customer_id: str) -> dict[str, str] | None:
    """Find and return a customer using their connection ID."""

    customers = read_csv_file("customers.csv")
    customer_id = customer_id.strip()

    for customer in customers:
        if customer["customer_id"] == customer_id:
            return customer

    return None


def check_signal(customer_id: str) -> dict[str, object]:
    """Check the optical signal condition of a customer."""

    customer = lookup_customer(customer_id)

    if customer is None:
        return {
            "success": False,
            "message": f"Customer {customer_id} was not found.",
        }

    try:
        rx_power = float(customer["rx_power_dbm"])
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "The customer's RX power value is invalid.",
        }

    if rx_power >= -23:
        condition = "good"
        recommendation = "The optical signal is within the normal range."
    elif rx_power >= -27:
        condition = "weak"
        recommendation = (
            "Inspect connectors, patch cords, bends and splitter loss."
        )
    else:
        condition = "critical"
        recommendation = (
            "Check for fiber damage, excessive loss or a faulty connector."
        )

    return {
        "success": True,
        "customer_id": customer_id,
        "rx_power_dbm": rx_power,
        "condition": condition,
        "recommendation": recommendation,
    }


def check_account(customer_id: str) -> dict[str, object]:
    """Check account, payment and router status."""

    customer = lookup_customer(customer_id)

    if customer is None:
        return {
            "success": False,
            "message": f"Customer {customer_id} was not found.",
        }

    return {
        "success": True,
        "customer_id": customer_id,
        "name": customer["name"],
        "package": customer["package"],
        "account_status": customer["account_status"],
        "payment_status": customer["payment_status"],
        "router_status": customer["router_status"],
    }


def check_area_outage(area: str) -> dict[str, object]:
    """Check whether an area currently has an active outage."""

    outages = read_csv_file("outages.csv")
    normalized_area = area.strip().lower()

    for outage in outages:
        same_area = outage["area"].strip().lower() == normalized_area
        is_active = outage["status"].strip().lower() == "active"

        if same_area and is_active:
            return {
                "success": True,
                "outage_found": True,
                "area": outage["area"],
                "issue": outage["issue"],
                "started_at": outage["started_at"],
                "estimated_restore": outage["estimated_restore"],
            }

    return {
        "success": True,
        "outage_found": False,
        "area": area,
        "message": "No active outage was found for this area.",
    }