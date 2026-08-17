from pathlib import Path

from models import CommunicationRecord


HISTORY_PATH = (
    Path(__file__).parent
    / "data"
    / "communication_history.jsonl"
)


class HistoryError(Exception):
    """Raised when communication history cannot be stored or loaded."""


def save_record(
    record: CommunicationRecord,
    history_path: Path | str = HISTORY_PATH,
) -> None:
    """Append one communication record to the JSONL history."""

    path = Path(history_path)

    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "a",
            encoding="utf-8",
        ) as history_file:
            history_file.write(
                record.model_dump_json()
                + "\n"
            )

    except Exception as exc:
        raise HistoryError(
            f"Could not save communication history: {exc}"
        ) from exc


def load_history(
    limit: int = 100,
    history_path: Path | str = HISTORY_PATH,
) -> list[CommunicationRecord]:
    """Load the newest valid communication records first."""

    path = Path(history_path)

    if not path.exists():
        return []

    try:
        records: list[CommunicationRecord] = []

        with path.open(
            "r",
            encoding="utf-8",
        ) as history_file:
            for line in history_file:
                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                try:
                    records.append(
                        CommunicationRecord.model_validate_json(
                            cleaned_line
                        )
                    )
                except Exception:
                    # Skip a damaged history line without crashing the app.
                    continue

        records.reverse()
        return records[:limit]

    except Exception as exc:
        raise HistoryError(
            f"Could not load communication history: {exc}"
        ) from exc