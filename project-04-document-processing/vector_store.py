import hashlib
from pathlib import Path
from typing import Any

import chromadb


CHROMA_PATH = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "isp_documents"


class VectorStoreError(Exception):
    """Raised when the Chroma document store cannot complete an operation."""


def get_collection():
    """Create or load the persistent ISP document collection."""

    try:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))

        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as exc:
        raise VectorStoreError(
            f"Could not open the Chroma database: {exc}"
        ) from exc


def split_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[str]:
    """Split document text into overlapping chunks for retrieval."""

    cleaned_text = " ".join(text.split())

    if not cleaned_text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(cleaned_text):
        end = start + chunk_size
        chunk = cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(cleaned_text):
            break

        start = end - overlap

    return chunks


def add_document(text: str, filename: str) -> int:
    """Add a document's text chunks to Chroma."""

    chunks = split_text(text)

    if not chunks:
        raise VectorStoreError("The document contains no indexable text.")

    document_hash = hashlib.sha256(
        f"{filename}:{text}".encode("utf-8")
    ).hexdigest()[:16]

    ids = [
        f"{document_hash}-chunk-{index}"
        for index in range(len(chunks))
    ]

    metadata = [
        {
            "filename": filename,
            "document_hash": document_hash,
            "chunk_number": index,
        }
        for index in range(len(chunks))
    ]

    try:
        collection = get_collection()
        collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadata,
        )
        return len(chunks)

    except Exception as exc:
        raise VectorStoreError(
            f"Could not index {filename}: {exc}"
        ) from exc


def search_documents(
    query: str,
    number_of_results: int = 3,
) -> list[dict[str, Any]]:
    """Retrieve the most relevant document chunks."""

    if not query.strip():
        return []

    try:
        collection = get_collection()
        available_documents = collection.count()

        if available_documents == 0:
            return []

        result_count = min(number_of_results, available_documents)

        results = collection.query(
            query_texts=[query],
            n_results=result_count,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadata = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        return [
            {
                "text": document,
                "metadata": item_metadata,
                "distance": distance,
            }
            for document, item_metadata, distance in zip(
                documents,
                metadata,
                distances,
            )
        ]

    except Exception as exc:
        raise VectorStoreError(
            f"Document search failed: {exc}"
        ) from exc