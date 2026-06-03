from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d["id"],
            title=d["title"],
            done=d.get("done", False),
            created_at=d.get("created_at", datetime.now(timezone.utc).isoformat()),
        )
