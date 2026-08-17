import json
import os
from functools import lru_cache
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import (
    END,
    START,
    StateGraph,
    add_messages,
)

from isp_tools import ISP_TOOLS
from models import (
    BotRequest,
    BotResponse,
    IntentType,
)
from prompts import SYSTEM_PROMPT


MODEL_NAME = "openai/gpt-oss-20b"
MAX_LLM_CALLS = 6

TOOLS_BY_NAME = {
    tool.name: tool
    for tool in ISP_TOOLS
}


class AgentGraphError(RuntimeError):
    """Raised when the ISP agent graph cannot complete."""


class AgentState(TypedDict):
    """State passed between LangGraph nodes."""

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]
    llm_calls: int


def normalize_message_content(content) -> str:
    """Convert different AI message formats into plain text."""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
                continue

            if not isinstance(item, dict):
                continue

            text = item.get("text")

            if isinstance(text, str):
                text_parts.append(text)
                continue

            nested_content = item.get("content")

            if isinstance(nested_content, str):
                text_parts.append(nested_content)

        return "\n".join(text_parts).strip()

    if content is None:
        return ""

    return str(content).strip()


def get_intent_from_values(
    possible_values: list[str],
) -> IntentType:
    """Return the first intent value supported by models.py."""
    for value in possible_values:
        try:
            return IntentType(value)
        except ValueError:
            continue

    try:
        return IntentType("general")
    except ValueError:
        return list(IntentType)[0]


def identify_intent(
    tools_used: list[str],
) -> IntentType:
    """Identify the completed user intent from selected tools."""
    tool_names = set(tools_used)

    # Higher-impact actions are checked first.
    if "create_support_ticket" in tool_names:
        return get_intent_from_values(
            [
                "support_ticket",
                "ticket_creation",
                "create_support_ticket",
            ]
        )

    if "troubleshoot_connection" in tool_names:
        return get_intent_from_values(
            [
                "troubleshooting",
                "troubleshoot",
            ]
        )

    if "analyze_signal" in tool_names:
        return get_intent_from_values(
            [
                "signal_analysis",
                "analyze_signal",
            ]
        )

    if "check_outage" in tool_names:
        return get_intent_from_values(
            [
                "outage_check",
                "check_outage",
            ]
        )

    if "lookup_customer" in tool_names:
        return get_intent_from_values(
            [
                "customer_lookup",
                "lookup_customer",
            ]
        )

    if "list_internet_packages" in tool_names:
        return get_intent_from_values(
            [
                "package_information",
                "package_query",
                "package_lookup",
                "packages",
            ]
        )

    return get_intent_from_values(["general"])


def serialize_tool_result(result) -> str:
    """Convert a tool result into text for ToolMessage."""
    if isinstance(result, str):
        return result

    try:
        return json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError):
        return str(result)


