import isp_tools
from isp_tools import (
    ISP_TOOLS,
    analyze_signal,
    check_outage,
    create_support_ticket,
    list_internet_packages,
    lookup_customer,
    troubleshoot_connection,
)


def test_all_required_tools_are_registered() -> None:
    tool_names = {
        tool.name
        for tool in ISP_TOOLS
    }

    assert tool_names == {
        "lookup_customer",
        "check_outage",
        "analyze_signal",
        "list_internet_packages",
        "troubleshoot_connection",
        "create_support_ticket",
    }


def test_lookup_existing_customer() -> None:
    result = lookup_customer.invoke(
        {"customer_id": "80102"}
    )

    assert "80102" in result
    assert "Hamza Khan" in result
    assert "TW-10MBPS" in result


def test_lookup_unknown_customer() -> None:
    result = lookup_customer.invoke(
        {"customer_id": "99999"}
    )

    result_lower = result.lower()

    assert '"found": false' in result_lower
    assert "99999" in result


def test_check_active_outage() -> None:
    result = check_outage.invoke(
        {"area": "Model Town"}
    )

    assert "OUT-001" in result
    assert "Model Town" in result
    assert "active" in result.lower()


def test_analyze_good_signal() -> None:
    result = analyze_signal.invoke(
        {"rx_power_dbm": -24.5}
    )

    assert "good" in result.lower()


def test_analyze_critical_signal() -> None:
    result = analyze_signal.invoke(
        {"rx_power_dbm": -30.2}
    )

    assert "critical" in result.lower()


def test_list_tw_packages() -> None:
    result = list_internet_packages.invoke(
        {"provider": "TW"}
    )

    assert "TW-6MBPS" in result
    assert "TW-10MBPS" in result
    assert "TW-20MBPS" in result


def test_troubleshoot_los_problem() -> None:
    result = troubleshoot_connection.invoke(
        {
            "symptoms": (
                "The internet is not working and the ONU "
                "LOS light is red."
            )
        }
    )

    result_lower = result.lower()

    assert "los" in result_lower

    assert (
        "fiber" in result_lower
        or "connector" in result_lower
        or "support" in result_lower
    )


def test_create_support_ticket_without_writing_file(
    monkeypatch,
) -> None:
    saved_tickets = []

    def fake_save_ticket(ticket):
        saved_tickets.append(ticket)
        return ticket

    # Prevent the test from modifying runtime ticket data.
    monkeypatch.setattr(
        isp_tools,
        "save_ticket",
        fake_save_ticket,
    )

    result = create_support_ticket.invoke(
        {
            "customer_id": "80105",
            "issue": "Internet is down and ONU LOS is red.",
            "priority": "high",
        }
    )

    assert len(saved_tickets) == 1
    assert "80105" in result
    assert "high" in result.lower()
    assert "ticket" in result.lower()