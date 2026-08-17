from data_store import (
    find_active_outages,
    find_customer,
    load_customers,
    load_outages,
    load_packages,
)
from models import CustomerStatus, OutageStatus


def test_load_customers() -> None:
    customers = load_customers()

    assert len(customers) >= 4
    assert all(customer.customer_id for customer in customers)


def test_find_existing_customer() -> None:
    customer = find_customer("80102")

    assert customer is not None
    assert customer.customer_id == "80102"
    assert customer.name == "Hamza Khan"
    assert customer.status == CustomerStatus.ACTIVE


def test_find_customer_normalizes_id() -> None:
    customer = find_customer(" 80 102 ")

    assert customer is not None
    assert customer.customer_id == "80102"


def test_find_unknown_customer() -> None:
    customer = find_customer("99999")

    assert customer is None


def test_load_outages() -> None:
    outages = load_outages()

    assert len(outages) >= 1
    assert any(
        outage.outage_id == "OUT-001"
        for outage in outages
    )


def test_find_active_model_town_outage() -> None:
    outages = find_active_outages("model town")

    assert len(outages) >= 1

    outage = outages[0]

    assert outage.outage_id == "OUT-001"
    assert outage.area == "Model Town"
    assert outage.status == OutageStatus.ACTIVE


def test_no_active_outage_for_unknown_area() -> None:
    outages = find_active_outages("Unknown Test Area")

    assert outages == []


def test_load_packages() -> None:
    packages = load_packages()

    assert len(packages) >= 6

    package_text = " ".join(
        str(package.model_dump())
        for package in packages
    )

    assert "TW-10MBPS" in package_text
    assert "Z-8MBPS" in package_text
    assert "MT-10MBPS" in package_text