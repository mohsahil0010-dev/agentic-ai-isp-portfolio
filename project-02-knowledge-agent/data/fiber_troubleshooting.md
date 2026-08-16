# SFN Fiber Troubleshooting Guide

Document ID: SFN-KB-FIBER-001
Document type: Internal demonstration knowledge
Data classification: Fictional course-project data

## Purpose

This guide describes the standard troubleshooting process for common fiber-internet complaints. It is intended to help support staff identify the probable cause, perform basic checks and decide when a field technician is required.

## Optical Signal Classification

The optical RX power reported by the ONU is classified using the following demonstration rules:

* RX power of -23 dBm or higher is considered good.
* RX power between -23 dBm and -27 dBm is considered weak.
* RX power below -27 dBm is considered critical.
* A missing RX value may indicate that the ONU is offline, disconnected or not communicating with the OLT.

A strong optical signal alone does not prove that internet service is working. Account status, router status, area outages and configuration problems must also be checked.

## Red LOS Light

A red LOS light normally means that the ONU is not receiving an optical signal.

Possible causes include:

* Broken or disconnected fiber cable
* Loose fiber connector
* Dirty connector
* Excessive bending of the fiber cable
* Damaged patch cord
* Faulty splitter port
* Main fiber outage
* ONU hardware problem

Recommended troubleshooting steps:

1. Check whether other customers in the same area are also offline.
2. Check the outage records for an active fiber or OLT incident.
3. Inspect the customer’s optical RX power.
4. Ask the customer whether the fiber cable was moved, bent or disconnected.
5. Ask the customer to confirm that the ONU has electrical power.
6. Verify the customer’s account and service status.
7. Escalate the case to a field technician if the LOS light remains red and no active area outage explains the problem.

A red LOS complaint with critical RX power should be treated as a high-priority fiber issue.

## ONU Has Power but No PON Light

If the ONU has power but the PON light is off, the ONU may not be registered or may have lost communication with the OLT.

Checks should include:

* ONU registration status
* ONU MAC address
* Correct OLT port and module
* Fiber connection
* Splitter port
* Optical RX power
* ONU authorization status

If the ONU was recently replaced, confirm that the new ONU MAC address has been registered.

## Slow Internet

Slow internet may be caused by the customer network, ISP network, package limitation or optical-signal loss.

Recommended checks:

1. Confirm the customer’s active package.
2. Check whether the customer account is active.
3. Check the optical RX power.
4. Check whether an area outage or network congestion is reported.
5. Ask whether the customer is testing through Wi-Fi or Ethernet.
6. Ask how many devices are connected.
7. Ask whether downloading, streaming or software updates are running.
8. Restart the router and ONU if no outage is active.
9. Perform a wired speed test when possible.
10. Escalate the issue if wired speed remains significantly below the package speed.

Wi-Fi speed can be affected by distance, walls, interference, device limitations and the number of connected devices.

## Internet Disconnected but No Red LOS

If the PON light is normal and there is no red LOS light, the fiber signal may still be working.

Possible causes include:

* Disabled customer account
* Unpaid invoice
* PPPoE authentication failure
* Incorrect username or password
* Router configuration problem
* WAN cable disconnection
* DNS problem
* MikroTik or upstream network issue
* Expired service period

Recommended checks:

1. Check account status.
2. Check payment status.
3. Check router status.
4. Check PPPoE session status.
5. Confirm the router’s WAN configuration.
6. Check whether the customer is receiving an IP address.
7. Check area and upstream network status.

An account or authentication problem should not be reported as a fiber break unless the optical evidence also indicates a fiber failure.

## Intermittent Disconnection

Intermittent service may be caused by:

* Weak optical signal
* Loose connector
* Fiber bending
* Unstable electrical power
* Faulty ONU power adapter
* Router overheating
* Wi-Fi interference
* OLT port instability
* Main fiber fluctuation

Recommended action:

1. Check current and previous RX power readings.
2. Inspect connectors and patch cords.
3. Confirm that the ONU power adapter is stable.
4. Check whether multiple customers in the area are affected.
5. Monitor the connection before replacing equipment.
6. Escalate if signal or session drops continue.

## Area Outage

When multiple customers in the same area report similar symptoms, staff should check for:

* Main fiber cable cut
* OLT power failure
* Switch or router failure
* Splitter failure
* Upstream internet outage
* Scheduled maintenance

If an active outage exists:

1. Inform the customer that the issue is area-wide.
2. Provide the estimated restoration time when available.
3. Avoid creating duplicate field tickets for every affected customer.
4. Escalate only when the outage exceeds the expected restoration time.
5. Confirm service restoration after the outage is marked resolved.

## Weak Signal Action

For weak RX power between -23 dBm and -27 dBm:

* Inspect fiber connectors.
* Clean connectors using approved tools.
* Check patch-cord condition.
* Check for tight bends.
* Check splitter and joint losses.
* Monitor whether the value changes.
* Schedule a technician visit if performance is affected.

## Critical Signal Action

For RX power below -27 dBm:

* Treat the issue as a likely physical fiber fault.
* Inspect the full customer drop cable.
* Check joints, connectors and splitter ports.
* Compare signal at the DP and customer ONU.
* Repair or replace damaged fiber.
* Do not close the ticket until the signal returns to an acceptable range.

## Technician Escalation Conditions

A field technician should be assigned when:

* Red LOS remains active without a known area outage.
* RX power is critical.
* A fiber cable is visibly broken.
* A connector or splitter port is damaged.
* Intermittent disconnections continue after basic checks.
* The ONU cannot register despite correct configuration.
* Service does not return after an outage is marked resolved.

## Safety Rules

* Customers should not look directly into a fiber connector.
* Fiber connectors should only be cleaned using suitable equipment.
* Customers should not open an ONU or power supply.
* Pole, DP and main-line work must be performed by authorized technicians.
* Support staff must not claim that a problem is fixed until service has been verified.

## Example Decision

Question:

A customer reports a red LOS light, RX power is -30 dBm and no active area outage exists.

Recommended decision:

The RX power is critical and the red LOS light indicates a probable physical fiber fault. Basic power and connector checks should be completed, followed by urgent escalation to a field technician.
