import pytest

from document_reader import (
    MAX_FILE_SIZE_BYTES,
    DocumentReadingError,
    extract_text,
)


def test_reads_text_document():
    result = extract_text(
        b"Customer ID: 80105",
        "customer.txt",
    )
    assert result == "Customer ID: 80105"


def test_reads_markdown_document():
    result = extract_text(
        b"# ISP Incident Report",
        "incident.md",
    )
    assert "ISP Incident Report" in result


def test_rejects_empty_document():
    with pytest.raises(
        DocumentReadingError,
        match="empty",
    ):
        extract_text(b"", "empty.txt")


def test_rejects_unsupported_file_type():
    with pytest.raises(
        DocumentReadingError,
        match="Unsupported",
    ):
        extract_text(b"test data", "document.exe")


def test_rejects_document_over_size_limit():
    oversized_document = b"x" * (
        MAX_FILE_SIZE_BYTES + 1
    )

    with pytest.raises(
        DocumentReadingError,
        match="10 MB",
    ):
        extract_text(
            oversized_document,
            "large.txt",
        )