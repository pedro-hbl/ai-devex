"""Log entry management for ai-devex."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LogEntry:
    """A single AI-assisted development session entry."""

    timestamp: str
    description: str
    tools: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    commit: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        description: str,
        tools: list[str] | None = None,
        files: list[str] | None = None,
        commit: str = "",
        tags: list[str] | None = None,
    ) -> LogEntry:
        """Create a new log entry with the current timestamp."""
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            description=description,
            tools=tools or [],
            files=files or [],
            commit=commit,
            tags=tags or [],
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LogEntry:
        """Load from a dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            description=data.get("description", ""),
            tools=data.get("tools", []),
            files=data.get("files", []),
            commit=data.get("commit", ""),
            tags=data.get("tags", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class LogFile:
    """Manages the append-only JSONL log file."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def append(self, entry: LogEntry) -> None:
        """Append a single entry to the log file."""
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def read_all(self) -> list[LogEntry]:
        """Read all entries from the log file."""
        if not self.path.exists():
            return []

        entries: list[LogEntry] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(LogEntry.from_dict(data))
                except json.JSONDecodeError:
                    continue
        return entries

    def tool_summary(self) -> dict[str, int]:
        """Count occurrences of each tool across all entries."""
        counts: dict[str, int] = {}
        for entry in self.read_all():
            for tool in entry.tools:
                counts[tool] = counts.get(tool, 0) + 1
        return counts

    def tag_summary(self) -> dict[str, int]:
        """Count occurrences of each tag across all entries."""
        counts: dict[str, int] = {}
        for entry in self.read_all():
            for tag in entry.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    def total_entries(self) -> int:
        """Return the total number of log entries."""
        return len(self.read_all())
