from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class EventType(str, Enum):
    NETWORK_OUTAGE = "network_outage"
    WEAK_SIGNAL = "weak_signal"
    PAYMENT_DUE = "payment_due"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"
    SERVICE_RESTORED = "service_restored"
    GENERAL_NOTICE = "general_notice"


class CommunicationChannel(str, Enum):
    EMAIL = "email"
    NOTIFICATION = "notification"
    BOTH = "both"
    NONE = "none"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryStatus(str, Enum):
    SIMULATED = "simulated"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class ISPEvent(BaseModel):
    """Validated ISP event supplied to the communication agent."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    event_type: EventType
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    area: Optional[str] = None
    package_name: Optional[str] = None
    amount_due: Optional[float] = Field(default=None, ge=0)
    due_date: Optional[str] = None
    rx_power_dbm: Optional[float] = None
    details: str = Field(min_length=5, max_length=2_000)

    @field_validator("customer_id")
    @classmethod
    def clean_customer_id(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if not value:
            return None
        return value.upper().replace(" ", "")

    @field_validator("phone_number")
    @classmethod
    def clean_phone_number(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if not value:
            return None

        cleaned = (
            value.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if cleaned.startswith("+92"):
            cleaned = "0" + cleaned[3:]

        return cleaned

    @model_validator(mode="after")
    def validate_event_requirements(self):
        if (
            self.event_type == EventType.PAYMENT_DUE
            and self.amount_due is None
        ):
            raise ValueError(
                "Payment-due events require an amount_due."
            )

        if (
            self.event_type == EventType.WEAK_SIGNAL
            and self.rx_power_dbm is None
        ):
            raise ValueError(
                "Weak-signal events require rx_power_dbm."
            )

        return self


class CommunicationPlan(BaseModel):
    """Structured communication decision prepared by the agent."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    should_communicate: bool
    channel: CommunicationChannel
    priority: Priority
    audience: str
    subject: str
    message: str
    reason: str


class CommunicationRecord(BaseModel):
    """History record created by a communication tool."""

    record_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    event_type: EventType
    channel: CommunicationChannel
    priority: Priority
    recipient: str
    subject: str
    message: str
    status: DeliveryStatus
    tool_name: str
    details: Optional[str] = None