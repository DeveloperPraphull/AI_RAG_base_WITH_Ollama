import json
import os
from datetime import datetime, timezone

# All usage is written to this file as JSON Lines (one record per line)
LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "logs", "usage.jsonl"
)


def _ensure_log_dir() -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def log_query(query: str, answer: str, source: str = "api") -> None:
    """
    Append a single usage record to the log file.

    Args:
        query:   The user's input query.
        answer:  The answer returned (first 300 chars stored).
        source:  'api' for FastAPI calls, 'mcp' for MCP tool calls.
    """
    _ensure_log_dir()

    now = datetime.now(timezone.utc)
    record = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "source": source,
        "query": query,
        "answer_preview": answer[:300] if answer else "",
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_all_logs() -> list[dict]:
    """Read and return all usage records from the log file."""
    _ensure_log_dir()

    if not os.path.exists(LOG_FILE):
        return []

    records = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return records


def read_logs_for_date(date_str: str) -> list[dict]:
    """
    Return all usage records for a specific date.

    Args:
        date_str: Date in YYYY-MM-DD format (e.g. '2026-05-10').
    """
    return [r for r in read_all_logs() if r.get("date") == date_str]
