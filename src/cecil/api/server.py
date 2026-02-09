"""FastAPI IPC server for CLI-to-UI communication.

Provides the local-only FastAPI application, the ServerManager lifecycle
controller, and the health-check client used by the CLI to verify
server readiness before launching the browser.
"""

from __future__ import annotations

import logging
import signal
import socket
import time
import types

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cecil.api.routes.filesystem import router as filesystem_router
from cecil.api.routes.scans import router as scans_router
from cecil.api.schemas import ErrorResponse, HealthResponse
from cecil.utils.errors import ServerStartupError
from cecil.utils.paths import get_ui_dist_path


logger = logging.getLogger(__name__)

_CECIL_VERSION = "0.1.0"


# ── FastAPI application factory ───────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A configured FastAPI instance with CORS middleware and the
        health endpoint registered.
    """
    application = FastAPI(
        title="Cecil IPC Server",
        version=_CECIL_VERSION,
        docs_url=None,
        redoc_url=None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1",
            "http://localhost",
        ],
        allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    @application.get(
        "/api/v1/health",
        response_model=HealthResponse,
        responses={500: {"model": ErrorResponse}},
    )
    async def health() -> HealthResponse:
        """Return server health status."""
        return HealthResponse(status="ok", version=_CECIL_VERSION)

    application.include_router(filesystem_router)
    application.include_router(scans_router)

    # Serve the built React UI.  Static assets (JS, CSS, images) are
    # served from ``/assets/`` by the ``StaticFiles`` mount.  A catch-all
    # route returns ``index.html`` for any other non-API path so that
    # client-side routing (e.g. /ingest, /audit) works correctly.
    try:
        ui_dist = get_ui_dist_path()
        index_html = ui_dist / "index.html"

        # Serve hashed asset bundles produced by Vite.
        assets_dir = ui_dist / "assets"
        if assets_dir.is_dir():
            application.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="ui-assets",
            )

        # SPA catch-all: any path not matched by API routes or /assets
        # returns index.html so React Router handles the route.
        @application.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(request: Request, full_path: str) -> FileResponse:
            """Serve index.html for all unmatched paths (SPA routing)."""
            # If a specific static file exists (e.g. vite.svg), serve it.
            candidate = ui_dist / full_path
            if full_path and candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(index_html))

        logger.info("Serving UI from %s", ui_dist)
    except FileNotFoundError:
        logger.warning(
            "UI assets not found — the web interface will not be available. "
            "Run 'npm run build' in ui/ to build the frontend.",
        )

    return application


app = create_app()


# ── Server lifecycle management ───────────────────────────────────────


class ServerManager:
    """Manages the FastAPI/Uvicorn server lifecycle for CLI-to-UI IPC.

    Handles dynamic port selection, signal-based shutdown, and server
    readiness verification.  The ``start`` method blocks until the
    server exits.
    """

    def __init__(self) -> None:
        self._port: int | None = None
        self._server: uvicorn.Server | None = None

    @property
    def port(self) -> int | None:
        """The port the server is bound to, or ``None`` if not started."""
        return self._port

    def set_port(self, port: int) -> None:
        """Pre-assign a port for the server to bind to.

        When set before :meth:`start`, the server uses this port
        instead of auto-selecting one.

        Args:
            port: The TCP port number to bind to.
        """
        self._port = port

    @staticmethod
    def find_available_port() -> int:
        """Find an available TCP port on the loopback interface.

        Binds to port 0 so the OS assigns an ephemeral port, then
        immediately releases the socket and returns the port number.

        Returns:
            An available port number.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port: int = sock.getsockname()[1]
        logger.info("Found available port", extra={"port": port})
        return port

    def start(self) -> int:
        """Start the Uvicorn server on an available port.

        This method **blocks** until the server shuts down.  Signal
        handlers for ``SIGTERM`` and ``SIGINT`` are installed to enable
        graceful shutdown when the CLI process is killed.

        If ``self._port`` has already been set (e.g. via ``--port``),
        that port is used instead of auto-selecting one.

        Returns:
            The port number the server started on.
        """
        if self._port is None:
            self._port = self.find_available_port()

        config = uvicorn.Config(
            app="cecil.api.server:app",
            host="127.0.0.1",
            port=self._port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)

        # Signal handlers can only be registered from the main thread.
        # When start() runs in a background thread (e.g. ``cecil map``),
        # we skip registration — the main thread handles KeyboardInterrupt
        # and calls shutdown() directly.
        import threading

        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info(
            "Starting IPC server",
            extra={"host": "127.0.0.1", "port": self._port},
        )
        self._server.run()
        return self._port

    def shutdown(self) -> None:
        """Request a graceful server shutdown.

        Safe to call even when no server is running.
        """
        if self._server is not None:
            logger.info("Shutting down IPC server")
            self._server.should_exit = True

    def _handle_shutdown(
        self,
        signum: int,
        frame: types.FrameType | None,
    ) -> None:
        """Signal handler that triggers graceful server shutdown.

        Args:
            signum: The signal number received.
            frame: The current stack frame (unused).
        """
        logger.info(
            "Received shutdown signal",
            extra={"signal": signal.Signals(signum).name},
        )
        self.shutdown()


# ── Health-check client ───────────────────────────────────────────────


def wait_for_server(port: int, timeout: float = 10.0) -> None:
    """Poll the health endpoint until the server responds.

    Used by the CLI to verify the IPC server is ready before opening
    the browser to the mapping UI.

    Args:
        port: The port the server is expected to be listening on.
        timeout: Maximum seconds to wait before giving up.

    Raises:
        ServerStartupError: If the server does not respond within
            the timeout period.
    """
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/api/v1/health"
    logger.info("Waiting for server", extra={"port": port, "timeout": timeout})

    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, timeout=1.0)
            if resp.status_code == 200:
                logger.info("Server is ready", extra={"port": port})
                return
        except httpx.ConnectError:
            time.sleep(0.2)

    raise ServerStartupError(f"Server did not start within {timeout}s on port {port}")
