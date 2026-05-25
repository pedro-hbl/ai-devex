"""MCP server for ai-devex.

Exposes tools and resources so AI assistants can read from and write to
ai-devex logs directly during development sessions.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ai_devex.config import Config, find_repo_root, get_config_path, get_log_path
from ai_devex.logger import LogEntry, LogFile
from ai_devex.reporter import generate_report
from ai_devex.scanner import GitScanner

mcp = FastMCP("ai-devex")


def _resolve_root() -> Path:
    """Determine the repository root for the current session."""
    cwd = Path.cwd()
    if (cwd / ".ai-devex.toml").exists() or (cwd / ".git").is_dir():
        return cwd
    try:
        return find_repo_root(cwd)
    except FileNotFoundError:
        return cwd


def _load_config_and_log() -> tuple[Config, LogFile, Path]:
    """Load config and log file for the current repo."""
    root = _resolve_root()
    config_path = get_config_path(root)
    if not config_path.exists():
        raise RuntimeError(
            "ai-devex is not initialized in this repository. "
            "Run 'ai-devex init' first."
        )
    config = Config.load(config_path)
    log_file = LogFile(get_log_path(config, root))
    return config, log_file, root


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def log_session(
    description: str,
    tools: list[str] | None = None,
    files: list[str] | None = None,
    commit: str = "",
    tags: list[str] | None = None,
) -> str:
    """Log an AI-assisted development session.

    Args:
        description: What was done during the session.
        tools: AI tools used (e.g., ["cursor", "copilot"]).
        files: Files touched during the session.
        commit: Related git commit hash, if any.
        tags: Categorical tags (e.g., ["feature", "refactor"]).
    """
    config, log_file, _root = _load_config_and_log()
    entry = LogEntry.create(
        description=description,
        tools=tools or [],
        files=files or [],
        commit=commit,
        tags=tags or [],
    )
    log_file.append(entry)
    return f"Logged entry: {description}"


@mcp.tool()
def generate_ai_report(max_commits: int = 50, no_scan: bool = False) -> str:
    """Generate a markdown report of AI-assisted development.

    Args:
        max_commits: Maximum recent commits to scan for AI keywords.
        no_scan: Skip git history scanning; use manual logs only.
    """
    config, log_file, root = _load_config_and_log()
    scanner: GitScanner | None = None
    if not no_scan:
        scanner = GitScanner(root)
    return generate_report(config, log_file, scanner, max_commits)


@mcp.tool()
def scan_commits(max_count: int = 20) -> str:
    """Scan recent git history for AI-related commits.

    Args:
        max_count: Maximum number of recent commits to inspect.
    """
    root = _resolve_root()
    scanner = GitScanner(root)
    if not scanner.is_git_repo():
        return "Error: Not inside a git repository."

    commits = scanner.scan_commits(max_count=max_count)
    if not commits:
        return f"No AI-related commits found in the last {max_count} commits."

    lines = [f"Found {len(commits)} AI-related commit(s):"]
    for commit in commits:
        lines.append(
            f"{commit.hash}  {commit.date[:10]}  {commit.subject}"
        )
        lines.append(f"  Keywords: {', '.join(commit.matched_keywords)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("ai-devex://config")
def read_config() -> str:
    """Return the contents of .ai-devex.toml."""
    config, _log_file, _root = _load_config_and_log()
    return config.to_toml()


@mcp.resource("ai-devex://log")
def read_log() -> str:
    """Return the contents of .ai-devex.jsonl."""
    _config, log_file, _root = _load_config_and_log()
    if not log_file.path.exists():
        return ""
    with open(log_file.path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("ai-devex://status")
def read_status() -> str:
    """Return a JSON summary of current tracking status."""
    config, log_file, _root = _load_config_and_log()
    return json.dumps(
        {
            "project_name": config.project_name,
            "description": config.description,
            "total_entries": log_file.total_entries(),
            "tool_summary": log_file.tool_summary(),
            "tag_summary": log_file.tag_summary(),
        },
        indent=2,
    )


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")
