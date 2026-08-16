import operator
from typing import Annotated, TypedDict

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from agents import (
    coordinator_agent,
    final_decision_agent,
    run_assigned_specialist,
)
from models import (
    FinalIncidentReport,
    IncidentInput,
    SpecialistFinding,
    SpecialistName,
    TriageDecision,
)


class IncidentState(TypedDict, total=False):
    """Shared state for the multi-agent incident workflow."""

    incident: IncidentInput
    triage: TriageDecision
    agent_name: SpecialistName

    findings: Annotated[
        list[SpecialistFinding],
        operator.add,
    ]

    final_report: FinalIncidentReport

    workflow_path: Annotated[
        list[str],
        operator.add,
    ]


def coordinator_node(
    state: IncidentState,
) -> IncidentState:
    """Triage the incident and select specialist agents."""

    triage = coordinator_agent(state["incident"])

    return {
        "triage": triage,
        "workflow_path": ["coordinator"],
    }


def route_to_specialists(
    state: IncidentState,
):
    """Create one task for every assigned specialist."""

    assigned_agents = state["triage"].assigned_agents

    if not assigned_agents:
        return "final_decision"

    return [
        Send(
            "specialist",
            {
                "incident": state["incident"],
                "triage": state["triage"],
                "agent_name": agent_name,
            },
        )
        for agent_name in assigned_agents
    ]


def specialist_node(
    state: IncidentState,
) -> IncidentState:
    """Run one specialist selected by the coordinator."""

    agent_name = state["agent_name"]

    finding = run_assigned_specialist(
        agent_name,
        state["incident"],
    )

    return {
        "findings": [finding],
        "workflow_path": [agent_name],
    }


def final_decision_node(
    state: IncidentState,
) -> IncidentState:
    """Combine all specialist findings into one final report."""

    findings = state.get("findings", [])

    report = final_decision_agent(
        incident=state["incident"],
        triage=state["triage"],
        findings=findings,
    )

    completed_path = (
        state.get("workflow_path", [])
        + ["final_decision"]
    )

    report = report.model_copy(
        update={
            "workflow_path": completed_path,
        }
    )

    return {
        "final_report": report,
        "workflow_path": ["final_decision"],
    }


def build_incident_graph():
    """Build and compile the multi-agent LangGraph workflow."""

    workflow = StateGraph(IncidentState)

    workflow.add_node(
        "coordinator",
        coordinator_node,
    )
    workflow.add_node(
        "specialist",
        specialist_node,
    )
    workflow.add_node(
        "final_decision",
        final_decision_node,
    )

    workflow.add_edge(
        START,
        "coordinator",
    )

    workflow.add_conditional_edges(
        "coordinator",
        route_to_specialists,
    )

    workflow.add_edge(
        "specialist",
        "final_decision",
    )
    workflow.add_edge(
        "final_decision",
        END,
    )

    return workflow.compile()


incident_graph = build_incident_graph()


def run_incident_response(
    incident: IncidentInput,
) -> FinalIncidentReport:
    """Run the complete multi-agent incident workflow."""

    result = incident_graph.invoke(
        {
            "incident": incident,
            "findings": [],
            "workflow_path": [],
        },
        config={
            "max_concurrency": 1,
        },
    )

    return result["final_report"]