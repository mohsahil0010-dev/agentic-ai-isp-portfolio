import json

from langchain_core.tools import tool

from data_store import (
    DataStoreError,
    find_active_outages,
    find_customer,
    find_packages,
    save_ticket,
)
from models import SupportTicket, TicketPriority


def json_result(data) -> str:
    return json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )


@tool
def lookup_customer(customer_id: str) -> str:
    """
    Look up an ISP customer by customer ID.
    Use this when a user asks about their account,
    package, status, area, or optical signal.
    """

    try:
        customer = find_customer(customer_id)

        if not customer:
            return json_result(
                {
                    "found": False,
                    "message": (
                        f"No customer was found with ID "
                        f"{customer_id}."
                    ),
                }
            )

        return json_result(
            {
                "found": True,
                "customer_id": customer.customer_id,
                "name": customer.name,
                "area": customer.area,
                "package_name": customer.package_name,
                "rx_power_dbm": customer.rx_power_dbm,
                "status": customer.status.value,
            }
        )

    except DataStoreError as exc:
        return json_result(
            {
                "found": False,
                "error": str(exc),
            }
        )


@tool
def check_outage(area: str = "") -> str:
    """
    Check active ISP network outages.
    Optionally filter the outage results by area.
    """

    try:
        outages = find_active_outages(
            area or None
        )

        if not outages:
            return json_result(
                {
                    "active_outage": False,
                    "area": area or "All areas",
                    "message": (
                        "No active outage was found "
                        "for the requested area."
                    ),
                }
            )

        return json_result(
            {
                "active_outage": True,
                "count": len(outages),
                "outages": [
                    {
                        "outage_id": outage.outage_id,
                        "area": outage.area,
                        "issue": outage.issue,
                        "started_at": outage.started_at,
                        "expected_resolution": (
                            outage.expected_resolution
                        ),
                    }
                    for outage in outages
                ],
            }
        )

    except DataStoreError as exc:
        return json_result(
            {
                "active_outage": False,
                "error": str(exc),
            }
        )


@tool
def analyze_signal(rx_power_dbm: float) -> str:
    """
    Analyze fiber ONU RX optical power in dBm.
    Use this when a user provides an RX value.
    """

    if rx_power_dbm >= -25:
        condition = "good"
        severity = "low"
        recommendation = (
            "The optical signal is within the acceptable range."
        )

    elif rx_power_dbm > -28:
        condition = "monitor"
        severity = "medium"
        recommendation = (
            "The optical signal should be monitored. "
            "Check connectors if performance problems occur."
        )

    elif rx_power_dbm > -30:
        condition = "weak"
        severity = "high"
        recommendation = (
            "The optical signal is weak. "
            "Inspect connectors, splices, bends, and fiber loss."
        )

    else:
        condition = "critical"
        severity = "critical"
        recommendation = (
            "The optical signal is critically weak. "
            "Arrange urgent fiber inspection."
        )

    return json_result(
        {
            "rx_power_dbm": rx_power_dbm,
            "condition": condition,
            "severity": severity,
            "recommendation": recommendation,
        }
    )


@tool
def list_internet_packages(
    provider: str = "",
) -> str:
    """
    List available ISP internet packages.
    Optionally filter by TW, Zong, or MT provider.
    """

    try:
        packages = find_packages(
            provider or None
        )

        if not packages:
            return json_result(
                {
                    "found": False,
                    "provider": provider,
                    "message": (
                        "No packages were found for "
                        "the requested provider."
                    ),
                }
            )

        return json_result(
            {
                "found": True,
                "count": len(packages),
                "packages": [
                    {
                        "name": package.name,
                        "provider": package.provider,
                        "speed_mbps": package.speed_mbps,
                        "monthly_price_pkr": (
                            package.monthly_price
                        ),
                        "description": package.description,
                    }
                    for package in packages
                ],
            }
        )

    except DataStoreError as exc:
        return json_result(
            {
                "found": False,
                "error": str(exc),
            }
        )


@tool
def troubleshoot_connection(
    symptoms: str,
) -> str:
    """
    Provide safe first-line troubleshooting guidance
    based on customer-reported internet symptoms.
    """

    normalized = symptoms.casefold()

    if (
        "los" in normalized
        or "red light" in normalized
        or "red" in normalized
    ):
        category = "fiber_signal_loss"
        steps = [
            "Confirm that the ONU has power.",
            "Do not bend or disconnect the fiber cable.",
            "Check whether the LOS light remains red.",
            "Check for an active outage in the area.",
            "Create a support ticket if LOS remains red.",
        ]

    elif (
        "slow" in normalized
        or "speed" in normalized
        or "buffer" in normalized
    ):
        category = "slow_internet"
        steps = [
            "Restart the Wi-Fi router once.",
            "Test speed near the router.",
            "Disconnect unused devices temporarily.",
            "Test using a network cable when possible.",
            "Create a ticket if speed remains below the package.",
        ]

    elif (
        "wifi" in normalized
        or "wi-fi" in normalized
        or "wireless" in normalized
    ):
        category = "wifi_problem"
        steps = [
            "Move closer to the Wi-Fi router.",
            "Place the router in an open central location.",
            "Restart the router once.",
            "Try both 2.4 GHz and 5 GHz Wi-Fi.",
            "Create a ticket if the problem continues.",
        ]

    else:
        category = "no_internet"
        steps = [
            "Confirm that the ONU and router have power.",
            "Check the PON and LOS indicator lights.",
            "Restart the router once.",
            "Check for an active outage in the area.",
            "Create a support ticket if service does not return.",
        ]

    return json_result(
        {
            "category": category,
            "reported_symptoms": symptoms,
            "steps": steps,
            "safety_note": (
                "Customers should not open fiber equipment "
                "or look directly into fiber connectors."
            ),
        }
    )


@tool
def create_support_ticket(
    customer_id: str,
    issue: str,
    priority: str = "medium",
) -> str:
    """
    Create an ISP support ticket after the user clearly
    requests technical assistance or reports an unresolved issue.
    """

    try:
        selected_priority = TicketPriority(
            priority.casefold()
        )

    except ValueError:
        return json_result(
            {
                "created": False,
                "message": (
                    "Priority must be low, medium, "
                    "high, or critical."
                ),
            }
        )

    normalized_customer_id = (
        customer_id.strip()
        if customer_id
        else ""
    )

    if normalized_customer_id:
        customer = find_customer(
            normalized_customer_id
        )

        if not customer:
            return json_result(
                {
                    "created": False,
                    "message": (
                        f"Customer ID {customer_id} "
                        f"was not found."
                    ),
                }
            )

    try:
        ticket = SupportTicket(
            customer_id=(
                normalized_customer_id
                or None
            ),
            issue=issue,
            priority=selected_priority,
        )

        save_ticket(ticket)

        return json_result(
            {
                "created": True,
                "ticket_id": ticket.ticket_id,
                "customer_id": ticket.customer_id,
                "issue": ticket.issue,
                "priority": ticket.priority.value,
                "status": ticket.status.value,
                "created_at": ticket.created_at,
            }
        )

    except Exception as exc:
        return json_result(
            {
                "created": False,
                "error": str(exc),
            }
        )


ISP_TOOLS = [
    lookup_customer,
    check_outage,
    analyze_signal,
    list_internet_packages,
    troubleshoot_connection,
    create_support_ticket,
]