# SFN Billing and Service Status Policy

Document ID: SFN-KB-BILLING-001
Document type: Internal demonstration policy
Data classification: Fictional course-project data

## Purpose

This document explains the demonstration billing, payment, discount, due and service-restoration rules used by the SFN Knowledge Decision Agent.

The agent should use this policy when answering questions about invoices, expected payments, unpaid accounts, partial payments, package changes and service restoration.

## Monthly Billing Cycle

The demonstration billing cycle runs from the first day to the last day of each calendar month.

Monthly invoices are prepared at the beginning of the month.

The main recovery period is from the 1st to the 5th of the month.

Customers are expected to pay their monthly internet charges during the recovery period unless a different date has been approved and recorded.

## Expected Payment

Expected payment is the amount that the customer is scheduled to pay for the current billing month.

Expected payment is normally based on:

* The customer’s active internet package
* Approved discounts
* Previous unpaid balance
* Additional approved charges
* Package upgrades or downgrades
* Manual corrections recorded by authorized staff

Support staff should not guess an expected payment. The amount must be confirmed from the billing record.

## Full Payment

A payment is considered complete when the customer has paid the full expected amount for the billing period.

After full payment:

* The invoice should be marked paid.
* A payment receipt should be created.
* The paid amount and payment method should be recorded.
* The customer’s expiry or next billing date should be updated.
* Suspended service may be restored after payment verification.
* Duplicate payment warnings should remain active for the same billing month.

## Partial Payment

A partial payment occurs when the received amount is less than the expected amount.

Example:

```text
Expected payment: 2200
Received payment: 2000
Remaining due: 200
```

For a partial payment:

* Record the amount received.
* Keep the remaining amount as due.
* Do not mark the invoice as fully paid.
* Inform the customer of the remaining balance.
* Apply service-status rules according to the approved billing decision.
* Do not create another customer record for the remaining amount.

## Overpayment

An overpayment occurs when the customer pays more than the expected amount.

Example:

```text
Expected payment: 2200
Received payment: 2500
Overpayment: 300
```

The additional amount must not be ignored.

Authorized staff should decide whether the additional amount is:

* Applied as advance credit
* Applied to a package upgrade
* Returned to the customer
* Used to clear an older balance

The selected action must be recorded in the payment note.

## Unpaid Account

An account is unpaid when the expected monthly payment has not been received.

Before reporting that service was disconnected because of non-payment, staff should confirm:

* Current invoice status
* Previous unpaid balance
* Expected payment amount
* Payment history
* Bank or cash receipt
* Approved extension or exception
* Account service status

A red LOS light should not normally be caused by billing status. Red LOS indicates an optical or physical fiber issue and should be diagnosed separately.

## Service Suspension

Service may be suspended when:

* The payment deadline has passed.
* No approved payment extension exists.
* The customer has an unpaid invoice.
* A previous balance remains unresolved.
* The account was manually disabled by authorized staff.

Before suspension:

1. Confirm the correct customer ID.
2. Confirm the correct billing month.
3. Check recent cash and bank payments.
4. Check whether a receipt has already been recorded.
5. Check for an approved extension.
6. Notify the customer when required.

The system should not suspend a different customer because of a similar name.

## Service Restoration

A suspended account may be restored after:

* Full payment is verified.
* An approved partial-payment arrangement is recorded.
* An authorized extension is approved.
* A billing mistake is corrected.
* Management authorizes temporary restoration.

Recommended restoration process:

1. Verify the customer ID.
2. Verify payment or approval.
3. Update the invoice status.
4. Enable the customer account.
5. Confirm that the PPPoE session reconnects.
6. Ask the customer to restart the router if necessary.
7. Record the restoration time and staff action.

If the account is active but the customer still has no internet, technical troubleshooting should begin.

## Payment Verification

A payment must be verified before changing the invoice status.

### Cash Payment

For a cash payment:

