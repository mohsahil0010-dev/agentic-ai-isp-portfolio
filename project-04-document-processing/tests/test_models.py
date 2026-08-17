import pytest
from pydantic import ValidationError

from models import DocumentType, ISPDocumentExtraction


def create_extraction(**changes):
    data = {
        "document_type": DocumentType.INVOICE,
        "summary": "Test invoice",
        "confidence_score": 0.9,
    }
    data.update(changes)
    return ISPDocumentExtraction(**data)


def test_customer_id_is_cleaned():
    result = create_extraction(customer_id=" 80 105 ")
    assert result.customer_id == "80105"


def test_pakistan_phone_number_is_normalized():
    result = create_extraction(
        phone_number="+92 300-1234567"
    )
    assert result.phone_number == "03001234567"


def test_negative_amount_is_rejected():
    with pytest.raises(ValidationError):
        create_extraction(amount=-100)


def test_invalid_confidence_score_is_rejected():
    with pytest.raises(ValidationError):
        create_extraction(confidence_score=1.5)