import json
import os
from datetime import date

import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError

from agent import (
    CommunicationAgentError,
    run_communication_agent,
)
from history import HistoryError, load_history
from models import EventType, ISPEvent


load_dotenv()


st.set_page_config(
    page_title="ISP Communication Assistant",
    page_icon="📣",
    layout="wide",
)


EVENT_LABELS = {
    EventType.NETWORK_OUTAGE: "Network Outage",
    EventType.WEAK_SIGNAL: "Weak Optical Signal",
    EventType.PAYMENT_DUE: "Payment Due",
    EventType.SCHEDULED_MAINTENANCE: "Scheduled Maintenance",
    EventType.SERVICE_RESTORED: "Service Restored",
    EventType.GENERAL_NOTICE: "General Notice",
}


DEFAULT_DETAILS = {
    EventType.NETWORK_OUTAGE: (
        "Internet service is unavailable in the selected area. "
        "The technical team is investigating the outage."
    ),
    EventType.WEAK_SIGNAL: (
        "The customer's ONU optical signal requires inspection."
    ),
    EventType.PAYMENT_DUE: (
        "The customer's monthly internet payment is due."
    ),
    EventType.SCHEDULED_MAINTENANCE: (
        "Scheduled fiber maintenance may temporarily interrupt service."
    ),
    EventType.SERVICE_RESTORED: (
        "Internet service has been restored successfully."
    ),
    EventType.GENERAL_NOTICE: (
        "A general service announcement is available for customers."
    ),
}


st.title("📣 ISP Communication & Notification Agent")
st.caption(
    "Project 5 — Intelligent Communication Assistant "
    "for SAHIL FIBER NET"
)


with st.sidebar:
    st.header("Project 5")
    st.write("Intelligent Communication Assistant")

    communication_mode = os.getenv(
        "COMMUNICATION_MODE",
        "simulation",
    ).lower()

    st.metric(
        "Communication mode",
        communication_mode.title(),
    )

    if communication_mode == "simulation":
        st.info(
            "Simulation mode is active. "
            "No real customer email will be sent."
        )
    else:
        st.warning(
            "Live mode is active. Configured tools may send messages."
        )

    try:
        history_count = len(
            load_history(limit=1_000)
        )
        st.metric(
            "Communication records",
            history_count,
        )
    except HistoryError:
        st.metric(
            "Communication records",
            "Unavailable",
        )

    st.markdown(
        """
        **Main concepts**

        - Email automation
        - Notifications
        - Tool calling
        - Agent + Tools
        - Pydantic validation
        - Defined conditions
        """
    )


create_tab, history_tab, rules_tab = st.tabs(
    [
        "Create Communication",
        "History",
        "Communication Rules",
    ]
)


