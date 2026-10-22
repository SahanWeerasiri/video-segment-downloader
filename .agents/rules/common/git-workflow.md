# Git Workflow & Branching Standards

---

## 1. Branch Strategy & Standards

* **Default Branch:** `main` (The name `master` is strictly retired).
* **Direct Pushes:** Direct pushes to `main` are **prohibited**. All changes must arrive via Pull Requests.
* **Branch Naming Standard:**
  - `feat/<description>` — New features (e.g. `feat/oauth-login`)
  - `fix/<description>` — Bug fixes (e.g. `fix/jwt-expiration`)
  - `refactor/<description>` — Refactoring code without behavior changes
  - `test/<description>` — Test suite improvements
  - `chore/<description>` — Maintenance and dependencies
  - `docs/<description>` — Documentation changes
  - `ci/<description>` — Pipeline and workflow updates
* **Branch Lifecycle:** Delete feature branches immediately once merged to keep the repository clean.

---

## 2. Commit Message Format (Conventional Commits)

Enforced via `.githooks/commit-msg`:
```text
<type>(<optional-scope>): <description>

[optional body]
```

* **Allowed types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`, `style`
* **Subject line:** Under 100 characters, imperative mood ("add feature" not "added feature").

---

## 3. Merge & Pull Request Rules

* **Merge Strategy:** **Squash and Merge** (Recommended). Condenses feature branch commits into a single clean commit on `main`.
* **Approvals:** At least 1 review approval required before merge.
* **Up-to-Date:** Feature branch must be rebased or synced with latest `main` before merging.
* **Passing Status Checks:** All CI pipelines must pass before the merge button unlocks.

---

## 4. Security & Quality Gates (CI/CD)

* **Pre-Commit (Local):** Secret detection (Gitleaks), `.env` block, conflict marker check.
* **Pre-Push (Local):** Blocks pushes to `main` and non-standard branch names.
* **SAST (Static Analysis in CI):** Semgrep OWASP Top 10 ruleset + Gitleaks on all PRs.
* **DAST (Dynamic Analysis):** OWASP ZAP baseline testing against deployed environments.
