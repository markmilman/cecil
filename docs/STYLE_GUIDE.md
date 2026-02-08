# Cecil Style Guide

This document defines the coding standards, conventions, and architectural patterns for the Cecil Data Sanitizer & Cost Optimizer. Every developer and Claude Code agent working on this project must follow these rules. When in doubt, defer to this guide.

---

## Table of Contents

1. [Python Code Style](#1-python-code-style)
2. [React/TypeScript Code Style](#2-reacttypescript-code-style)
3. [Testing Standards](#3-testing-standards)
4. [Git & Version Control](#4-git--version-control)
5. [API Design](#5-api-design)
6. [Security Standards](#6-security-standards)
7. [Documentation](#7-documentation)
8. [Architecture Patterns](#8-architecture-patterns)
   - 8.1 [Provider Pattern](#81-provider-pattern-for-data-ingestion)
   - 8.2 [Strategy Pattern](#82-strategy-pattern-for-sanitization)
   - 8.3 [Dependency Injection](#83-dependency-injection-for-testability)
   - 8.4 [Streaming & Memory Efficiency](#84-streaming-and-memory-efficiency)
   - 8.5 [Safe-Pipe Data Flow Integrity](#85-safe-pipe-data-flow-integrity)
   - 8.6 [Single-Binary Distribution](#86-single-binary-distribution-patterns)
   - 8.7 [Multi-Mode Execution](#87-multi-mode-execution)
   - 8.8 [IPC & Real-Time Communication](#88-ipc-and-real-time-communication)
   - 8.9 [Error Propagation Across Stages](#89-error-propagation-across-safe-pipe-stages)
   - 8.10 [Configuration Hierarchy](#810-configuration-hierarchy)
   - 8.11 [Provider Implementation Checklist](#811-provider-implementation-checklist)

---

## 1. Python Code Style

### 1.1 Formatting

Cecil uses **ruff** for both linting and formatting. The canonical configuration lives in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 99
src = ["src"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "RUF",  # ruff-specific rules
    "S",    # flake8-bandit (security)
]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.lint.isort]
known-first-party = ["cecil"]
force-single-line = false
lines-after-imports = 2
```

**Line length:** 99 characters. This is enforced by the ruff formatter, not the linter.

**Trailing commas:** Always use trailing commas in multi-line collections, function signatures, and function calls. This produces cleaner diffs.

```python
# Yes
providers = [
    "aws_cloudwatch",
    "azure_monitor",
    "gcp_logging",
]

# No
providers = [
    "aws_cloudwatch",
    "azure_monitor",
    "gcp_logging"
]
```

### 1.2 Import Ordering

Ruff manages import ordering via isort integration. Imports must appear in this order, separated by blank lines:

1. Standard library
2. Third-party packages
3. First-party (`cecil.*`)
4. Local relative imports

```python
import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from presidio_analyzer import AnalyzerEngine

from cecil.core.providers.base import BaseDataProvider
from cecil.core.sanitizer.engine import SanitizationEngine
from cecil.utils.paths import get_resource_path

from .models import ScanResult
```

Never use wildcard imports (`from module import *`). Never use relative imports that go up more than one level.

### 1.3 Type Hints

Cecil enforces **mypy strict mode**. Every function signature must have complete type annotations. The `pyproject.toml` configuration:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

**Rules:**

- All function parameters and return types must be annotated.
- Use `from __future__ import annotations` at the top of every module to enable PEP 604 union syntax (`X | None` instead of `Optional[X]`).
- Use built-in generics (`list[str]`, `dict[str, int]`) instead of `typing.List`, `typing.Dict`.
- Use `Self` from `typing` for methods that return their own class.
- Avoid `Any`. If you must use it, add a `# type: ignore[<code>]` comment with the specific mypy error code and a brief explanation.

```python
from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Self


def fetch_records(
    provider_id: str,
    limit: int | None = None,
) -> Generator[dict[str, str], None, None]:
    """Yield sanitized records from the specified provider."""
    ...


class ScanConfig:
    def with_strict_mode(self, enabled: bool = True) -> Self:
        self._strict = enabled
        return self
```

### 1.4 Naming Conventions

| Element         | Convention       | Example                           |
|-----------------|------------------|-----------------------------------|
| Modules         | `snake_case`     | `cost_analyzer.py`                |
| Packages        | `snake_case`     | `cecil/core/providers/`           |
| Classes         | `PascalCase`     | `BaseDataProvider`                |
| Functions       | `snake_case`     | `stream_records()`                |
| Methods         | `snake_case`     | `def fetch_metadata(self)`        |
| Variables       | `snake_case`     | `record_count`                    |
| Constants       | `UPPER_SNAKE`    | `MAX_CHUNK_SIZE = 8192`           |
| Type aliases    | `PascalCase`     | `RecordBatch = list[dict[str, str]]` |
| Private members | `_leading_under` | `_engine`, `_validate_input()`    |
| ABCs            | `Base` prefix    | `BaseDataProvider`                |
| Protocols       | Descriptive noun | `Sanitizable`, `Streamable`       |
| Enums           | `PascalCase`     | `RedactionLevel.STRICT`           |

**Provider classes** must be suffixed with `Provider`: `AWSCloudWatchProvider`, `LocalFileProvider`.

**Exception classes** must be suffixed with `Error`: `ProviderConnectionError`, `SanitizationError`.

### 1.5 Docstring Format

Use **Google-style docstrings**. Docstrings are required on:

- All public modules (module-level docstring)
- All public classes
- All public functions and methods
- Any private function longer than 10 lines

Docstrings are **not** required on:

- `__init__` if the class docstring covers the constructor parameters
- Single-line trivial properties
- Test functions (the test name should be self-documenting)

```python
def sanitize_record(
    record: dict[str, str],
    strategy: RedactionStrategy,
    *,
    preserve_keys: set[str] | None = None,
) -> SanitizedRecord:
    """Apply redaction rules to a single data record.

    Traverses the record using the given strategy and replaces
    sensitive values with redacted placeholders. Keys listed in
    preserve_keys are passed through without inspection.

    Args:
        record: Raw key-value record from a data provider.
        strategy: The redaction strategy to apply (STRICT or DEEP).
        preserve_keys: Field names to skip during sanitization.

    Returns:
        A SanitizedRecord containing the cleaned data and a
        redaction audit log.

    Raises:
        SanitizationError: If the record cannot be parsed or the
            strategy encounters an unrecoverable conflict.
    """
```

### 1.6 Error Handling

**Rules:**

1. Never catch bare `Exception` unless re-raising. Catch the most specific exception type.
2. Define custom exception classes in `cecil/utils/errors.py` for domain errors. All custom exceptions inherit from `CecilError`.
3. Use `raise ... from err` to preserve the exception chain.
4. Log the error at the point of catching; do not silently swallow exceptions.
5. CLI entry points are the only place where broad `except CecilError` blocks are acceptable for user-facing error messages.

```python
# cecil/utils/errors.py
class CecilError(Exception):
    """Base exception for all Cecil errors."""


class ProviderConnectionError(CecilError):
    """Raised when a data provider cannot establish a connection."""


class SanitizationError(CecilError):
    """Raised when the sanitization engine encounters invalid data."""


# Usage in provider code
class AWSCloudWatchProvider(BaseDataProvider):
    def connect(self) -> None:
        try:
            self._client = boto3.client("logs", region_name=self._region)
            self._client.describe_log_groups(limit=1)
        except ClientError as err:
            raise ProviderConnectionError(
                f"Failed to connect to CloudWatch in {self._region}"
            ) from err


# Usage in CLI entry point
def main() -> int:
    try:
        run_scan(config)
    except ProviderConnectionError as err:
        console.print(f"[red]Connection failed:[/red] {err}")
        return 1
    except CecilError as err:
        console.print(f"[red]Error:[/red] {err}")
        logger.exception("Unhandled Cecil error")
        return 1
    return 0
```

### 1.7 Logging

Use the standard library `logging` module. Never use `print()` for diagnostics.

- Each module creates its own logger: `logger = logging.getLogger(__name__)`
- Use structured key-value pairs in log messages for machine parseability.
- Log levels: `DEBUG` for internals, `INFO` for operational milestones, `WARNING` for recoverable issues, `ERROR` for failures that affect output.
- Never log PII or sensitive data. Log record counts and identifiers, not content.

```python
logger = logging.getLogger(__name__)


def stream_records(self) -> Generator[dict[str, str], None, None]:
    logger.info("Starting record stream", extra={
        "provider": self.provider_id,
        "source": self._source_path,
    })
    count = 0
    for record in self._reader:
        count += 1
        yield record
    logger.info("Record stream complete", extra={
        "provider": self.provider_id,
        "records_yielded": count,
    })
```

### 1.8 Module Organization

Each Python package must contain an `__init__.py` that explicitly re-exports its public API. Do not put implementation logic in `__init__.py`.

```
src/cli/cecil/core/providers/
    __init__.py          # Re-exports: BaseDataProvider, LocalFileProvider, etc.
    base.py              # ABC definition
    local_file.py        # LocalFileProvider implementation
    aws_cloudwatch.py    # AWSCloudWatchProvider implementation
    registry.py          # Provider discovery and registration
```

```python
# __init__.py
from cecil.core.providers.base import BaseDataProvider
from cecil.core.providers.local_file import LocalFileProvider

__all__ = [
    "BaseDataProvider",
    "LocalFileProvider",
]
```

---

## 2. React/TypeScript Code Style

### 2.1 Language and Configuration

The frontend uses **TypeScript** exclusively. No `.js` or `.jsx` files in the `src/web/src/` directory. Use strict TypeScript configuration:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "forceConsistentCasingInFileNames": true,
    "jsx": "react-jsx"
  }
}
```

### 2.2 Component Patterns

All components are **functional components** using hooks. No class components. No default exports for components; always use named exports.

```tsx
// Yes: named export, typed props interface
interface ScanResultCardProps {
  result: ScanResult;
  onDismiss: (id: string) => void;
}

export function ScanResultCard({ result, onDismiss }: ScanResultCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <h3 className="text-sm font-medium text-slate-900">{result.name}</h3>
      <button onClick={() => onDismiss(result.id)}>Dismiss</button>
    </div>
  );
}

// No: default export, inline types
export default function ScanResultCard({ result, onDismiss }: {
  result: ScanResult;
  onDismiss: (id: string) => void;
}) { ... }
```

**Hook rules:**

- Custom hooks must be prefixed with `use` and live in `src/web/src/hooks/`.
- Extract logic into custom hooks when a component exceeds ~80 lines or when logic is reused.
- Always specify dependency arrays explicitly in `useEffect`, `useMemo`, and `useCallback`.

```tsx
// src/web/src/hooks/useScanStatus.ts
export function useScanStatus(scanId: string) {
  const [status, setStatus] = useState<ScanStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    pollStatus(scanId, controller.signal)
      .then(setStatus)
      .catch((err) => setError(err.message));
    return () => controller.abort();
  }, [scanId]);

  return { status, error };
}
```

### 2.3 File and Component Naming

| Element           | Convention          | Example                          |
|-------------------|---------------------|----------------------------------|
| Component files   | `PascalCase.tsx`    | `ScanResultCard.tsx`             |
| Hook files        | `camelCase.ts`      | `useScanStatus.ts`               |
| Utility files     | `camelCase.ts`      | `formatCurrency.ts`              |
| Type/interface files | `camelCase.ts`   | `scanTypes.ts`                   |
| Test files        | `*.test.tsx`        | `ScanResultCard.test.tsx`        |
| Constants         | `UPPER_SNAKE_CASE`  | `MAX_RETRY_COUNT`                |
| CSS class tokens  | Tailwind utilities  | `text-slate-900 bg-indigo-600`   |

Directory structure inside `src/web/src/`:

```
src/web/src/
  components/        # Reusable UI components
    common/          # Buttons, inputs, modals, layout primitives
    mapping/         # Mapping view components
    audit/           # Audit view components
  hooks/             # Custom React hooks
  lib/               # API client, utilities, constants
  types/             # Shared TypeScript type definitions
  pages/             # Top-level route pages
  App.tsx
  main.tsx
```

### 2.4 State Management

Cecil's frontend is intentionally simple. Use these patterns in this priority order:

1. **Local state** (`useState`) for component-scoped data.
2. **React Context** for cross-cutting concerns (theme, API client instance, auth token).
3. **URL state** (query params via the router) for view filters and pagination.

Do not introduce Redux, Zustand, or other state management libraries without explicit architectural review.

**Data fetching pattern:** Use a thin `ApiClient` class in `src/web/src/lib/apiClient.ts` that wraps `fetch` (or Axios) with the local FastAPI base URL. All API calls go through this client.

```tsx
// src/web/src/lib/apiClient.ts
const BASE_URL = `http://127.0.0.1:${window.__CECIL_PORT__ ?? 8787}`;

export const apiClient = {
  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`);
    if (!res.ok) {
      throw new ApiError(res.status, await res.text());
    }
    return res.json() as Promise<T>;
  },

  async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new ApiError(res.status, await res.text());
    }
    return res.json() as Promise<T>;
  },
};
```

### 2.5 Tailwind CSS Conventions

Follow the Cecil design tokens strictly:

| Token       | Tailwind Class  | Usage                          |
|-------------|-----------------|--------------------------------|
| Primary     | `slate-900`     | Headings, primary text, nav    |
| Accent      | `indigo-600`    | Buttons, links, active states  |
| Success     | `emerald-500`   | Savings indicators, success    |
| Danger      | `red-500`       | Errors, destructive actions    |
| Background  | `white`/`slate-50` | Page and card backgrounds   |
| Border      | `slate-200`     | Card borders, dividers         |
| Muted text  | `slate-500`     | Secondary labels, captions     |

**Rules:**

- Use Tailwind utility classes directly. No custom CSS files except for global resets in `src/web/src/index.css`.
- Do not use `@apply` in component stylesheets. If a pattern repeats, extract a component.
- Use `lucide-react` for all icons. Do not import icons from other libraries.
- Responsive breakpoints: mobile-first. Use `sm:`, `md:`, `lg:` prefixes.
- Dark mode: not in scope for v1. Do not add `dark:` variants.

```tsx
import { ShieldCheck } from "lucide-react";

export function StatusBadge({ safe }: { safe: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
        safe
          ? "bg-emerald-50 text-emerald-700"
          : "bg-red-50 text-red-700"
      }`}
    >
      <ShieldCheck className="h-3 w-3" />
      {safe ? "Clean" : "PII Detected"}
    </span>
  );
}
```

### 2.6 Import Ordering (TypeScript)

Order imports in this sequence, separated by blank lines:

1. React and React-related (`react`, `react-dom`, `react-router`)
2. Third-party libraries (`lucide-react`, `axios`)
3. Internal absolute imports (`@/components/...`, `@/hooks/...`)
4. Relative imports (`./`, `../`)
5. Type-only imports (`import type { ... }`)

```tsx
import { useState, useEffect } from "react";

import { ShieldCheck } from "lucide-react";

import { apiClient } from "@/lib/apiClient";
import { StatusBadge } from "@/components/common/StatusBadge";

import { formatRedactionSummary } from "./utils";

import type { ScanResult } from "@/types/scanTypes";
```

---

## 3. Testing Standards

### 3.1 Test Framework

- **Python:** pytest with pytest-asyncio for async tests.
- **Frontend:** Vitest with React Testing Library.
- **E2E:** Playwright for full-stack integration tests.

### 3.2 Test File Naming and Organization

```
tests/
  unit/
    core/
      providers/
        test_local_file.py
        test_aws_cloudwatch.py
      sanitizer/
        test_engine.py
        test_strategies.py
    api/
      test_routes.py
      test_ipc.py
    cli/
      test_commands.py
  integration/
    test_provider_to_sanitizer.py
    test_api_scan_flow.py
    test_safe_pipe.py          # Safe-Pipe leak detection suite
  e2e/
    test_mapping_ui.py
    test_audit_view.py
  conftest.py              # Shared fixtures
  fixtures/                # Test data files
    sample_logs.jsonl
    pii_records.csv
```

Python test files are prefixed with `test_`. Test classes (when grouping related tests) are prefixed with `Test`.

Frontend test files sit alongside their source files: `ScanResultCard.test.tsx` next to `ScanResultCard.tsx`.

### 3.3 Test Naming Conventions

Test function names describe the scenario and expected outcome using this pattern:

```
test_<unit>_<scenario>_<expected_result>
```

Use plain English with underscores. The name should read as a sentence.

```python
# Yes: descriptive, reads as a specification
def test_sanitize_record_with_email_field_replaces_with_placeholder():
    ...

def test_local_file_provider_with_missing_path_raises_connection_error():
    ...

def test_stream_records_with_10mb_file_stays_under_memory_bound():
    ...

# No: vague, uninformative
def test_sanitize():
    ...

def test_error():
    ...
```

For frontend tests, use `describe`/`it` blocks with plain English descriptions:

```tsx
describe("ScanResultCard", () => {
  it("renders the scan name and record count", () => { ... });
  it("calls onDismiss with the result id when dismiss is clicked", () => { ... });
  it("shows a danger badge when PII is detected", () => { ... });
});
```

### 3.4 Fixture Patterns

Use pytest fixtures for test setup. Place shared fixtures in `tests/conftest.py`. Place module-specific fixtures in the test file or a local `conftest.py`.

```python
# tests/conftest.py
import pytest
from cecil.core.sanitizer.engine import SanitizationEngine
from cecil.core.sanitizer.strategies import StrictStrategy


@pytest.fixture
def strict_engine() -> SanitizationEngine:
    """A sanitization engine configured with strict redaction."""
    return SanitizationEngine(strategy=StrictStrategy())


@pytest.fixture
def sample_record() -> dict[str, str]:
    """A single record containing known PII for testing."""
    return {
        "timestamp": "2025-01-15T10:30:00Z",
        "user": "jane.doe@example.com",
        "message": "User SSN 123-45-6789 processed",
        "model": "gpt-4",
        "tokens": "1523",
    }


@pytest.fixture
def pii_log_path(tmp_path: Path) -> Path:
    """Write a temporary JSONL file with PII records."""
    log_file = tmp_path / "test_logs.jsonl"
    records = [
        {"user": "john@example.com", "data": "secret-key-abc123"},
        {"user": "555-12-3456", "data": "normal content"},
    ]
    log_file.write_text("\n".join(json.dumps(r) for r in records))
    return log_file
```

**Rules:**

- Fixtures must have docstrings explaining what they provide.
- Use `tmp_path` for file-system tests. Never write to the real filesystem.
- Use `monkeypatch` or dedicated mocks to replace external services. Never make real network calls in unit tests.
- Prefer factory fixtures over complex parameterized fixtures when the test data varies significantly.

### 3.5 Coverage Requirements

- **Target:** 80% line coverage for `src/cli/`.
- **Required 100% coverage:** `cecil/core/sanitizer/` (the PII redaction engine is safety-critical).
- **Excluded from coverage:** `tests/`, `scripts/`, `src/web/`.
- Run coverage: `pytest --cov=cecil --cov-report=term-missing --cov-fail-under=80`

### 3.6 What to Test vs. What Not to Test

**Always test:**

- PII detection and redaction (every entity type: email, SSN, phone, API key, etc.)
- Provider `stream_records()` output shape and error handling
- API endpoint request/response contracts
- CLI command output and exit codes
- Memory bounds on streaming operations (50MB ceiling)
- Error paths: missing files, invalid input, connection failures

**Do not test:**

- Third-party library internals (Presidio, boto3, FastAPI framework behavior)
- Tailwind class rendering (trust the framework)
- Private helper functions directly unless they contain complex logic; test them through their public callers
- PyInstaller bundling (handled by build scripts and manual verification)

### 3.7 Safe-Pipe Integration Tests

Every release must include an end-to-end test verifying that no PII leaks from provider through to the telemetry payload. This is the most critical test category.

```python
from __future__ import annotations

import json


KNOWN_PII = [
    "jane.doe@example.com",
    "123-45-6789",
    "sk-secret-api-key-12345",
    "192.168.1.100",
]


def test_safe_pipe_cost_fingerprint_contains_zero_pii(strict_engine: SanitizationEngine) -> None:
    """Verify that the CostFingerprint contains none of the known PII strings."""
    records = [
        {
            "user": "jane.doe@example.com",
            "message": "SSN 123-45-6789 key sk-secret-api-key-12345",
            "ip": "192.168.1.100",
            "model": "gpt-4",
            "tokens": "1523",
        },
    ]
    provider = MockDataProvider(records=records)

    with provider:
        sanitized = list(strict_engine.process_stream(provider.stream_records()))

    fingerprint = CostFingerprint.from_scan(sanitized)
    fingerprint_json = json.dumps(fingerprint.__dict__)

    for pii_value in KNOWN_PII:
        assert pii_value not in fingerprint_json, (
            f"PII leak detected in CostFingerprint: {pii_value!r}"
        )


def test_safe_pipe_telemetry_payload_is_allowlisted_fields_only(
    strict_engine: SanitizationEngine,
) -> None:
    """Verify the telemetry payload contains only allowlisted keys."""
    allowed_keys = {
        "scan_id", "total_records", "total_tokens",
        "model_breakdown", "time_range_start", "time_range_end",
        "policy_hash",
    }
    provider = MockDataProvider(records=[{"user": "test@test.com", "model": "gpt-4", "tokens": "100"}])

    with provider:
        sanitized = list(strict_engine.process_stream(provider.stream_records()))

    fingerprint = CostFingerprint.from_scan(sanitized)
    actual_keys = set(fingerprint.__dict__.keys())
    assert actual_keys == allowed_keys, f"Unexpected fields in fingerprint: {actual_keys - allowed_keys}"
```

### 3.8 Property-Based Testing

Use **Hypothesis** to fuzz the sanitization engine with arbitrary inputs. This catches edge cases that hand-written tests miss.

```python
from __future__ import annotations

from hypothesis import given, settings, strategies as st


@given(st.text(min_size=1, max_size=1000))
@settings(max_examples=200)
def test_sanitizer_never_crashes_on_arbitrary_input(
    strict_engine: SanitizationEngine,
    text: str,
) -> None:
    """The sanitizer must handle any input without raising."""
    record = {"field": text}
    result = strict_engine.sanitize(record)
    assert isinstance(result, SanitizedRecord)


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.text(min_size=0, max_size=500),
    min_size=1,
    max_size=20,
))
def test_sanitizer_output_never_exceeds_input_field_count(
    strict_engine: SanitizationEngine,
    record: dict[str, str],
) -> None:
    """Sanitized output should not add extra fields."""
    result = strict_engine.sanitize(record)
    assert len(result.data) <= len(record)
```

### 3.9 Mode-Specific Test Patterns

Each execution mode has distinct invariants that must be tested:

```python
from __future__ import annotations

from unittest.mock import patch


def test_audit_mode_makes_zero_network_calls(tmp_path: Path) -> None:
    """In Audit mode, no network calls should occur."""
    config = CecilConfig(mode=ExecutionMode.AUDIT, output_dir=tmp_path)

    with patch("socket.socket.connect") as mock_connect:
        run_scan(config, provider=MockDataProvider(records=[{"data": "test"}]))
        mock_connect.assert_not_called()


def test_ai_optimization_mode_extracts_cost_metadata() -> None:
    """AI-Optimization mode must extract token counts and model IDs."""
    records = [
        {"model": "gpt-4", "tokens": "1523", "content": "secret data"},
        {"model": "claude-3", "tokens": "890", "content": "more secrets"},
    ]
    config = CecilConfig(mode=ExecutionMode.AI_OPTIMIZATION)
    result = run_scan(config, provider=MockDataProvider(records=records))

    assert result.fingerprint.total_tokens == 2413
    assert "gpt-4" in result.fingerprint.model_breakdown
    assert "claude-3" in result.fingerprint.model_breakdown


def test_generic_mode_applies_user_defined_schema() -> None:
    """Generic mode must respect custom field mappings."""
    mapping = {"email_field": RedactionAction.REDACT, "safe_field": RedactionAction.KEEP}
    config = CecilConfig(mode=ExecutionMode.GENERIC, field_mapping=mapping)
    records = [{"email_field": "user@example.com", "safe_field": "public info"}]
    result = run_scan(config, provider=MockDataProvider(records=records))

    output = result.sanitized_records[0]
    assert "user@example.com" not in output["email_field"]
    assert output["safe_field"] == "public info"
```

---

## 4. Git & Version Control

### 4.1 Branch Naming

All branches must use a category prefix:

```
feat/<short-description>     # New features
fix/<short-description>      # Bug fixes
refactor/<short-description> # Code restructuring without behavior change
docs/<short-description>     # Documentation only
test/<short-description>     # Adding or improving tests
chore/<short-description>    # Tooling, deps, CI config
```

Use kebab-case for the description. Keep it under 50 characters total.

```
feat/aws-cloudwatch-provider
fix/sanitizer-ssn-false-positive
refactor/provider-streaming-interface
docs/api-endpoint-reference
```

### 4.2 Commit Message Format

Follow Conventional Commits. The format is:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type** must be one of: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

**Scope** is the affected area: `providers`, `sanitizer`, `api`, `cli`, `ui`, `build`.

**Subject** is imperative mood, lowercase, no period at the end, under 72 characters.

**Body** explains _why_, not _what_. Wrap at 72 characters.

```
feat(providers): add AWS CloudWatch log ingestion

Implements streaming ingestion from CloudWatch log groups using
the boto3 client. Records are yielded in chunks of 1000 to keep
memory under the 50MB bound.

Closes #12
```

```
fix(sanitizer): handle nested JSON strings in deep interceptor

The deep interceptor was skipping values that contained serialized
JSON strings (e.g., a stringified object inside a log message).
This adds a recursive parse step before field-level scanning.

Closes #34
```

When Claude Code creates commits, they must include the co-author trailer:

```
Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### 4.3 PR Requirements

Every pull request must:

1. Have a descriptive title matching the commit message format (`type(scope): subject`).
2. Include a summary section explaining the change and its motivation.
3. Include a test plan with steps to verify the change.
4. Pass all CI checks (ruff, mypy, pytest, npm test).
5. Have at least one approval before merging.
6. Be squash-merged into `main` to maintain a linear history.

---

## 5. API Design

### 5.1 Endpoint Naming

The FastAPI server exposes localhost-only IPC endpoints. Use RESTful resource naming:

```
GET    /api/v1/providers              # List available providers
POST   /api/v1/scans                  # Start a new scan
GET    /api/v1/scans/{scan_id}        # Get scan status and results
GET    /api/v1/scans/{scan_id}/records # Stream sanitized records
DELETE /api/v1/scans/{scan_id}        # Cancel a running scan
GET    /api/v1/mappings               # Get field mapping configuration
PUT    /api/v1/mappings               # Update field mapping
GET    /api/v1/health                 # Server health check
WS     /api/v1/scans/{scan_id}/ws    # Real-time scan progress
```

**Rules:**

- Use plural nouns for resources: `/scans`, `/providers`, `/mappings`.
- Use path parameters for identifiers: `/scans/{scan_id}`.
- Use query parameters for filtering and pagination: `/scans?status=running&limit=20`.
- All endpoints live under `/api/v1/` for versioning.
- No trailing slashes.

### 5.2 Request/Response Schemas

Use Pydantic v2 models for all request and response schemas. Place them in `cecil/api/schemas.py`.

```python
from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    provider_id: str = Field(description="Identifier of the data provider to scan")
    source: str = Field(description="Path or URI of the data source")
    strategy: RedactionStrategy = Field(default=RedactionStrategy.STRICT)
    output_format: OutputFormat = Field(default=OutputFormat.JSONL)


class ScanResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    created_at: str
    records_processed: int
    records_redacted: int
    errors: list[str]


class ErrorResponse(BaseModel):
    error: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    details: dict[str, str] | None = Field(
        default=None,
        description="Additional context about the error",
    )
```

### 5.3 Error Response Format

All API errors return a consistent JSON structure with the appropriate HTTP status code:

```json
{
  "error": "provider_connection_failed",
  "message": "Could not connect to AWS CloudWatch in us-east-1. Check your credentials.",
  "details": {
    "provider": "aws_cloudwatch",
    "region": "us-east-1"
  }
}
```

HTTP status code mapping:

| Status | Usage                                      |
|--------|--------------------------------------------|
| 200    | Successful read/update                     |
| 201    | Resource created (new scan started)        |
| 400    | Invalid request (bad input, missing fields)|
| 404    | Resource not found                         |
| 409    | Conflict (scan already running)            |
| 422    | Validation error (Pydantic)                |
| 500    | Internal server error                      |

### 5.4 Versioning

API version is embedded in the URL path: `/api/v1/...`. When breaking changes are needed, introduce `/api/v2/` and maintain `/api/v1/` until all clients migrate. Since this is localhost IPC between the CLI and UI shipped in the same binary, version bumps should be coordinated in a single release.

---

## 6. Security Standards

### 6.1 PII Handling Rules

Cecil's core purpose is PII redaction. These rules are non-negotiable:

1. **No PII in logs.** Never log field values, user data, or record content. Log counts, identifiers, and metadata only.
2. **No PII in error messages.** Sanitize error messages before returning them through the API or CLI. If a parsing error includes raw data, strip it.
3. **No PII in telemetry.** The SaaS metadata push must contain only aggregate cost fingerprints (token counts, model identifiers, timestamps). Zero raw content.
4. **Redaction is irreversible.** The sanitization engine must replace sensitive values with non-reversible placeholders (e.g., `[EMAIL_REDACTED]`, `[SSN_REDACTED]`). Never use reversible encoding.
5. **Test with known PII.** Every sanitization test must assert that specific PII strings are absent from the output. Use the "Data Fixture" pattern with fake but realistic PII.

```python
def test_email_is_redacted_from_output(strict_engine, sample_record):
    result = strict_engine.sanitize(sample_record)
    assert "jane.doe@example.com" not in str(result.data)
    assert "[EMAIL_REDACTED]" in result.data["user"]
```

### 6.2 No Secrets in Code

- Never commit API keys, tokens, passwords, or credentials.
- Use environment variables loaded via `cecil/utils/config.py`. Never import `os.environ` directly outside of that module.
- The `.env` file is gitignored. Provide a `.env.example` with placeholder values.
- Use the system keyring (via the `keyring` library) for storing provider credentials persistently.

```python
# cecil/utils/config.py
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CecilConfig:
    aws_region: str = field(default_factory=lambda: os.environ.get("CECIL_AWS_REGION", "us-east-1"))
    log_level: str = field(default_factory=lambda: os.environ.get("CECIL_LOG_LEVEL", "INFO"))
    server_port: int = field(default_factory=lambda: int(os.environ.get("CECIL_PORT", "8787")))
```

### 6.3 CORS Policy

The FastAPI server binds exclusively to `127.0.0.1`. CORS is configured to allow only the local origin:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:*", "http://localhost:*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=False,
)
```

Never add external origins. Never set `allow_origins=["*"]`. The server must refuse connections from non-local origins.

### 6.4 Input Validation

- All API inputs are validated by Pydantic models. Never access raw request bodies.
- File paths provided by users must be resolved and checked to prevent path traversal. Use `Path.resolve()` and verify the resolved path is within an expected directory.
- Provider URIs must be validated against an allowlist of schemes (`file://`, `s3://`, `az://`, `gs://`).
- Set size limits on uploaded data: reject payloads over 100MB at the API layer.

```python
from pathlib import Path

def validate_source_path(raw_path: str, allowed_root: Path) -> Path:
    """Resolve and validate that a source path is within the allowed root."""
    resolved = Path(raw_path).resolve()
    if not resolved.is_relative_to(allowed_root):
        raise ValueError(f"Path {raw_path} is outside the allowed directory")
    if not resolved.exists():
        raise FileNotFoundError(f"Source path does not exist: {resolved}")
    return resolved
```

---

## 7. Documentation

### 7.1 When Comments Are Required

Comments explain **why**, not **what**. If the code needs a comment to explain _what_ it does, refactor the code to be clearer.

**Required comments:**

- Non-obvious business logic or domain rules.
- Performance optimizations that sacrifice readability.
- Workarounds for third-party library bugs (include a link to the issue).
- Security-sensitive decisions (e.g., why a particular redaction approach was chosen).
- `TODO` comments for known technical debt, with an issue number: `# TODO(#42): migrate to async streaming`.

**Do not comment:**

- Self-explanatory code.
- What a standard library function does.
- Closing braces or end-of-block markers.

```python
# Yes: explains a non-obvious constraint
# Presidio's EntityRecognizer does not detect API keys by default.
# We prepend a custom regex recognizer to catch common key patterns
# (e.g., sk-..., AKIA...) before the NLP pass.
engine.add_recognizer(ApiKeyRecognizer())

# No: restates the code
# Initialize the logger
logger = logging.getLogger(__name__)
```

### 7.2 Module-Level Documentation

Every Python module (`.py` file) under `src/cli/` must have a module-level docstring explaining:

1. What the module does (one sentence).
2. Its role within the larger system (one sentence).

```python
"""AWS CloudWatch log provider.

Implements the BaseDataProvider interface for streaming log records
from AWS CloudWatch log groups via the boto3 client.
"""
```

### 7.3 README per Package

Each top-level package directory (`core/providers/`, `core/sanitizer/`, `api/`, `cli/`) should contain a brief README.md only if the package has non-obvious setup steps or architectural decisions. Do not create READMEs that merely restate file names.

### 7.4 Inline Documentation in TypeScript

Use JSDoc comments on exported functions and interfaces only when the type signature alone is insufficient to communicate intent:

```tsx
/**
 * Polls the scan status endpoint until the scan reaches a terminal state.
 * Aborts polling if the provided signal is triggered.
 */
export async function pollStatus(
  scanId: string,
  signal: AbortSignal,
): Promise<ScanStatus> {
  ...
}
```

Do not add JSDoc to component props interfaces; the TypeScript types are the documentation.

---

## 8. Architecture Patterns

### 8.1 Provider Pattern for Data Ingestion

All data sources are abstracted behind the `BaseDataProvider` ABC. This allows the sanitization engine to process data without knowing its origin.

```python
from __future__ import annotations

import abc
from collections.abc import Generator
from typing import Any


class BaseDataProvider(abc.ABC):
    """Abstract base for all data ingestion providers.

    Subclasses must implement connect(), stream_records(), and close().
    The stream_records method must yield records as dictionaries to
    maintain the 50MB memory bound.
    """

    @abc.abstractmethod
    def connect(self) -> None:
        """Establish a connection to the data source."""

    @abc.abstractmethod
    def stream_records(self) -> Generator[dict[str, Any], None, None]:
        """Yield data records one at a time from the source.

        Implementations must not buffer the entire dataset in memory.
        Each yielded record should be a flat or nested dictionary.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Release resources and close the connection."""

    @abc.abstractmethod
    def fetch_metadata(self) -> dict[str, Any]:
        """Return non-sensitive metadata about the data source.

        Metadata may include record count estimates, schema info,
        and source identifiers. Must never include PII.
        """

    def __enter__(self) -> BaseDataProvider:
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
```

New providers are registered in `cecil/core/providers/registry.py`:

```python
PROVIDER_REGISTRY: dict[str, type[BaseDataProvider]] = {
    "local_file": LocalFileProvider,
    "aws_cloudwatch": AWSCloudWatchProvider,
    "azure_monitor": AzureMonitorProvider,
}


def get_provider(provider_id: str, **kwargs: Any) -> BaseDataProvider:
    """Instantiate a provider by its registered identifier."""
    cls = PROVIDER_REGISTRY.get(provider_id)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider_id}")
    return cls(**kwargs)
```

### 8.2 Strategy Pattern for Sanitization

The sanitization engine accepts interchangeable redaction strategies. Each strategy defines what to scan and how to redact.

```python
from __future__ import annotations

import abc


class RedactionStrategy(abc.ABC):
    """Defines rules for detecting and redacting sensitive data."""

    @abc.abstractmethod
    def scan_value(self, key: str, value: str) -> list[Detection]:
        """Scan a single field value for sensitive data."""

    @abc.abstractmethod
    def redact(self, value: str, detections: list[Detection]) -> str:
        """Replace detected sensitive spans with placeholders."""


class StrictStrategy(RedactionStrategy):
    """Keeps only explicitly mapped fields; redacts everything else."""
    ...


class DeepInterceptorStrategy(RedactionStrategy):
    """Recursively inspects nested structures for sensitive key patterns."""
    ...
```

The engine composes providers and strategies:

```python
class SanitizationEngine:
    def __init__(self, strategy: RedactionStrategy) -> None:
        self._strategy = strategy

    def process_stream(
        self,
        records: Generator[dict[str, Any], None, None],
    ) -> Generator[SanitizedRecord, None, None]:
        for record in records:
            yield self._sanitize_record(record)
```

### 8.3 Dependency Injection for Testability

Components receive their dependencies through constructor parameters, not by importing and instantiating them internally. This makes testing with mocks straightforward.

```python
# Yes: injectable dependencies
class ScanCommand:
    def __init__(
        self,
        provider: BaseDataProvider,
        engine: SanitizationEngine,
        output_writer: OutputWriter,
    ) -> None:
        self._provider = provider
        self._engine = engine
        self._writer = output_writer

    def execute(self) -> ScanResult:
        with self._provider:
            stream = self._provider.stream_records()
            sanitized = self._engine.process_stream(stream)
            return self._writer.write(sanitized)


# No: hard-coded dependencies
class ScanCommand:
    def execute(self, source_path: str) -> ScanResult:
        provider = LocalFileProvider(source_path)  # Not injectable
        engine = SanitizationEngine(StrictStrategy())  # Not injectable
        ...
```

In tests, inject mocks or fakes:

```python
def test_scan_command_writes_sanitized_output(tmp_path):
    provider = MockDataProvider(records=[{"user": "test@example.com"}])
    engine = SanitizationEngine(strategy=StrictStrategy())
    writer = OutputWriter(output_dir=tmp_path, fmt=OutputFormat.JSONL)

    command = ScanCommand(provider=provider, engine=engine, output_writer=writer)
    result = command.execute()

    assert result.records_processed == 1
    output_content = (tmp_path / "sanitized.jsonl").read_text()
    assert "test@example.com" not in output_content
```

### 8.4 Streaming and Memory Efficiency

Cecil must handle large datasets without loading them entirely into memory. The hard ceiling is **50MB of resident memory** during a scan.

**Rules:**

1. All data flows through Python generators. Never collect a full dataset into a list.
2. Use `Generator[T, None, None]` as the return type for all streaming methods.
3. Chunk-based reading: file providers read in 8KB chunks; cloud providers paginate API responses.
4. Output writers flush incrementally (e.g., write one JSONL line per record, not the whole file at once).
5. Test memory bounds explicitly using `tracemalloc` in integration tests.

```python
import tracemalloc


def test_stream_10mb_file_stays_under_memory_bound(pii_log_10mb: Path):
    """Verify that processing a 10MB file uses less than 50MB of memory."""
    tracemalloc.start()

    provider = LocalFileProvider(source=str(pii_log_10mb))
    engine = SanitizationEngine(strategy=StrictStrategy())

    with provider:
        for _ in engine.process_stream(provider.stream_records()):
            pass

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < 50 * 1024 * 1024, f"Peak memory {peak / 1024 / 1024:.1f}MB exceeds 50MB bound"
```

**Anti-patterns to avoid:**

```python
# WRONG: loads everything into memory
records = list(provider.stream_records())
sanitized = [engine.sanitize(r) for r in records]

# RIGHT: generator chain
sanitized = engine.process_stream(provider.stream_records())
for record in sanitized:
    writer.write_record(record)
```

#### 8.4.1 Error Recovery in Streams

Use a `StreamErrorPolicy` to control behavior when individual records fail:

```python
from __future__ import annotations

from enum import Enum


class StreamErrorPolicy(Enum):
    SKIP_RECORD = "skip_record"   # Log and skip; continue processing
    ABORT_STREAM = "abort_stream"  # Raise immediately; halt pipeline


class SanitizationEngine:
    def __init__(
        self,
        strategy: RedactionStrategy,
        error_policy: StreamErrorPolicy = StreamErrorPolicy.SKIP_RECORD,
    ) -> None:
        self._strategy = strategy
        self._error_policy = error_policy
        self._error_count = 0

    def process_stream(
        self,
        records: Generator[dict[str, Any], None, None],
    ) -> Generator[SanitizedRecord, None, None]:
        for record in records:
            try:
                yield self._sanitize_record(record)
            except SanitizationError as err:
                self._error_count += 1
                logger.warning("Record sanitization failed", extra={
                    "error": str(err),
                    "error_count": self._error_count,
                })
                if self._error_policy == StreamErrorPolicy.ABORT_STREAM:
                    raise
                # SKIP_RECORD: continue to next record
```

#### 8.4.2 Async Generators for FastAPI Streaming

Use async generators for API endpoints that stream results to the UI:

```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi.responses import StreamingResponse


async def stream_scan_results(
    scan_id: str,
    engine: SanitizationEngine,
    provider: BaseDataProvider,
) -> AsyncGenerator[str, None]:
    """Yield NDJSON lines for streaming to the frontend."""
    with provider:
        for record in engine.process_stream(provider.stream_records()):
            yield json.dumps(record.data) + "\n"


@app.get("/api/v1/scans/{scan_id}/records")
async def get_scan_records(scan_id: str) -> StreamingResponse:
    provider, engine = resolve_scan(scan_id)
    return StreamingResponse(
        stream_scan_results(scan_id, engine, provider),
        media_type="application/x-ndjson",
    )
```

#### 8.4.3 Pagination and Retry for Cloud Providers

Cloud providers must paginate API responses and retry on transient failures:

```python
from __future__ import annotations

import time
from collections.abc import Generator
from typing import Any


class AWSCloudWatchProvider(BaseDataProvider):
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds

    def stream_records(self) -> Generator[dict[str, Any], None, None]:
        next_token: str | None = None

        while True:
            response = self._fetch_page_with_retry(next_token)
            for event in response.get("events", []):
                yield self._normalize_event(event)

            next_token = response.get("nextForwardToken")
            if next_token == response.get("previousToken"):
                break  # No more pages

    def _fetch_page_with_retry(self, token: str | None) -> dict[str, Any]:
        for attempt in range(self.MAX_RETRIES):
            try:
                params: dict[str, Any] = {"logGroupName": self._log_group, "limit": 1000}
                if token:
                    params["nextToken"] = token
                return self._client.filter_log_events(**params)
            except self._client.exceptions.ThrottlingException:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                delay = self.BASE_DELAY * (2 ** attempt)
                logger.warning("Throttled, retrying", extra={"attempt": attempt, "delay": delay})
                time.sleep(delay)
        raise ProviderConnectionError("Max retries exceeded")
```

### 8.5 Safe-Pipe Data Flow Integrity

The Safe-Pipe framework enforces a strict data flow:

```
[Source] -> [Provider] -> [Sanitization Engine] -> [Local Output] -> [Optional: SaaS Metadata Push]
```

**Invariants:**

1. **No raw data leaves the local machine.** The SaaS push receives only the cost fingerprint (token counts, model identifiers, timestamps). This must be enforced at the schema level with a allowlisted set of fields.
2. **Sanitization is mandatory.** There is no code path from a provider to output that bypasses the sanitization engine. The `ScanCommand` class enforces this by requiring both a provider and an engine.
3. **Audit trail.** Every sanitization produces a `RedactionAudit` listing what was detected and where. This audit is available in the UI's Audit View and stored locally.
4. **Policy hash.** The metadata push includes a hash derived from the sanitization rules that were applied. The SaaS backend verifies this hash to confirm the data was actually processed by Cecil.

```python
@dataclass(frozen=True)
class CostFingerprint:
    """The only data structure permitted to leave the local machine."""

    scan_id: str
    total_records: int
    total_tokens: int
    model_breakdown: dict[str, int]     # model_id -> token_count
    time_range_start: str               # ISO 8601
    time_range_end: str                 # ISO 8601
    policy_hash: str                    # SHA-256 of applied sanitization rules

    # This class must NEVER contain:
    # - Raw log content
    # - User identifiers
    # - IP addresses
    # - API keys or credentials
    # - Any field value from the source data
```

#### 8.5.1 Type-Level Enforcement

Use `NewType` to create distinct types for raw vs. sanitized data, preventing accidental mixing at the type-checker level:

```python
from __future__ import annotations

from typing import NewType

RawRecord = NewType("RawRecord", dict[str, Any])
SanitizedData = NewType("SanitizedData", dict[str, Any])


# Functions that accept raw data cannot receive sanitized data and vice versa
def ingest_record(record: RawRecord) -> RawRecord:
    """Provider output — always raw, never passed directly to output."""
    ...


def write_output(data: SanitizedData) -> None:
    """Output writer — only accepts sanitized data."""
    ...


# The sanitization engine is the ONLY bridge between raw and sanitized
def sanitize(record: RawRecord) -> SanitizedData:
    """The only function that converts RawRecord -> SanitizedData."""
    ...
```

#### 8.5.2 Telemetry Gate

A `TelemetryGate` validates the `CostFingerprint` against a deny-list before any network call:

```python
from __future__ import annotations

import re


class TelemetryGate:
    """Validates that outbound telemetry contains no PII before sending."""

    PII_PATTERNS = [
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),  # email
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                              # SSN
        re.compile(r"\b(?:sk-|AKIA)[a-zA-Z0-9]{20,}\b"),                   # API keys
        re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),                        # IPv4
    ]

    def validate(self, fingerprint: CostFingerprint) -> None:
        """Raise if any PII pattern is found in the serialized fingerprint."""
        serialized = json.dumps(fingerprint.__dict__)
        for pattern in self.PII_PATTERNS:
            match = pattern.search(serialized)
            if match:
                raise TelemetryBlockedError(
                    f"PII detected in telemetry payload: pattern={pattern.pattern!r}"
                )
```

#### 8.5.3 Audit Mode Telemetry Blocking

In Audit mode, inject a `NoOpTelemetryClient` that raises if accidentally called:

```python
from __future__ import annotations

import abc


class BaseTelemetryClient(abc.ABC):
    @abc.abstractmethod
    def send_fingerprint(self, fingerprint: CostFingerprint) -> None: ...


class SaaSTelemetryClient(BaseTelemetryClient):
    """Sends cost fingerprints to the SaaS backend."""
    def send_fingerprint(self, fingerprint: CostFingerprint) -> None:
        gate = TelemetryGate()
        gate.validate(fingerprint)
        # ... send to SaaS endpoint


class NoOpTelemetryClient(BaseTelemetryClient):
    """Blocks all telemetry. Used in Audit mode."""
    def send_fingerprint(self, fingerprint: CostFingerprint) -> None:
        raise TelemetryBlockedError(
            "Telemetry is disabled in Audit mode. "
            "This call should never occur — check the execution path."
        )
```

#### 8.5.4 Bypass Prevention

**Rule:** All new data paths MUST flow through `SanitizationEngine.process_stream()`. Never construct output directly from provider records. The `ScanCommand` class is the single orchestration point — all scan workflows must go through it. Any PR that introduces a new path from provider to output without passing through the engine must be rejected.

---

### 8.6 Single-Binary Distribution Patterns

Cecil is distributed as a PyInstaller single-binary. All asset resolution must account for the frozen environment.

#### Resource Path Resolution

```python
# src/cli/cecil/utils/paths.py
from __future__ import annotations

import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Resolve a resource path for both development and PyInstaller environments.

    In development, paths resolve relative to the project root.
    In a frozen PyInstaller binary, paths resolve relative to the
    temporary _MEIPASS directory where bundled assets are extracted.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        # Development: project root is 3 levels up from this file
        base = Path(__file__).resolve().parent.parent.parent
    return base / relative_path
```

#### Forbidden Patterns in Frozen Executables

```python
# WRONG: breaks in PyInstaller — __file__ points to temp extraction dir
config_path = Path(__file__).parent / "config.toml"

# WRONG: dynamic imports may not be bundled
module = importlib.import_module(f"cecil.providers.{name}")

# RIGHT: use get_resource_path for all bundled assets
config_path = get_resource_path("config.toml")

# RIGHT: use the provider registry instead of dynamic imports
provider = get_provider(name)
```

#### Bundled Asset Locations

```python
# NLP models (spaCy/Presidio)
model_path = get_resource_path("models/en_core_web_sm")
nlp = spacy.load(str(model_path))

# React UI build output
ui_dist = get_resource_path("web_dist")
app.mount("/", StaticFiles(directory=str(ui_dist), html=True))
```

#### Testing Frozen Environment

```python
def test_get_resource_path_in_frozen_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Simulate PyInstaller frozen environment."""
    monkeypatch.setattr(sys, "frozen", True)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path))

    result = get_resource_path("models/en_core_web_sm")
    assert result == tmp_path / "models" / "en_core_web_sm"
```

---

### 8.7 Multi-Mode Execution

Cecil supports three execution modes with distinct behaviors:

```python
from __future__ import annotations

from enum import Enum


class ExecutionMode(Enum):
    AI_OPTIMIZATION = "ai_optimization"  # Pre-configured for LLM logs
    GENERIC = "generic"                   # User-defined schemas
    AUDIT = "audit"                       # Forced local, no telemetry
```

#### Mode Selection

```bash
# CLI usage
cecil scan --mode audit --source ./logs.jsonl
cecil scan --mode ai_optimization --source s3://bucket/logs/
cecil scan --mode generic --source ./data.csv --mapping ./schema.json
```

#### Mode-Specific Behavior

| Behavior              | AI-Optimization        | Generic              | Audit                |
|-----------------------|------------------------|----------------------|----------------------|
| Provider auto-detect  | Yes (LLM log patterns) | No (user specifies)  | No (user specifies)  |
| Cost metadata extract | Yes                    | No                   | No                   |
| Telemetry client      | `SaaSTelemetryClient`  | `SaaSTelemetryClient`| `NoOpTelemetryClient`|
| Network calls allowed | Yes (opt-in)           | Yes (opt-in)         | **No — blocked**     |
| Output format default | JSONL                  | Matches input        | JSONL                |

#### Audit Mode Enforcement

```python
from __future__ import annotations


def build_telemetry_client(mode: ExecutionMode) -> BaseTelemetryClient:
    """Factory that enforces Audit mode telemetry blocking."""
    if mode == ExecutionMode.AUDIT:
        return NoOpTelemetryClient()
    return SaaSTelemetryClient()
```

---

### 8.8 IPC and Real-Time Communication

The CLI launches a local FastAPI server for IPC with the bundled React UI.

#### ServerManager Lifecycle

```python
from __future__ import annotations

import signal
import socket

import uvicorn


class ServerManager:
    """Manages the FastAPI server lifecycle for CLI-to-UI communication."""

    def __init__(self) -> None:
        self._port: int | None = None
        self._server: uvicorn.Server | None = None

    def find_available_port(self) -> int:
        """Bind to port 0 to let the OS assign an available port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    def start(self) -> int:
        """Start the server and return the assigned port."""
        self._port = self.find_available_port()
        config = uvicorn.Config(
            app="cecil.api.server:app",
            host="127.0.0.1",
            port=self._port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)

        # Register shutdown on CLI termination
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        self._server.run()
        return self._port

    def _handle_shutdown(self, signum: int, frame: object) -> None:
        """Gracefully stop the server when CLI is killed."""
        if self._server:
            self._server.should_exit = True
```

#### WebSocket for Real-Time Scan Progress

```python
from __future__ import annotations

from fastapi import WebSocket


@app.websocket("/api/v1/scans/{scan_id}/ws")
async def scan_progress(websocket: WebSocket, scan_id: str) -> None:
    """Stream scan progress to the UI in real-time."""
    await websocket.accept()
    try:
        async for progress in scan_registry.subscribe(scan_id):
            await websocket.send_json({
                "records_processed": progress.records_processed,
                "records_redacted": progress.records_redacted,
                "percent_complete": progress.percent_complete,
                "status": progress.status.value,
            })
    finally:
        await websocket.close()
```

#### Health Check Flow

The CLI must verify the server is ready before opening the browser:

```python
from __future__ import annotations

import time

import httpx


def wait_for_server(port: int, timeout: float = 10.0) -> None:
    """Poll the health endpoint until the server responds."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"http://127.0.0.1:{port}/api/v1/health", timeout=1.0)
            if resp.status_code == 200:
                return
        except httpx.ConnectError:
            time.sleep(0.2)
    raise ServerStartupError(f"Server did not start within {timeout}s on port {port}")
```

---

### 8.9 Error Propagation Across Safe-Pipe Stages

Errors are classified by the pipeline stage where they originate:

```python
from __future__ import annotations

# cecil/utils/errors.py — stage-specific hierarchy
class CecilError(Exception):
    """Base exception for all Cecil errors."""

class IngestionError(CecilError):
    """Errors during data ingestion (providers)."""

class ProviderConnectionError(IngestionError):
    """Cannot connect to data source."""

class ProviderReadError(IngestionError):
    """Error reading records from data source."""

class SanitizationError(CecilError):
    """Errors during PII detection or redaction."""

class OutputError(CecilError):
    """Errors writing sanitized output."""

class TelemetryError(CecilError):
    """Errors during SaaS metadata push."""

class TelemetryBlockedError(TelemetryError):
    """Telemetry was blocked by policy (e.g., Audit mode or PII detected)."""
```

#### Partial Failure Handling

Individual record failures do not kill the pipeline. They are logged and counted:

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScanResult:
    records_processed: int = 0
    records_sanitized: int = 0
    records_failed: int = 0
    error_samples: list[str] = field(default_factory=list)

    def record_failure(self, error: str) -> None:
        self.records_failed += 1
        # Keep only first 10 error samples (sanitized — no PII in messages)
        if len(self.error_samples) < 10:
            self.error_samples.append(error)
```

#### Cloud Provider Resilience

Use retry with exponential backoff. Circuit-break after consecutive failures:

```python
from __future__ import annotations


class CircuitBreaker:
    """Halt provider reads after too many consecutive failures."""

    def __init__(self, threshold: int = 5) -> None:
        self._consecutive_failures = 0
        self._threshold = threshold

    def record_success(self) -> None:
        self._consecutive_failures = 0

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._threshold:
            raise ProviderConnectionError(
                f"Circuit breaker tripped after {self._threshold} consecutive failures"
            )
```

---

### 8.10 Configuration Hierarchy

Configuration values are resolved in this precedence order (highest wins):

```
1. CLI arguments          (--mode audit, --output ./out)
2. Environment variables  (CECIL_MODE=audit)
3. Config file            (cecil.toml)
4. Defaults               (hardcoded in CecilConfig)
```

#### Config File Format

```toml
# cecil.toml
[cecil]
mode = "ai_optimization"
output_dir = "./sanitized_output"
log_level = "INFO"

[cecil.sanitizer]
strategy = "deep_interceptor"
custom_patterns = ["ACCT-\\d{8}", "MRN-\\d+"]

[cecil.providers.aws]
region = "us-east-1"
log_group = "/aws/lambda/my-function"

[cecil.providers.local]
default_format = "jsonl"

[cecil.telemetry]
enabled = true
endpoint = "https://api.cecil.dev/v1/fingerprints"
```

#### Configuration Merging

```python
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CecilConfig:
    mode: ExecutionMode = ExecutionMode.AI_OPTIMIZATION
    output_dir: Path = field(default_factory=lambda: Path("./sanitized_output"))
    log_level: str = "INFO"
    server_port: int = 8787

    @classmethod
    def from_sources(
        cls,
        cli_args: dict[str, Any] | None = None,
        config_path: Path | None = None,
    ) -> CecilConfig:
        """Build config by merging sources in precedence order."""
        # Start with defaults
        values: dict[str, Any] = {}

        # Layer 1: config file (lowest precedence after defaults)
        if config_path and config_path.exists():
            with open(config_path, "rb") as f:
                file_config = tomllib.load(f).get("cecil", {})
                values.update(file_config)

        # Layer 2: environment variables
        env_mapping = {
            "CECIL_MODE": "mode",
            "CECIL_OUTPUT_DIR": "output_dir",
            "CECIL_LOG_LEVEL": "log_level",
            "CECIL_PORT": "server_port",
        }
        for env_key, config_key in env_mapping.items():
            env_val = os.environ.get(env_key)
            if env_val is not None:
                values[config_key] = env_val

        # Layer 3: CLI arguments (highest precedence)
        if cli_args:
            values.update({k: v for k, v in cli_args.items() if v is not None})

        return cls(**values)
```

---

### 8.11 Provider Implementation Checklist

Follow these steps when adding a new data provider:

1. **Create the provider file** at `src/cli/cecil/core/providers/<name>.py`

2. **Subclass `BaseDataProvider`** and implement all abstract methods:
   - `connect()` — establish connection, validate credentials
   - `stream_records()` — yield records as dicts via generator
   - `close()` — release resources
   - `fetch_metadata()` — return non-PII metadata

3. **Handle optional dependencies** gracefully:
   ```python
   from __future__ import annotations

   try:
       import boto3
   except ImportError:
       boto3 = None  # type: ignore[assignment]

   class AWSCloudWatchProvider(BaseDataProvider):
       def __init__(self, **kwargs: Any) -> None:
           if boto3 is None:
               raise ProviderDependencyError(
                   "AWS provider requires boto3. Install with: pip install cecil[aws]"
               )
           super().__init__(**kwargs)
   ```

4. **Register in `registry.py`**:
   ```python
   PROVIDER_REGISTRY["my_provider"] = MyProvider
   ```

5. **Add unit tests** in `tests/unit/core/providers/test_<name>.py`

6. **Add integration test** verifying the full provider-to-sanitizer flow

7. **Add memory bound test** — stream 10MB+ and verify <50MB peak memory

8. **Update `cecil.toml` example** with provider-specific config section

9. **Document** any required credentials or setup steps in the provider's module docstring

---

## Appendix: Quick Reference Checklist

Use this checklist before opening a PR:

- [ ] All Python functions have type annotations.
- [ ] `ruff check` and `ruff format --check` pass with zero issues.
- [ ] `mypy --strict` passes.
- [ ] All new public functions have Google-style docstrings.
- [ ] No PII appears in logs, error messages, or test output.
- [ ] Tests follow the `test_<unit>_<scenario>_<expected>` naming pattern.
- [ ] No `print()` statements in production code.
- [ ] No hardcoded secrets, paths, or ports.
- [ ] Streaming methods use generators; no full-dataset `list()` calls.
- [ ] Frontend components use named exports and typed props.
- [ ] Tailwind classes follow the Cecil design token palette.
- [ ] Commit message follows Conventional Commits format.
- [ ] Branch name uses the correct prefix (`feat/`, `fix/`, etc.).
- [ ] Execution mode behavior verified (Audit mode blocks all telemetry).
- [ ] IPC health endpoint responds before UI launch.
- [ ] Safe-Pipe leak assertion: `CostFingerprint` contains no PII.
- [ ] `get_resource_path()` used for all bundled asset access.
- [ ] Configuration follows hierarchy (CLI > env > file > defaults).
- [ ] New providers registered in `registry.py` and follow the implementation checklist.
- [ ] Error propagation follows stage hierarchy (no bare `Exception` catches crossing stage boundaries).
