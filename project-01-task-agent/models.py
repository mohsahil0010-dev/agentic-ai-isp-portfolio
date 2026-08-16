from pydantic import BaseModel, Field, field_validator


class DiagnosticRequest(BaseModel):
    """Validated input for an ISP diagnostic request."""

    customer_id: str = Field(
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
    )

    complaint: str = Field(
        min_length=5,
        max_length=500,
    )

    @field_validator("customer_id", "complaint", mode="before")
    @classmethod
    def remove_extra_spaces(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    def to_agent_goal(self) -> str:
        return (
            f"Diagnose customer {self.customer_id}. "
            f"Customer complaint: {self.complaint}"
        )