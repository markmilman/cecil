"""Shared fixtures for E2E tests.

Provides server lifecycle management, browser context setup for
Playwright, and API client helpers.  Browser-based tests are skipped
when Playwright browsers are not installed or the React frontend has
not been built.
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Generator
from typing import Any

import pytest


# ── Utility helpers ───────────────────────────────────────────────────


def _find_available_port() -> int:
    """Find an available TCP port on the loopback interface.

    Returns:
        An available port number assigned by the OS.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _server_is_available() -> bool:
    """Check whether the FastAPI server module is importable.

    The server module (``cecil.api.server``) may not yet exist on
    ``main`` if the API PR has not been merged.

    Returns:
        True if the server module can be imported.
    """
    try:
        import cecil.api.server  # noqa: F401

        return True
    except (ImportError, ModuleNotFoundError):
        return False


# ── Conditional skip helpers ──────────────────────────────────────────


def _playwright_browsers_installed() -> bool:
    """Check whether Playwright browser binaries are installed.

    Returns:
        True if at least Chromium can be launched.
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False


def _ui_is_built() -> bool:
    """Check whether the React frontend has been built.

    Looks for the ``ui/dist/index.html`` file that Vite produces.

    Returns:
        True if the built frontend assets exist.
    """
    from pathlib import Path

    ui_dist = Path(__file__).resolve().parents[2] / "ui" / "dist" / "index.html"
    return ui_dist.exists()


# ── Pytest markers ────────────────────────────────────────────────────


requires_server = pytest.mark.skipif(
    not _server_is_available(),
    reason="FastAPI server module (cecil.api.server) not available",
)

requires_playwright = pytest.mark.skipif(
    not _playwright_browsers_installed(),
    reason="Playwright browsers not installed (run 'playwright install')",
)

requires_ui = pytest.mark.skipif(
    not _ui_is_built(),
    reason="React frontend not built (run 'npm run build' in ui/)",
)


# ── Server fixtures ──────────────────────────────────────────────────


@pytest.fixture(scope="session")
def e2e_server_port() -> Generator[int, None, None]:
    """Start a FastAPI test server in a background thread.

    Yields the port number the server is listening on.  Shuts down
    the server when the test session ends.

    Yields:
        The TCP port the test server is bound to.
    """
    if not _server_is_available():
        pytest.skip("FastAPI server module not available")

    import uvicorn

    from cecil.api.server import create_app

    port = _find_available_port()
    app = create_app()

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for the server to become ready
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.1)
    else:
        pytest.fail(f"E2E server did not start within 10s on port {port}")

    yield port

    server.should_exit = True
    thread.join(timeout=5.0)


@pytest.fixture()
def api_base_url(e2e_server_port: int) -> str:
    """Return the base URL for API requests against the test server.

    Args:
        e2e_server_port: The port from the session-scoped server fixture.

    Returns:
        The full base URL including scheme, host, and port.
    """
    return f"http://127.0.0.1:{e2e_server_port}"


# ── Playwright fixtures ──────────────────────────────────────────────


@pytest.fixture(scope="session")
def browser_context_args() -> dict[str, Any]:
    """Override default Playwright browser context arguments.

    Returns:
        A dictionary of context options for Playwright.
    """
    return {
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }
