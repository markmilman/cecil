"""Shared fixtures for integration tests.

Provides FastAPI test client and test isolation for integration testing
across API endpoints and background task execution.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cecil.api.server import create_app


@pytest.fixture
def app() -> FastAPI:
    """A fresh FastAPI application instance for each test.

    Returns:
        A configured FastAPI application.
    """
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """A TestClient bound to the test FastAPI app.

    Args:
        app: The FastAPI application fixture.

    Returns:
        A TestClient instance that runs background tasks synchronously.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_stores() -> Generator[None, None, None]:
    """Clear in-memory stores between tests for isolation.

    This fixture runs automatically for all integration tests and ensures
    that the mapping and scan stores are empty at the start of each test.
    """
    from cecil.api.routes.mappings import _mapping_store
    from cecil.api.routes.scans import _scan_store

    _mapping_store.clear()
    _scan_store.clear()
    yield
    _mapping_store.clear()
    _scan_store.clear()