@lru_cache(maxsize=1)
def get_agent_graph():
    """Build and cache the LangGraph ISP agent."""
    load_dotenv()

    api_key = os.getenv(
        "GROQ_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise AgentGraphError(
            "GROQ_API_KEY was not found in the .env file."
        )

    # Groq safely retries connection, timeout, rate-limit,
    # and temporary server failures at the model-request level.
    model = ChatGroq(
        model=MODEL_NAME,
        temperature=0,
        api_key=api_key,
        timeout=60,
        max_retries=4,
    )

    model_with_tools = model.bind_tools(
        ISP_TOOLS
    )

    def call_model(
        state: AgentState,
    ) -> dict:
        """Allow the model to answer or select an ISP tool."""
        llm_calls = state.get("llm_calls", 0)

        if llm_calls >= MAX_LLM_CALLS:
            raise AgentGraphError(
                "The agent reached its model-call safety limit."
            )

        response = model_with_tools.invoke(
            [
                SystemMessage(
                    content=SYSTEM_PROMPT
                )
            ]
            + state["messages"]
        )

        return {
            "messages": [response],
            "llm_calls": llm_calls + 1,
        }

    def call_tools(
        state: AgentState,
    ) -> dict:
        """Execute every tool selected by the model."""
        last_message = state["messages"][-1]
        tool_messages: list[ToolMessage] = []

        if not isinstance(last_message, AIMessage):
            return {
                "messages": tool_messages,
            }

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_call_id = tool_call.get(
                "id",
                "unknown-tool-call",
            )

            selected_tool = TOOLS_BY_NAME.get(
                tool_name
            )

            if not selected_tool:
                tool_messages.append(
                    ToolMessage(
                        content=(
                            "The requested tool is not "
                            f"available: {tool_name}"
                        ),
                        tool_call_id=tool_call_id,
                        name=tool_name,
                    )
                )
                continue

            try:
                tool_result = selected_tool.invoke(
                    tool_call.get("args", {})
                )

                tool_content = serialize_tool_result(
                    tool_result
                )

            except Exception as exc:
                tool_content = json.dumps(
                    {
                        "success": False,
                        "tool": tool_name,
                        "error": (
                            "The tool could not complete "
                            "the requested action."
                        ),
                        "error_type": type(exc).__name__,
                    },
                    ensure_ascii=False,
                )

            tool_messages.append(
                ToolMessage(
                    content=tool_content,
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

        return {
            "messages": tool_messages,
        }

    def route_after_agent(
        state: AgentState,
    ) -> Literal["tools", "end"]:
        """Continue to tools when the model requests them."""
        last_message = state["messages"][-1]

        if (
            isinstance(last_message, AIMessage)
            and last_message.tool_calls
        ):
            return "tools"

        return "end"

    workflow = StateGraph(AgentState)

    workflow.add_node(
        "agent",
        call_model,
    )

    workflow.add_node(
        "tools",
        call_tools,
    )

    workflow.add_edge(
        START,
        "agent",
    )

    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "end": END,
        },
    )

    workflow.add_edge(
        "tools",
        "agent",
    )

    checkpointer = InMemorySaver()

    return workflow.compile(
        checkpointer=checkpointer
    )


def process_user_message(
    message: str,
    chat_id: str = "streamlit-demo",
    username: str | None = None,
) -> BotResponse:
    """Process one Telegram or Streamlit message."""
    try:
        request = BotRequest(
            chat_id=str(chat_id),
            username=username,
            message=message,
        )

        agent_graph = get_agent_graph()

        result = agent_graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=request.message
                    )
                ],
                "llm_calls": 0,
            },
            config={
                "configurable": {
                    "thread_id": request.chat_id,
                },
                "recursion_limit": 12,
            },
        )

        messages = result["messages"]

        last_human_index = max(
            index
            for index, selected_message
            in enumerate(messages)
            if isinstance(
                selected_message,
                HumanMessage,
            )
        )

        current_turn_messages = messages[
            last_human_index + 1:
        ]

        tools_used = [
            selected_message.name
            for selected_message
            in current_turn_messages
            if (
                isinstance(
                    selected_message,
                    ToolMessage,
                )
                and selected_message.name
            )
        ]

        # Remove duplicate tool names while keeping their order.
        tools_used = list(
            dict.fromkeys(tools_used)
        )

        final_ai_messages = [
            selected_message
            for selected_message
            in current_turn_messages
            if (
                isinstance(
                    selected_message,
                    AIMessage,
                )
                and not selected_message.tool_calls
            )
        ]

        if not final_ai_messages:
            raise AgentGraphError(
                "The agent did not produce a final response."
            )

        response_text = normalize_message_content(
            final_ai_messages[-1].content
        )

        if not response_text:
            raise AgentGraphError(
                "The agent returned an empty response."
            )

        return BotResponse(
            success=True,
            intent=identify_intent(
                tools_used
            ),
            response=response_text,
            tools_used=tools_used,
        )

    except AgentGraphError:
        raise

    except Exception as exc:
        raise AgentGraphError(
            "The ISP agent could not process "
            f"the message: {exc}"
        ) from exc