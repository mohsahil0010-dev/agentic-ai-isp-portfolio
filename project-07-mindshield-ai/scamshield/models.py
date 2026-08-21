"""Validated input and output models for ScamShield AI."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(StrEnum):
    AUTO = "Auto-detect"
    WHATSAPP = "WhatsApp"
    SMS = "SMS"
    EMAIL = "Email"
    WEBSITE = "Website"
    JOB = "Job offer"
    MARKETPLACE = "Marketplace"
    SOCIAL = "Social media"


class RiskLevel(StrEnum):
    LOW = "Low observed risk"
    CAUTION = "Caution"
    HIGH = "High risk"
    CRITICAL = "Critical risk"


class CaseInput(BaseModel):
    """Information supplied by the user for one analysis."""

    content: str = Field(min_length=15, max_length=20_000)
    source_type: SourceType = SourceType.AUTO
    user_context: str = Field(default="", max_length=1_000)
    clicked_link: bool = False
    sent_money: bool = False
    shared_sensitive_info: bool = False

    @field_validator("content", "user_context")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.split()).strip()


class ExtractedEntity(BaseModel):
    entity_type: Literal["URL", "Email", "Phone", "Amount", "Payment service", "Credential request"]
    value: str = Field(min_length=1, max_length=500)
    normalized_value: str = Field(min_length=1, max_length=500)
    concern: str


class UrlInspection(BaseModel):
    url: str
    hostname: str
    risk_points: int = Field(ge=0, le=40)
    findings: list[str] = Field(default_factory=list, max_length=8)


class RiskIndicator(BaseModel):
    category: str
    evidence: str
    explanation: str
    weight: int = Field(ge=1, le=25)
    severity: Literal["Low", "Medium", "High", "Critical"]


class PatternMatch(BaseModel):
    pattern_id: str
    name: str
    category: str
    similarity: float = Field(ge=0, le=1)
    matched_signals: list[str]
    explanation: str


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    verdict: str
    confidence: Literal["Low", "Medium", "High"]
    score_breakdown: dict[str, int]


class SafeAction(BaseModel):
    priority: Literal["Immediate", "Next", "Preventive"]
    action: str
    reason: str


class AgentTrace(BaseModel):
    agent: str
    status: Literal["completed", "warning", "fallback"]
    decision: str
    evidence: list[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    """Structured result assembled after every specialist has completed."""

    case: CaseInput
    detected_source: SourceType
    assessment: RiskAssessment
    summary: str
    entities: list[ExtractedEntity]
    url_inspections: list[UrlInspection]
    indicators: list[RiskIndicator]
    pattern_matches: list[PatternMatch]
    recommended_actions: list[SafeAction]
    safe_reply: str
    reporting_guidance: list[str]
    retrieved_guidance: list[str]
    limitations: list[str]
    agent_trace: list[AgentTrace]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def critical_report_has_immediate_action(self) -> "AnalysisReport":
        if self.assessment.level is RiskLevel.CRITICAL and not any(
            action.priority == "Immediate" for action in self.recommended_actions
        ):
            raise ValueError("critical reports must contain an immediate safety action")
        return self

