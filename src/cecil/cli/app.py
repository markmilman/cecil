"""The ``cecil app`` CLI subcommand.

Launches the local FastAPI server and opens the Cecil web UI in the
user's default browser.  The server binds to ``127.0.0.1`` on an
auto-selected port (overridable with ``--port``).

Press Ctrl+C to shut down the server and exit.
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import webbrowser

from cecil.api.server import ServerManager, wait_for_server
from cecil.utils.errors import CecilError


logger = logging.getLogger(__name__)


def register_app_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register the ``app`` subcommand with the CLI argument parser.

    Args:
        subparsers: The subparsers action from the parent
            :class:`argparse.ArgumentParser`.
    """
    parser = subparsers.add_parser(
        "app",
        help="Launch the Cecil web UI for mapping and audit.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the server to (default: auto-select).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        default=False,
        help="Start the server without opening a browser window.",
    )
    parser.set_defaults(func=run_app)


def run_app(args: argparse.Namespace) -> int:
    """Execute the app subcommand.

    Starts the IPC server in a background thread, waits for it to
    become ready, opens the browser, and blocks until the user
    presses Ctrl+C.

    Args:
        args: Parsed CLI arguments from :mod:`argparse`.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    manager = ServerManager()

    if args.port is not None:
        manager.set_port(args.port)
    else:
        manager.set_port(manager.find_available_port())

    port = manager.port
    assert port is not None  # noqa: S101

    server_thread = threading.Thread(
        target=manager.start,
        daemon=True,
        name="cecil-ipc-server",
    )
    server_thread.start()

    try:
        wait_for_server(port)
    except CecilError as err:
        sys.stderr.write(f"Error: {err}\n")
        manager.shutdown()
        server_thread.join(timeout=5.0)
        return 1

    url = f"http://127.0.0.1:{port}"
    sys.stdout.write(f"Cecil is running at {url}\n")
    sys.stdout.write("Press Ctrl+C to stop.\n")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server_thread.join()
    except KeyboardInterrupt:
        sys.stdout.write("\nShutting down...\n")
        manager.shutdown()
        server_thread.join(timeout=5.0)

    return 0
