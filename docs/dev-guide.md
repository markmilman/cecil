# Development Guide

## Prerequisites

- **Python 3.11+** — macOS ships with an older Python. Install via Homebrew:
  ```bash
  brew install python@3.11
  ```
  Then use `python3.11` instead of `python3` for all commands below.
- **Node.js** (with npm)
- **Git**

## Initial Setup

```bash
# Clone and enter the project
git clone <repo-url> && cd cecil

# Install Python package in editable mode with dev dependencies
python3.11 -m pip install -e ".[dev]"

# Install frontend dependencies
cd ui && npm install && cd ..
```

## Running the Dev Environment

### Frontend (React UI)

```bash
cd ui && npm run dev
```

Opens a Vite dev server at **http://localhost:5173/** with hot module replacement — edits to `.tsx`, `.ts`, and `.css` files under `ui/src/` reflect instantly in the browser.

### Backend (FastAPI)

```bash
uvicorn cecil.api:app --host 127.0.0.1 --port 4921 --reload
```

The `--reload` flag watches for Python file changes and restarts automatically.

### Full Stack

Run both commands in separate terminals. The Vite dev server proxies API requests to the FastAPI backend on `127.0.0.1:4921`.

## Linting and Type Checking

```bash
# Python
ruff check src/ tests/
ruff format --check src/ tests/
mypy --strict src/cecil/

# Frontend
cd ui && npm run lint
```

## Running Tests

```bash
# Python tests with coverage
pytest --cov=cecil --cov-report=term-missing --cov-fail-under=80

# Frontend tests
cd ui && npm test
```

## Building for Distribution

Cecil ships as a single binary that bundles the Python CLI, FastAPI backend, React UI, and NLP models via PyInstaller.

### Full Build

```bash
# Install build dependencies (PyInstaller)
python3.11 -m pip install -e ".[build]"

# Run the build orchestrator
python3.11 scripts/build.py
```

This executes two stages:

1. **Frontend build** — runs `npm run build` in `ui/`, outputting static assets to `src/cecil/ui_dist/`
2. **PyInstaller packaging** — bundles everything into a single binary using `cecil.spec`, output goes to `dist/`

### Build Options

```bash
# Skip the frontend build (use existing ui_dist)
python scripts/build.py --skip-frontend

# Skip PyInstaller (only build the frontend)
python scripts/build.py --skip-pyinstaller
```

### Build Output

The final binary is written to `dist/`. It includes:

- Python CLI and FastAPI server
- Compiled React UI (from `src/cecil/ui_dist/`)
- Presidio NLP models for PII detection

The binary resolves bundled assets at runtime via `cecil/utils/paths.py:get_resource_path()`, which handles the difference between development paths and PyInstaller's `_MEIPASS` temp directory.
