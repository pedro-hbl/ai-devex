# ai-devex

Track and report AI-assisted development in your repositories.

When you use tools like Cursor, Claude, Copilot, or ChatGPT to write code, `ai-devex` helps you stay transparent. It generates clean, shareable reports that document how AI was involved in your project, useful for:

- Job interviews and portfolio reviews
- Team documentation and retrospectives
- Open-source contribution transparency
- Personal development tracking

## Install

```bash
pip install ai-devex
```

Or install from source:

```bash
git clone https://github.com/pedro-hbl/ai-devex.git
cd ai-devex
pip install -e ".[dev]"
```

## Quick Start

Initialize tracking in any repository:

```bash
cd my-project
ai-devex init
```

Log an AI-assisted session:

```bash
ai-devex log "Refactored auth module with Cursor" \
  --tools cursor \
  --files src/auth.py,src/middleware.py \
  --tags refactor,security
```

Generate a report:

```bash
ai-devex report --output AI_REPORT.md
```

## Commands

### `init`

Create `.ai-devex.toml` and `.ai-devex.jsonl` in the current directory.

### `log <description>`

Record a development session. Options:

- `--tools`: Comma-separated AI tools used
- `--files`: Files touched during the session
- `--commit`: Related commit hash
- `--tags`: Tags for categorization

### `report`

Generate a markdown report. Options:

- `--output, -o`: Output file path (default: `AI_DEVELOPMENT_REPORT.md`)
- `--max-commits`: Number of recent commits to scan for AI keywords (default: 50)
- `--no-scan`: Skip git history scanning

### `scan`

Scan recent git commits for AI-related keywords without generating a full report.

### `status`

Show current tracking status, including entry counts and tool usage.

## How It Works

`ai-devex` stores data in two files at your repository root:

- `.ai-devex.toml`: Project metadata
- `.ai-devex.jsonl`: Append-only log of AI-assisted sessions

The `report` command reads these files, optionally scans your git history for commits mentioning AI tools, and renders a markdown report using a built-in template.

## Example Report

See [`AI_DEVELOPMENT_REPORT.md`](AI_DEVELOPMENT_REPORT.md) in this repository for a live example.

## Development

Run tests:

```bash
pytest
```

Lint:

```bash
ruff check src tests
```

## License

MIT
