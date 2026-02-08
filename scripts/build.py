"""Cecil single-binary build orchestrator.

Orchestrates the full build pipeline:
  1. Build the React frontend (``npm run build`` in ``ui/``).
  2. Verify the UI distribution output exists in ``src/cecil/ui_dist/``.
  3. Invoke PyInstaller with ``cecil.spec`` to produce the signed binary.

Usage:
    python scripts/build.py [--skip-frontend] [--skip-pyinstaller]

Exit codes:
    0  Build succeeded.
    1  Build failed (check stderr for details).
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path


# ── Constants ─────────────────────────────────────────────────────────────

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
UI_DIR: Path = PROJECT_ROOT / "ui"
UI_DIST_DIR: Path = PROJECT_ROOT / "src" / "cecil" / "ui_dist"
SPEC_FILE: Path = PROJECT_ROOT / "cecil.spec"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    label: str = "",
) -> None:
    """Run a subprocess command and raise on failure.

    Args:
        cmd: Command and arguments to execute.
        cwd: Working directory for the subprocess.
        label: Human-readable label for log messages.

    Raises:
        SystemExit: If the subprocess exits with a non-zero return code.
    """
    display = label or " ".join(cmd)
    logger.info("Running: %s", display)

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        for line in result.stdout.strip().splitlines():
            logger.info("  %s", line)
    if result.stderr:
        for line in result.stderr.strip().splitlines():
            logger.warning("  %s", line)

    if result.returncode != 0:
        logger.error("%s failed with exit code %d", display, result.returncode)
        sys.exit(1)


def _clean_ui_dist() -> None:
    """Remove previous UI build artifacts from ``src/cecil/ui_dist/``.

    This ensures stale files from a prior build do not contaminate the
    new bundle.
    """
    if UI_DIST_DIR.exists():
        logger.info("Cleaning previous UI build: %s", UI_DIST_DIR)
        shutil.rmtree(UI_DIST_DIR)


def _find_npm() -> str:
    """Locate the npm executable on the system PATH.

    Returns:
        The absolute path to the npm binary.

    Raises:
        SystemExit: If npm is not found.
    """
    npm_path = shutil.which("npm")
    if npm_path is None:
        logger.error("npm not found on PATH. Install Node.js to build the frontend.")
        sys.exit(1)
    return npm_path


# ── Build stages ──────────────────────────────────────────────────────────


def build_frontend() -> None:
    """Build the React frontend and verify output.

    Runs ``npm run build`` in the ``ui/`` directory.  The Vite config is
    expected to output to ``src/cecil/ui_dist/``.

    Raises:
        SystemExit: If the frontend build fails or the output directory
            is missing.
    """
    if not UI_DIR.exists():
        logger.error("Frontend directory not found: %s", UI_DIR)
        sys.exit(1)

    npm = _find_npm()

    # Install dependencies if node_modules is missing.
    node_modules = UI_DIR / "node_modules"
    if not node_modules.exists():
        logger.info("node_modules not found; running npm install.")
        _run([npm, "install"], cwd=UI_DIR, label="npm install")

    # Clean stale build output.
    _clean_ui_dist()

    # Build the frontend.
    _run([npm, "run", "build"], cwd=UI_DIR, label="npm run build")

    # Verify output.
    if not UI_DIST_DIR.exists():
        logger.error(
            "Frontend build did not produce expected output at %s",
            UI_DIST_DIR,
        )
        sys.exit(1)

    index_html = UI_DIST_DIR / "index.html"
    if not index_html.exists():
        logger.error("index.html not found in %s", UI_DIST_DIR)
        sys.exit(1)

    file_count = sum(1 for _ in UI_DIST_DIR.rglob("*") if _.is_file())
    logger.info("Frontend build complete: %d files in %s", file_count, UI_DIST_DIR)


def build_pyinstaller() -> None:
    """Invoke PyInstaller using the spec file to produce the binary.

    Raises:
        SystemExit: If the spec file is missing or PyInstaller fails.
    """
    if not SPEC_FILE.exists():
        logger.error("PyInstaller spec file not found: %s", SPEC_FILE)
        sys.exit(1)

    # Verify PyInstaller is importable.
    pyinstaller_path = shutil.which("pyinstaller")
    if pyinstaller_path is None:
        logger.error("PyInstaller not found. Install with: pip install 'cecil[build]'")
        sys.exit(1)

    _run(
        [pyinstaller_path, str(SPEC_FILE), "--noconfirm", "--clean"],
        cwd=PROJECT_ROOT,
        label="pyinstaller cecil.spec",
    )

    # Check for output binary.
    dist_dir = PROJECT_ROOT / "dist"
    if not dist_dir.exists():
        logger.error("PyInstaller did not create dist/ directory.")
        sys.exit(1)

    binaries = list(dist_dir.iterdir())
    if not binaries:
        logger.error("No output files found in dist/")
        sys.exit(1)

    for binary in binaries:
        logger.info("Built: %s (%d bytes)", binary.name, binary.stat().st_size)

    logger.info("Build complete. Binary available in %s", dist_dir)


# ── Main ──────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the build orchestrator.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Cecil single-binary build orchestrator",
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Skip the React frontend build step",
    )
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Skip the PyInstaller packaging step",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run the full build pipeline.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).
    """
    args = parse_args(argv)

    logger.info("Cecil Build Orchestrator")
    logger.info("Project root: %s", PROJECT_ROOT)

    if not args.skip_frontend:
        build_frontend()
    else:
        logger.info("Skipping frontend build (--skip-frontend)")

    if not args.skip_pyinstaller:
        build_pyinstaller()
    else:
        logger.info("Skipping PyInstaller packaging (--skip-pyinstaller)")

    logger.info("All build stages completed successfully.")


if __name__ == "__main__":
    main()
