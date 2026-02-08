"""Fixtures for API unit tests."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cecil.api.server import create_app


@pytest.fixture
def app() -> FastAPI:
    """A fresh FastAPI application instance for each test."""
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """A TestClient bound to the test FastAPI app."""
    return TestClient(app)
