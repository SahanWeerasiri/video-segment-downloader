# ADR-0005: Modular Directory Structure (src, scripts, docs)

**Date**: 2026-10-22
**Status**: accepted
**Deciders**: Project Team

## Context

Initially, the Python implementation (`video_sniffer_downloader.py`), the runner script (`run.sh`), temporary files, downloaded media files, and documentation were placed in the project root directory.

As downloaded videos, tests, and documentation accumulated, the root workspace became cluttered, making it harder to navigate, maintain separation of concerns, and enforce clean CI/CD and linting boundaries.

## Decision

We organize the project into dedicated, standard directories:
- `src/`: Houses core Python source code and business logic (`video_sniffer_downloader.py`).
- `scripts/`: Houses execution wrappers, CLI helpers, and environment orchestrators (`run.sh`).
- `docs/`: Contains technical architecture documentation and ADR records (`docs/adr/`).
- `downloaded_files/`: Standard directory designated for downloaded media outputs.

## Alternatives Considered

### Alternative 1: Flat Root Structure
- **Pros**: Minimal directory nesting.
- **Cons**: Mixes source code, bash scripts, video outputs, and configuration in one folder; messy git status.
- **Why not**: Violates clean software engineering standards and reduces cohesion.

### Alternative 2: Full Python Packaging (pyproject.toml / setuptools package)
- **Pros**: Installable via `pip install -e .`.
- **Cons**: Adds packaging boilerplate for what is primarily a standalone CLI tool and pairing workspace.
- **Why not**: Premature complexity; a clean `src/` layout with `scripts/run.sh` provides the right balance of simplicity and structure.

## Consequences

### Positive
- Clear separation between execution scripts, source code, and artifacts.
- Improved discoverability for developers and AI pairing agents.
- Easier to configure linters (`ruff`, `flake8`) specifically targeted at `src/`.

### Negative
- Shell scripts must resolve paths relative to `$(dirname "$0")/..` rather than assuming root execution.

### Risks
- **Risk**: Hardcoded paths break when scripts are executed from outside the project directory.
- **Mitigation**: `scripts/run.sh` dynamically derives the repository root using `BASH_SOURCE[0]`.
