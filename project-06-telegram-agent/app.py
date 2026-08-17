import uuid

import streamlit as st

from graph import process_user_message


st.set_page_config(
    page_title="ISP Telegram Agent",
    page_icon="🤖",
    layout="wide",
)


st.markdown(
    """
    <style>
        .block-container {
            max-width: 1050px;
            padding-top: 2rem;
        }

        .status-box {
            background-color: #12372a;
            border: 1px solid #25d366;
            border-radius: 10px;
            color: #dcf8c6;
            padding: 12px 16px;
            margin-bottom: 18px;
        }

        .telegram-header {
            background: linear-gradient(90deg, #168acd, #229ed9);
            padding: 22px;
            border-radius: 14px;
            color: white;
            margin-bottom: 20px;
        }

        .telegram-header h1 {
            margin: 0;
        }

        .telegram-header p {
            margin: 8px 0 0 0;
            opacity: 0.9;
        }

        div[data-testid="stChatMessage"] {
            border-radius: 12px;
            padding: 6px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Welcome to SAHIL FIBER NET Assistant. "
                    "How can I help you today?"
                ),
                "intent": "general",
                "tools_used": [],
            }
        ]

    if "chat_id" not in st.session_state:
        st.session_state.chat_id = (
            f"streamlit-{uuid.uuid4().hex[:12]}"
        )

    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None


def reset_conversation() -> None:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Conversation cleared. How can I help you?"
            ),
            "intent": "general",
            "tools_used": [],
        }
    ]

    # A new ID creates a fresh LangGraph conversation.
    st.session_state.chat_id = (
        f"streamlit-{uuid.uuid4().hex[:12]}"
    )

    st.session_state.pending_prompt = None


def queue_example(prompt: str) -> None:
    st.session_state.pending_prompt = prompt


def show_sidebar() -> None:
    with st.sidebar:
        st.title("Project 6")
        st.write("Telegram Agentic AI Assistant")

        st.subheader("Main technologies")
        st.markdown(
            """
            - Telegram Bot API
            - LangGraph
            - Groq
            - Agent tools
            - Streamlit
            """
        )

        st.subheader("Agent capabilities")
        st.markdown(
            """
            - Customer lookup
            - Outage checking
            - Signal analysis
            - Package information
            - Troubleshooting
            - Support tickets
            """
        )

        st.info(
            "Telegram demo mode is active because a bot token "
            "is not currently available."
        )

        st.caption(
            f"Demo Chat ID: {st.session_state.chat_id}"
        )

        if st.button(
            "Clear conversation",
            use_container_width=True,
        ):
            reset_conversation()
            st.rerun()


def show_example_prompts() -> None:
    st.subheader("Try an example")

    column1, column2, column3 = st.columns(3)

    with column1:
        if st.button(
            "Check Model Town outage",
            use_container_width=True,
        ):
            queue_example(
                "Is there an active internet outage in Model Town?"
            )

        if st.button(
            "Look up customer 80105",
            use_container_width=True,
        ):
            queue_example(
                "Show account information for customer 80105."
            )

    with column2:
        if st.button(
            "Analyze weak signal",
            use_container_width=True,
        ):
            queue_example(
                "Analyze an RX power reading of -30.2 dBm."
            )

        if st.button(
            "Show internet packages",
            use_container_width=True,
        ):
            queue_example(
                "What internet packages are currently available?"
            )

    with column3:
        if st.button(
            "Troubleshoot connection",
            use_container_width=True,
        ):
            queue_example(
                "My internet is not working and the ONU LOS "
                "light is red. What should I do?"
            )

        if st.button(
            "Create support ticket",
            use_container_width=True,
        ):
            queue_example(
                "Create a high-priority support ticket for "
                "customer 80105 because the internet is not "
                "working and the LOS light is red."
            )


def display_conversation() -> None:
    for message in st.session_state.messages:
        avatar = "👤" if message["role"] == "user" else "🤖"

        with st.chat_message(
            message["role"],
            avatar=avatar,
        ):
            st.markdown(message["content"])

            tools_used = message.get("tools_used", [])
            intent = message.get("intent")

            if message["role"] == "assistant" and tools_used:
                with st.expander("Agent activity"):
                    st.write(
                        f"Detected intent: `{intent}`"
                    )

                    st.write(
                        "Tools used: "
                        + ", ".join(
                            f"`{tool}`" for tool in tools_used
                        )
                    )


def process_prompt(prompt: str) -> None:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner(
            "The agent is deciding which tools to use..."
        ):
            try:
                result = process_user_message(
                    prompt,
                    chat_id=st.session_state.chat_id,
                    username="Streamlit Demo User",
                )

                st.markdown(result.response)

                if result.tools_used:
                    with st.expander("Agent activity"):
                        st.write(
                            f"Detected intent: `{result.intent}`"
                        )

                        st.write(
                            "Tools used: "
                            + ", ".join(
                                f"`{tool}`"
                                for tool in result.tools_used
                            )
                        )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result.response,
                        "intent": result.intent,
                        "tools_used": result.tools_used,
                    }
                )

            except Exception as error:
                error_message = (
                    "The agent could not process the request. "
                    "Check your GROQ_API_KEY and try again."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "intent": "error",
                        "tools_used": [],
                    }
                )

                # Log only to the local terminal.
                print(
                    f"Streamlit agent error: "
                    f"{type(error).__name__}: {error}"
                )


def main() -> None:
    initialize_session()
    show_sidebar()

    st.markdown(
        """
        <div class="telegram-header">
            <h1>🤖 SAHIL FIBER NET Telegram Agent</h1>
            <p>
                A LangGraph-powered ISP assistant that autonomously
                selects and executes customer-support tools.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-box">
            ● Demo bot online — Telegram-style browser simulation
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_example_prompts()
    st.divider()

    display_conversation()

    typed_prompt = st.chat_input(
        "Ask the ISP assistant a question..."
    )

    prompt = typed_prompt or st.session_state.pending_prompt

    if prompt:
        st.session_state.pending_prompt = None
        process_prompt(prompt)


if __name__ == "__main__":
    main()