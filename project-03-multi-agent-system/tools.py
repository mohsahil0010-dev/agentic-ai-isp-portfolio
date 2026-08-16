from langchain_core.tools import tool

from models import ToolObservation


@tool
def check_optical_signal(
    onu_pon_status: str,
    onu_los_status: str,
    rx_power_dbm: float | None,
) -> dict:
    """Evaluate fictional ONU PON, LOS and RX-power measurements."""

    if onu_los_status == "red":
        result = ToolObservation(
            tool_name="check_optical_signal",
            status="fault",
            summary=(
                "The ONU has a red LOS indication, which shows "
                "loss of the incoming optical signal."
            ),
            recommended_check=(
                "Inspect the drop fiber, connectors, bends, splices, "
                "DP port and upstream optical signal."
            ),
        )
        return result.model_dump()

    if onu_pon_status == "offline":
        result = ToolObservation(
            tool_name="check_optical_signal",
            status="fault",
            summary=(
                "The ONU is offline and is not registered normally "
                "with the optical network."
            ),
            recommended_check=(
                "Check ONU power, fiber continuity, OLT registration, "
                "PON port and service configuration."
            ),
        )
        return result.model_dump()

    if rx_power_dbm is None:
        result = ToolObservation(
            tool_name="check_optical_signal",
            status="unknown",
            summary="No RX-power measurement was supplied.",
            recommended_check=(
                "Measure and record the ONU RX power before making "
                "a final optical diagnosis."
            ),
        )
        return result.model_dump()

    if rx_power_dbm >= -23:
        result = ToolObservation(
            tool_name="check_optical_signal",
            status="normal",
            summary=(
                f"The RX power is {rx_power_dbm:.1f} dBm, which is "
                "within the fictional good-signal range."
            ),
            recommended_check=(
                "Continue with PPPoE, router and account checks if "
                "the customer still has no internet."
            ),
        )
        return result.model_dump()

    if rx_power_dbm >= -27:
        result = ToolObservation(
            tool_name="check_optical_signal",
            status="warning",
            summary=(
                f"The RX power is {rx_power_dbm:.1f} dBm, which is "
                "within the fictional weak-signal range."
            ),
            recommended_check=(
                "Clean connectors and inspect bends, splices, the DP "
                "signal and avoidable optical loss."
            ),
        )
        return result.model_dump()

    result = ToolObservation(
        tool_name="check_optical_signal",
        status="fault",
        summary=(
            f"The RX power is {rx_power_dbm:.1f} dBm, which is "
            "within the fictional critical-signal range."
        ),
        recommended_check=(
            "Do not accept the connection as normal. Inspect the "
            "fiber route, connectors, splices, splitter and DP signal."
        ),
    )
    return result.model_dump()


@tool
def check_pppoe_service(
    pppoe_status: str,
    account_status: str,
) -> dict:
    """Evaluate fictional PPPoE and account activation information."""

    if pppoe_status == "active":
        result = ToolObservation(
            tool_name="check_pppoe_service",
            status="normal",
            summary="The PPPoE session is active.",
            recommended_check=(
                "If service is still unavailable, check router LAN, "
                "Wi-Fi, DNS and customer-device connectivity."
            ),
        )
        return result.model_dump()

    if account_status == "disabled":
        result = ToolObservation(
            tool_name="check_pppoe_service",
            status="fault",
            summary=(
                "The PPPoE session is inactive and the customer "
                "account is disabled."
            ),
            recommended_check=(
                "Verify the billing status and authorization before "
                "enabling the account."
            ),
        )
        return result.model_dump()

    if pppoe_status == "inactive":
        result = ToolObservation(
            tool_name="check_pppoe_service",
            status="fault",
            summary=(
                "The customer has no active PPPoE session even though "
                "the account is not confirmed as disabled."
            ),
            recommended_check=(
                "Check the PPPoE username, password, router WAN "
                "configuration, service profile and MikroTik logs."
            ),
        )
        return result.model_dump()

    result = ToolObservation(
        tool_name="check_pppoe_service",
        status="unknown",
        summary="The PPPoE session status is unknown.",
        recommended_check=(
            "Check active PPPoE sessions and confirm the account "
            "status before making a network diagnosis."
        ),
    )
    return result.model_dump()


@tool
def check_billing_account(
    payment_status: str,
    account_status: str,
) -> dict:
    """Evaluate fictional customer payment and account status."""

    if payment_status == "paid" and account_status == "disabled":
        result = ToolObservation(
            tool_name="check_billing_account",
            status="fault",
            summary=(
                "The customer is marked paid but the service account "
                "is still disabled."
            ),
            recommended_check=(
                "Verify the receipt and billing period, then restore "
                "service through the approved activation process."
            ),
        )
        return result.model_dump()

    if payment_status == "unpaid":
        result = ToolObservation(
            tool_name="check_billing_account",
            status="warning",
            summary="The customer has an unpaid balance.",
            recommended_check=(
                "Confirm the outstanding amount and follow the "
                "fictional billing and suspension policy."
            ),
        )
        return result.model_dump()

    if payment_status == "partial":
        result = ToolObservation(
            tool_name="check_billing_account",
            status="warning",
            summary="The customer has made only a partial payment.",
            recommended_check=(
                "Review the remaining balance and determine whether "
                "service is permitted under the billing policy."
            ),
        )
        return result.model_dump()

    if payment_status == "paid" and account_status == "enabled":
        result = ToolObservation(
            tool_name="check_billing_account",
            status="normal",
            summary="The customer is paid and the account is enabled.",
            recommended_check=(
                "Continue with fiber, PPPoE and router diagnostics."
            ),
        )
        return result.model_dump()

    result = ToolObservation(
        tool_name="check_billing_account",
        status="unknown",
        summary=(
            "The supplied billing information is not sufficient for "
            "a final account decision."
        ),
        recommended_check=(
            "Verify the payment record, billing period, outstanding "
            "balance and account activation state."
        ),
    )
    return result.model_dump()


FIBER_TOOLS = [check_optical_signal]
NETWORK_TOOLS = [check_pppoe_service]
BILLING_TOOLS = [check_billing_account]

ALL_DIAGNOSTIC_TOOLS = (
    FIBER_TOOLS
    + NETWORK_TOOLS
    + BILLING_TOOLS
)