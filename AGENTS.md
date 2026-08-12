# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

mikrotik-inspector is a Python CLI tool that connects to MikroTik routers via
SSH to execute commands and parse their output into structured data. The tool
uses Fabric for SSH connectivity and Pydantic for data validation and settings
management.

## Development Commands

### Essential Commands

Run all checks (lint + type check + tests):

```bash
just check
```

Individual commands:

```bash
just lint        # Run ruff linter
just mypy        # Run mypy strict type checking
just test        # Run pytest
just coveralls   # Run coverage report and upload to coveralls
```

### Running Single Tests

```bash
uv run pytest tests/test_parse_response.py::test_parse_response
```

### Type Checking

Always use strict mypy:

```bash
uv run mypy --strict mikrotik_inspector tests
```

### Linting and Formatting

```bash
uv run ruff check mikrotik_inspector tests
uv run ruff fmt mikrotik_inspector tests
```

### Running the Tool

```bash
# Via installed script
mikrotik-inspector --host <hostname> --user <username> "<mikrotik command>"

# With debug logging
mikrotik-inspector --host <hostname> --debug "/ip dhcp-server lease print detail"

# Via module
uv run python -m mikrotik_inspector --host <hostname> "<mikrotik command>"
```

## Architecture

### Core Components

1. **mikrotik_inspector/**init**.py**: Core functionality
   - `connect()`: Establishes SSH connection via Fabric
   - `parse_response()`: Generic parser that converts MikroTik command output
     into `list[dict[str, str]]`
   - `parse_dhcp_response()`: Specialized parser for DHCP leases, returns
     `list[LeaseInfo]`
   - `parse_duration()`: Converts MikroTik duration strings (e.g., "4h29m") to
     `timedelta` objects
   - `LeaseInfo`: Pydantic model representing a DHCP lease with:
     - Field aliases for MikroTik naming conventions (e.g., "mac-address" →
       "mac_address")
     - `@model_validator` that automatically converts duration strings to
       `datetime` objects
   - `parse_kv()`: Helper to parse key=value pairs from MikroTik output

2. **mikrotik_inspector/**main**.py**: CLI entry point
   - Click-based CLI with `--host`, `--user`, and `--debug` options
   - Takes a required `command` argument (any MikroTik command)
   - Connects to router, runs the specified command
   - Uses `parse_response()` to parse output into generic dictionaries
   - Outputs JSON objects (one per line)

3. **mikrotik_inspector/config.py**: Configuration and logging
   - `Settings`: Pydantic settings with `MIKROTIK_` env prefix
   - `configure_logging()`: Sets up logging with proper stream separation:
     - Creates logger named "mikrotik_inspector"
     - INFO logs → stdout (simple format)
     - DEBUG/WARNING/ERROR logs → stderr (with timestamps and log levels)

### Data Flow

1. CLI accepts hostname/user (command line or
   `MIKROTIK_HOSTNAME`/`MIKROTIK_USER` env vars) and command
2. Establish SSH connection via Fabric
3. Execute the specified MikroTik command
4. Parse multi-line output where records start with numeric ID
5. Convert to dictionaries with key=value pairs
6. Output as JSON (one object per line)

### MikroTik Response Parsing

The parser handles MikroTik's custom output format where:

- Lines starting with a number indicate a new lease record
- Key=value pairs may span multiple lines (continuation lines are indented)
- Field names use hyphens (converted via Pydantic aliases to snake_case)
- Some fields are quoted, some aren't

## Configuration

Environment variables (optional):

- `MIKROTIK_HOSTNAME`: Default router hostname
- `MIKROTIK_USER`: SSH username (defaults to current `$USER`)

## Testing

Tests use example MikroTik output to validate parsing logic. The test data in
`tests/test_parse_response.py` shows the expected format of MikroTik DHCP lease
output.

## Key Implementation Details

### Duration Parsing

The `parse_duration()` function (mikrotik_inspector/**init**.py:74) uses a regex
to parse MikroTik duration strings:

- Format: `[Ww][Dd][Hh][Mm][Ss]` (e.g., "4h29m", "2d3h", "1w2d")
- Returns `timedelta` objects for calculations
- Handles special cases like "never" or empty strings

### LeaseInfo Model Validator

The `LeaseInfo.convert_durations()` validator
(mikrotik_inspector/**init**.py:46) automatically converts:

- `last_seen`: Duration string → `datetime` (now - duration)
- `expires_after`: Duration string → `datetime` (now + duration)

This allows for easy comparison and time-based filtering of lease data.

### Logging Architecture

The logging system ensures clean output separation:

- `_LevelFilter` class allows filtering by exact log level or level threshold
- stdout handler: Only INFO messages (user-facing output)
- stderr handler: DEBUG/WARNING/ERROR (diagnostics), only when `--debug` is used
- Logger uses name "mikrotik_inspector" for proper hierarchy

## Dependencies

- `click`: CLI framework
- `fabric`: SSH connectivity (uses Paramiko under the hood)
- `pydantic` + `pydantic-settings`: Data validation and settings management
