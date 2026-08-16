import unittest

from tools import (
    check_account,
    check_area_outage,
    check_signal,
    lookup_customer,
)


class TestISPTools(unittest.TestCase):

    def test_existing_customer_is_found(self):
        customer = lookup_customer("80102")

        self.assertIsNotNone(customer)
        self.assertEqual(customer["name"], "Hamza Khan")

    def test_unknown_customer_returns_none(self):
        customer = lookup_customer("99999")

        self.assertIsNone(customer)

    def test_good_signal(self):
        result = check_signal("80101")

        self.assertTrue(result["success"])
        self.assertEqual(result["condition"], "good")

    def test_weak_signal(self):
        result = check_signal("80107")

        self.assertTrue(result["success"])
        self.assertEqual(result["condition"], "weak")

    def test_critical_signal(self):
        result = check_signal("80105")

        self.assertTrue(result["success"])
        self.assertEqual(result["condition"], "critical")

    def test_active_outage_is_found(self):
        result = check_area_outage("Model Town")

        self.assertTrue(result["outage_found"])
        self.assertEqual(result["issue"], "Fiber cable cut")

    def test_resolved_outage_is_not_active(self):
        result = check_area_outage("College Road")

        self.assertFalse(result["outage_found"])

    def test_disabled_account(self):
        result = check_account("20104")

        self.assertTrue(result["success"])
        self.assertEqual(result["account_status"], "disabled")
        self.assertEqual(result["payment_status"], "unpaid")


if __name__ == "__main__":
    unittest.main()