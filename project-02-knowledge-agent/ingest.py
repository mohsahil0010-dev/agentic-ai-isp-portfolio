from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DATABASE_DIR = PROJECT_DIR / "chroma_db"
COLLECTION_NAME = "sfn_knowledge"


def load_markdown_documents() -> list[tuple[str, str]]:
    """Load all non-empty Markdown knowledge documents."""

    documents: list[tuple[str, str]] = []

    for file_path in sorted(DATA_DIR.glob("*.md")):
        content = file_path.read_text(encoding="utf-8").strip()

        if content:
            documents.append((file_path.name, content))

    if not documents:
        raise FileNotFoundError(
            f"No Markdown documents were found inside {DATA_DIR}"
        )

    return documents


def create_chunks(
    source_documents: list[tuple[str, str]],
) -> tuple[list[str], list[str], list[dict[str, object]]]:
    """Split the knowledge documents into overlapping RAG chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=[
            "\n## ",
            "\n### ",
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunk_ids: list[str] = []
    chunk_texts: list[str] = []
    chunk_metadata: list[dict[str, object]] = []

    for source_name, document_text in source_documents:
        chunks = splitter.split_text(document_text)
        source_stem = Path(source_name).stem

        for chunk_number, chunk in enumerate(chunks):
            chunk_ids.append(f"{source_stem}-{chunk_number:03d}")
            chunk_texts.append(chunk)
            chunk_metadata.append(
                {
                    "source": source_name,
                    "chunk_number": chunk_number,
                }
            )

    return chunk_ids, chunk_texts, chunk_metadata


def rebuild_knowledge_base() -> dict[str, object]:
    """Create or rebuild the persistent Chroma knowledge base."""

    source_documents = load_markdown_documents()

    chunk_ids, chunk_texts, chunk_metadata = create_chunks(
        source_documents
    )

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(DATABASE_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    existing_records = collection.get()
    existing_ids = existing_records.get("ids", [])

    if existing_ids:
        collection.delete(ids=existing_ids)

    collection.add(
        ids=chunk_ids,
        documents=chunk_texts,
        metadatas=chunk_metadata,
    )

    return {
        "source_documents": len(source_documents),
        "chunks": len(chunk_ids),
        "collection": COLLECTION_NAME,
        "database_directory": str(DATABASE_DIR),
    }


if __name__ == "__main__":
    result = rebuild_knowledge_base()

    print("\nKnowledge base created successfully")
    print(f"Source documents: {result['source_documents']}")
    print(f"Stored chunks: {result['chunks']}")
    print(f"Collection: {result['collection']}")
    print(f"Database directory: {result['database_directory']}")