with create_tab:
    st.subheader("Analyze an ISP event")

    selected_event_type = st.selectbox(
        "Event type",
        options=list(EventType),
        format_func=lambda event: EVENT_LABELS[event],
    )

    with st.form("communication_form"):
        column1, column2 = st.columns(2)

        with column1:
            customer_id = st.text_input(
                "Customer ID",
                placeholder="80105",
            )

            customer_name = st.text_input(
                "Customer name",
                placeholder="Ali Raza",
            )

            email = st.text_input(
                "Customer email",
                placeholder="ali@example.com",
            )

            phone_number = st.text_input(
                "Phone number",
                placeholder="03001234567",
            )

        with column2:
            area = st.text_input(
                "Area",
                placeholder="Model Town, Layyah",
            )

            package_name = st.text_input(
                "Internet package",
                placeholder="TW-10MBPS",
            )

            amount_due = None
            due_date = None
            rx_power_dbm = None

            if selected_event_type == EventType.PAYMENT_DUE:
                amount_due = st.number_input(
                    "Amount due (PKR)",
                    min_value=0.0,
                    value=2200.0,
                    step=100.0,
                )

                selected_due_date = st.date_input(
                    "Due date",
                    value=date.today(),
                )

                due_date = selected_due_date.isoformat()

            if selected_event_type == EventType.WEAK_SIGNAL:
                rx_power_dbm = st.number_input(
                    "RX power (dBm)",
                    value=-29.0,
                    step=0.1,
                )

        details = st.text_area(
            "Event details",
            value=DEFAULT_DETAILS[selected_event_type],
            height=140,
            key=f"details_{selected_event_type.value}",
        )

        submitted = st.form_submit_button(
            "Analyze and prepare communication",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            event = ISPEvent(
                event_type=selected_event_type,
                customer_id=customer_id or None,
                customer_name=customer_name or None,
                email=email or None,
                phone_number=phone_number or None,
                area=area or None,
                package_name=package_name or None,
                amount_due=amount_due,
                due_date=due_date,
                rx_power_dbm=rx_power_dbm,
                details=details,
            )

            with st.spinner(
                "Evaluating conditions and calling communication tools..."
            ):
                result = run_communication_agent(event)

            st.session_state["last_agent_result"] = result

        except ValidationError as exc:
            st.error(
                "Event validation failed. "
                "Please check the entered information."
            )
            st.code(str(exc))

        except CommunicationAgentError as exc:
            st.error(str(exc))

        except Exception as exc:
            st.error(
                f"Unexpected application error: {exc}"
            )

    result = st.session_state.get(
        "last_agent_result"
    )

    if result:
        st.divider()

        plan = result["plan"]
        tool_results = result["tool_results"]

        if plan["should_communicate"]:
            st.success(
                "Communication prepared and tool calling completed."
            )
        else:
            st.info(
                "The rules determined that no communication is required."
            )

        column1, column2, column3, column4 = st.columns(4)

        column1.metric(
            "Channel",
            plan["channel"].replace("_", " ").title(),
        )

        column2.metric(
            "Priority",
            plan["priority"].title(),
        )

        column3.metric(
            "Audience",
            plan["audience"],
        )

        column4.metric(
            "Tools called",
            len(tool_results),
        )

        st.subheader("Communication plan")

        st.text_input(
            "Generated subject",
            value=plan["subject"],
            disabled=True,
        )

        st.text_area(
            "Generated message",
            value=plan["message"],
            height=260,
            disabled=True,
        )

        st.caption(
            f"Decision reason: {plan['reason']}"
        )

        if tool_results:
            st.subheader("Tool execution results")

            for number, tool_result in enumerate(
                tool_results,
                start=1,
            ):
                status = tool_result["status"].title()
                tool_name = tool_result["tool_name"]

                with st.expander(
                    f"Tool {number}: {tool_name} — {status}",
                    expanded=True,
                ):
                    st.write(
                        f"**Recipient:** "
                        f"{tool_result['recipient']}"
                    )
                    st.write(
                        f"**Channel:** "
                        f"{tool_result['channel']}"
                    )
                    st.write(
                        f"**Status:** "
                        f"{tool_result['status']}"
                    )
                    st.write(
                        f"**Details:** "
                        f"{tool_result.get('details')}"
                    )

        with st.expander("Rule decision"):
            st.json(result["rule_decision"])

        with st.expander("Complete agent result"):
            st.json(result)

        download_json = json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )

        st.download_button(
            "Download communication result",
            data=download_json,
            file_name="communication_result.json",
            mime="application/json",
        )


with history_tab:
    st.subheader("Communication history")

    try:
        records = load_history(limit=100)

        if not records:
            st.info(
                "No communication records are available yet."
            )
        else:
            history_rows = [
                {
                    "Time": record.created_at,
                    "Event": record.event_type.value,
                    "Channel": record.channel.value,
                    "Priority": record.priority.value,
                    "Recipient": record.recipient,
                    "Subject": record.subject,
                    "Status": record.status.value,
                    "Tool": record.tool_name,
                }
                for record in records
            ]

            st.dataframe(
                history_rows,
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Message details")

            for record in records[:10]:
                with st.expander(
                    f"{record.subject} — "
                    f"{record.recipient}"
                ):
                    st.write(record.message)
                    st.caption(
                        f"{record.created_at} | "
                        f"{record.status.value} | "
                        f"{record.tool_name}"
                    )

    except HistoryError as exc:
        st.error(str(exc))


with rules_tab:
    st.subheader("Defined communication conditions")

    rule_rows = [
        {
            "Condition": "Network outage",
            "Priority": "Critical",
            "Preferred channel": "Email + notification",
            "Action": "Notify affected customers immediately",
        },
        {
            "Condition": "RX power ≤ -30 dBm",
            "Priority": "Critical",
            "Preferred channel": "Email + notification",
            "Action": "Urgent optical signal warning",
        },
        {
            "Condition": "RX power ≤ -28 dBm",
            "Priority": "High",
            "Preferred channel": "Email + notification",
            "Action": "Arrange fiber inspection",
        },
        {
            "Condition": "RX power ≤ -25 dBm",
            "Priority": "Medium",
            "Preferred channel": "Notification",
            "Action": "Monitor optical signal",
        },
        {
            "Condition": "Payment due",
            "Priority": "Medium or high",
            "Preferred channel": "Email",
            "Action": "Send payment reminder",
        },
        {
            "Condition": "Scheduled maintenance",
            "Priority": "Medium",
            "Preferred channel": "Email + notification",
            "Action": "Send advance maintenance notice",
        },
        {
            "Condition": "Service restored",
            "Priority": "Low",
            "Preferred channel": "Notification",
            "Action": "Confirm service restoration",
        },
    ]

    st.dataframe(
        rule_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "When a customer email is unavailable, "
        "the rules automatically fall back to an internal notification."
    )