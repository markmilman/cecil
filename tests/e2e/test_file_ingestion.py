"""E2E tests for the file ingestion flow.

Verifies the complete ingestion pipeline from scan creation through
progress tracking to completion, using the same API endpoints the
React frontend calls.

Tests use ``httpx`` against the real FastAPI server started by the
``e2e_server_port`` session fixture.  Browser-based Playwright tests
for accessibility and keyboard navigation are marked with
``requires_playwright`` and ``requires_ui`` so they skip gracefully
when those dependencies are not available.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
import pytest

from tests.e2e.conftest import requires_server
from tests.fixtures.pii_samples import (
    all_known_pii_values,
    generate_sample_csv,
    generate_sample_jsonl,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _assert_no_pii_in_text(text: str, pii_values: list[str]) -> None:
    """Assert that none of the known PII values appear in *text*.

    Args:
        text: The serialized text to scan for PII leaks.
        pii_values: The list of PII strings that must be absent.

    Raises:
        AssertionError: If any PII value is found in the text.
    """
    for value in pii_values:
        assert value not in text, f"PII LEAK DETECTED: '{value}' found in output."


def _wait_for_scan_completion(
    base_url: str,
    scan_id: str,
    *,
    timeout: float = 10.0,
) -> dict:
    """Poll ``GET /api/v1/scans/{scan_id}`` until the scan finishes.

    Args:
        base_url: The scheme + host + port of the test server.
        scan_id: The UUID of the scan to monitor.
        timeout: Maximum seconds to wait before raising.

    Returns:
        The JSON body of the final scan status response.

    Raises:
        TimeoutError: If the scan does not reach a terminal state
            within *timeout* seconds.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = httpx.get(f"{base_url}/api/v1/scans/{scan_id}")
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        time.sleep(0.3)
    raise TimeoutError(f"Scan {scan_id} did not complete within {timeout}s")


# ── Happy-path tests ────────────────────────────────────────────────


@requires_server
@pytest.mark.e2e
class TestFileIngestionHappyPath:
    """Verify the complete happy-path ingestion flow."""

    def test_ingest_jsonl_completes_successfully(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Ingest a JSONL file and verify the scan completes with correct count."""
        jsonl_file = tmp_path / "test_data.jsonl"
        records = [{"id": i, "msg": f"record_{i}"} for i in range(5)]
        jsonl_file.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n",
        )

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["file_format"] == "jsonl"
        scan_id = body["scan_id"]

        result = _wait_for_scan_completion(api_base_url, scan_id)
        assert result["status"] == "completed"
        assert result["records_processed"] == 5
        assert result["errors"] == []

    def test_ingest_csv_completes_successfully(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Ingest a CSV file and verify the scan completes."""
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(
            "id,name,value\n1,alpha,100\n2,beta,200\n3,gamma,300\n",
        )

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(csv_file)},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["file_format"] == "csv"
        scan_id = body["scan_id"]

        result = _wait_for_scan_completion(api_base_url, scan_id)
        assert result["status"] == "completed"
        assert result["records_processed"] == 3

    def test_auto_detect_format_from_extension(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify format is auto-detected from the file extension."""
        jsonl_file = tmp_path / "auto.jsonl"
        jsonl_file.write_text('{"key": "value"}\n')

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        assert resp.status_code == 201
        assert resp.json()["file_format"] == "jsonl"

    def test_explicit_format_overrides_extension(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify explicit format takes precedence over the extension."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b,c\n1,2,3\n")

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(csv_file), "file_format": "csv"},
        )
        assert resp.status_code == 201
        assert resp.json()["file_format"] == "csv"

    def test_scan_response_contains_required_fields(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify the scan creation response includes all expected fields."""
        jsonl_file = tmp_path / "fields.jsonl"
        jsonl_file.write_text('{"k": 1}\n')

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        assert resp.status_code == 201
        body = resp.json()

        required_keys = {
            "scan_id",
            "status",
            "source",
            "file_format",
            "created_at",
            "records_processed",
            "records_redacted",
            "errors",
        }
        assert required_keys <= set(body.keys()), (
            f"Missing fields: {required_keys - set(body.keys())}"
        )


# ── Error-path tests ────────────────────────────────────────────────


@requires_server
@pytest.mark.e2e
class TestFileIngestionErrors:
    """Verify error handling for invalid inputs."""

    def test_nonexistent_file_returns_404(
        self,
        api_base_url: str,
    ) -> None:
        """Verify 404 for a file that does not exist."""
        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": "/nonexistent/path/to/file.jsonl"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"] == "file_not_found"

    def test_unsupported_format_returns_422(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify 422 for a file with an unsupported extension."""
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("some text content\n")

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(txt_file)},
        )
        assert resp.status_code == 422
        assert resp.json()["error"] == "unsupported_format"

    def test_path_traversal_returns_403(
        self,
        api_base_url: str,
    ) -> None:
        """Verify 403 for path traversal attempts."""
        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": "../../etc/passwd"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"] == "path_traversal"

    def test_empty_source_returns_422(
        self,
        api_base_url: str,
    ) -> None:
        """Verify 422 for an empty source string."""
        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": ""},
        )
        assert resp.status_code == 422

    def test_empty_file_scan_fails_gracefully(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify that an empty file causes the scan to fail.

        The LocalFileProvider rejects zero-byte files during connect(),
        so the background task should transition to ``failed`` status.
        """
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("")

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(empty_file)},
        )
        # The file exists but is empty, so scan creation succeeds but
        # the background task will fail during provider.connect().
        assert resp.status_code == 201
        scan_id = resp.json()["scan_id"]

        result = _wait_for_scan_completion(api_base_url, scan_id)
        assert result["status"] == "failed"

    def test_missing_source_field_returns_422(
        self,
        api_base_url: str,
    ) -> None:
        """Verify 422 when the source field is omitted entirely."""
        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={},
        )
        assert resp.status_code == 422


