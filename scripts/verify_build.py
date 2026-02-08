"""Post-build verification script for the Cecil binary.

Performs smoke tests on a built ``ai-sanitizer`` binary to confirm that
it was packaged correctly and can start up:

  1. Checks the binary exists in ``dist/``.
  2. Runs the binary with ``--help`` and verifies exit code 0.
  3. Reports file size and basic metadata.

Usage:
    python scripts/verify_build.py [--binary PATH]

This script is intended to run after ``python scripts/build.py`` completes,
or in CI as a post-merge verification step.
"""

from __future__ import annotations

import argparse
import logging
import platform
import subprocess
import sys
from pathlib import Path


# ── Constants ─────────────────────────────────────────────────────────────

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_BINARY_NAME: str = "ai-sanitizer.exe" if platform.system() == "Windows" else "ai-sanitizer"
DEFAULT_BINARY_PATH: Path = PROJECT_ROOT / "dist" / DEFAULT_BINARY_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Verification steps ───────────────────────────────────────────────────


def verify_binary_exists(binary_path: Path) -> bool:
    """Check that the built binary file exists on disk.

    Args:
        binary_path: Path to the expected binary.

    Returns:
        True if the binary exists, False otherwise.
    """
    if not binary_path.exists():
        logger.error("Binary not found: %s", binary_path)
        return False

    size_mb = binary_path.stat().st_size / (1024 * 1024)
    logger.info("Binary found: %s (%.1f MB)", binary_path, size_mb)
    return True


def verify_help_flag(binary_path: Path) -> bool:
    """Run the binary with --help and verify it exits cleanly.

    Args:
        binary_path: Path to the binary to test.

    Returns:
        True if the binary exits with code 0, False otherwise.
    """
    logger.info("Running: %s --help", binary_path.name)

    try:
        result = subprocess.run(
            [str(binary_path), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        logger.error("Binary timed out after 30 seconds on --help")
        return False

    if result.returncode != 0:
        logger.error(
            "--help exited with code %d\nstdout: %s\nstderr: %s",
            result.returncode,
            result.stdout[:500],
            result.stderr[:500],
        )
        return False

    output_lines = result.stdout.strip().splitlines()
    logger.info("--help output (%d lines):", len(output_lines))
    for line in output_lines[:10]:
        logger.info("  %s", line)
    if len(output_lines) > 10:
        logger.info("  ... (%d more lines)", len(output_lines) - 10)

    return True


def verify_binary_metadata(binary_path: Path) -> None:
    """Log metadata about the built binary for diagnostics.

    Args:
        binary_path: Path to the binary to inspect.
    """
    stat = binary_path.stat()
    logger.info("Binary metadata:")
    logger.info("  Size: %.1f MB", stat.st_size / (1024 * 1024))
    logger.info("  Platform: %s", platform.system())
    logger.info("  Architecture: %s", platform.machine())

    # Check if the binary is executable (Unix-only).
    if platform.system() != "Windows":
        import stat as stat_module

        mode = stat.st_mode
        is_executable = bool(mode & stat_module.S_IXUSR)
        logger.info("  Executable: %s", is_executable)
        if not is_executable:
            logger.warning("Binary is not marked as executable. Run: chmod +x %s", binary_path)


# ── Main ──────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the verification script.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Verify a built Cecil (ai-sanitizer) binary",
    )
    parser.add_argument(
        "--binary",
        type=Path,
        default=DEFAULT_BINARY_PATH,
        help=f"Path to the binary to verify (default: {DEFAULT_BINARY_PATH})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run all verification checks against the binary.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).
    """
    args = parse_args(argv)
    binary_path: Path = args.binary

    logger.info("Cecil Build Verification")
    logger.info("Binary: %s", binary_path)

    checks_passed = 0
    checks_total = 2

    if verify_binary_exists(binary_path):
        checks_passed += 1
        verify_binary_metadata(binary_path)
    else:
        logger.error("Cannot proceed without binary. Build first: python scripts/build.py")
        sys.exit(1)

    if verify_help_flag(binary_path):
        checks_passed += 1

    logger.info("Verification: %d/%d checks passed", checks_passed, checks_total)

    if checks_passed < checks_total:
        logger.error("Build verification FAILED")
        sys.exit(1)

    logger.info("Build verification PASSED")


if __name__ == "__main__":
    main()
