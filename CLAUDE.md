# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project

Cecil is a **Data Sanitizer & Cost Optimizer** — a local-first CLI tool that sanitizes sensitive data (PII/PHI) from AI/LLM logs and structured data, with an optional SaaS upgrade path for cost analysis reports.

- **Architecture**: "Safe-Pipe" — Local-First, Cloud-Optional
- **Target persona**: CFOs managing AI/LLM spend
- **Status**: Pre-implementation (documentation and design complete, no source code yet)
- **Data flow**: `[Source] → [Provider] → [Sanitization Engine] → [Local Output] → [Optional: SaaS Metadata Push]`

## Tech Stack

| Component | Technology |
|-----------|------------|
| CLI | Python 3.11+, PyInstaller (single-binary distribution) |
| Frontend | React + Vite + TypeScript (strict) + Tailwind CSS |
| Backend API | FastAPI (localhost-only IPC via loopback) |
| PII Detection | Microsoft Presidio + custom regex |
| Cloud SDKs | boto3 (AWS), Azure SDK, GCP Cloud Logging |
| Icons | lucide-react |
| HTTP Client | Axios (or fetch wrapper in `ui/src/lib/apiClient.ts`) |
| Testing | pytest + pytest-asyncio, Vitest + React Testing Library, Playwright (E2E) |

## Project Structure

```
src/cecil/                   # Python CLI core
  core/
    providers/               # BaseDataProvider ABC + implementations
      base.py                # ABC: connect(), stream_records(), close(), fetch_metadata()
      local_file.py          # LocalFileProvider
      aws_cloudwatch.py      # AWSCloudWatchProvider
      registry.py            # Provider discovery and registration
    sanitizer/               # Sanitization engine + strategies
      engine.py              # SanitizationEngine (composes providers + strategies)
      strategies.py          # StrictStrategy, DeepInterceptorStrategy
  api/                       # FastAPI endpoints + Pydantic schemas
    schemas.py               # Request/response models (Pydantic v2)
  cli/                       # CLI entry points and commands
  utils/
    errors.py                # CecilError base + domain exceptions
    config.py                # CecilConfig (env vars, no direct os.environ elsewhere)
    paths.py                 # get_resource_path() for PyInstaller _MEIPASS resolution
ui/                          # React/Vite frontend (TypeScript only, no .js/.jsx)
  src/
    components/              # Reusable UI (common/, mapping/, audit/)
    hooks/                   # Custom React hooks (use* prefix)
    lib/                     # API client, utilities, constants
    types/                   # Shared TypeScript type definitions
    pages/                   # Top-level route pages
tests/
  unit/                      # Mirrors src/ structure
  integration/               # Cross-component tests
  e2e/                       # Playwright tests
  conftest.py                # Shared fixtures
  fixtures/                  # Test data files (.jsonl, .csv)
scripts/                     # Build scripts (PyInstaller orchestrator)
docs/                        # Project documentation
```

## Commands

```bash
# Python linting & formatting
ruff check src/ tests/
ruff format --check src/ tests/

# Type checking
mypy --strict src/cecil/

# Python tests
pytest --cov=cecil --cov-report=term-missing --cov-fail-under=80

# Frontend
cd ui && npm run lint && npm test

# Build single binary
python scripts/build.py
```

## Python Code Style

Full details in `docs/STYLE_GUIDE.md`. Key rules:

- **Tooling**: ruff (lint + format) + mypy (strict mode)
- **Line length**: 99 characters
- **Every module**: starts with `from __future__ import annotations`
- **Docstrings**: Google-style; required on all public modules, classes, functions, methods
- **Trailing commas**: always in multi-line collections, signatures, calls
- **Import order**: stdlib → third-party → first-party (`cecil.*`) → relative
- **Never use**: `print()` in production code, wildcard imports, bare `except Exception`

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Modules/functions/vars | `snake_case` | `stream_records()` |
| Classes | `PascalCase` | `SanitizationEngine` |
| ABCs | `Base` prefix | `BaseDataProvider` |
| Providers | `Provider` suffix | `AWSCloudWatchProvider` |
| Exceptions | `Error` suffix, inherit `CecilError` | `ProviderConnectionError` |
| Constants | `UPPER_SNAKE` | `MAX_CHUNK_SIZE` |