# ── Progress tracking tests ─────────────────────────────────────────


@requires_server
@pytest.mark.e2e
class TestScanProgressTracking:
    """Verify scan progress via the GET endpoint."""

    def test_get_scan_returns_completed_status(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify GET /api/v1/scans/{scan_id} returns completed status."""
        jsonl_file = tmp_path / "progress.jsonl"
        jsonl_file.write_text('{"key": "value"}\n')

        post_resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        scan_id = post_resp.json()["scan_id"]

        _wait_for_scan_completion(api_base_url, scan_id)

        get_resp = httpx.get(f"{api_base_url}/api/v1/scans/{scan_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["scan_id"] == scan_id
        assert data["status"] == "completed"
        assert "records_processed" in data

    def test_get_unknown_scan_returns_404(
        self,
        api_base_url: str,
    ) -> None:
        """Verify 404 for an unknown scan ID."""
        resp = httpx.get(
            f"{api_base_url}/api/v1/scans/00000000-0000-0000-0000-000000000000",
        )
        assert resp.status_code == 404
        assert resp.json()["error"] == "scan_not_found"

    def test_scan_initial_status_is_pending_or_running(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify the initial scan status is pending or running.

        Immediately after creation the scan has not yet been picked up
        by the background executor, so the status should be ``pending``
        or ``running``.
        """
        jsonl_file = tmp_path / "initial.jsonl"
        jsonl_file.write_text('{"k": "v"}\n')

        post_resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        body = post_resp.json()
        assert body["status"] in ("pending", "running")


# ── PII leak detection tests ───────────────────────────────────────


@requires_server
@pytest.mark.e2e
@pytest.mark.safe_pipe
class TestIngestionPIILeakDetection:
    """Verify no PII leaks through scan API responses.

    Ingests files containing known PII from the fixture generator and
    asserts that none of the PII values appear in any API response body.
    """

    def test_no_pii_in_scan_creation_response(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify the scan creation response contains no PII."""
        jsonl_file = tmp_path / "pii_data.jsonl"
        generate_sample_jsonl(str(jsonl_file), count=5)
        pii_values = all_known_pii_values()

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        assert resp.status_code == 201
        _assert_no_pii_in_text(resp.text, pii_values)

    def test_no_pii_in_scan_status_response(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify PII is absent from both creation and completion responses."""
        jsonl_file = tmp_path / "pii_status.jsonl"
        generate_sample_jsonl(str(jsonl_file), count=5)
        pii_values = all_known_pii_values()

        post_resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(jsonl_file)},
        )
        assert post_resp.status_code == 201
        scan_id = post_resp.json()["scan_id"]

        result = _wait_for_scan_completion(api_base_url, scan_id)
        _assert_no_pii_in_text(json.dumps(result), pii_values)

    def test_no_pii_in_csv_scan_response(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify PII is absent from CSV scan responses."""
        csv_file = tmp_path / "pii_data.csv"
        generate_sample_csv(str(csv_file), count=5)
        pii_values = all_known_pii_values()

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(csv_file)},
        )
        assert resp.status_code == 201
        _assert_no_pii_in_text(resp.text, pii_values)

        scan_id = resp.json()["scan_id"]
        result = _wait_for_scan_completion(api_base_url, scan_id)
        _assert_no_pii_in_text(json.dumps(result), pii_values)

    def test_no_pii_in_error_responses(
        self,
        api_base_url: str,
    ) -> None:
        """Verify error responses do not leak PII."""
        pii_values = all_known_pii_values()

        # Nonexistent file error
        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": "/nonexistent/file.jsonl"},
        )
        _assert_no_pii_in_text(resp.text, pii_values)

        # Path traversal error
        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": "../../etc/passwd"},
        )
        _assert_no_pii_in_text(resp.text, pii_values)

    def test_error_list_contains_no_raw_data(
        self,
        api_base_url: str,
        tmp_path: Path,
    ) -> None:
        """Verify that scan error lists contain only exception class names.

        When a scan fails, the errors list should contain only the
        exception type name (e.g. ``ProviderConnectionError``), never
        raw file content or PII.
        """
        empty_file = tmp_path / "empty_errors.jsonl"
        empty_file.write_text("")

        resp = httpx.post(
            f"{api_base_url}/api/v1/scans/",
            json={"source": str(empty_file)},
        )
        assert resp.status_code == 201
        scan_id = resp.json()["scan_id"]

        result = _wait_for_scan_completion(api_base_url, scan_id)
        assert result["status"] == "failed"

        for error_entry in result["errors"]:
            # Error entries should be short class names, not raw messages.
            assert len(error_entry) < 100, (
                f"Error entry suspiciously long (possible data leak): {error_entry[:50]}..."
            )
            pii_values = all_known_pii_values()
            _assert_no_pii_in_text(error_entry, pii_values)
