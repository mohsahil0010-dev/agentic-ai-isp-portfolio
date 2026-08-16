from pathlib import Path

import chromadb

from models import RetrievedChunk


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_DIR = PROJECT_DIR / "chroma_db"
COLLECTION_NAME = "sfn_knowledge"


def get_knowledge_collection():
    """Open the existing persistent Chroma collection."""

    if not DATABASE_DIR.exists():
        raise FileNotFoundError(
            "The Chroma database does not exist. Run ingest.py first."
        )

    client = chromadb.PersistentClient(path=str(DATABASE_DIR))

    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception as error:
        raise RuntimeError(
            "The knowledge collection was not found. Run ingest.py first."
        ) from error


def retrieve_knowledge(
    question: str,
    top_k: int = 4,
) -> list[RetrievedChunk]:
    """Retrieve the most relevant knowledge chunks."""

    normalized_question = question.strip()

    if not normalized_question:
        raise ValueError("The question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection = get_knowledge_collection()
    result_count = min(top_k, collection.count())

    if result_count == 0:
        return []

    results = collection.query(
        query_texts=[normalized_question],
        n_results=result_count,
        include=["documents", "metadatas", "distances"],
    )

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    retrieved_chunks: list[RetrievedChunk] = []

    for content, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        metadata = metadata or {}

        retrieved_chunks.append(
            RetrievedChunk(
                content=content,
                source=str(metadata.get("source", "unknown")),
                chunk_number=int(
                    metadata.get("chunk_number", -1)
                ),
                distance=float(distance),
            )
        )

    return retrieved_chunks


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks for the language model."""

    context_sections: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        context_sections.append(
            (
                f"Knowledge Source {index}\n"
                f"Document: {chunk.source}\n"
                f"Chunk: {chunk.chunk_number}\n"
                f"Content:\n{chunk.content}"
            )
        )

    return "\n\n---\n\n".join(context_sections)