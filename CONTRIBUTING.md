# Contributing to SteamScoop

Thank you for contributing to SteamScoop! This document outlines our engineering workflow, code standards, and contribution process.

---

## 1. Development Principles

All contributions must follow the engineering standards documented in [`Docs/CODING_STANDARDS.md`](Docs/CODING_STANDARDS.md) and the operational rules in [`AGENTS.md`](AGENTS.md):
- **Type Safety**: Backend uses strict Python 3.11+ type hints; Frontend uses strict TypeScript (`strict: true`). No `any`.
- **Response Envelopes**: All public API endpoints adhere to the standard envelope (`data`, `error`, `meta`) specified in [`Docs/API_SPECIFICATION.md`](Docs/API_SPECIFICATION.md).
- **Separation of Concerns**: API routes (`api/endpoints`), business logic (`services`), persistence (`repositories`), and asynchronous jobs (`workers`) are strictly segregated.
- **Dependency Isolation**: Virtual environments, `node_modules`, cache files, and `.env` must never be committed.

---

## 2. Getting Started

1. Read [`Docs/DEVELOPMENT.md`](Docs/DEVELOPMENT.md) for full environment setup instructions.
2. Initialize your local configuration:
   ```bash
   cp .env.example .env
   ```
3. Start the local containerized stack:
   ```bash
   # Make:
   make up
   # Or PowerShell:
   .\scripts\dev.ps1 up
   ```
4. Verify environment health:
   ```bash
   python scripts/validate_env.py
   ```

---

## 3. Branching & Commits

### Branch Naming Conventions
- `feature/<feature-name>` (e.g. `feature/game-overview`)
- `fix/<bug-name>` (e.g. `fix/cors-parsing`)
- `refactor/<module-name>` (e.g. `refactor/redis-client`)
- `docs/<topic>` (e.g. `docs/api-contracts`)
- `test/<suite-name>` (e.g. `test/health-contract`)

### Conventional Commits
Use standard conventional commit prefixes:
```text
feat(api): add game overview endpoint
fix(ingestion): preserve cursor on failed batch
docs(ml): document sentiment evaluation
test(reviews): cover cursor pagination
refactor(db): isolate review query repository
chore(deps): update fastapi dependencies
```

---

## 4. Pre-Commit Verification Checklist

Before staging or committing any code, run the unified verification suite to ensure all linters, typecheckers, and test suites pass:

```bash
# On Linux / macOS / Git Bash:
make check

# On Windows PowerShell:
.\scripts\dev.ps1 check
```

The check verifies:
1. **Backend Linting**: `ruff check apps/api` (0 errors, 0 warnings)
2. **Backend Formatting**: `ruff format --check apps/api` (all files formatted)
3. **Backend Type Checking**: `mypy --config-file apps/api/pyproject.toml apps/api/app` (0 issues)
4. **Backend Tests**: `pytest -c apps/api/pyproject.toml apps/api/tests` (all unit and contract tests passing)
5. **Frontend Linting**: `npm --prefix apps/web run lint` (ESLint clean)
6. **Frontend Type Checking**: `npm --prefix apps/web run typecheck` (`tsc --noEmit` clean)
7. **Frontend Unit Tests**: `npm --prefix apps/web run test` (Vitest clean)

---

## 5. Submitting Changes

1. Verify your branch is rebased on latest `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. Review unstaged changes:
   ```bash
   git status
   git diff
   ```
3. Stage and commit manually:
   ```bash
   git add <target_files>
   git commit -m "feat(module): descriptive explanation of change"
   ```
4. Push to remote and open a Pull Request:
   ```bash
   git push origin <your-branch>
   ```

*(Note: Per AGENTS.md, AI coding assistants are strictly prohibited from executing `git commit` or `git push`. All commits must be executed manually by the human developer).*

