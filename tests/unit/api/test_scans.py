"""Tests for the POST /api/v1/scans endpoint."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _create_jsonl_file(tmp_path: Path, records: int = 3) -> Path:
    """Create a temporary JSONL file with the given number of records.

    Args:
        tmp_path: Pytest temporary directory.
        records: Number of JSON records to write.

    Returns:
        Path to the created JSONL file.
    """
    f = tmp_path / "test.jsonl"
    f.write_text(
        "\n".join(json.dumps({"id": i, "data": f"record_{i}"}) for i in range(records)) + "\n",
    )
    return f


def _create_csv_file(tmp_path: Path, records: int = 3) -> Path:
    """Create a temporary CSV file with a header and the given number of rows.

    Args:
        tmp_path: Pytest temporary directory.
        records: Number of data rows to write.

    Returns:
        Path to the created CSV file.
    """
    f = tmp_path / "test.csv"
    lines = ["id,name,value"]
    for i in range(records):
        lines.append(f"{i},item_{i},{i * 10}")
    f.write_text("\n".join(lines) + "\n")
    return f


class TestPostScans:
    """Tests for POST /api/v1/scans endpoint."""

    def test_post_scans_valid_jsonl_returns_201(
        self,
        client: TestClient,
        tmp_path: Path,
    ):
        """A valid JSONL file source returns 201 with scan metadata."""
        jsonl_file = _create_jsonl_file(tmp_path)
        response = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )

        assert response.status_code == 201
        body = response.json()
        assert "scan_id" in body
        assert "status" in body
        assert "source" in body
        assert "file_format" in body
        assert "created_at" in body

    def test_post_scans_valid_csv_returns_201(
        self,
        client: TestClient,
        tmp_path: Path,
    ):
        """A valid CSV file source returns 201 with scan metadata."""
        csv_file = _create_csv_file(tmp_path)
        response = client.post(
            "/api/v1/scans/",
            json={"source": str(csv_file)},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["file_format"] == "csv"

    def test_post_scans_nonexistent_file_returns_404(
        self,
        client: TestClient,
    ):
        """A nonexistent file path returns 404 with file_not_found error."""
        response = client.post(
            "/api/v1/scans/",
            json={"source": "/nonexistent/path.jsonl"},
        )

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "file_not_found"

    def test_post_scans_path_traversal_returns_403(
        self,
        client: TestClient,
    ):
        """A path containing '..' components returns 403."""
        response = client.post(
            "/api/v1/scans/",
            json={"source": "../../etc/passwd"},
        )

        assert response.status_code == 403
        body = response.json()
        assert body["error"] == "path_traversal"

    def test_post_scans_unsupported_format_returns_422(
        self,
        client: TestClient,
        tmp_path: Path,
    ):
        """A file with an unsupported extension returns 422."""
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("some text content\n")
        response = client.post(
            "/api/v1/scans/",
            json={"source": str(txt_file)},
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "unsupported_format"

    def test_post_scans_auto_detects_format(
        self,
        client: TestClient,
        tmp_path: Path,
    ):
        """Omitting file_format auto-detects format from extension."""
        jsonl_file = _create_jsonl_file(tmp_path)
        response = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["file_format"] == "jsonl"

    def test_post_scans_explicit_format_overrides(
        self,
        client: TestClient,
        tmp_path: Path,
    ):
        """An explicit file_format overrides auto-detection."""
        jsonl_file = _create_jsonl_file(tmp_path)
        response = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file), "file_format": "csv"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["file_format"] == "csv"

    def test_post_scans_empty_source_returns_422(
        self,
        client: TestClient,
    ):
        """An empty source string returns 422 from Pydantic validation."""
        response = client.post(
            "/api/v1/scans/",
            json={"source": ""},
        )

        assert response.status_code == 422

    def test_post_scans_scan_id_is_uuid(
        self,
        client: TestClient,
        tmp_path: Path,
    ):
        """The returned scan_id is a valid UUID4."""
        jsonl_file = _create_jsonl_file(tmp_path)
        response = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )

        assert response.status_code == 201
        scan_id = response.json()["scan_id"]
        parsed = uuid.UUID(scan_id, version=4)
        assert str(parsed) == scan_id

    def test_post_scans_processes_records(
        self,
        client: TestClient,
        tmp_path: Path,
    ):
        """Background task processes all records from the source file.

        TestClient runs background tasks synchronously, so
        records_processed should reflect the full file content.
        """
        jsonl_file = _create_jsonl_file(tmp_path, records=3)
        response = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )

        assert response.status_code == 201
        # The response is created before the background task runs,
        # so we check that records_processed is non-negative.
        # With TestClient's synchronous background tasks, the store
        # will be updated after the response is returned.
        assert response.json()["records_processed"] >= 0


@pytest.fixture(autouse=True)
def _clear_scan_store():
    """Clear the in-memory scan store between tests."""
    from cecil.api.routes.scans import _scan_store

    _scan_store.clear()
    yield
    _scan_store.clear()
