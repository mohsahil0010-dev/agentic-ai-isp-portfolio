import os

import streamlit as st


st.set_page_config(
    page_title="SFN Knowledge Decision Agent",
    page_icon="📚",
    layout="wide",
)


def configure_api_key() -> None:
    """Load the API key from Streamlit secrets when deployed."""

    if os.getenv("GROQ_API_KEY"):
        return

    try:
        secret_key = st.secrets.get("GROQ_API_KEY")

        if secret_key:
            os.environ["GROQ_API_KEY"] = secret_key
    except Exception:
        pass


configure_api_key()

from graph import run_knowledge_agent
from ingest import DATA_DIR, rebuild_knowledge_base
from retriever import get_knowledge_collection


SAMPLE_QUESTIONS = [
    "A DP has 8 ports and all 8 are used. Can I install another customer?",
    "The estimated fiber route is 150 meters. How much fiber is required?",
    "A newly installed ONU has an RX power of -29 dBm. Can we complete the installation?",
    "The customer's ONU has a red LOS light. What checks should be performed?",
    "A customer paid the bill but the account is still disabled. What should support do?",
    "Can a customer downgrade their package while an unpaid balance remains?",
]


@st.cache_resource(show_spinner=False)
def prepare_knowledge_base() -> dict[str, int]:
    """Open the existing database or build it when missing."""

    source_count = len(list(DATA_DIR.glob("*.md")))

    try:
        collection = get_knowledge_collection()
        chunk_count = collection.count()

        if chunk_count > 0:
            return {
                "source_documents": source_count,
                "chunks": chunk_count,
            }
    except Exception:
        pass

    result = rebuild_knowledge_base()

    return {
        "source_documents": int(result["source_documents"]),
        "chunks": int(result["chunks"]),
    }


try:
    with st.spinner("Preparing the SFN knowledge base..."):
        knowledge_stats = prepare_knowledge_base()
except Exception as error:
    st.error("The knowledge base could not be prepared.")

    with st.expander("Technical error details"):
        st.exception(error)

    st.stop()


if "question_input" not in st.session_state:
    st.session_state.question_input = ""


with st.sidebar:
    st.header("Knowledge Base")

    metric_column_1, metric_column_2 = st.columns(2)

    metric_column_1.metric(
        "Documents",
        knowledge_stats["source_documents"],
    )
    metric_column_2.metric(
        "Chunks",
        knowledge_stats["chunks"],
    )

    st.markdown(
        """
The agent searches fictional SFN documents covering:

- Fiber troubleshooting
- Billing policies
- New connection installation
- Internet package policies
"""
    )

    st.divider()
    st.subheader("Sample Questions")

    selected_question = st.selectbox(
        "Choose a demonstration question",
        SAMPLE_QUESTIONS,
    )

    if st.button(
        "Use Selected Question",
        use_container_width=True,
    ):
        st.session_state.question_input = selected_question

    st.divider()

    st.info(
        "This application uses fictional demonstration data "
        "created for an academic course project."
    )


st.title("📚 SFN Knowledge Decision Agent")

st.write(
    """
Ask an operational ISP question. The Agentic RAG workflow will
retrieve relevant SFN knowledge, evaluate whether the evidence is
sufficient, and either make a grounded decision or request
clarification.
"""
)


with st.form("knowledge_question_form"):
    question = st.text_area(
        "Operational Question",
        key="question_input",
        height=140,
        placeholder=(
            "Example: A new ONU has an RX power of -29 dBm. "
            "Can the installation be completed?"
        ),
    )

    submitted = st.form_submit_button(
        "Run Knowledge Decision",
        use_container_width=True,
    )


if submitted:
    if not question.strip():
        st.warning("Enter an operational question first.")
    else:
        try:
            with st.spinner(
                "Retrieving evidence and evaluating the decision..."
            ):
                result = run_knowledge_agent(question)

            st.session_state.last_result = result

        except Exception as error:
            st.error(
                "The decision could not be completed. Check the "
                "internet connection and API configuration."
            )

            with st.expander("Technical error details"):
                st.exception(error)


result = st.session_state.get("last_result")

if result:
    workflow_path = result.get("workflow_path", [])
    final_node = workflow_path[-1] if workflow_path else ""

    if final_node == "generate_answer":
        st.success("Evidence accepted — grounded decision generated.")
    else:
        st.warning(
            "Evidence was insufficient — clarification requested."
        )

    st.subheader("Agent Decision Report")
    st.markdown(result.get("answer", "No answer was generated."))

    st.divider()

    workflow_column, source_column = st.columns(2)

    with workflow_column:
        st.markdown("#### Agentic Workflow")

        st.code(
            " → ".join(workflow_path),
            language=None,
        )

        st.caption(
            f"Evidence grade: "
            f"{result.get('grading_result', 'Not available')}"
        )

    with source_column:
        st.markdown("#### Approved Sources")

        sources = result.get("sources", [])

        if sources:
            for source in sources:
                st.markdown(f"- `{source}`")
        else:
            st.write("No source was approved for the final answer.")

    chunks = result.get("chunks", [])

    with st.expander(
        "View Retrieved Knowledge Evidence",
        expanded=False,
    ):
        if not chunks:
            st.write("No knowledge chunks were retrieved.")
        else:
            for index, chunk in enumerate(chunks, start=1):
                st.markdown(
                    f"#### Result {index}: `{chunk.source}`"
                )

                st.caption(
                    f"Chunk {chunk.chunk_number} · "
                    f"Vector distance {chunk.distance:.4f}"
                )

                st.write(chunk.content)

                if index < len(chunks):
                    st.divider()