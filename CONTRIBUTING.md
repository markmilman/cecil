# Contributing to Cecil

## Branching Strategy

All development happens in feature branches off `main`. Direct pushes to `main` are not allowed.

### Branch Naming

Use a category prefix followed by a kebab-case description (under 50 characters total):

| Prefix      | Purpose                                  | Example                            |
|-------------|------------------------------------------|------------------------------------|
| `feat/`     | New features                             | `feat/aws-cloudwatch-provider`     |
| `fix/`      | Bug fixes                                | `fix/sanitizer-ssn-false-positive` |
| `refactor/` | Code restructuring (no behavior change)  | `refactor/provider-streaming`      |
| `docs/`     | Documentation only                       | `docs/api-endpoint-reference`      |
| `test/`     | Adding or improving tests                | `test/sanitizer-edge-cases`        |
| `chore/`    | Tooling, dependencies, CI configuration  | `chore/upgrade-ruff`               |

### Workflow

1. Create a branch from `main` using the naming convention above.
2. Make your changes. Ensure pre-commit hooks pass (ruff + mypy).
3. Write or update tests for any changed behavior.
4. Open a pull request against `main`.
5. PRs require at least one approval and all CI checks passing.
6. PRs are **squash-merged** to maintain a linear history.

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>
```

- **Type**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`
- **Scope**: `providers`, `sanitizer`, `api`, `cli`, `ui`, `build`
- **Subject**: imperative mood, lowercase, no period, under 72 characters
- **Body**: explains *why*, not *what*

Example:

```
feat(providers): add AWS CloudWatch log ingestion

Implements streaming ingestion from CloudWatch log groups using
the boto3 client. Records are yielded in chunks of 1000 to keep
memory under the 50MB bound.

Closes #12
```

## Development Setup

```bash
# Clone and enter the repo
git clone https://github.com/markmilman/cecil.git
cd cecil

# Create a virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Checks

```bash
# Linting and formatting
ruff check src/ tests/
ruff format --check src/ tests/

# Type checking
mypy --strict src/cecil/

# Tests
pytest --cov=cecil --cov-report=term-missing --cov-fail-under=80
```

## Code Style

See [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md) for the full coding standards.
