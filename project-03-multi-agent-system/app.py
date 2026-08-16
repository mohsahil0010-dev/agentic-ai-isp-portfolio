import json
import os
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="SFN Multi-Agent Incident Response",
    page_icon="🧠",
    layout="wide",
)


PROJECT_DIR = Path(__file__).resolve().parent
INCIDENT_FILE = PROJECT_DIR / "data" / "incident_cases.json"


def configure_api_key() -> None:
    """Load the Groq key from Streamlit secrets when deployed."""

    if os.getenv("GROQ_API_KEY"):
        return

    try:
        secret_key = st.secrets.get("GROQ_API_KEY")

        if secret_key:
            os.environ["GROQ_API_KEY"] = secret_key
    except Exception:
        pass


configure_api_key()

from graph import run_incident_response
from models import FinalIncidentReport, IncidentInput


@st.cache_data(show_spinner=False)
def load_demo_cases() -> list[dict]:
    """Load fictional demonstration incidents."""

    if not INCIDENT_FILE.exists():
        return []

    return json.loads(
        INCIDENT_FILE.read_text(encoding="utf-8")
    )


demo_cases = load_demo_cases()


def load_case_into_form(case: dict) -> None:
    """Copy one demonstration incident into the input form."""

    st.session_state.incident_id = case["incident_id"]
    st.session_state.customer_id = case["customer_id"]
    st.session_state.description = case["description"]
    st.session_state.onu_pon_status = case["onu_pon_status"]
    st.session_state.onu_los_status = case["onu_los_status"]
    st.session_state.pppoe_status = case["pppoe_status"]
    st.session_state.account_status = case["account_status"]
    st.session_state.payment_status = case["payment_status"]
    st.session_state.notes = case.get("notes", "")

    rx_power = case.get("rx_power_dbm")

    st.session_state.rx_available = rx_power is not None
    st.session_state.rx_power_dbm = (
        float(rx_power)
        if rx_power is not None
        else -20.0
    )

    st.session_state.pop("last_report", None)


def initialize_form() -> None:
    """Set the initial form values."""

    if "form_initialized" in st.session_state:
        return

    if demo_cases:
        load_case_into_form(demo_cases[0])
    else:
        st.session_state.incident_id = "INC-001"
        st.session_state.customer_id = "SFN-DEMO-001"
        st.session_state.description = ""
        st.session_state.onu_pon_status = "unknown"
        st.session_state.onu_los_status = "unknown"
        st.session_state.rx_available = False
        st.session_state.rx_power_dbm = -20.0
        st.session_state.pppoe_status = "unknown"
        st.session_state.account_status = "unknown"
        st.session_state.payment_status = "unknown"
        st.session_state.notes = ""

    st.session_state.form_initialized = True


initialize_form()


with st.sidebar:
    st.header("Multi-Agent System")

    st.markdown(
        """
This application coordinates specialized fictional ISP agents:

- **Coordinator Agent**
- **Fiber Agent**
- **Network Agent**
- **Billing Agent**
- **Final Decision Agent**
"""
    )

    st.divider()

    st.subheader("Workflow")

    st.code(
        (
            "Coordinator\n"
            "    ↓\n"
            "Selected Specialists\n"
            "    ↓\n"
            "Diagnostic Tools\n"
            "    ↓\n"
            "Final Decision"
        ),
        language=None,
    )

    st.divider()

    st.subheader("Demonstration Incidents")

    if demo_cases:
        selected_index = st.selectbox(
            "Select an incident",
            options=range(len(demo_cases)),
            format_func=lambda index: (
                f"{demo_cases[index]['incident_id']} — "
                f"{demo_cases[index]['title']}"
            ),
        )

        st.button(
            "Load Selected Incident",
            use_container_width=True,
            on_click=load_case_into_form,
            args=(demo_cases[selected_index],),
        )
    else:
        st.warning(
            "No demonstration incidents were found."
        )

    st.divider()

    st.info(
        "All incidents, identifiers and operational records in this "
        "application are fictional course-project data."
    )


st.title("🧠 SFN Multi-Agent Incident Response System")

st.write(
    """
Submit a fictional ISP incident. A coordinator analyzes the case,
selects the required specialists, executes diagnostic tools and
combines their findings into one incident-response plan.
"""
)


