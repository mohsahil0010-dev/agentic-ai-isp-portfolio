# SFN Internet Package and Service Policy

Document ID: SFN-KB-PACKAGE-001
Document type: Internal demonstration policy
Data classification: Fictional course-project data

## Purpose

This document describes the fictional package families, connection-ID mapping, package-selection guidance and package-change rules used by the SFN Knowledge Decision Agent.

The agent should use this document when answering questions about available packages, suitable speeds, upgrades, downgrades, expected payments and bandwidth-related complaints.

## Connection ID Mapping

The first two digits of a customer connection ID identify the demonstration service family.

| ID prefix | Service family |
| --------- | -------------- |
| `80`      | TW             |
| `60`      | Z              |
| `20`      | MT             |

Examples:

* Connection ID `80125` belongs to the TW service family.
* Connection ID `60110` belongs to the Z service family.
* Connection ID `20220` belongs to the MT service family.

The agent must not determine a service family from the customer’s name. It should use the connection-ID prefix or verified customer record.

## TW Package Family

The demonstration TW package family contains:

* TW-6MBPS
* TW-8MBPS
* TW-10MBPS
* TW-15MBPS
* TW-20MBPS
* TW-25MBPS

A customer ID beginning with `80` should normally use a TW package.

## Z Package Family

The demonstration Z package family contains:

* Z-4MBPS
* Z-6MBPS
* Z-8MBPS

A customer ID beginning with `60` should normally use a Z package.

## MT Package Family

The demonstration MT package family contains:

* MT-8MBPS
* MT-10MBPS

A customer ID beginning with `20` should normally use an MT package.

## Package Naming Rules

Package names should follow this format:

```text
SERVICE-SPEED
```

Examples:

```text
TW-10MBPS
Z-6MBPS
MT-8MBPS
```

The service-family prefix and speed should not be removed from the stored package name.

Incorrect:

```text
10MBPS
```

Correct:

```text
TW-10MBPS
```

## Package Selection Factors

A package recommendation should consider:

* Number of users
* Number of connected devices
* Video-streaming quality
* Online classes
* Video calls
* Social-media use
* Gaming
* Cloud backups
* Large downloads
* CCTV remote viewing
* Work-from-home requirements
* Router capability
* Wi-Fi coverage
* Available service family

The agent should explain that actual Wi-Fi performance may be lower than the package speed because of distance, interference, walls, device limitations and router capability.

## Light-Usage Recommendation

Light usage normally includes:

* Messaging
* Basic web browsing
* Social-media browsing
* Email
* One or two connected devices
* Standard-quality video

A lower available package may be sufficient for light usage.

Possible recommendations include:

* Z-4MBPS
* Z-6MBPS
* TW-6MBPS
* TW-8MBPS
* MT-8MBPS

The final recommendation must match the customer’s available service family.

## Medium-Usage Recommendation

Medium usage normally includes:

* Multiple smartphones
* HD video streaming
* Online classes
* Video calls
* General downloads
* Three to five active devices

Possible recommendations include:

* TW-10MBPS
* TW-15MBPS
* Z-8MBPS
* MT-10MBPS

The package should be selected according to the available service family and customer requirements.

## Heavy-Usage Recommendation

Heavy usage normally includes:

* Multiple simultaneous HD streams
* 4K video
* Large downloads
* Cloud backups
* Online gaming
* Work-from-home use
* CCTV remote access
* More than five active devices

Possible TW recommendations include:

* TW-20MBPS
* TW-25MBPS

If the customer’s service family does not provide a suitable higher package, the case should be referred for a service-availability decision instead of inventing an unavailable package.

## Package Speed and Wi-Fi Speed

The package speed represents the configured internet-service profile.

It does not guarantee that every wireless device will receive the full package speed.

Wi-Fi performance depends on:

* Router model
* Wireless standard
* Frequency band
* Distance from router
* Walls and building structure
* Channel interference
* Customer device capability
* Number of active devices
* Background downloads

A wired Ethernet test near the router is preferred when verifying package speed.

## Package Upgrade

A package upgrade moves a customer to a higher speed.

Before an upgrade:

1. Verify the customer ID.
2. Confirm the current service family.
3. Confirm that the requested package exists.
4. Confirm the current package.
5. Confirm the effective date.
6. Confirm the new expected payment.
7. Confirm whether an additional payment is required.
8. Check router capability when necessary.
9. Update the bandwidth profile.
10. Test the new speed.

After an upgrade:

* Record the previous package.
* Record the new package.
* Record the effective date.
* Update the expected payment.
* Update the monthly recovery target.
* Keep previous invoice history unchanged.
* Generate a receipt for any additional payment.

The system must not rewrite old invoices to show the new package.

## Immediate Upgrade

