# ADR-0001: Record Architecture Decisions

**Date**: 2026-10-20
**Status**: accepted
**Deciders**: Project Team

## Context

We need a structured, version-controlled mechanism to record significant technical and architectural choices (frameworks, tooling, streaming protocols, security policies) along with the context, alternatives, and trade-offs behind each decision.

Without a persistent record, critical architectural context is lost across development sessions, leading to accidental regressions and repeated debates.

## Decision

We will use Architecture Decision Records (ADRs) stored in `docs/adr/` in Markdown format following the standard Michael Nygard format.

Each record follows the numbering format `NNNN-short-description.md` and contains:
* Context & Problem Statement
* Decision & Rationale
* Alternatives Considered
* Consequences (Positive, Negative, Risks)

## Alternatives Considered

### Alternative 1: Git Commit Messages Only
- **Pros**: Native to version control; no extra files.
- **Cons**: Difficult to search, browse, or review collectively; easily fragmented across rebase/squash workflows.
- **Why not**: Lacks discoverability and high-level structure needed for architectural reasoning.

### Alternative 2: External Documentation (Wiki / Notion)
- **Pros**: Rich collaborative editing interface.
- **Cons**: Decoupled from code; goes stale quickly; unavailable offline or directly to local AI agents.
- **Why not**: Architectural decisions must live directly alongside the code in the repository.

## Consequences

### Positive
- Decisions are transparent and auditable in git history.
- Historical context is preserved when new developers or AI agents join the project.
- Prevents architectural drift and uncoordinated paradigm shifts.

### Negative
- Requires team discipline to draft and review ADRs during major design changes.

### Risks
- **Risk**: ADRs become obsolete as code evolves.
- **Mitigation**: Mark superseded ADRs explicitly with links to replacement records (`superseded by ADR-NNNN`).
