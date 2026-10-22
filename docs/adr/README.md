# Architecture Decision Records (ADRs)

Architecture Decision Records (ADRs) capture important architectural choices made during the lifecycle of this project.

## Index of Decisions

| ADR | Title | Status | Date |
|:---:|:------|:------:|:----:|
| [0001](0001-record-architecture-decisions.md) | Record Architecture Decisions | accepted | 2026-10-20 |
| [0002](0002-headless-browser-cdp-network-sniffing.md) | Headless Browser Automation with CDP Network Sniffing | accepted | 2026-10-21 |
| [0003](0003-fmp4-initialization-and-hybrid-assembly.md) | Fragmented MP4 (fMP4/CMAF) Initialization & Hybrid Assembly | accepted | 2026-10-21 |
| [0004](0004-zero-secret-configuration-no-env.md) | Zero Secret Configuration (No .env Dependency) | accepted | 2026-10-22 |
| [0005](0005-modular-directory-structure.md) | Modular Directory Structure (src, scripts, docs) | accepted | 2026-10-22 |
| [0006](0006-lifecycle-cleanup-and-resource-optimization.md) | Lifecycle Process Cleanup & CPU Resource Optimization | accepted | 2026-10-22 |

---

## How to Add a New ADR

1. Duplicate the template format: `docs/adr/template.md` to `docs/adr/NNNN-decision-title.md`.
2. Follow the standard sections:
   - **Context:** The problem or design decision we faced.
   - **Decision:** The chosen path and rationale.
   - **Alternatives Considered:** Options analyzed and evaluated with pros, cons, and why rejected.
   - **Consequences:** Positive, negative, and risks.
3. Update the index table in this `README.md`.
