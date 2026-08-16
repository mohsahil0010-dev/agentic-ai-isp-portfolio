import streamlit as st
from pydantic import ValidationError

from agent import run_diagnosis
from models import DiagnosticRequest


st.set_page_config(
    page_title="SFN Intelligent Troubleshooting Agent",
    page_icon="🌐",
    layout="wide",
)


st.title("SFN Intelligent Troubleshooting Agent")

st.write(
    "Enter a customer connection ID and complaint. The agent will "
    "autonomously select diagnostic tools and recommend an action."
)


with st.sidebar:
    st.header("Demonstration Data")

    st.write("Available sample customer IDs:")

    st.code(
        """
80101
80102
60103
20104
80105
60106
80107
20108
        """
    )

    st.subheader("Signal Rules")

    st.write(
        """
- Good: -23 dBm or higher
- Weak: -23 to -27 dBm
- Critical: below -27 dBm
        """
    )

    st.warning(
        "This application uses fictional demonstration data."
    )


with st.form("diagnostic_form"):
    customer_id = st.text_input(
        "Customer Connection ID",
        placeholder="Example: 80105",
        max_chars=5,
    )

    complaint = st.text_area(
        "Customer Complaint",
        placeholder="Example: Customer has no internet and a red LOS light.",
        height=130,
        max_chars=500,
    )

    submitted = st.form_submit_button(
        "Run Intelligent Diagnosis",
        use_container_width=True,
    )


if submitted:
    try:
        request = DiagnosticRequest(
            customer_id=customer_id,
            complaint=complaint,
        )

    except ValidationError as error:
        st.error("Please correct the following input problems:")

        for problem in error.errors():
            field_name = problem["loc"][0]
            message = problem["msg"]

            st.write(f"- **{field_name}:** {message}")

    else:
        with st.spinner(
            "The agent is selecting tools and investigating the issue..."
        ):
            try:
                diagnosis = run_diagnosis(request.to_agent_goal())

            except Exception as error:
                st.error(
                    "The diagnosis could not be completed. "
                    "Check your internet connection and API configuration."
                )

                with st.expander("Technical error details"):
                    st.code(str(error))

            else:
                st.success("Diagnosis completed successfully")

                st.subheader("Agent Diagnostic Report")

                st.markdown(diagnosis)