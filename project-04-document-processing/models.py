from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentType(str, Enum):
    CUSTOMER_APPLICATION = "customer_application"
    INVOICE = "invoice"
    INCIDENT_REPORT = "incident_report"
    UNKNOWN = "unknown"


class ISPDocumentExtraction(BaseModel):
    """Validated information extracted from an ISP document."""

    model_config = ConfigDict(str_strip_whitespace=True)

    document_type: DocumentType
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    package_name: Optional[str] = None

    invoice_number: Optional[str] = None
    amount: Optional[float] = Field(default=None, ge=0)
    document_date: Optional[str] = None

    issue_type: Optional[str] = None
    rx_power_dbm: Optional[float] = None
    status: Optional[str] = None

    summary: str = Field(min_length=1)
    confidence_score: float = Field(ge=0, le=1)
    validation_warnings: list[str] = Field(default_factory=list)

    @field_validator("customer_id")
    @classmethod
    def clean_customer_id(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return value.strip().upper().replace(" ", "")

    @field_validator("phone_number")
    @classmethod
    def clean_phone_number(cls, value: Optional[str]) -> Optional[str]:
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