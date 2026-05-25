"""Tests for the ai-devex MCP server."""

from pathlib import Path

import pytest

from ai_devex.config import Config
from ai_devex.logger import LogEntry, LogFile

pytest.importorskip("mcp")

from ai_devex.mcp_server import (  # noqa: E402
    generate_ai_report,
    log_session,
    read_config,
    read_log,
    read_status,
    scan_commits,
)


class TestMCPTools:
    def test_log_session(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = Config(project_name="mcp-test")
        config.save(tmp_path / ".ai-devex.toml")
        (tmp_path / ".ai-devex.jsonl").touch()

        result = log_session("MCP test entry", tools=["claude"], files=["src/main.py"])
        assert "Logged entry" in result

        log_file = LogFile(tmp_path / ".ai-devex.jsonl")
        entries = log_file.read_all()
        assert len(entries) == 1
        assert entries[0].description == "MCP test entry"
        assert entries[0].tools == ["claude"]
        assert entries[0].files == ["src/main.py"]

    def test_generate_ai_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = Config(project_name="report-test")
        config.save(tmp_path / ".ai-devex.toml")
        log_file = LogFile(tmp_path / ".ai-devex.jsonl")
        log_file.append(LogEntry.create("Did work", tools=["cursor"]))

        report = generate_ai_report(no_scan=True)
        assert "AI Development Report: report-test" in report
        assert "Did work" in report

    def test_scan_commits_no_git(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = scan_commits(max_count=10)
        assert "Not inside a git repository" in result


class TestMCPResources:
    def test_read_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = Config(project_name="resource-test", description="A test project")
        config.save(tmp_path / ".ai-devex.toml")
        (tmp_path / ".ai-devex.jsonl").touch()

        content = read_config()
        assert "resource-test" in content
        assert "A test project" in content

    def test_read_log(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = Config(project_name="log-test")
        config.save(tmp_path / ".ai-devex.toml")
        log_file = LogFile(tmp_path / ".ai-devex.jsonl")
        log_file.append(LogEntry.create("Entry 1", tools=["copilot"]))

        content = read_log()
        assert "Entry 1" in content
        assert "copilot" in content

    def test_read_status(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = Config(project_name="status-test")
        config.save(tmp_path / ".ai-devex.toml")
        log_file = LogFile(tmp_path / ".ai-devex.jsonl")
        log_file.append(LogEntry.create("Entry 1", tools=["cursor"]))
        log_file.append(LogEntry.create("Entry 2", tools=["cursor", "claude"]))

        content = read_status()
        assert '"project_name": "status-test"' in content
        assert '"total_entries": 2' in content
        assert '"cursor": 2' in content
        assert '"claude": 1' in content