with st.form("incident_form"):
    st.subheader("Incident Information")

    incident_column, customer_column = st.columns(2)

    with incident_column:
        incident_id = st.text_input(
            "Incident ID",
            key="incident_id",
        )

    with customer_column:
        customer_id = st.text_input(
            "Fictional Customer ID",
            key="customer_id",
        )

    description = st.text_area(
        "Incident Description",
        key="description",
        height=120,
        placeholder=(
            "Describe the ONU, LOS, signal, PPPoE, account or "
            "payment problem."
        ),
    )

    st.subheader("Fiber and ONU Evidence")

    pon_column, los_column, rx_column = st.columns(3)

    with pon_column:
        onu_pon_status = st.selectbox(
            "ONU PON Status",
            options=[
                "normal",
                "offline",
                "unknown",
            ],
            key="onu_pon_status",
            format_func=str.title,
        )

    with los_column:
        onu_los_status = st.selectbox(
            "ONU LOS Status",
            options=[
                "off",
                "red",
                "unknown",
            ],
            key="onu_los_status",
            format_func=str.title,
        )

    with rx_column:
        rx_available = st.checkbox(
            "RX power is available",
            key="rx_available",
        )

        rx_power_dbm = st.number_input(
            "RX Power (dBm)",
            min_value=-50.0,
            max_value=0.0,
            step=0.1,
            key="rx_power_dbm",
            disabled=not rx_available,
        )

    st.subheader("Network and Billing Evidence")

    pppoe_column, account_column, payment_column = st.columns(3)

    with pppoe_column:
        pppoe_status = st.selectbox(
            "PPPoE Status",
            options=[
                "active",
                "inactive",
                "unknown",
            ],
            key="pppoe_status",
            format_func=str.title,
        )

    with account_column:
        account_status = st.selectbox(
            "Account Status",
            options=[
                "enabled",
                "disabled",
                "unknown",
            ],
            key="account_status",
            format_func=str.title,
        )

    with payment_column:
        payment_status = st.selectbox(
            "Payment Status",
            options=[
                "paid",
                "unpaid",
                "partial",
                "unknown",
            ],
            key="payment_status",
            format_func=str.title,
        )

    notes = st.text_area(
        "Additional Notes",
        key="notes",
        height=80,
    )

    submitted = st.form_submit_button(
        "Run Multi-Agent Investigation",
        use_container_width=True,
        type="primary",
    )


if submitted:
    try:
        incident = IncidentInput(
            incident_id=incident_id,
            customer_id=customer_id,
            description=description,
            onu_pon_status=onu_pon_status,
            onu_los_status=onu_los_status,
            rx_power_dbm=(
                float(rx_power_dbm)
                if rx_available
                else None
            ),
            pppoe_status=pppoe_status,
            account_status=account_status,
            payment_status=payment_status,
            notes=notes,
        )

        with st.spinner(
            "Coordinator and specialist agents are investigating..."
        ):
            report = run_incident_response(incident)

        st.session_state.last_report = report.model_dump()

    except Exception as error:
        st.error(
            "The incident investigation could not be completed."
        )

        with st.expander("Technical error details"):
            st.exception(error)


report_data = st.session_state.get("last_report")

if report_data:
    report = FinalIncidentReport.model_validate(report_data)

    st.divider()
    st.header("Multi-Agent Incident Report")

    if report.requires_human_escalation:
        st.warning(
            "Human escalation required — specialist or administrator "
            "action is needed."
        )
    else:
        st.success(
            "No immediate human escalation was identified."
        )

    category_column, priority_column, confidence_column, team_column = (
        st.columns(4)
    )

    category_column.metric(
        "Category",
        report.category.title(),
    )
    priority_column.metric(
        "Priority",
        report.priority.title(),
    )
    confidence_column.metric(
        "Confidence",
        report.confidence.title(),
    )
    team_column.metric(
        "Specialists",
        len(report.specialist_findings),
    )

    decision_column, cause_column = st.columns(2)

    with decision_column:
        st.subheader("Decision")
        st.write(report.decision)

    with cause_column:
        st.subheader("Probable Root Cause")
        st.write(report.probable_root_cause)

    st.subheader("Assigned Team")
    st.write(report.assigned_team)

    st.subheader("Ordered Action Plan")

    for index, action in enumerate(
        report.action_plan,
        start=1,
    ):
        st.markdown(f"{index}. {action}")

    st.divider()

    st.subheader("Agentic Workflow")

    st.code(
        " → ".join(report.workflow_path),
        language=None,
    )

    st.caption(
        "The coordinator selected the specialists. Each specialist "
        "used its diagnostic tool before the final decision agent "
        "combined the findings."
    )

    st.subheader("Specialist Findings")

    if report.specialist_findings:
        for finding in report.specialist_findings:
            title = finding.agent.replace("_", " ").title()

            with st.expander(
                f"{title} — {finding.confidence.title()} confidence",
                expanded=True,
            ):
                st.markdown("#### Diagnosis")
                st.write(finding.diagnosis)

                evidence_column, actions_column = st.columns(2)

                with evidence_column:
                    st.markdown("#### Evidence")

                    for evidence in finding.evidence:
                        st.markdown(f"- {evidence}")

                with actions_column:
                    st.markdown("#### Recommended Actions")

                    for action in finding.recommended_actions:
                        st.markdown(f"- {action}")

                st.markdown("#### Diagnostic Tool Output")

                for observation in finding.tool_observations:
                    st.json(
                        observation.model_dump(),
                        expanded=True,
                    )

                if finding.requires_escalation:
                    st.warning(
                        "This specialist recommends escalation."
                    )
    else:
        st.info(
            "No specialist was assigned because the supplied "
            "incident did not contain enough routing evidence."
        )

    st.divider()

    st.download_button(
        "Download Incident Report as JSON",
        data=report.model_dump_json(indent=2),
        file_name=(
            f"{report.incident_id.lower()}-multi-agent-report.json"
        ),
        mime="application/json",
        use_container_width=True,
    )