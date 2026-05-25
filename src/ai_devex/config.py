"""Configuration management for ai-devex."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_NAME = ".ai-devex.toml"
DEFAULT_LOG_NAME = ".ai-devex.jsonl"


@dataclass
class Config:
    """Represents ai-devex configuration for a repository."""

    project_name: str
    description: str = ""
    owner: str = ""
    repo_url: str = ""
    log_file: str = DEFAULT_LOG_NAME

    def to_toml(self) -> str:
        """Serialize config to TOML string."""
        lines = [
            '[project]',
            f'name = {self.project_name!r}',
        ]
        if self.description:
            lines.append(f'description = {self.description!r}')
        if self.owner:
            lines.append(f'owner = {self.owner!r}')
        if self.repo_url:
            lines.append(f'repo_url = {self.repo_url!r}')
        lines.append(f'log_file = {self.log_file!r}')
        return "\n".join(lines) + "\n"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Load config from parsed TOML dict."""
        project = data.get("project", {})
        return cls(
            project_name=project.get("name", ""),
            description=project.get("description", ""),
            owner=project.get("owner", ""),
            repo_url=project.get("repo_url", ""),
            log_file=project.get("log_file", DEFAULT_LOG_NAME),
        )

    @classmethod
    def load(cls, path: Path | str) -> Config:
        """Load config from a TOML file."""
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls.from_dict(data)

    def save(self, path: Path | str) -> None:
        """Save config to a TOML file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_toml())


def find_repo_root(start: Path | str | None = None) -> Path:
    """Find the repository root by looking for .git or .ai-devex.toml."""
    if start is None:
        start = Path.cwd()
    else:
        start = Path(start).resolve()

    for path in [start, *start.parents]:
        if (path / ".git").is_dir() or (path / DEFAULT_CONFIG_NAME).is_file():
            return path

    raise FileNotFoundError(
        "Could not find repository root. Looked for .git/ or .ai-devex.toml. "
        "Run 'ai-devex init' to initialize."
    )


def get_config_path(root: Path | None = None) -> Path:
    """Return the expected path to the config file."""
    if root is None:
        root = find_repo_root()
    return root / DEFAULT_CONFIG_NAME


def get_log_path(config: Config, root: Path | None = None) -> Path:
    """Return the path to the log file."""
    if root is None:
        root = find_repo_root()
    return root / config.log_file
