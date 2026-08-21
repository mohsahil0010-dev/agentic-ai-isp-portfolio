"""Conditional LangGraph orchestration for ScamShield analysis."""

from __future__ import annotations

from functools import lru_cache
from typing import TypedDict

from .agents import (
    balanced_response_agent,
    coordinator_agent,
    entity_agent,
    intake_agent,
    persuasion_agent,
    response_route,
    retrieval_agent,
    risk_agent,
    urgent_response_agent,
)
from .models import AgentTrace, AnalysisReport, CaseInput, SourceType


class ScamShieldState(TypedDict, total=False):
    case: CaseInput
    detected_source: SourceType
    entities: list
    url_inspections: list
    indicators: list
    pattern_matches: list
    retrieved_guidance: list[str]
    assessment: object
    recommended_actions: list
    response_route: str
    agent_trace: list[AgentTrace]
    report: AnalysisReport


@lru_cache(maxsize=1)
def build_graph():
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(ScamShieldState)
    graph.add_node("intake", intake_agent)
    graph.add_node("entity_inspector", entity_agent)
    graph.add_node("social_engineering", persuasion_agent)
    graph.add_node("pattern_retrieval", retrieval_agent)
    graph.add_node("risk_scoring", risk_agent)
    graph.add_node("urgent_response", urgent_response_agent)
    graph.add_node("balanced_response", balanced_response_agent)
    graph.add_node("coordinator", coordinator_agent)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "entity_inspector")
    graph.add_edge("entity_inspector", "social_engineering")
    graph.add_edge("social_engineering", "pattern_retrieval")
    graph.add_edge("pattern_retrieval", "risk_scoring")
    graph.add_conditional_edges(
        "risk_scoring",
        response_route,
        {"urgent_response": "urgent_response", "balanced_response": "balanced_response"},
    )
    graph.add_edge("urgent_response", "coordinator")
    graph.add_edge("balanced_response", "coordinator")
    graph.add_edge("coordinator", END)
    return graph.compile()


def _fallback(case: CaseInput) -> AnalysisReport:
    state: dict = {"case": case, "agent_trace": []}
    for node in (intake_agent, entity_agent, persuasion_agent, retrieval_agent, risk_agent):
        state.update(node(state))
    state.update(urgent_response_agent(state) if response_route(state) == "urgent_response" else balanced_response_agent(state))
    state.update(coordinator_agent(state))
    return state["report"]


def analyze_message(
    content: str,
    source_type: SourceType | str = SourceType.AUTO,
    user_context: str = "",
    clicked_link: bool = False,
    sent_money: bool = False,
    shared_sensitive_info: bool = False,
) -> AnalysisReport:
    case = CaseInput(
        content=content,
        source_type=source_type,
        user_context=user_context,
        clicked_link=clicked_link,
        sent_money=sent_money,
        shared_sensitive_info=shared_sensitive_info,
    )
    try:
        graph = build_graph()
    except (ImportError, ModuleNotFoundError):
        return _fallback(case)
    result = graph.invoke({"case": case, "agent_trace": []})
    return result["report"]

