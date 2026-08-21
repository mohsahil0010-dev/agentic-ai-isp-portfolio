import pytest
from pydantic import ValidationError

from scamshield.models import CaseInput, RiskAssessment, RiskLevel


def test_case_normalizes_whitespace():
    case = CaseInput(content="  Please   verify this ordinary message tomorrow.  ")
    assert case.content == "Please verify this ordinary message tomorrow."


def test_case_rejects_too_short_content():
    with pytest.raises(ValidationError):
        CaseInput(content="short")


def test_risk_assessment_is_bounded():
    with pytest.raises(ValidationError):
        RiskAssessment(
            score=101,
            level=RiskLevel.CRITICAL,
            verdict="Invalid",
            confidence="High",
            score_breakdown={},
        )

