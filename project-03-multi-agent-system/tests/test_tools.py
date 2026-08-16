import unittest

from agents import (
    deterministic_triage,
    fiber_agent,
)
from models import IncidentInput
from tools import (
    check_billing_account,
    check_optical_signal,
    check_pppoe_service,
)


class TestDiagnosticTools(unittest.TestCase):
    def test_red_los_is_fiber_fault(self):
        result = check_optical_signal.invoke(
            {
                "onu_pon_status": "offline",
                "onu_los_status": "red",
                "rx_power_dbm": -29.0,
            }
        )

        self.assertEqual(result["status"], "fault")
        self.assertIn("red LOS", result["summary"])

    def test_good_rx_power_is_normal(self):
        result = check_optical_signal.invoke(
            {
                "onu_pon_status": "normal",
                "onu_los_status": "off",
                "rx_power_dbm": -20.0,
            }
        )

        self.assertEqual(result["status"], "normal")

    def test_weak_rx_power_returns_warning(self):
        result = check_optical_signal.invoke(
            {
                "onu_pon_status": "normal",
                "onu_los_status": "off",
                "rx_power_dbm": -25.0,
            }
        )

        self.assertEqual(result["status"], "warning")

    def test_critical_rx_power_returns_fault(self):
        result = check_optical_signal.invoke(
            {
                "onu_pon_status": "normal",
                "onu_los_status": "off",
                "rx_power_dbm": -29.0,
            }
        )

        self.assertEqual(result["status"], "fault")

    def test_inactive_pppoe_disabled_account_is_fault(self):
        result = check_pppoe_service.invoke(
            {
                "pppoe_status": "inactive",
                "account_status": "disabled",
            }
        )

        self.assertEqual(result["status"], "fault")
        self.assertIn("disabled", result["summary"])

    def test_active_pppoe_is_normal(self):
        result = check_pppoe_service.invoke(
            {
                "pppoe_status": "active",
                "account_status": "enabled",
            }
        )

        self.assertEqual(result["status"], "normal")

    def test_paid_but_disabled_account_is_fault(self):
        result = check_billing_account.invoke(
            {
                "payment_status": "paid",
                "account_status": "disabled",
            }
        )

        self.assertEqual(result["status"], "fault")
        self.assertIn("paid", result["summary"])

    def test_paid_enabled_account_is_normal(self):
        result = check_billing_account.invoke(
            {
                "payment_status": "paid",
                "account_status": "enabled",
            }
        )

        self.assertEqual(result["status"], "normal")

    def test_mixed_incident_assigns_three_agents(self):
        incident = IncidentInput(
            incident_id="INC-TEST-001",
            customer_id="SFN-DEMO-TEST",
            description=(
                "ONU has red LOS, PPPoE is inactive and the paid "
                "customer account remains disabled."
            ),
            onu_pon_status="offline",
            onu_los_status="red",
            rx_power_dbm=-29.0,
            pppoe_status="inactive",
            account_status="disabled",
            payment_status="paid",
        )

        triage = deterministic_triage(incident)

        self.assertEqual(triage.category, "mixed")
        self.assertEqual(triage.priority, "high")
        self.assertEqual(
            set(triage.assigned_agents),
            {
                "fiber_agent",
                "network_agent",
                "billing_agent",
            },
        )

    def test_fiber_agent_preserves_tool_observation(self):
        incident = IncidentInput(
            incident_id="INC-TEST-002",
            customer_id="SFN-DEMO-TEST",
            description="ONU has a red LOS light.",
            onu_pon_status="offline",
            onu_los_status="red",
            rx_power_dbm=-29.0,
        )

        finding = fiber_agent(incident)

        self.assertEqual(finding.agent, "fiber_agent")
        self.assertEqual(finding.confidence, "high")
        self.assertTrue(finding.requires_escalation)
        self.assertEqual(
            finding.tool_observations[0].tool_name,
            "check_optical_signal",
        )
        self.assertEqual(
            finding.tool_observations[0].status,
            "fault",
        )


if __name__ == "__main__":
    unittest.main()