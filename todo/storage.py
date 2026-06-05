import json
import sys
from dataclasses import asdict
from pathlib import Path

from todo.models import Task

STORAGE_PATH = Path.home() / ".todoman.json"


def load() -> list[Task]:
    if not STORAGE_PATH.exists():
        return []
    try:
        raw = json.loads(STORAGE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(
            f"Error: {STORAGE_PATH} contains invalid JSON.\n"
            f"Details: {exc}\n"
            "Please fix or delete the file and try again."
        )
    if not isinstance(raw, list):
        sys.exit(
            f"Error: {STORAGE_PATH} has unexpected format "
            f"(expected a JSON array, got {type(raw).__name__}).\n"
            "Please fix or delete the file and try again."
        )
    return [Task.from_dict(d) for d in raw]


def save(tasks: list[Task]) -> None:
    try:
        STORAGE_PATH.write_text(
            json.dumps([asdict(t) for t in tasks], indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        sys.exit(f"Error: could not write to {STORAGE_PATH}.\nDetails: {exc}")
