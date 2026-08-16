import json
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq

from tools import (
    check_account as data_check_account,
    check_area_outage as data_check_area_outage,
    check_signal as data_check_signal,
    lookup_customer as data_lookup_customer,
)


load_dotenv()


def convert_to_json(data: object) -> str:
    """Convert Python data into readable JSON for the agent."""

    return json.dumps(data, indent=2)


@tool
def find_customer(customer_id: str) -> str:
    """Find a customer by connection ID. Use this before diagnosing them."""

    customer = data_lookup_customer(customer_id)

    if customer is None:
        return convert_to_json(
            {
                "success": False,
                "message": f"Customer {customer_id} was not found.",
            }
        )

    return convert_to_json(
        {
            "success": True,
            "customer": customer,
        }
    )


@tool
def inspect_optical_signal(customer_id: str) -> str:
    """Check a customer's fiber RX power and signal condition."""

    return convert_to_json(data_check_signal(customer_id))


@tool
def inspect_account_status(customer_id: str) -> str:
    """Check a customer's account, payment, package and router status."""

    return convert_to_json(data_check_account(customer_id))


@tool
def inspect_area_outage(area: str) -> str:
    """Check whether an ISP area currently has an active outage."""

    return convert_to_json(data_check_area_outage(area))


AGENT_TOOLS = [
    find_customer,
    inspect_optical_signal,
    inspect_account_status,
    inspect_area_outage,
]


SYSTEM_PROMPT = """
You are an intelligent ISP troubleshooting agent for Sahil Fiber Net.

Your job is to receive a troubleshooting goal, break it into diagnostic
tasks, select the correct tools, observe their results and produce a useful
final recommendation.

Rules:
1. When a connection ID is provided, call find_customer first.
2. Use the returned customer area when checking for an area outage.
3. Check account status when disconnection or payment may be involved.
4. Check optical signal when the complaint mentions slow speed, LOS,
   disconnection, weak signal or fiber problems.
5. Do not invent customer information or diagnostic results.
6. Clearly state when information is unavailable.
7. Base every conclusion on evidence returned by the tools.
8. Do not expose hidden reasoning. Summarize only the checks performed.

The final response must contain:
- Customer summary
- Checks performed and evidence
- Most probable cause
- Recommended actions
- Urgency: Low, Medium, High or Critical
"""


def build_agent():
    """Create and return the ISP diagnostic agent."""

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to the local .env file."
        )

    model = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        timeout=60,
        max_retries=3,
    )

    return create_agent(
        model=model,
        tools=AGENT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


def run_diagnosis(user_goal: str) -> str:
    """Run a user's troubleshooting goal through the agent."""

    if not user_goal.strip():
        return "Please provide a troubleshooting goal."

    agent = build_agent()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_goal,
                }
            ]
        }
    )

    final_content = result["messages"][-1].content

    if isinstance(final_content, str):
        return final_content

    if isinstance(final_content, list):
        text_blocks = []

        for block in final_content:
            if isinstance(block, dict) and "text" in block:
                text_blocks.append(block["text"])
            else:
                text_blocks.append(str(block))

        return "\n".join(text_blocks)

    return str(final_content)