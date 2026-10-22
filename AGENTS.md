# Agent Guidelines & Engineering Standards

These instructions guide AI assistants (Antigravity, Claude Code, Codex, Cursor) when developing in this repository.

---

## 1. Core Principles

1. **Security-First** — Never hardcode secrets, tokens, or credentials. Validate and sanitize all external inputs.
2. **Plan Before Execute** — Always restate requirements, assess risks, and produce a concise plan before writing code.
3. **Test-Driven Development (TDD)** — Reproduce bugs with failing tests first; write unit tests before implementation. Target 80%+ test coverage.
4. **Immutability & Safety** — Avoid in-place mutations. Create new objects and return fresh copies. Handle errors at every boundary without swallowing exceptions.
5. **Research Before Reinventing** — Check existing workspace utilities and standard library functions before hand-rolling custom helpers.

---

## 2. Development Workflow

```text
Plan ➔ Test (TDD) ➔ Implement ➔ Review ➔ Verify ➔ Commit
```

1. **Plan:**
   - Review requirements, identify edge cases, and outline files to be touched.
   - For complex tasks, write an Architecture Decision Record (ADR) or summary.
2. **Test (TDD):**
   - Write failing unit/integration tests (RED).
   - Verify the test actually fails for the expected reason.
3. **Implement:**
   - Write minimal, clean code to make the tests pass (GREEN).
   - Follow project-specific language conventions found in `.agents/rules/`.
4. **Review & Refactor:**
   - Audit changes against security, performance, and readability standards.
   - Ensure coverage remains at or above 80%.
5. **Verify:**
   - Run the project's test suite, linter, and build commands.
6. **Commit:**
   - Follow Conventional Commits format: `<type>: <description>` (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`).

---

## 3. Security Guidelines

### Mandatory Checks Before ANY Commit:
- [ ] **No Hardcoded Secrets:** No API keys, passwords, database URLs, or private keys. Always use environment variables or secret managers.
- [ ] **Input Validation:** Validate and sanitize all user input at system boundaries. Fail fast with explicit errors.
- [ ] **Injection Prevention:** Parameterize all database queries (prevent SQL/NoSQL injection). Sanitize rendered output (prevent XSS).
- [ ] **Authentication & Authorization:** Verify permissions on every endpoint and sensitive operation.
- [ ] **Safe Error Handling:** Never leak sensitive stack traces or internal environment variables to users.
- [ ] **Rate Limiting:** Protect public and expensive endpoints against abuse.

---

## 4. Coding Style & Quality

* **Immutability:** Do not mutate shared state. Return new collections/objects.
* **File Organization:** High cohesion, low coupling. Focus on small, domain-driven modules (<400 lines typical, 800 lines max).
* **Function Design:** Keep functions small (<50 lines) with a single responsibility. Avoid deep nesting (>4 levels).
* **Error Propagation:** Never silently catch and ignore errors (`catch (e) {}`). Log detailed context on the server side and propagate clear error messages.
* **Naming:** Use clear, intention-revealing names without cryptic abbreviations.

---

## 5. Available Workspace Customizations

* **Rules:** `.agents/rules/common/` contains universal rules. Stack-specific rules live in `.agents/rules/<language>/`.
* **Skills:** Curated workflows available in `.agents/skills/` (e.g., `tdd-workflow`, `security-scan`, `api-design`, `docker-patterns`).
* **Workflows:** Interactive playbooks available in `.agents/workflows/` (e.g., `plan.md`, `code-review.md`).

---

## 6. Success Metrics

- All automated tests pass with 80%+ coverage.
- Zero security vulnerabilities or leaked secrets.
- Linters and typecheckers pass with zero errors.
- Code is maintainable, readable, and properly documented.
