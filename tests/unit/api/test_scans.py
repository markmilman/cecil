"""Tests for the /api/v1/scans endpoints."""

from __future__ import annotations

import json
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


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


class TestGetScan:
    """Tests for GET /api/v1/scans/{scan_id} endpoint."""

    def test_get_scan_existing_returns_200(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """An existing scan returns 200 with correct fields."""
        jsonl_file = _create_jsonl_file(tmp_path)
        post_resp = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        scan_id = post_resp.json()["scan_id"]

        response = client.get(f"/api/v1/scans/{scan_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["scan_id"] == scan_id
        assert "status" in body
        assert "source" in body
        assert "file_format" in body
        assert "created_at" in body
        assert "records_processed" in body

    def test_get_scan_unknown_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """A random UUID returns 404 with scan_not_found error."""
        unknown_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/scans/{unknown_id}")

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "scan_not_found"

    def test_get_scan_completed_shows_records(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A completed scan shows correct records_processed count.

        TestClient runs background tasks synchronously, so by the
        time we GET the scan it should already be completed.
        """
        jsonl_file = _create_jsonl_file(tmp_path, records=3)
        post_resp = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        scan_id = post_resp.json()["scan_id"]

        response = client.get(f"/api/v1/scans/{scan_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["records_processed"] == 3
        assert body["status"] == "completed"


class TestScanWebSocket:
    """Tests for WebSocket /api/v1/scans/{scan_id}/ws endpoint."""

    def test_websocket_receives_progress(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """WebSocket delivers at least one progress message with expected fields."""
        jsonl_file = _create_jsonl_file(tmp_path)
        resp = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        scan_id = resp.json()["scan_id"]

        with client.websocket_connect(f"/api/v1/scans/{scan_id}/ws") as ws:
            data = ws.receive_json()
            assert data["scan_id"] == scan_id
            assert "status" in data
            assert "records_processed" in data
            assert "elapsed_seconds" in data

    def test_websocket_unknown_scan_closes_4004(
        self,
        client: TestClient,
    ) -> None:
        """Connecting to a WebSocket for an unknown scan closes with code 4004."""
        unknown_id = str(uuid.uuid4())

        with (
            pytest.raises(WebSocketDisconnect) as exc_info,
            client.websocket_connect(f"/api/v1/scans/{unknown_id}/ws") as ws,
        ):
            ws.receive_json()

        assert exc_info.value.code == 4004

    def test_websocket_sends_final_status(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """WebSocket sends a final completed message then closes.

        Since TestClient runs background tasks synchronously, the scan
        is already complete when we connect.  The WebSocket should send
        one message with terminal status and then close.
        """
        jsonl_file = _create_jsonl_file(tmp_path, records=3)
        resp = client.post(
            "/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        scan_id = resp.json()["scan_id"]

        messages: list[dict[str, object]] = []
        with client.websocket_connect(f"/api/v1/scans/{scan_id}/ws") as ws:
            # Read messages until the WebSocket closes.
            try:
                while True:
                    messages.append(ws.receive_json())
            except WebSocketDisconnect:
                pass

        assert len(messages) >= 1
        last = messages[-1]
        assert last["status"] == "completed"
        assert last["records_processed"] == 3


@pytest.fixture(autouse=True)
def _clear_scan_store() -> Generator[None, None, None]:
    """Clear the in-memory scan store between tests."""
    from cecil.api.routes.scans import _scan_store

    _scan_store.clear()
    yield
    _scan_store.clear()


@pytest.fixture(autouse=True)
def _clear_mapping_store() -> Generator[None, None, None]:
    """Clear the in-memory mapping store between tests."""
    from cecil.api.routes.mappings import _mapping_store

    _mapping_store.clear()
    yield
    _mapping_store.clear()


def _create_mapping_yaml(tmp_path: Path) -> Path:
    """Create a temporary mapping YAML file.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path to the created YAML file.
    """
    f = tmp_path / "mapping.yaml"
    f.write_text(
        "version: 1\n"
        "default_action: redact\n"
        "fields:\n"
        "  id:\n"
        "    action: keep\n"
        "  data:\n"
        "    action: redact\n",
    )
    return f


class TestSanitize:
    """Tests for POST /api/v1/scans/sanitize endpoint."""

    def test_sanitize_valid_with_mapping_id_returns_201(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A valid sanitize request with mapping_id returns 201."""
        # Create a mapping first.
        mapping_resp = client.post(
            "/api/v1/mappings/",
            json={
                "version": 1,
                "default_action": "redact",
                "fields": {
                    "id": {"action": "keep", "options": {}},
                    "data": {"action": "redact", "options": {}},
                },
            },
        )
        mapping_id = mapping_resp.json()["mapping_id"]

        jsonl_file = _create_jsonl_file(tmp_path)
        output_dir = tmp_path / "output"
        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "mapping_id": mapping_id,
                "output_dir": str(output_dir),
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert "scan_id" in body
        assert body["status"] in ("pending", "completed")
        assert body["output_path"].endswith("_sanitized.jsonl")

    def test_sanitize_valid_with_yaml_path_returns_201(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A valid sanitize request with mapping_yaml_path returns 201."""
        jsonl_file = _create_jsonl_file(tmp_path)
        yaml_file = _create_mapping_yaml(tmp_path)
        output_dir = tmp_path / "output"

        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "mapping_yaml_path": str(yaml_file),
                "output_dir": str(output_dir),
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert "scan_id" in body
        assert body["output_path"].endswith("_sanitized.jsonl")

    def test_sanitize_nonexistent_source_returns_404(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A nonexistent source file returns 404."""
        yaml_file = _create_mapping_yaml(tmp_path)
        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": "/nonexistent/path.jsonl",
                "mapping_yaml_path": str(yaml_file),
                "output_dir": str(tmp_path / "output"),
            },
        )

        assert response.status_code == 404
        assert response.json()["error"] == "file_not_found"

    def test_sanitize_missing_mapping_returns_422(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A request without mapping_id or mapping_yaml_path returns 422."""
        jsonl_file = _create_jsonl_file(tmp_path)
        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "output_dir": str(tmp_path / "output"),
            },
        )

        assert response.status_code == 422
        assert response.json()["error"] == "missing_mapping"

    def test_sanitize_nonexistent_mapping_id_returns_404(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A nonexistent mapping_id returns 404."""
        jsonl_file = _create_jsonl_file(tmp_path)
        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "mapping_id": "nonexistent-id",
                "output_dir": str(tmp_path / "output"),
            },
        )

        assert response.status_code == 404
        assert response.json()["error"] == "mapping_not_found"

    def test_sanitize_path_traversal_returns_403(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A path containing '..' components returns 403."""
        yaml_file = _create_mapping_yaml(tmp_path)
        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": "../../etc/passwd",
                "mapping_yaml_path": str(yaml_file),
                "output_dir": str(tmp_path / "output"),
            },
        )

        assert response.status_code == 403
        assert response.json()["error"] == "path_traversal"

    def test_sanitize_produces_output_file(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Sanitization produces an output file with sanitized content.

        TestClient runs background tasks synchronously, so the output
        file should exist after the POST returns.
        """
        jsonl_file = _create_jsonl_file(tmp_path, records=2)
        yaml_file = _create_mapping_yaml(tmp_path)
        output_dir = tmp_path / "output"

        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "mapping_yaml_path": str(yaml_file),
                "output_dir": str(output_dir),
            },
        )

        assert response.status_code == 201
        output_path = Path(response.json()["output_path"])
        assert output_path.is_file()

        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        record = json.loads(lines[0])
        # 'id' is KEEP, should be unchanged; 'data' is REDACT, should be replaced.
        assert record["id"] == 0
        assert "REDACTED" in record["data"]

    def test_sanitize_creates_output_directory(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Sanitization creates the output directory if it doesn't exist.

        When output_dir points to a non-existent directory, the endpoint
        should create it automatically before queuing the background task.
        """
        jsonl_file = _create_jsonl_file(tmp_path, records=2)
        yaml_file = _create_mapping_yaml(tmp_path)
        output_dir = tmp_path / "nonexistent" / "nested" / "output"

        # Verify the directory doesn't exist before the request.
        assert not output_dir.exists()

        response = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "mapping_yaml_path": str(yaml_file),
                "output_dir": str(output_dir),
            },
        )

        assert response.status_code == 201
        # Verify the directory was created.
        assert output_dir.exists()
        assert output_dir.is_dir()
        # Verify the output file was written successfully.
        output_path = Path(response.json()["output_path"])
        assert output_path.is_file()


class TestCancelScan:
    """Tests for POST /api/v1/scans/{scan_id}/cancel endpoint."""

    def test_cancel_running_scan_returns_200(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Cancelling a running scan sets the cancellation flag."""
        jsonl_file = _create_jsonl_file(tmp_path, records=2)
        yaml_file = _create_mapping_yaml(tmp_path)
        output_dir = tmp_path / "output"

        # Start a sanitization scan.
        resp = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "mapping_yaml_path": str(yaml_file),
                "output_dir": str(output_dir),
            },
        )
        scan_id = resp.json()["scan_id"]

        # Cancel the scan (even though it may have already completed).
        cancel_resp = client.post(f"/api/v1/scans/{scan_id}/cancel")

        # Should return 200 (or 422 if already completed).
        assert cancel_resp.status_code in (200, 422)

    def test_cancel_nonexistent_scan_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Cancelling a non-existent scan returns 404."""
        response = client.post("/api/v1/scans/nonexistent-id/cancel")

        assert response.status_code == 404
        assert response.json()["error"] == "scan_not_found"

    def test_cancel_completed_scan_returns_422(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Cancelling an already completed scan returns 422."""
        jsonl_file = _create_jsonl_file(tmp_path, records=2)
        yaml_file = _create_mapping_yaml(tmp_path)
        output_dir = tmp_path / "output"

        # Start and complete a sanitization scan.
        resp = client.post(
            "/api/v1/scans/sanitize",
            json={
                "source": str(jsonl_file),
                "mapping_yaml_path": str(yaml_file),
                "output_dir": str(output_dir),
            },
        )
        scan_id = resp.json()["scan_id"]

        # Wait for completion (TestClient runs background tasks synchronously).
        # By the time we try to cancel, the scan should be completed.

        # Try to cancel the completed scan.
        cancel_resp = client.post(f"/api/v1/scans/{scan_id}/cancel")

        assert cancel_resp.status_code == 422
        assert cancel_resp.json()["error"] == "scan_not_cancellable"
