"""Basic tests for ai-devex."""

from pathlib import Path

import pytest

from ai_devex.config import Config, find_repo_root
from ai_devex.logger import LogEntry, LogFile
from ai_devex.reporter import generate_report


class TestConfig:
    def test_roundtrip(self, tmp_path: Path) -> None:
        config = Config(
            project_name="test-project",
            description="A test project",
            owner="tester",
            repo_url="https://github.com/tester/test-project",
        )
        path = tmp_path / ".ai-devex.toml"
        config.save(path)
        loaded = Config.load(path)
        assert loaded.project_name == "test-project"
        assert loaded.description == "A test project"
        assert loaded.owner == "tester"
        assert loaded.repo_url == "https://github.com/tester/test-project"

    def test_find_repo_root_with_config(self, tmp_path: Path) -> None:
        (tmp_path / ".ai-devex.toml").touch()
        assert find_repo_root(tmp_path) == tmp_path

    def test_find_repo_root_with_git(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        assert find_repo_root(tmp_path) == tmp_path


class TestLogger:
    def test_create_entry(self) -> None:
        entry = LogEntry.create(
            description="Built auth flow",
            tools=["cursor"],
            files=["src/auth.py"],
        )
        assert entry.description == "Built auth flow"
        assert entry.tools == ["cursor"]
        assert entry.files == ["src/auth.py"]
        assert entry.timestamp

    def test_logfile_append_and_read(self, tmp_path: Path) -> None:
        log = LogFile(tmp_path / "test.jsonl")
        entry = LogEntry.create("Test entry", tools=["copilot"])
        log.append(entry)
        entries = log.read_all()
        assert len(entries) == 1
        assert entries[0].description == "Test entry"
        assert entries[0].tools == ["copilot"]

    def test_tool_summary(self, tmp_path: Path) -> None:
        log = LogFile(tmp_path / "test.jsonl")
        log.append(LogEntry.create("A", tools=["cursor"]))
        log.append(LogEntry.create("B", tools=["cursor", "copilot"]))
        summary = log.tool_summary()
        assert summary["cursor"] == 2
        assert summary["copilot"] == 1


class TestReporter:
    def test_generate_empty_report(self, tmp_path: Path) -> None:
        config = Config(project_name="empty")
        log_file = LogFile(tmp_path / "empty.jsonl")
        report = generate_report(config, log_file)
        assert "AI Development Report: empty" in report
        assert "Logged AI sessions | 0" in report

    def test_generate_with_entries(self, tmp_path: Path) -> None:
        config = Config(project_name="with-data")
        log_file = LogFile(tmp_path / "log.jsonl")
        log_file.append(LogEntry.create("Did something", tools=["claude"]))
        report = generate_report(config, log_file)
        assert "Logged AI sessions | 1" in report
        assert "Did something" in report
        assert "claude" in report
