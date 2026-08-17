from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"


class OutageStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IntentType(str, Enum):
    CUSTOMER_LOOKUP = "customer_lookup"
    OUTAGE_CHECK = "outage_check"
    SIGNAL_ANALYSIS = "signal_analysis"
    PACKAGE_INFORMATION = "package_information"
    TROUBLESHOOTING = "troubleshooting"
    CREATE_TICKET = "create_ticket"
    GENERAL = "general"


class Customer(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    customer_id: str
    name: str
    phone_number: Optional[str] = None
    area: str
    package_name: str
    rx_power_dbm: float
    status: CustomerStatus

    @field_validator("customer_id")
    @classmethod
    def clean_customer_id(cls, value: str) -> str:
        return value.upper().replace(" ", "")


class Outage(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    outage_id: str
    area: str
    issue: str
    status: OutageStatus
    started_at: str
    expected_resolution: Optional[str] = None


class InternetPackage(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str
    provider: str
    speed_mbps: int = Field(gt=0)
    monthly_price: float = Field(ge=0)
    description: str


class SupportTicket(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    ticket_id: str = Field(
        default_factory=lambda: (
            "TKT-" + str(uuid4())[:8].upper()
        )
    )
    customer_id: Optional[str] = None
    issue: str = Field(min_length=5, max_length=1_000)
    priority: TicketPriority
    status: TicketStatus = TicketStatus.OPEN
    created_at: str = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    @field_validator("customer_id")
    @classmethod
    def clean_ticket_customer_id(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if not value:
            return None
        return value.upper().replace(" ", "")


class BotRequest(BaseModel):
    chat_id: str
    username: Optional[str] = None
    message: str = Field(min_length=1, max_length=4_000)


class BotResponse(BaseModel):
    success: bool
    intent: IntentType
    response: str
    tools_used: list[str] = Field(default_factory=list)