An immediate upgrade may be applied during the current billing month when:

* The requested package is available.
* The additional payment is confirmed.
* Authorized staff approve the effective date.
* The bandwidth profile is updated.

The payment note should explain how the additional amount was calculated.

## Package Downgrade

A package downgrade moves a customer to a lower speed.

Before a downgrade:

* Verify the customer ID.
* Verify the current package.
* Confirm the requested package exists.
* Confirm the effective billing month.
* Inform the customer about the lower speed.
* Update future expected payments.

A downgrade should normally apply from the approved billing cycle.

Previous invoices and payments should not be changed.

## Invalid Package Change

A package change should be rejected or referred for review when:

* The package does not exist.
* The package belongs to an incompatible service family.
* The customer ID is invalid.
* The customer record cannot be verified.
* Payment requirements are unresolved.
* The requested speed is not available in the area.
* The required network profile does not exist.
* The request would overwrite previous invoice history.

## Expected Payment After Package Change

The expected payment for future billing periods should be updated according to the new package.

Example:

```text
Previous package: TW-10MBPS
New package: TW-15MBPS
Effective month: September
```

The September expected payment and recovery target should use the TW-15MBPS price.

August invoices should remain based on the package that was active during August unless an authorized immediate upgrade was recorded.

## Package Price

Package prices must be retrieved from the authorized package record.

The agent should not invent a price when the knowledge base does not contain one.

If the user asks for a price that is not available in the retrieved information, the agent should state that the price must be confirmed from the current billing system.

## Package Purchase Cost

Package purchase cost is internal accounting information.

It may be used to calculate:

* Service cost
* Gross profit
* Load requirement
* Package profitability
* Monthly accounting totals

Purchase cost should not be shown to customers unless authorized.

## TW Load and Z Load

Demonstration accounting may use separate load categories.

* Customer IDs beginning with `80` use TW LOAD.
* Customer IDs beginning with `60` use ZONG LOAD.
* MT accounting should use its approved service category.

A load category should be selected from the connection-ID prefix, not from the customer name.

## Package Complaint

When a customer says the package speed is not being received:

1. Confirm the active package.
2. Confirm account status.
3. Confirm optical signal.
4. Check for an area outage.
5. Ask whether the test uses Wi-Fi or Ethernet.
6. Check the number of connected devices.
7. Stop large downloads during the test.
8. Perform a wired speed test.
9. Verify the assigned bandwidth profile.
10. Escalate if wired performance remains below the expected range.

A speed complaint should not automatically result in a package upgrade. The existing connection must be tested first.

## Router Capability

An old or low-capability router may limit performance.

Router checks may include:

* Maximum wireless standard
* Supported frequency bands
* Ethernet port speed
* CPU capability
* Number of connected devices
* Wi-Fi coverage
* Firmware condition

A higher internet package may not improve performance if the router or customer device is the actual limitation.

## Fair Usage and Network Management

The demonstration packages are intended for normal residential or small-business usage.

The provider may investigate:

* Unusual continuous high-bandwidth traffic
* Unauthorized service resale
* Network abuse
* Security threats
* Activities that affect other customers

The agent should not claim that a customer is being limited unless verified evidence is available.

## Package Recommendation Guardrails

The Knowledge Decision Agent must:

* Recommend only packages listed in this document.
* Match the package to the correct service family.
* Ask about user needs before recommending a speed.
* Avoid guaranteeing Wi-Fi performance.
* Avoid inventing prices.
* Explain limitations when information is missing.
* Distinguish package limitations from technical faults.
* Preserve previous billing history during package changes.

## Example Decision 1

Question:

A customer ID begins with `80` and the customer wants a 15 Mbps package.

Decision:

The customer belongs to the TW family. TW-15MBPS is a valid package recommendation, subject to availability and price confirmation.

## Example Decision 2

Question:

A customer ID begins with `60` and requests TW-20MBPS.

Decision:

The customer belongs to the Z family, but TW-20MBPS belongs to the TW family. The request should not be approved without an authorized service-family change.

## Example Decision 3

Question:

A customer uses five devices, HD streaming, online classes and video calls.

Decision:

This is medium usage. Recommend an available medium package matching the customer’s service family, such as TW-10MBPS, TW-15MBPS, Z-8MBPS or MT-10MBPS.

## Example Decision 4

Question:

A TW-10MBPS customer reports slow Wi-Fi in another room.

Decision:

Do not immediately recommend an upgrade. First check signal, outage status, router capability, Wi-Fi distance, interference and wired speed.

## Example Decision 5

Question:

A customer asks for the current price of TW-25MBPS, but no price is present in the knowledge base.

Decision:

State that TW-25MBPS is an available package, but its current price must be confirmed from the authorized billing system. Do not invent a price.
