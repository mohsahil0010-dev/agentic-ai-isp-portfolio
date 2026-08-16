from typing import Literal

from pydantic import BaseModel, Field


IncidentCategory = Literal[
    "fiber",
    "network",
    "billing",
    "mixed",
    "unknown",
]

IncidentPriority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

SpecialistName = Literal[
    "fiber_agent",
    "network_agent",
    "billing_agent",
]

FindingStatus = Literal[
    "normal",
    "warning",
    "fault",
    "unknown",
]


class IncidentInput(BaseModel):
    """Structured fictional ISP incident submitted by the user."""

    incident_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    description: str = Field(min_length=5)

    onu_pon_status: Literal[
        "normal",
        "offline",
        "unknown",
    ] = "unknown"

    onu_los_status: Literal[
        "off",
        "red",
        "unknown",
    ] = "unknown"

    rx_power_dbm: float | None = None

    pppoe_status: Literal[
        "active",
        "inactive",
        "unknown",
    ] = "unknown"

    account_status: Literal[
        "enabled",
        "disabled",
        "unknown",
    ] = "unknown"

    payment_status: Literal[
        "paid",
        "unpaid",
        "partial",
        "unknown",
    ] = "unknown"

    notes: str = ""


class TriageDecision(BaseModel):
    """Coordinator decision describing which specialists are needed."""

    category: IncidentCategory
    priority: IncidentPriority
    assigned_agents: list[SpecialistName]
    reason: str
    requires_human_escalation: bool = False


class ToolObservation(BaseModel):
    """Result returned by one deterministic diagnostic tool."""

    tool_name: str
    status: FindingStatus
    summary: str
    recommended_check: str


class SpecialistFinding(BaseModel):
    """Finding returned by a specialized diagnostic agent."""

    agent: SpecialistName
    diagnosis: str
    evidence: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    requires_escalation: bool = False
    tool_observations: list[ToolObservation] = Field(
        default_factory=list
    )


class FinalIncidentReport(BaseModel):
    """Combined report prepared by the final decision agent."""

    incident_id: str
    category: IncidentCategory
    priority: IncidentPriority
    probable_root_cause: str
    decision: str
    action_plan: list[str]
    assigned_team: str
    confidence: Literal["high", "medium", "low"]
    requires_human_escalation: bool
    specialist_findings: list[SpecialistFinding] = Field(
        default_factory=list
    )
    workflow_path: list[str] = Field(default_factory=list)