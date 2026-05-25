"""Command-line interface for ai-devex."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from ai_devex import __version__
from ai_devex.config import Config, find_repo_root, get_config_path, get_log_path
from ai_devex.logger import LogEntry, LogFile
from ai_devex.reporter import generate_report, write_report
from ai_devex.scanner import GitScanner


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="ai-devex")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Track and report AI-assisted development in your repositories."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option("--name", prompt="Project name", help="Name of the project.")
@click.option("--description", default="", help="Short project description.")
@click.option("--owner", default="", help="Project owner or team name.")
@click.option(
    "--repo-url",
    default="",
    help="Repository URL (e.g., https://github.com/user/repo).",
)
def init(name: str, description: str, owner: str, repo_url: str) -> None:
    """Initialize ai-devex tracking in the current directory."""
    root = Path.cwd()
    config_path = root / ".ai-devex.toml"
    log_path = root / ".ai-devex.jsonl"

    if config_path.exists():
        click.echo("ai-devex is already initialized in this directory.")
        sys.exit(1)

    config = Config(
        project_name=name,
        description=description,
        owner=owner,
        repo_url=repo_url,
    )
    config.save(config_path)
    log_path.touch(exist_ok=True)

    click.echo(f"Initialized ai-devex in {root}")
    click.echo(f"  Config: {config_path}")
    click.echo(f"  Log:    {log_path}")
    click.echo("")
    click.echo("Next steps:")
    click.echo("  ai-devex log 'Built initial auth flow' --tools cursor,copilot")
    click.echo("  ai-devex report --output AI_REPORT.md")


@main.command()
@click.argument("description")
@click.option(
    "--tools",
    help="Comma-separated list of AI tools used (e.g., cursor,copilot,claude).",
)
@click.option(
    "--files",
    help="Comma-separated list of files touched.",
)
@click.option("--commit", default="", help="Related commit hash.")
@click.option(
    "--tags",
    help="Comma-separated list of tags (e.g., feature,refactor,bugfix).",
)
def log(
    description: str,
    tools: str | None,
    files: str | None,
    commit: str,
    tags: str | None,
) -> None:
    """Log an AI-assisted development session."""
    try:
        root = find_repo_root()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}")
        sys.exit(1)

    config_path = get_config_path(root)
    if not config_path.exists():
        click.echo("Error: ai-devex not initialized. Run 'ai-devex init' first.")
        sys.exit(1)

    config = Config.load(config_path)
    log_file = LogFile(get_log_path(config, root))

    tool_list = [t.strip() for t in (tools or "").split(",") if t.strip()]
    file_list = [f.strip() for f in (files or "").split(",") if f.strip()]
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    entry = LogEntry.create(
        description=description,
        tools=tool_list,
        files=file_list,
        commit=commit,
        tags=tag_list,
    )
    log_file.append(entry)
    click.echo(f"Logged entry: {description}")


@main.command()
@click.option(
    "--output",
    "-o",
    default="AI_DEVELOPMENT_REPORT.md",
    help="Output file path for the report.",
)
@click.option(
    "--max-commits",
    default=50,
    help="Maximum number of recent commits to scan for AI keywords.",
)
@click.option(
    "--no-scan",
    is_flag=True,
    help="Skip scanning git history; only use manual logs.",
)
def report(output: str, max_commits: int, no_scan: bool) -> None:
    """Generate a markdown report of AI-assisted development."""
    try:
        root = find_repo_root()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}")
        sys.exit(1)

    config_path = get_config_path(root)
    if not config_path.exists():
        click.echo("Error: ai-devex not initialized. Run 'ai-devex init' first.")
        sys.exit(1)

    config = Config.load(config_path)
    log_file = LogFile(get_log_path(config, root))

    scanner: GitScanner | None = None
    if not no_scan:
        scanner = GitScanner(root)

    content = generate_report(config, log_file, scanner, max_commits)
    out_path = Path(output)
    if not out_path.is_absolute():
        out_path = root / out_path

    write_report(out_path, content)
    click.echo(f"Report written to {out_path}")


@main.command()
@click.option("--max-commits", default=20, help="Maximum commits to display.")
def scan(max_commits: int) -> None:
    """Scan git history for AI-related commits."""
    try:
        root = find_repo_root()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}")
        sys.exit(1)

    scanner = GitScanner(root)
    if not scanner.is_git_repo():
        click.echo("Error: Not inside a git repository.")
        sys.exit(1)

    commits = scanner.scan_commits(max_count=max_commits)
    if not commits:
        click.echo(f"No AI-related commits found in the last {max_commits} commits.")
        return

    click.echo(f"Found {len(commits)} AI-related commit(s):\n")
    for commit in commits:
        click.echo(f"  {commit.hash}  {commit.date[:10]}  {commit.subject}")
        click.echo(f"    Keywords: {', '.join(commit.matched_keywords)}")
        click.echo("")


@main.command()
def status() -> None:
    """Show current tracking status for the repository."""
    try:
        root = find_repo_root()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}")
        sys.exit(1)

    config_path = get_config_path(root)
    if not config_path.exists():
        click.echo("ai-devex is not initialized in this repository.")
        sys.exit(1)

    config = Config.load(config_path)
    log_file = LogFile(get_log_path(config, root))
    tool_summary = log_file.tool_summary()
    total = log_file.total_entries()

    click.echo(f"Project:   {config.project_name}")
    if config.description:
        click.echo(f"Description: {config.description}")
    click.echo(f"Log file:  {config.log_file}")
    click.echo(f"Entries:   {total}")
    if tool_summary:
        click.echo("Tools:")
        for tool, count in tool_summary.items():
            click.echo(f"  - {tool}: {count}")


if __name__ == "__main__":
    main()