### Error Handling

- All custom exceptions inherit from `CecilError` (in `cecil/utils/errors.py`)
- Catch specific exceptions, not bare `Exception`
- Use `raise ... from err` to preserve chains
- Log at the catch point; never silently swallow
- Only CLI entry points may use broad `except CecilError` blocks

### Logging

- `logger = logging.getLogger(__name__)` per module
- Structured key-value pairs in log messages
- **Never log PII or sensitive data** — log counts and identifiers only

## React/TypeScript Code Style

Full details in `docs/STYLE_GUIDE.md` §2. Key rules:

- **TypeScript strict mode**; no `.js`/`.jsx` files in `ui/src/`
- **Named exports only** — no default exports for components
- **Functional components** with hooks; no class components
- **Custom hooks**: `use` prefix, live in `ui/src/hooks/`
- **State management priority**: `useState` → React Context → URL state (no Redux/Zustand)
- **Import order**: React → third-party → internal (`@/...`) → relative → `import type`

### Tailwind Design Tokens

| Token | Class | Usage |
|-------|-------|-------|
| Primary | `slate-900` | Headings, primary text, nav |
| Accent | `indigo-600` | Buttons, links, active states |
| Success | `emerald-500` | Savings indicators, success |
| Danger | `red-500` | Errors, destructive actions |
| Background | `white`/`slate-50` | Page and card backgrounds |
| Border | `slate-200` | Card borders, dividers |
| Muted | `slate-500` | Secondary labels, captions |

- Use Tailwind utilities directly; no custom CSS files (except `ui/src/index.css` resets)
- No `@apply`; no dark mode variants (not in scope for v1)
- Use `lucide-react` for all icons; no other icon libraries

## Architecture Patterns

### Provider Pattern
All data sources implement `BaseDataProvider` ABC with: `connect()`, `stream_records()`, `close()`, `fetch_metadata()`. Registered in `providers/registry.py`. Supports context manager protocol.

### Strategy Pattern
Sanitization uses interchangeable `RedactionStrategy` implementations: `StrictStrategy` (only keeps mapped fields) and `DeepInterceptorStrategy` (recursive PII detection via Presidio + regex).

### Dependency Injection
Components receive dependencies via constructor parameters. Never hard-code instantiation of providers or engines internally. This enables testing with mocks/fakes.

### Generator Streaming (Zero-Copy)
All data flows through Python generators. Hard ceiling: **50MB resident memory** during a scan. Never `list()` a full dataset. File providers read in 8KB chunks; cloud providers paginate API responses. Output writers flush incrementally.

### Safe-Pipe Invariants
1. **No raw data leaves the machine.** SaaS receives only `CostFingerprint` (token counts, model IDs, timestamps, policy hash). Enforced at the schema level.
2. **Sanitization is mandatory.** No code path from provider to output bypasses the engine.
3. **Audit trail.** Every sanitization produces a `RedactionAudit` for the UI's Audit View.
4. **Policy hash.** SHA-256 of sanitization rules included in metadata upload for SaaS verification.

## Non-Negotiable Constraints

- **Privacy-First**: Raw data NEVER hits a network socket. Only anonymized `CostFingerprint` may exit.
- **Single-Binary**: PyInstaller bundles Python CLI + React UI + NLP models. Use `get_resource_path()` for runtime vs dev asset resolution.
- **Redaction is irreversible**: Use `[EMAIL_REDACTED]`, `[SSN_REDACTED]` etc. Never reversible encoding.
- **No PII in logs, errors, or telemetry.**
- **No secrets in code**: Use env vars via `cecil/utils/config.py`; use system keyring for persistent credentials. `.env` is gitignored; provide `.env.example`.
- **CORS**: FastAPI binds to `127.0.0.1` only. Never `allow_origins=["*"]`.

