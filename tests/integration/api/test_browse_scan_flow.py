"""Integration tests for the browse → scan flow.

Verifies that files discovered via the filesystem browse endpoint can
be successfully used with the scan creation endpoint.  Tests the full
workflow from directory browsing to scan completion.
"""

from __future__ import annotations

import json
from pathlib import Path

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


@pytest.fixture(autouse=True)
def _clear_scan_store() -> None:
    """Clear the in-memory scan store between tests."""
    from cecil.api.routes.scans import _scan_store

    _scan_store.clear()
    yield  # type: ignore[misc]
    _scan_store.clear()


class TestBrowseThenScan:
    """Integration tests for browsing a directory then scanning a discovered file."""

    def test_browse_directory_then_scan_jsonl_file(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Browse a directory, pick a JSONL file, then create a scan for it."""
        # Create test data.
        jsonl_file = tmp_path / "data.jsonl"
        jsonl_file.write_text(
            "\n".join(json.dumps({"id": i, "value": f"row_{i}"}) for i in range(5)) + "\n",
        )

        # Step 1: Browse the directory.
        browse_resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(tmp_path)},
        )
        assert browse_resp.status_code == 200
        browse_data = browse_resp.json()
        assert browse_data["error"] is None

        # Verify the file appears in browse results.
        file_names = [f["name"] for f in browse_data["files"]]
        assert "data.jsonl" in file_names

        # Get the file's details from browse results.
        file_entry = next(f for f in browse_data["files"] if f["name"] == "data.jsonl")
        assert file_entry["format"] == "jsonl"
        assert file_entry["is_directory"] is False
        assert file_entry["size"] is not None

        # Step 2: Create a scan using the discovered file path.
        scan_resp = client.post(
            "/api/v1/scans/",
            json={"source": file_entry["path"], "file_format": file_entry["format"]},
        )
        assert scan_resp.status_code == 201
        scan_data = scan_resp.json()
        scan_id = scan_data["scan_id"]
        assert scan_data["file_format"] == "jsonl"

        # Step 3: Verify scan completed (TestClient runs tasks synchronously).
        get_resp = client.get(f"/api/v1/scans/{scan_id}")
        assert get_resp.status_code == 200
        result = get_resp.json()
        assert result["status"] == "completed"
        assert result["records_processed"] == 5

    def test_browse_directory_then_scan_csv_file(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Browse a directory, pick a CSV file, then create a scan for it."""
        csv_file = tmp_path / "report.csv"
        csv_file.write_text("id,name,score\n1,Alice,95\n2,Bob,87\n3,Carol,92\n")

        # Browse.
        browse_resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(tmp_path)},
        )
        browse_data = browse_resp.json()
        file_entry = next(f for f in browse_data["files"] if f["name"] == "report.csv")
        assert file_entry["format"] == "csv"

        # Scan.
        scan_resp = client.post(
            "/api/v1/scans/",
            json={"source": file_entry["path"]},
        )
        assert scan_resp.status_code == 201
        scan_id = scan_resp.json()["scan_id"]

        # Verify completion.
        result = client.get(f"/api/v1/scans/{scan_id}").json()
        assert result["status"] == "completed"
        assert result["records_processed"] == 3

    def test_browse_filtered_hides_unsupported_files(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Unsupported file types are hidden from browse results and cannot be scanned."""
        (tmp_path / "valid.jsonl").write_text('{"a": 1}\n')
        (tmp_path / "invalid.txt").write_text("plain text\n")
        (tmp_path / "readme.md").write_text("# Readme\n")

        # Browse with default filter.
        browse_resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(tmp_path)},
        )
        file_names = [f["name"] for f in browse_resp.json()["files"]]
        assert "valid.jsonl" in file_names
        assert "invalid.txt" not in file_names
        assert "readme.md" not in file_names

        # Attempt to scan the unsupported file directly.
        scan_resp = client.post(
            "/api/v1/scans/",
            json={"source": str(tmp_path / "invalid.txt")},
        )
        assert scan_resp.status_code == 422

    def test_browse_subdirectory_navigation_then_scan(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Navigate into a subdirectory via browse, then scan a file found there."""
        # Create nested structure.
        subdir = tmp_path / "project" / "data"
        subdir.mkdir(parents=True)
        jsonl_file = subdir / "records.jsonl"
        jsonl_file.write_text(
            "\n".join(json.dumps({"x": i}) for i in range(3)) + "\n",
        )

        # Browse root, find subdirectory.
        root_resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(tmp_path)},
        )
        dir_names = [d["name"] for d in root_resp.json()["directories"]]
        assert "project" in dir_names

        # Navigate into "project".
        project_resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(tmp_path / "project")},
        )
        dir_names = [d["name"] for d in project_resp.json()["directories"]]
        assert "data" in dir_names

        # Navigate into "data".
        data_resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(subdir)},
        )
        data_data = data_resp.json()
        file_entry = next(f for f in data_data["files"] if f["name"] == "records.jsonl")
        assert data_data["parent_path"] == str(tmp_path / "project")

        # Scan the discovered file.
        scan_resp = client.post(
            "/api/v1/scans/",
            json={"source": file_entry["path"]},
        )
        assert scan_resp.status_code == 201
        result = client.get(f"/api/v1/scans/{scan_resp.json()['scan_id']}").json()
        assert result["status"] == "completed"
        assert result["records_processed"] == 3

    def test_browse_path_traversal_cannot_reach_scan(
        self,
        client: TestClient,
    ) -> None:
        """Path traversal in browse returns an error, cannot reach scan endpoint."""
        browse_resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": "/tmp/../etc"},  # noqa: S108
        )
        browse_data = browse_resp.json()
        assert browse_data["error"] == "Path traversal is not allowed"
        assert browse_data["files"] == []

        # Even directly, scan blocks path traversal.
        scan_resp = client.post(
            "/api/v1/scans/",
            json={"source": "/tmp/../etc/passwd"},  # noqa: S108
        )
        assert scan_resp.status_code == 403
