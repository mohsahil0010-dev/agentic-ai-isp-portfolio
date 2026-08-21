"""Specialist LangGraph agent nodes for the scam-analysis workflow."""

from __future__ import annotations

from typing import Any

from .llm import scam_summary
from .models import AgentTrace, AnalysisReport, RiskLevel
from .tools import (
    build_actions,
    detect_indicators,
    detect_source,
    extract_entities,
    inspect_url,
    reporting_guidance,
    retrieve_patterns,
    retrieve_safety_guidance,
    score_risk,
)


def _trace(state: dict[str, Any], item: AgentTrace) -> list[AgentTrace]:
    return [*state.get("agent_trace", []), item]


def intake_agent(state: dict[str, Any]) -> dict[str, Any]:
    case = state["case"]
    source = detect_source(case)
    item = AgentTrace(
        agent="Intake & Intent Agent",
        status="completed",
        decision=f"Validated the case and classified the source as {source.value}.",
        evidence=[f"Content length: {len(case.content):,} characters", f"User context supplied: {'yes' if case.user_context else 'no'}"],
    )
    return {"detected_source": source, "agent_trace": _trace(state, item)}


def entity_agent(state: dict[str, Any]) -> dict[str, Any]:
    entities = extract_entities(state["case"].content)
    inspections = [inspect_url(entity.normalized_value) for entity in entities if entity.entity_type == "URL"]
    risky_links = sum(item.risk_points > 0 for item in inspections)
    item = AgentTrace(
        agent="Entity & Link Inspector",
        status="warning" if risky_links else "completed",
        decision=f"Extracted {len(entities)} entities and inspected {len(inspections)} links without opening them.",
        evidence=[f"Structurally suspicious links: {risky_links}", *[f"{entity.entity_type}: {entity.value[:80]}" for entity in entities[:5]]],
    )
    return {"entities": entities, "url_inspections": inspections, "agent_trace": _trace(state, item)}


def persuasion_agent(state: dict[str, Any]) -> dict[str, Any]:
    indicators = detect_indicators(state["case"].content, state["url_inspections"])
    item = AgentTrace(
        agent="Social Engineering Analyst",
        status="warning" if indicators else "completed",
        decision=f"Detected {len(indicators)} persuasion, payment, credential, or link indicators.",
        evidence=[f"{indicator.category}: {indicator.evidence}" for indicator in indicators[:6]],
    )
    return {"indicators": indicators, "agent_trace": _trace(state, item)}


def retrieval_agent(state: dict[str, Any]) -> dict[str, Any]:
    matches = retrieve_patterns(state["case"].content, state["indicators"])
    query = " ".join([state["case"].content[:1_500], *[item.category for item in state["indicators"]]])
    guidance = retrieve_safety_guidance(query)
    item = AgentTrace(
        agent="Scam Pattern Retrieval Agent",
        status="warning" if matches else "completed",
        decision=f"Compared the case with the local pattern library and retrieved {len(guidance)} safety sections.",
        evidence=[f"Pattern: {match.name} ({match.similarity:.0%})" for match in matches],
    )
    return {"pattern_matches": matches, "retrieved_guidance": guidance, "agent_trace": _trace(state, item)}


def risk_agent(state: dict[str, Any]) -> dict[str, Any]:
    assessment = score_risk(
        state["case"], state["indicators"], state["url_inspections"], state["pattern_matches"]
    )
    item = AgentTrace(
        agent="Evidence & Risk Scoring Agent",
        status="warning" if assessment.score >= 25 else "completed",
        decision=f"Calculated {assessment.score}/100 with {assessment.confidence.casefold()} confidence: {assessment.level.value}.",
        evidence=[f"{name.replace('_', ' ').title()}: {points} points" for name, points in assessment.score_breakdown.items()],
    )
    return {"assessment": assessment, "agent_trace": _trace(state, item)}


def response_route(state: dict[str, Any]) -> str:
    return "urgent_response" if state["assessment"].score >= 55 else "balanced_response"


def urgent_response_agent(state: dict[str, Any]) -> dict[str, Any]:
    actions = build_actions(state["case"], state["assessment"])
    item = AgentTrace(
        agent="Urgent Protection Agent",
        status="warning",
        decision="Selected the urgent protection route because strong risk signals or reported exposure were present.",
        evidence=[f"Immediate actions: {sum(action.priority == 'Immediate' for action in actions)}"],
    )
    return {"recommended_actions": actions, "response_route": "urgent", "agent_trace": _trace(state, item)}


def balanced_response_agent(state: dict[str, Any]) -> dict[str, Any]:
    actions = build_actions(state["case"], state["assessment"])
    item = AgentTrace(
        agent="Balanced Verification Agent",
        status="completed",
        decision="Selected the balanced verification route to avoid falsely declaring the content safe or fraudulent.",
        evidence=["Independent verification remains required even at a low score."],
    )
    return {"recommended_actions": actions, "response_route": "balanced", "agent_trace": _trace(state, item)}


def coordinator_agent(state: dict[str, Any]) -> dict[str, Any]:
    case = state["case"]
    assessment = state["assessment"]
    summary, llm_used, llm_error = scam_summary(case, assessment, len(state["indicators"]))
    if assessment.score >= 55:
        safe_reply = "I will not continue through this link or share any code or payment. I will verify the request through the organization's official contact channel."
    else:
        safe_reply = "Thanks. I will verify this request independently through the official contact channel before taking any action."
    trace_item = AgentTrace(
        agent="Lead Safety Coordinator",
        status="fallback" if llm_error else "completed",
        decision="Assembled the evidence, route-specific actions, limitations, and reporting guidance into a validated report.",
        evidence=["Groq summary used." if llm_used else "Deterministic summary used.", *([llm_error] if llm_error else [])],
    )
    agent_trace = _trace(state, trace_item)
    report = AnalysisReport(
        case=case,
        detected_source=state["detected_source"],
        assessment=assessment,
        summary=summary,
        entities=state["entities"],
        url_inspections=state["url_inspections"],
        indicators=state["indicators"],
        pattern_matches=state["pattern_matches"],
        recommended_actions=state["recommended_actions"],
        safe_reply=safe_reply,
        reporting_guidance=reporting_guidance(state["detected_source"], case),
        retrieved_guidance=state["retrieved_guidance"],
        limitations=[
            "This is a risk assessment, not proof that a sender is legitimate or criminal.",
            "Links are inspected structurally and are not opened or live reputation-checked.",
            "Novel scams may not match the local pattern library.",
            "Independently verify important requests through official channels.",
        ],
        agent_trace=agent_trace,
    )
    return {"report": report, "agent_trace": agent_trace}

