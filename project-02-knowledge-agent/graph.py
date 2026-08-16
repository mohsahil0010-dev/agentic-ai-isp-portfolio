import os
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from models import RetrievedChunk
from retriever import format_context, retrieve_knowledge


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

DEFAULT_MODEL = "openai/gpt-oss-20b"


class KnowledgeState(TypedDict, total=False):
    """Shared state used by the LangGraph workflow."""

    question: str
    chunks: list[RetrievedChunk]
    context: str
    evidence_status: str
    grading_result: str
    answer: str
    sources: list[str]
    workflow_path: list[str]


def get_llm() -> ChatGroq:
    """Create the Groq language model."""

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to the local .env file."
        )

    model_name = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    return ChatGroq(
        model=model_name,
        temperature=0,
    )


def response_to_text(content: object) -> str:
    """Convert different LLM response formats into plain text."""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []

        for item in content:
            if isinstance(item, dict):
                text_parts.append(str(item.get("text", "")))
            else:
                text_parts.append(str(item))

        return "\n".join(text_parts).strip()

    return str(content)


def retrieve_node(state: KnowledgeState) -> KnowledgeState:
    """Retrieve relevant chunks from the Chroma knowledge base."""

    question = state["question"]
    chunks = retrieve_knowledge(question, top_k=5)
    context = format_context(chunks)

    sources = list(
        dict.fromkeys(chunk.source for chunk in chunks)
    )

    return {
        "chunks": chunks,
        "context": context,
        "sources": sources,
        "workflow_path": (
            state.get("workflow_path", []) + ["retrieve"]
        ),
    }


def grade_evidence_node(state: KnowledgeState) -> KnowledgeState:
    """Ask the LLM whether the retrieved evidence is sufficient."""

    chunks = state.get("chunks", [])

    if not chunks:
        return {
            "evidence_status": "insufficient",
            "grading_result": "No knowledge chunks were retrieved.",
            "workflow_path": (
                state.get("workflow_path", []) + ["grade_evidence"]
            ),
        }

    system_prompt = """
You are a strict evidence grader for the fictional SFN ISP
knowledge base.

Determine whether the retrieved knowledge contains enough relevant
information to answer the user's question accurately.

Reply using exactly one word:

RELEVANT

or

INSUFFICIENT

Do not provide an explanation.
""".strip()

    human_prompt = f"""
User question:

{state["question"]}

Retrieved knowledge:

{state["context"]}
""".strip()

    response = get_llm().invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
    )

    grading_result = response_to_text(response.content).strip()
    normalized_grade = grading_result.upper()

    if (
        "INSUFFICIENT" in normalized_grade
        or "NOT RELEVANT" in normalized_grade
        or "NOT_RELEVANT" in normalized_grade
    ):
        evidence_status = "insufficient"
    elif "RELEVANT" in normalized_grade:
        evidence_status = "relevant"
    else:
        best_distance = min(
            chunk.distance for chunk in chunks
        )

        evidence_status = (
            "relevant"
            if best_distance <= 1.35
            else "insufficient"
        )

    return {
        "evidence_status": evidence_status,
        "grading_result": grading_result,
        "workflow_path": (
            state.get("workflow_path", []) + ["grade_evidence"]
        ),
    }


def route_after_grading(
    state: KnowledgeState,
) -> Literal["generate_answer", "request_clarification"]:
    """Choose the next graph node based on evidence quality."""

    if state.get("evidence_status") == "relevant":
        return "generate_answer"

    return "request_clarification"


def generate_answer_node(state: KnowledgeState) -> KnowledgeState:
    """Generate a grounded decision using retrieved evidence."""

    system_prompt = """
You are the SFN Knowledge Decision Agent for a fictional ISP
course project.

Answer using only the retrieved knowledge supplied to you.

Rules:

1. Do not invent policies, prices, technical limits or procedures.
2. Give a clear operational decision.
3. Explain the evidence supporting the decision.
4. Provide practical recommended actions.
5. Mention uncertainty when the evidence is incomplete.
6. Do not expose private credentials or customer information.
7. Use concise Markdown.

Use this exact response structure:

### Decision

Your direct decision.

### Explanation

Your evidence-based explanation.

### Recommended Actions

A numbered action list.

### Confidence

High, Medium or Low, followed by a short reason.
""".strip()

    human_prompt = f"""
User question:

{state["question"]}

Approved retrieved knowledge:

{state["context"]}
""".strip()

    response = get_llm().invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
    )

    answer = response_to_text(response.content).strip()

    return {
        "answer": answer,
        "workflow_path": (
            state.get("workflow_path", []) + ["generate_answer"]
        ),
    }


def request_clarification_node(
    state: KnowledgeState,
) -> KnowledgeState:
    """Return a safe response when evidence is insufficient."""

    answer = """
### Clarification Required

The current SFN knowledge base does not contain enough relevant
information to make a reliable decision.

Please provide more specific details about the customer issue,
installation, billing case, package or fiber condition. The agent
will not invent an unsupported policy or technical procedure.
""".strip()

    return {
        "answer": answer,
        "sources": [],
        "workflow_path": (
            state.get("workflow_path", [])
            + ["request_clarification"]
        ),
    }


def build_knowledge_graph():
    """Build and compile the Agentic RAG workflow."""

    workflow = StateGraph(KnowledgeState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_evidence", grade_evidence_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node(
        "request_clarification",
        request_clarification_node,
    )

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_evidence")

    workflow.add_conditional_edges(
        "grade_evidence",
        route_after_grading,
        {
            "generate_answer": "generate_answer",
            "request_clarification": "request_clarification",
        },
    )

    workflow.add_edge("generate_answer", END)
    workflow.add_edge("request_clarification", END)

    return workflow.compile()


knowledge_graph = build_knowledge_graph()


def run_knowledge_agent(question: str) -> KnowledgeState:
    """Run the complete knowledge-decision workflow."""

    normalized_question = question.strip()

    if not normalized_question:
        raise ValueError("The question cannot be empty.")

    result = knowledge_graph.invoke(
        {
            "question": normalized_question,
            "workflow_path": [],
        }
    )

    return result