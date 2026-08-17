import json
from pathlib import Path

import streamlit as st

from document_reader import DocumentReadingError, extract_text
from extractor import ExtractionError, extract_document_data
from rag import RAGError, answer_document_question
from vector_store import (
    VectorStoreError,
    add_document,
    get_collection,
)


st.set_page_config(
    page_title="ISP Document Intelligence Agent",
    page_icon="📄",
    layout="wide",
)


st.title("📄 ISP Document Intelligence Agent")
st.caption(
    "Automated document extraction, validation, storage, and RAG "
    "for SAHIL FIBER NET."
)


with st.sidebar:
    st.header("Project 4")
    st.write("Automated Document Processing System")

    st.markdown(
        """
        **Main technologies**

        - Groq
        - Pydantic
        - Chroma
        - RAG
        - Streamlit
        """
    )

    try:
        stored_chunks = get_collection().count()
        st.metric("Stored document chunks", stored_chunks)
    except VectorStoreError:
        st.metric("Stored document chunks", "Unavailable")


process_tab, search_tab = st.tabs(
    ["Process Document", "Ask Documents"]
)


with process_tab:
    st.subheader("Upload an ISP document")

    uploaded_file = st.file_uploader(
        "Select a PDF, TXT, or Markdown document",
        type=["pdf", "txt", "md"],
    )

    if uploaded_file is not None:
        safe_filename = Path(uploaded_file.name).name

        try:
            document_text = extract_text(
                uploaded_file.getvalue(),
                safe_filename,
            )

            with st.expander("Document text preview"):
                st.text_area(
                    "Extracted text",
                    value=document_text,
                    height=250,
                    disabled=True,
                )

            if st.button(
                "Extract, validate, and store",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Processing the document..."):
                    extraction = extract_document_data(document_text)
                    stored_count = add_document(
                        document_text,
                        safe_filename,
                    )

                st.session_state["last_extraction"] = (
                    extraction.model_dump(mode="json")
                )
                st.session_state["last_filename"] = safe_filename
                st.session_state["last_chunk_count"] = stored_count

        except (
            DocumentReadingError,
            ExtractionError,
            VectorStoreError,
        ) as exc:
            st.error(str(exc))

    result = st.session_state.get("last_extraction")

    if result:
        st.divider()
        st.success(
            f"Processed {st.session_state['last_filename']} successfully."
        )

        document_type = result["document_type"].replace(
            "_", " "
        ).title()

        amount = result.get("amount")
        amount_display = (
            f"Rs {amount:,.2f}"
            if amount is not None
            else "Not found"
        )

        confidence = result["confidence_score"]

        column1, column2, column3, column4 = st.columns(4)

        column1.metric("Document type", document_type)
        column2.metric(
            "Customer ID",
            result.get("customer_id") or "Not found",
        )
        column3.metric("Amount", amount_display)
        column4.metric("Confidence", f"{confidence:.0%}")

        st.progress(confidence)

        warnings = result.get("validation_warnings", [])

        if warnings:
            st.warning(
                "Validation warnings:\n\n- "
                + "\n- ".join(warnings)
            )
        else:
            st.success("No validation warnings were found.")

        st.subheader("Structured extraction")
        st.json(result)

        download_data = json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )

        output_name = (
            Path(st.session_state["last_filename"]).stem
            + "_extraction.json"
        )

        st.download_button(
            label="Download structured JSON",
            data=download_data,
            file_name=output_name,
            mime="application/json",
        )

        st.caption(
            f"Stored "
            f"{st.session_state['last_chunk_count']} "
            f"document chunk(s) in Chroma."
        )


with search_tab:
    st.subheader("Ask questions about stored documents")

    question = st.text_input(
        "Question",
        placeholder="What amount did customer 80102 have to pay?",
    )

    if st.button(
        "Ask document agent",
        type="primary",
        disabled=not question.strip(),
        use_container_width=True,
    ):
        try:
            with st.spinner("Searching documents and generating answer..."):
                answer, sources = answer_document_question(question)

            st.success("Answer generated")
            st.markdown(answer)

            if sources:
                st.subheader("Retrieved sources")

                for number, source in enumerate(sources, start=1):
                    metadata = source["metadata"]
                    filename = metadata.get(
                        "filename",
                        "Unknown document",
                    )

                    relevance = max(
                        0.0,
                        min(1.0, 1.0 - source["distance"]),
                    )

                    with st.expander(
                        f"Source {number}: {filename}"
                    ):
                        st.caption(
                            f"Retrieval relevance: {relevance:.0%}"
                        )
                        st.write(source["text"])

        except (RAGError, VectorStoreError) as exc:
            st.error(str(exc))