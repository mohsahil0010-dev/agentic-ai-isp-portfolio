import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from models import (
    Customer,
    InternetPackage,
    Outage,
    SupportTicket,
)


DATA_DIRECTORY = Path(__file__).parent / "data"

CUSTOMERS_PATH = DATA_DIRECTORY / "customers.json"
OUTAGES_PATH = DATA_DIRECTORY / "outages.json"
PACKAGES_PATH = DATA_DIRECTORY / "packages.json"
SAMPLE_TICKETS_PATH = DATA_DIRECTORY / "tickets.json"
RUNTIME_TICKETS_PATH = (
    DATA_DIRECTORY / "runtime_tickets.json"
)


ModelType = TypeVar(
    "ModelType",
    bound=BaseModel,
)


class DataStoreError(Exception):
    """Raised when ISP data cannot be loaded or stored."""


def load_json_list(
    path: Path,
    model_class: type[ModelType],
) -> list[ModelType]:
    """Load and validate a JSON list using a Pydantic model."""

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as data_file:
            raw_data = json.load(data_file)

        if not isinstance(raw_data, list):
            raise DataStoreError(
                f"{path.name} must contain a JSON list."
            )

        return [
            model_class.model_validate(item)
            for item in raw_data
        ]

    except FileNotFoundError as exc:
        raise DataStoreError(
            f"Required data file was not found: {path.name}"
        ) from exc

    except json.JSONDecodeError as exc:
        raise DataStoreError(
            f"Invalid JSON in {path.name}: {exc}"
        ) from exc

    except ValidationError as exc:
        raise DataStoreError(
            f"Invalid data inside {path.name}: {exc}"
        ) from exc


def load_customers() -> list[Customer]:
    return load_json_list(
        CUSTOMERS_PATH,
        Customer,
    )


def find_customer(
    customer_id: str,
) -> Customer | None:
    """Find one customer by normalized customer ID."""

    normalized_id = customer_id.upper().replace(
        " ",
        "",
    )

    for customer in load_customers():
        if customer.customer_id == normalized_id:
            return customer

    return None


def load_outages() -> list[Outage]:
    return load_json_list(
        OUTAGES_PATH,
        Outage,
    )


def find_active_outages(
    area: str | None = None,
) -> list[Outage]:
    """Return active outages, optionally filtered by area."""

    active_outages = [
        outage
        for outage in load_outages()
        if outage.status.value == "active"
    ]

    if not area:
        return active_outages

    normalized_area = area.casefold().strip()

    return [
        outage
        for outage in active_outages
        if (
            normalized_area
            in outage.area.casefold()
            or outage.area.casefold()
            in normalized_area
        )
    ]


def load_packages() -> list[InternetPackage]:
    return load_json_list(
        PACKAGES_PATH,
        InternetPackage,
    )


def find_packages(
    provider: str | None = None,
) -> list[InternetPackage]:
    """Return packages, optionally filtered by provider."""

    packages = load_packages()

    if not provider:
        return packages

    normalized_provider = provider.casefold().strip()

    return [
        package
        for package in packages
        if package.provider.casefold()
        == normalized_provider
    ]


def get_ticket_storage_path() -> Path:
    """Use runtime storage without modifying the sample file."""

    if RUNTIME_TICKETS_PATH.exists():
        return RUNTIME_TICKETS_PATH

    return SAMPLE_TICKETS_PATH


def load_tickets() -> list[SupportTicket]:
    return load_json_list(
        get_ticket_storage_path(),
        SupportTicket,
    )


def save_ticket(
    ticket: SupportTicket,
) -> None:
    """Store a ticket using an atomic JSON-file update."""

    try:
        existing_tickets = load_tickets()
        existing_tickets.append(ticket)

        output_data = [
            item.model_dump(mode="json")
            for item in existing_tickets
        ]

        RUNTIME_TICKETS_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            RUNTIME_TICKETS_PATH.with_suffix(".tmp")
        )

        temporary_path.write_text(
            json.dumps(
                output_data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            RUNTIME_TICKETS_PATH
        )

    except DataStoreError:
        raise

    except Exception as exc:
        raise DataStoreError(
            f"Could not save support ticket: {exc}"
        ) from exc