* Confirm the amount received.
* Record the collection date.
* Record the receiving operator.
* Generate a receipt.
* Update the invoice and accounting totals.

### Bank Payment

For a bank payment:

* Confirm the transaction amount.
* Check the transaction reference.
* Confirm the receiving account.
* Check whether the transaction was already recorded.
* Generate a receipt after verification.

A screenshot alone may not be sufficient if the transaction cannot be confirmed.

## Duplicate Payment Protection

Before creating a new payment, the system should check whether the customer already paid for the selected month.

If a payment already exists:

* Display a warning.
* Show the previous receipt.
* Do not automatically create another invoice payment.
* Allow authorized staff to continue only when the second payment is genuine.

Duplicate entries should be corrected without deleting unrelated payment history.

## Discount Policy

A discount is a reduction from the expected payment.

Every discount must include:

* Original expected amount
* Discount amount
* Final received amount
* Reason for discount
* Billing month
* Name or identity of the approving person

Example:

```text
Expected payment: 2200
Discount: 200
Final payment: 2000
```

The discount must be included in accounting reports as a recovery discount.

A discount should not silently change the normal package price for future months unless a permanent package-price change is approved.

## Package Upgrade

When a customer upgrades to a higher package:

* Record the new package.
* Record the effective date.
* Update the next expected payment.
* Update the monthly recovery target.
* Record any additional amount received.
* Update package cost and accounting information when required.

The customer’s old package history should remain available.

## Package Downgrade

When a customer downgrades:

* Record the new package.
* Record the effective billing month.
* Update future expected payments.
* Do not rewrite previous invoices.
* Update the monthly recovery target for the applicable month.

Previous payment history must remain unchanged.

## Payment Extension

An approved payment extension allows a customer additional time to pay.

An extension record should contain:

* Customer ID
* Customer name
* Current due amount
* Original payment date
* New expected payment date
* Reason
* Approving staff member

An extension does not mean that the payment was received. The invoice remains unpaid until payment is verified.

## Billing Dispute

When a customer disputes an invoice:

1. Confirm the customer ID.
2. Confirm the billing month.
3. Review expected payment.
4. Review package history.
5. Review receipts and payment method.
6. Review discounts and previous dues.
7. Do not delete records while the dispute is open.
8. Escalate unclear cases to authorized accounting staff.

## Relationship Between Billing and Technical Faults

The decision agent must distinguish billing problems from technical problems.

Examples:

* Disabled account with normal PON light may indicate a billing or account problem.
* Active paid account with red LOS indicates a technical fiber problem.
* Active paid account with good signal but no internet may indicate router, PPPoE, DNS or upstream issues.
* Unpaid account and critical RX power may contain both billing and fiber problems. Both must be reported.
* An active area outage should be reported even if the customer also has an unpaid invoice.

## Customer Communication

Billing messages should be respectful and clear.

A payment message should include:

* Customer ID
* Billing month
* Expected amount
* Received amount, if any
* Remaining due
* Payment deadline
* Approved payment methods
* Contact method for disputes

Private billing information must only be shared after confirming the correct customer identity.

## Data Protection

Billing records must not expose:

* Account passwords
* API keys
* Bank credentials
* Full private identity records
* Information belonging to another customer

Staff must verify the customer ID before sharing account-specific information.

## Example Decision 1

Question:

A customer has an active account, full payment and a red LOS light.

Decision:

The complaint is not caused by billing. Red LOS indicates an optical fiber problem. The fiber troubleshooting guide should be used.

## Example Decision 2

Question:

A customer has a normal PON light, good optical signal and an unpaid disabled account.

Decision:

The fiber connection appears operational. The likely cause is account suspension due to non-payment. Payment verification and restoration procedures should be followed.

## Example Decision 3

Question:

The customer expected payment is 2200, but only 2000 was received.

Decision:

Record a partial payment of 2000 and keep 200 as due. Do not mark the invoice fully paid unless an authorized discount or adjustment is recorded.
