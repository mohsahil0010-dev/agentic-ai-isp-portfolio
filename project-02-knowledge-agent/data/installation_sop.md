# SFN New Fiber Connection Installation SOP

Document ID: SFN-KB-INSTALL-001
Document type: Internal demonstration procedure
Data classification: Fictional course-project data

## Purpose

This standard operating procedure explains the demonstration process for surveying, approving, installing, testing and documenting a new fiber-internet connection.

The Knowledge Decision Agent should use this document when answering questions about new installations, poles, DPs, fiber length, ports, ONUs, signals, testing and technician handover.

## Installation Workflow

A standard new connection follows these stages:

1. Receive the connection request.
2. Verify the customer and address.
3. Perform a site survey.
4. Identify the nearest suitable pole and DP.
5. Confirm DP port availability.
6. Estimate fiber length and required materials.
7. Approve or reject the installation plan.
8. Install the fiber drop cable.
9. Install and register the ONU.
10. Configure the customer router.
11. Test optical signal and internet service.
12. Record installation details.
13. Complete customer handover.

A connection should not be marked installed until technical testing and documentation are complete.

## Required Customer Information

Before starting the survey, collect:

* Customer name
* Father’s name when required
* Connection address
* Installation address
* Phone number
* Identification reference when required
* Requested package
* Preferred installation date
* Connection ID
* Payment information
* Special installation notes

Private customer information must not be placed in public demonstration datasets.

## Site Survey

The site survey determines whether the requested connection is technically and financially feasible.

The survey should check:

* Exact customer location
* Nearest network pole
* Nearest DP
* Available DP ports
* Existing splitter type
* Current DP signal
* Proposed fiber route
* Estimated fiber distance
* Road crossings
* Electrical hazards
* Tree interference
* Building height
* Required support points
* Required installation materials

Survey information should be recorded before installation approval.

## Pole Selection

The selected pole should:

* Be part of the approved SFN fiber route.
* Be structurally suitable.
* Provide a safe route to the customer.
* Avoid unnecessary road crossings.
* Have access to a usable DP or approved fiber path.
* Not create excessive fiber length.
* Not place the cable near unsafe electrical lines.

A technician should not use an unapproved pole simply because it is closer.

## DP Selection

The selected DP must be checked for:

* DP identification number
* Pole identification number
* Splitter type
* Total ports
* Used ports
* Available ports
* Current input signal
* Output signal
* Main fiber source
* Physical condition
* Labeling

A DP with no available port cannot be used unless an approved splitter or capacity upgrade is completed.

The agent must not recommend an unavailable port.

## DP Port Capacity

Available ports are calculated as:

```text
Available ports = Total ports - Used ports
```

Example:

```text
Total ports: 8
Used ports: 7
Available ports: 1
```

The DP can support one additional connection.

If the used-port count equals the total-port count, the DP is full.

A full DP requires one of the following:

* Select another suitable DP.
* Upgrade the splitter or DP capacity.
* Add a new DP.
* Reject or delay the installation.

## Fiber Distance

Fiber distance should follow the actual planned cable route, not only the straight-line distance.

The estimate should include:

* Pole-to-pole route
* DP-to-customer route
* Building entry route
* Vertical cable length
* Safe service loops
* Splicing allowance
* Maintenance allowance

A demonstration allowance of 10 percent should be added to the estimated route length.

Example:

```text
Estimated route length: 100 meters
Additional allowance: 10 meters
Required fiber: 110 meters
```

The final used length must be recorded after installation.

## Installation Approval

A connection may be approved when:

* Customer information is complete.
* The location is within the service area.
* A safe fiber route exists.
* A suitable pole and DP are available.
* A DP port is available.
* Required fiber and equipment are in stock.
* Estimated signal is acceptable.
* Installation cost is approved.
* No unresolved safety hazard exists.

## Installation Rejection or Delay

A connection should be rejected or delayed when:

* The area is outside network coverage.
* No safe cable route exists.
* No DP capacity is available.
* Estimated optical loss is unacceptable.
* Required material is unavailable.
* The installation requires an unauthorized pole.
* Electrical hazards make the route unsafe.
* Customer information is incomplete.
* Required approval or payment is missing.

The rejection or delay reason must be clearly recorded.

## Required Materials

Possible installation materials include:

* Fiber drop cable
* ONU
* ONU power adapter
* Wi-Fi router
* Fiber connector
* Patch cord
* Protective sleeve
* Cable clips
* Cable ties
* Support wire
* Joint enclosure
* Splice protection
* Labels
* Customer receipt
* Installation form

The technician should confirm inventory before leaving for the site.

## Fiber Cable Installation

During cable installation:

1. Follow the approved route.
2. Avoid sharp bends.
3. Avoid excessive cable tension.
4. Maintain safe clearance from electrical cables.
5. Secure the cable at suitable intervals.
6. Protect the cable at building entry points.
7. Leave a reasonable service loop.
8. Label the cable where required.
9. Do not leave loose cable hanging at unsafe heights.
10. Record the final fiber length used.

