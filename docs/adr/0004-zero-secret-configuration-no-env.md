# ADR-0004: Zero Secret Configuration (No .env Dependency)

**Date**: 2026-10-22
**Status**: accepted
**Deciders**: Project Team

## Context

The initial project template included boilerplate for `.env` and `.env.example` configurations. However, this application operates as a standalone local media utility that captures streaming traffic directly from the user's browser session.

It does not interact with third-party proprietary APIs, paid cloud services, or external database stores requiring secret keys, authentication tokens, or private environment variables.

Requiring a `.env` file introduces unnecessary setup friction, user confusion, and creates accidental secret leak risks during git operations.

## Decision

We eliminate all `.env` and `.env.example` requirements. The project operates under a zero-configuration model where all runtime inputs are supplied dynamically via standard command-line flags (`argparse`) or detected automatically during browser execution.

## Alternatives Considered

### Alternative 1: Keep Mandatory .env File
- **Pros**: Matches standard full-stack web application starter templates.
- **Cons**: Creates empty, redundant files; fails early if `.env` is missing even though no secrets are required; confusing for onboarding.
- **Why not**: YAGNI (You Aren't Gonna Need It) principle; no secrets exist in this utility.

### Alternative 2: Store Browser Configuration in .env (e.g. BROWSER_TYPE, HEADLESS)
- **Pros**: Global configuration across multiple scripts.
- **Cons**: CLI arguments (`--wait`, `--threads`, `--output`) already provide immediate, transparent per-run control.
- **Why not**: Command-line arguments are more ergonomic and self-documenting for a CLI automation tool.

## Consequences

### Positive
- Zero onboarding friction: users run the script immediately without creating configuration files.
- Zero risk of leaking API tokens, passwords, or credentials into source control.
- Simplifies repository structure and eliminates dead template files.

### Negative
- If external cloud storage (e.g., S3 upload) or authenticated proxy endpoints are introduced in the future, environment variable loading would need to be reintroduced.

### Risks
- **Risk**: User accidentally commits `.env` if created locally.
- **Mitigation**: `.gitignore` and `.gitleaksignore` continue to ignore `.env*` files as a defensive safety measure.
