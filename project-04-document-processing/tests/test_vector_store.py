from vector_store import split_text


def test_empty_text_returns_no_chunks():
    assert split_text("") == []


def test_short_text_returns_one_chunk():
    chunks = split_text(
        "Customer 80105 paid Rs 2200."
    )

    assert len(chunks) == 1
    assert "80105" in chunks[0]


def test_long_text_is_split_into_multiple_chunks():
    text = "A" * 100

    chunks = split_text(
        text,
        chunk_size=40,
        overlap=10,
    )

    assert len(chunks) == 3
    assert chunks[0][-10:] == chunks[1][:10]


def test_extra_whitespace_is_removed():
    chunks = split_text(
        "  ISP\n\ncustomer     invoice  "
    )

    assert chunks == ["ISP customer invoice"]