The customer drop cable should not obstruct roads, doors or pedestrian areas.

## Fiber Bending

Tight fiber bends may increase signal loss or break the cable.

Technicians should:

* Avoid folding the cable.
* Avoid crushing the cable under doors or furniture.
* Use smooth turns.
* Protect the cable at corners.
* Recheck RX power after routing changes.

If signal becomes weaker after cable routing, bends and connectors should be inspected.

## Connector and Splice Handling

Before connecting fiber:

* Inspect the connector.
* Clean the connector using approved tools.
* Do not touch the connector end.
* Check splice quality.
* Protect the splice.
* Confirm correct fiber color and route.
* Avoid looking directly into a fiber connector.

Dirty or damaged connectors may cause weak or unstable signal.

## ONU Installation

The ONU should be installed:

* Near a stable electrical outlet
* In a dry and ventilated location
* Away from direct heat
* Away from water
* Where indicator lights can be inspected
* Where the customer cannot easily damage the fiber

The ONU serial number or MAC address should be recorded.

## ONU Registration

The ONU must be correctly registered on the OLT.

Registration checks include:

* Correct OLT
* Correct PON or EPON port
* Correct ONU MAC address
* Correct customer ID
* Correct description
* Correct service profile
* Correct VLAN or service configuration
* Correct package or bandwidth profile

The ONU should not be assigned to another customer’s record.

## Optical Signal Test

After installation, record the ONU RX power.

Demonstration classification:

* -23 dBm or higher: good
* Between -23 dBm and -27 dBm: weak
* Below -27 dBm: critical

A new installation with critical signal should not be accepted as complete.

For a weak signal:

* Inspect connectors.
* Check bends.
* Check splice loss.
* Check DP signal.
* Compare DP and ONU readings.
* Correct avoidable loss before handover.

## Router Configuration

The customer router should be configured with:

* Correct PPPoE username
* Correct PPPoE password
* Secure Wi-Fi name
* Secure Wi-Fi password
* Suitable wireless channel
* Correct WAN connection
* DNS settings when required

Private passwords should not be written in public datasets or GitHub documentation.

## Internet Testing

Before handover:

1. Confirm the ONU PON light is normal.
2. Confirm there is no red LOS light.
3. Confirm the router obtains a connection.
4. Confirm the PPPoE session is active.
5. Open a website.
6. Perform a speed test.
7. Compare the result with the selected package.
8. Test Wi-Fi near the router.
9. Confirm basic browsing on the customer device.
10. Record the test result.

A Wi-Fi speed result may be affected by customer-device limitations and interference. A wired test is preferred for final technical verification.

## Installation Documentation

Record:

* Customer ID
* Customer name
* Installation date
* Technician name
* Pole ID
* DP ID
* DP port
* ONU MAC address
* OLT module
* Fiber length used
* RX power
* Package
* Installation payment
* Equipment issued
* Test result
* Notes
* Customer acceptance

Missing documentation should be completed before closing the installation job.

## Customer Handover

Explain to the customer:

* ONU and router power requirements
* Meaning of normal indicator lights
* Meaning of a red LOS light
* Wi-Fi name and password
* Package speed
* Support contact method
* Billing cycle
* Basic equipment-care instructions

The customer should be advised not to bend, cut or disconnect the fiber cable.

## Post-Installation Problem

If a new connection fails shortly after installation:

1. Review the installation record.
2. Check ONU registration.
3. Check optical RX power.
4. Check the DP port.
5. Check the fiber route and connectors.
6. Check router configuration.
7. Confirm account activation.
8. Escalate to the original installation technician when necessary.

## Safety Requirements

* Pole work must be performed by authorized technicians.
* Electrical clearance must be maintained.
* Suitable ladder and safety equipment must be used.
* Roads should not be crossed without an approved safe route.
* Fiber ends must not be viewed directly.
* Unsafe installations must be stopped and reported.
* Customer pressure must not override safety requirements.

## Example Decision 1

Question:

A nearby DP has eight total ports and all eight ports are in use.

Decision:

The DP is full and cannot support another connection. Select another suitable DP or complete an approved capacity upgrade before installation.

Example Decision 2

Question:

The estimated route length is 150 meters.

Decision:

Add the 10 percent demonstration allowance. The estimated required fiber is 165 meters.

## Example Decision 3

Question:

The new ONU has an RX power of -29 dBm.

Decision:

The signal is critical. The connection should not be accepted as complete. Inspect the cable route, connectors, splice, DP signal and splitter loss before handover.

## Example Decision 4

Question:

The ONU is registered, RX power is good and PON is normal, but the router does not connect.

Decision:

The physical fiber connection appears operational. Check PPPoE credentials, router WAN configuration, account activation and service profile.
