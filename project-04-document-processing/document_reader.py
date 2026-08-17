from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class DocumentReadingError(Exception):
    """Raised when an uploaded document cannot be processed."""


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from a supported PDF, TXT, or Markdown document."""

    if not filename:
        raise DocumentReadingError("The uploaded document has no filename.")

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentReadingError(
            f"Unsupported file type: {extension}. "
            "Please upload a PDF, TXT, or Markdown document."
        )

    if not file_bytes:
        raise DocumentReadingError("The uploaded document is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise DocumentReadingError("The document is larger than the 10 MB limit.")

    try:
        if extension == ".pdf":
            reader = PdfReader(BytesIO(file_bytes))

            if reader.is_encrypted:
                raise DocumentReadingError(
                    "Password-protected PDF documents are not supported."
                )

            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)

        else:
            text = file_bytes.decode("utf-8", errors="replace")

    except DocumentReadingError:
        raise
    except Exception as exc:
        raise DocumentReadingError(
            f"Could not read {filename}: {exc}"
        ) from exc

    text = text.strip()

    if not text:
        raise DocumentReadingError(
            "No readable text was found in the document."
        )

    return text