"""Unit tests for the FastAPI IPC server, ServerManager, and health endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cecil.api.schemas import ErrorResponse, HealthResponse
from cecil.api.server import ServerManager, create_app, wait_for_server
from cecil.utils.errors import CecilError, ServerError, ServerStartupError


# ── Health endpoint tests ──────────────────────────────────────────────


class TestHealthEndpoint:
    """Tests for the /api/v1/health endpoint."""

    def test_health_endpoint_returns_200_with_ok_status(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_endpoint_returns_version_string(self, client: TestClient):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_endpoint_response_matches_schema(self, client: TestClient):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert set(data.keys()) == {"status", "version"}
        # Validate it parses into the Pydantic model
        health = HealthResponse(**data)
        assert health.status == "ok"


# ── CORS configuration tests ──────────────────────────────────────────


class TestCorsConfiguration:
    """Tests for CORS middleware configuration."""

    def test_cors_allows_localhost_origin(self, client: TestClient):
        resp = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_allows_127_0_0_1_origin(self, client: TestClient):
        resp = client.get(
            "/api/v1/health",
            headers={"Origin": "http://127.0.0.1:5173"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"

    def test_cors_allows_localhost_without_port(self, client: TestClient):
        resp = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost"},
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost"

    def test_cors_rejects_external_origin(self, client: TestClient):
        resp = client.get(
            "/api/v1/health",
            headers={"Origin": "http://evil.example.com"},
        )
        assert "access-control-allow-origin" not in resp.headers

    def test_cors_preflight_allows_expected_methods(self, client: TestClient):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        allowed = resp.headers.get("access-control-allow-methods", "")
        for method in ("GET", "POST", "PUT", "DELETE"):
            assert method in allowed

    def test_cors_credentials_not_allowed(self, client: TestClient):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-credentials") != "true"


# ── create_app factory tests ──────────────────────────────────────────


class TestCreateApp:
    """Tests for the create_app factory function."""

    def test_create_app_returns_fastapi_instance(self):
        application = create_app()
        assert isinstance(application, FastAPI)

    def test_create_app_has_health_route(self):
        application = create_app()
        paths = [route.path for route in application.routes]  # type: ignore[union-attr]
        assert "/api/v1/health" in paths

    def test_create_app_disables_docs(self):
        application = create_app()
        assert application.docs_url is None
        assert application.redoc_url is None

    def test_create_app_produces_independent_instances(self):
        app1 = create_app()
        app2 = create_app()
        assert app1 is not app2


# ── ServerManager tests ───────────────────────────────────────────────


class TestServerManagerPortSelection:
    """Tests for ServerManager.find_available_port."""

    def test_find_available_port_returns_positive_integer(self):
        port = ServerManager.find_available_port()
        assert isinstance(port, int)
        assert port > 0

    def test_find_available_port_returns_unprivileged_port(self):
        port = ServerManager.find_available_port()
        assert port > 1023

    def test_find_available_port_returns_valid_range(self):
        port = ServerManager.find_available_port()
        assert 1024 <= port <= 65535


class TestServerManagerInit:
    """Tests for ServerManager initialization."""

    def test_port_is_none_before_start(self):
        manager = ServerManager()
        assert manager.port is None

    def test_shutdown_is_safe_before_start(self):
        manager = ServerManager()
        manager.shutdown()  # Should not raise

    def test_shutdown_sets_should_exit_on_server(self):
        manager = ServerManager()
        mock_server = MagicMock()
        manager._server = mock_server
        manager.shutdown()
        assert mock_server.should_exit is True

    def test_handle_shutdown_calls_shutdown(self):
        manager = ServerManager()
        mock_server = MagicMock()
        manager._server = mock_server
        manager._handle_shutdown(15, None)
        assert mock_server.should_exit is True


# ── wait_for_server tests ─────────────────────────────────────────────


class TestWaitForServer:
    """Tests for the wait_for_server health check poller."""

    def test_wait_for_server_raises_on_timeout(self, monkeypatch):
        def mock_get(*args: object, **kwargs: object) -> None:
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(httpx, "get", mock_get)

        with pytest.raises(ServerStartupError, match="did not start within"):
            wait_for_server(port=99999, timeout=0.5)

    def test_wait_for_server_succeeds_after_retries(self, monkeypatch):
        call_count = 0

        def mock_get(*args: object, **kwargs: object) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("not ready yet")
            return httpx.Response(
                200,
                json={"status": "ok", "version": "0.1.0"},
            )

        monkeypatch.setattr(httpx, "get", mock_get)
        wait_for_server(port=12345, timeout=10.0)
        assert call_count == 3

    def test_wait_for_server_succeeds_immediately_on_200(self, monkeypatch):
        def mock_get(*args: object, **kwargs: object) -> httpx.Response:
            return httpx.Response(
                200,
                json={"status": "ok", "version": "0.1.0"},
            )

        monkeypatch.setattr(httpx, "get", mock_get)
        wait_for_server(port=12345, timeout=5.0)  # Should not raise


# ── Schema tests ──────────────────────────────────────────────────────


class TestSchemas:
    """Tests for Pydantic request/response schemas."""

    def test_health_response_serialization(self):
        resp = HealthResponse(status="ok", version="0.1.0")
        data = resp.model_dump()
        assert data == {"status": "ok", "version": "0.1.0"}

    def test_error_response_with_details(self):
        resp = ErrorResponse(
            error="server_error",
            message="Something went wrong",
            details={"hint": "check logs"},
        )
        data = resp.model_dump()
        assert data["error"] == "server_error"
        assert data["details"] == {"hint": "check logs"}

    def test_error_response_details_default_none(self):
        resp = ErrorResponse(error="not_found", message="Resource not found")
        assert resp.details is None


# ── Error hierarchy tests ─────────────────────────────────────────────


class TestServerErrors:
    """Tests for server-related error classes."""

    def test_server_startup_error_is_cecil_error(self):
        assert issubclass(ServerStartupError, CecilError)

    def test_server_startup_error_is_server_error(self):
        assert issubclass(ServerStartupError, ServerError)

    def test_server_error_is_cecil_error(self):
        assert issubclass(ServerError, CecilError)

    def test_server_startup_error_message_preserved(self):
        err = ServerStartupError("port 8080 unavailable")
        assert "port 8080 unavailable" in str(err)