## Testing

Full details in `docs/STYLE_GUIDE.md` §3.

- **Naming**: `test_<unit>_<scenario>_<expected_result>` (reads as a sentence)
- **Coverage**: 80% overall; **100% for `cecil/core/sanitizer/`** (safety-critical)
- **Fixtures**: shared in `tests/conftest.py` with docstrings; use `tmp_path` for filesystem; `monkeypatch` for external services
- **No real network calls** in unit tests
- **Memory bounds**: test with `tracemalloc` (50MB ceiling)
- **PII testing**: every sanitization test asserts specific PII strings are absent from output
- **Frontend**: `describe`/`it` blocks; test files alongside source (`*.test.tsx`)

## Git Conventions

- **Branch naming**: `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `chore/` + kebab-case (under 50 chars)
- **Commit format**: Conventional Commits — `type(scope): subject`
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`
  - Scopes: `providers`, `sanitizer`, `api`, `cli`, `ui`, `build`
  - Subject: imperative mood, lowercase, no period, under 72 chars
  - Body: explains _why_ not _what_
- **Claude commits**: include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- **PRs**: squash-merge into `main`; require CI pass + approval; title matches commit format
- **GitHub Issues**: Use **sub-issues** for task breakdowns — never use markdown task checklists (`- [ ]`) in issue bodies. Create each task as a separate sub-issue linked to the parent via the GitHub sub-issues API (`addSubIssue` GraphQL mutation). Parent issues should contain only the description, assignment, dependencies, and status.

## Post-Task Checklist

After completing each task (issue), you **must** perform these steps before considering it done:

1. **Verify CI pipeline**: After pushing or creating a PR, check that the GitHub Actions CI pipeline passes (`gh pr checks <number>` or `gh run list`). If any job fails, investigate the logs (`gh run view <id> --log-failed`), fix the issue, and push again. Do not leave a PR with failing CI.
2. **Update GitHub issue status**: Close the relevant GitHub issue when the PR is merged, or add a comment noting the PR number and current status. Use `gh issue close <number>` after merge confirmation, or `gh issue comment <number> --body "..."` for status updates.

## API Design

- All endpoints under `/api/v1/` (versioned)
- RESTful: plural nouns (`/scans`, `/providers`, `/mappings`), no trailing slashes
- Path params for IDs (`/scans/{scan_id}`), query params for filtering/pagination
- All request/response bodies use Pydantic v2 models (in `cecil/api/schemas.py`)
- Consistent error responses: `{ "error": "...", "message": "...", "details": {...} }`

## CLI Commands

- `ai-sanitizer` — main entry point
- `ai-sanitizer map` — launches local FastAPI + React UI for mapping/audit
- `ai-sanitizer report` — triggers cost analysis PDF generation (SaaS handshake)

## Sanitization Actions

Field-level actions defined in `mapping.yaml`:

| Action | Behavior |
|--------|----------|
| `REDACT` | Remove value entirely |
| `MASK` | Partial hide (e.g., `j***@example.com`) |
| `HASH` | Consistent anonymization (deterministic hash) |
| `KEEP` | Pass through without modification |

## Reference Documentation

- `docs/STYLE_GUIDE.md` — Comprehensive coding standards (Python, React/TS, testing, git, API, security, architecture patterns)
- `docs/detailed_design.md` — Full architecture blueprint (Safe-Pipe, providers, sanitization, SaaS integration)
- `docs/user_stories.md` — Feature requirements with acceptance criteria
- `docs/github_issues.md` — Engineering backlog (7 issues across 4 epics, ready for implementation)
- `docs/agents/` — Agent role definitions (product_manager, software_architect, tech_lead)
