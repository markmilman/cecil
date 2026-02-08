"""Cecil API — FastAPI IPC server and schemas."""

from __future__ import annotations

from cecil.api.schemas import ErrorResponse, HealthResponse
from cecil.api.server import ServerManager, create_app, wait_for_server


__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "ServerManager",
    "create_app",
    "wait_for_server",
]
