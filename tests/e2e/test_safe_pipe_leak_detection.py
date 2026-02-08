"""Safe-Pipe leak detection E2E tests.

Verifies the core Cecil invariant: **no raw data leaves the machine**.
These tests ingest mock data with known PII, run it through available
pipeline stages, and assert that:

1. All known PII strings are absent from any output.
2. No raw data is transmitted over any network socket.
3. Error responses do not leak PII.
4. The health endpoint returns only safe metadata.

Tests that require the full sanitization engine or the FastAPI server
are skipped when those modules are not yet available.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

import pytest

from cecil.core.providers.mock import MockDataProvider
from tests.fixtures.pii_samples import (
    KNOWN_PII_BUNDLES,
    all_known_pii_values,
    generate_sample_csv,
    generate_sample_jsonl,
    make_log_records_from_bundles,
    stream_log_records,
)


# ── Helpers ───────────────────────────────────────────────────────────


def _assert_no_pii_in_text(text: str, pii_values: list[str]) -> None:
    """Assert that none of the known PII values appear in the text.

    Args:
        text: The text to scan for PII leaks.
        pii_values: The list of PII strings that must be absent.

    Raises:
        AssertionError: If any PII value is found in the text.
    """
    for value in pii_values:
        assert value not in text, (
            f"PII LEAK DETECTED: '{value}' found in output. Safe-Pipe invariant violated."
        )


def _server_is_available() -> bool:
    """Check whether the FastAPI server module can be imported."""
    try:
        import cecil.api.server  # noqa: F401

        return True
    except (ImportError, ModuleNotFoundError):
        return False


def _sanitizer_is_available() -> bool:
    """Check whether the sanitization engine module can be imported."""
    try:
        import cecil.core.sanitizer.engine  # noqa: F401

        return True
    except (ImportError, ModuleNotFoundError):
        return False


# ── Network socket monitor ───────────────────────────────────────────


class NetworkSocketMonitor:
    """Monitors for outbound network connections during a test.

    Patches ``socket.socket.connect`` to intercept and record any
    connection attempts to non-loopback addresses.  This enforces
    the Safe-Pipe invariant that no raw data leaves the machine.
    """

    _LOOPBACK_PREFIXES = ("127.", "::1", "localhost")

    def __init__(self) -> None:
        self._outbound_connections: list[tuple[str, int]] = []
        self._original_connect: Any = None

    @property
    def outbound_connections(self) -> list[tuple[str, int]]:
        """Return the list of non-loopback connection attempts.

        Returns:
            A list of (host, port) tuples for outbound connections.
        """
        return list(self._outbound_connections)

    def _patched_connect(
        self,
        sock_instance: socket.socket,
        address: Any,
    ) -> Any:
        """Intercept socket.connect calls and log non-loopback ones.

        Args:
            sock_instance: The socket instance being connected.
            address: The target address (host, port) tuple.

        Returns:
            The result of the original connect call.
        """
        if isinstance(address, tuple) and len(address) >= 2:
            host = str(address[0])
            port = int(address[1])
            is_loopback = any(host.startswith(p) for p in self._LOOPBACK_PREFIXES)
            if not is_loopback:
                self._outbound_connections.append((host, port))

        assert self._original_connect is not None
        return self._original_connect(sock_instance, address)

    def __enter__(self) -> NetworkSocketMonitor:
        """Start monitoring by patching socket.connect."""
        self._original_connect = socket.socket.connect
        socket.socket.connect = self._patched_connect  # type: ignore[assignment]
        return self

    def __exit__(self, *exc: object) -> None:
        """Restore the original socket.connect."""
        if self._original_connect is not None:
            socket.socket.connect = self._original_connect  # type: ignore[assignment]
            self._original_connect = None


# ── PII fixture data tests ───────────────────────────────────────────


@pytest.mark.safe_pipe
class TestPIIFixtureIntegrity:
    """Verify that test fixtures contain the expected PII values.

    These tests ensure our test data is valid before using it for
    leak detection.
    """

    def test_known_pii_bundles_contain_expected_count(self):
        """Verify we have at least 3 known PII bundles."""
        assert len(KNOWN_PII_BUNDLES) >= 3

    def test_all_known_pii_values_returns_nonempty_list(self):
        """Verify the flat PII values list is populated."""
        values = all_known_pii_values()
        assert len(values) > 0
        # 8 fields per bundle, 3 bundles = 24 values minimum
        assert len(values) >= 24

    def test_log_records_contain_embedded_pii(self):
        """Verify generated log records actually contain PII strings."""
        records = make_log_records_from_bundles()
        serialized = json.dumps(records)

        for bundle in KNOWN_PII_BUNDLES:
            assert bundle.email in serialized
            assert bundle.ssn in serialized
            assert bundle.name in serialized

    def test_stream_log_records_yields_expected_count(self):
        """Verify the streaming generator yields the requested count."""
        count = 50
        records = list(stream_log_records(count=count))
        assert len(records) == count

    def test_generated_jsonl_contains_pii(self, tmp_path: Path):
        """Verify the JSONL fixture generator embeds PII."""
        path = str(tmp_path / "test.jsonl")
        pii_values = generate_sample_jsonl(path, count=5)

        content = Path(path).read_text(encoding="utf-8")
        for value in pii_values[:8]:  # Check first bundle's values
            assert value in content

    def test_generated_csv_contains_pii(self, tmp_path: Path):
        """Verify the CSV fixture generator embeds PII."""
        path = str(tmp_path / "test.csv")
        pii_values = generate_sample_csv(path, count=5)

        content = Path(path).read_text(encoding="utf-8")
        for value in pii_values[:4]:  # Check first bundle's PII fields
            assert value in content


# ── Network isolation tests ──────────────────────────────────────────


@pytest.mark.safe_pipe
class TestNetworkIsolation:
    """Verify that no raw data is transmitted over the network.

    The Safe-Pipe invariant requires that only anonymized
    ``CostFingerprint`` data may leave the machine.  These tests
    monitor for any outbound network connections during pipeline
    operations.
    """

    def test_provider_stream_no_outbound_connections(self):
        """Verify MockDataProvider does not make outbound network calls."""
        records = make_log_records_from_bundles()
        provider = MockDataProvider(records=records)

        with NetworkSocketMonitor() as monitor:
            provider.connect()
            consumed = list(provider.stream_records())
            provider.close()

        assert len(consumed) == len(records)
        assert monitor.outbound_connections == [], (
            f"Outbound connections detected during provider stream: {monitor.outbound_connections}"
        )

    def test_record_serialization_no_outbound_connections(self):
        """Verify serializing records does not trigger network calls."""
        records = make_log_records_from_bundles()

        with NetworkSocketMonitor() as monitor:
            serialized = json.dumps(records)
            _ = json.loads(serialized)

        assert monitor.outbound_connections == [], (
            f"Outbound connections detected during serialization: {monitor.outbound_connections}"
        )

    def test_streaming_large_dataset_no_outbound_connections(self):
        """Verify streaming many records does not trigger network calls."""
        with NetworkSocketMonitor() as monitor:
            count = 0
            for record in stream_log_records(count=500):
                count += 1
                # Simulate processing the record
                _ = json.dumps(record)

        assert count == 500
        assert monitor.outbound_connections == [], (
            f"Outbound connections during large stream: {monitor.outbound_connections}"
        )


# ── API endpoint leak detection tests ────────────────────────────────


@pytest.mark.safe_pipe
@pytest.mark.e2e
class TestAPILeakDetection:
    """Verify API endpoints do not leak PII in responses.

    These tests require the FastAPI server module to be available.
    """

    @pytest.fixture()
    def _require_server(self):
        """Skip tests if the FastAPI server module is not available."""
        if not _server_is_available():
            pytest.skip("FastAPI server module not available")

    @pytest.mark.usefixtures("_require_server")
    def test_health_endpoint_contains_no_pii(self):
        """Verify /api/v1/health response contains no PII."""
        from fastapi.testclient import TestClient

        from cecil.api.server import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health")
        pii_values = all_known_pii_values()
        response_text = response.text

        _assert_no_pii_in_text(response_text, pii_values)
        assert response.status_code == 200

    @pytest.mark.usefixtures("_require_server")
    def test_health_endpoint_returns_only_safe_fields(self):
        """Verify health response contains only status and version."""
        from fastapi.testclient import TestClient

        from cecil.api.server import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health")
        data = response.json()

        # Health response should only contain safe metadata
        allowed_keys = {"status", "version"}
        actual_keys = set(data.keys())
        assert actual_keys <= allowed_keys, (
            f"Health endpoint returned unexpected keys: {actual_keys - allowed_keys}"
        )

    @pytest.mark.usefixtures("_require_server")
    def test_404_error_response_contains_no_pii(self):
        """Verify error responses for unknown routes contain no PII."""
        from fastapi.testclient import TestClient

        from cecil.api.server import create_app

        app = create_app()
        client = TestClient(app)

        # Request a non-existent endpoint with PII in the URL
        pii_in_url = "john.doe@example.com"
        response = client.get(f"/api/v1/nonexistent/{pii_in_url}")
        pii_values = all_known_pii_values()

        _assert_no_pii_in_text(response.text, pii_values)

    @pytest.mark.usefixtures("_require_server")
    def test_health_endpoint_no_outbound_connections(self):
        """Verify the health endpoint makes no outbound network calls."""
        from fastapi.testclient import TestClient

        from cecil.api.server import create_app

        app = create_app()
        client = TestClient(app)

        with NetworkSocketMonitor() as monitor:
            response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert monitor.outbound_connections == [], (
            f"Health endpoint triggered outbound connections: {monitor.outbound_connections}"
        )


# ── Full pipeline leak detection tests ───────────────────────────────


@pytest.mark.safe_pipe
class TestFullPipelineLeakDetection:
    """End-to-end leak detection through the full sanitization pipeline.

    These tests require the sanitization engine, which is being built
    in a separate issue.  They are skipped until the engine is available.
    """

    @pytest.mark.skip(reason="Awaiting sanitization engine (Issue #3)")
    def test_sanitized_output_contains_no_known_pii(self):
        """Ingest records with known PII and verify all PII is redacted.

        Flow:
            1. Create MockDataProvider with known PII records.
            2. Run through SanitizationEngine with StrictStrategy.
            3. Serialize output and assert 0% of known PII strings remain.
        """
        # Future implementation:
        # from cecil.core.sanitizer.engine import SanitizationEngine
        # from cecil.core.sanitizer.strategies import StrictStrategy
        #
        # records = make_log_records_from_bundles()
        # provider = MockDataProvider(records=records)
        # engine = SanitizationEngine(strategy=StrictStrategy())
        #
        # provider.connect()
        # sanitized = [engine.sanitize(r) for r in provider.stream_records()]
        # provider.close()
        #
        # output = json.dumps(sanitized)
        # pii_values = all_known_pii_values()
        # _assert_no_pii_in_text(output, pii_values)

    @pytest.mark.skip(reason="Awaiting sanitization engine (Issue #3)")
    def test_deep_interceptor_catches_nested_pii(self):
        """Verify DeepInterceptorStrategy finds PII in nested structures.

        The deep interceptor should recursively scan all string values
        in nested dictionaries and lists.
        """
        # Future implementation:
        # from cecil.core.sanitizer.engine import SanitizationEngine
        # from cecil.core.sanitizer.strategies import DeepInterceptorStrategy
        #
        # record = {
        #     "outer": {
        #         "inner": {
        #             "deeply_nested_email": "john.doe@example.com",
        #         }
        #     },
        #     "list_field": [
        #         {"ssn": "123-45-6789"},
        #     ],
        # }
        # ...

    @pytest.mark.skip(reason="Awaiting sanitization engine (Issue #3)")
    def test_sanitized_jsonl_output_contains_no_pii(self):
        """Verify JSONL output files have all PII redacted."""
        # Future implementation: write sanitized records to JSONL,
        # then re-read and check for PII.

    @pytest.mark.skip(reason="Awaiting sanitization engine (Issue #3)")
    def test_sanitized_csv_output_contains_no_pii(self):
        """Verify CSV output files have all PII redacted."""
        # Future implementation: write sanitized records to CSV,
        # then re-read and check for PII.

    @pytest.mark.skip(reason="Awaiting sanitization engine (Issue #3)")
    def test_redaction_audit_trail_produced(self):
        """Verify sanitization produces a RedactionAudit for each record."""
        # Future implementation: assert every sanitized record has
        # an associated audit entry.

    @pytest.mark.skip(reason="Awaiting sanitization engine (Issue #3)")
    def test_cost_fingerprint_contains_only_safe_fields(self):
        """Verify CostFingerprint sent to SaaS contains no PII.

        Only token counts, model IDs, timestamps, and policy hash
        should be present.
        """
        # Future implementation:
        # allowed_fields = {
        #     "token_count", "model_id", "timestamp", "policy_hash",
        #     "record_count", "session_id_hash",
        # }
        # assert set(fingerprint.keys()) <= allowed_fields


# ── Telemetry isolation tests ────────────────────────────────────────


@pytest.mark.safe_pipe
class TestTelemetryIsolation:
    """Verify that telemetry payloads contain only safe metadata.

    When the optional SaaS upload is enabled, only ``CostFingerprint``
    data (token counts, model IDs, timestamps, policy hash) may be sent.
    No raw data or PII may appear in telemetry.
    """

    def test_mock_telemetry_payload_contains_only_safe_fields(self):
        """Verify a mock telemetry payload has no PII.

        Since the telemetry module is not yet built, this test validates
        the schema contract using a mock payload.
        """
        # This is what the CostFingerprint payload SHOULD look like
        safe_payload = {
            "token_count_in": 45,
            "token_count_out": 22,
            "model_id": "gpt-4",
            "timestamp": "2026-01-15T10:30:00Z",
            "policy_hash": "sha256:abc123def456",
            "record_count": 100,
        }

        serialized = json.dumps(safe_payload)
        pii_values = all_known_pii_values()
        _assert_no_pii_in_text(serialized, pii_values)

    def test_mock_telemetry_payload_rejects_pii_fields(self):
        """Verify that adding PII fields to a payload is detectable.

        Simulates the check that should run before any SaaS upload.
        """
        unsafe_payload = {
            "token_count_in": 45,
            "model_id": "gpt-4",
            "user_email": "john.doe@example.com",  # PII leak!
        }

        serialized = json.dumps(unsafe_payload)
        pii_values = all_known_pii_values()

        # This SHOULD fail -- proving our detection works
        with pytest.raises(AssertionError, match="PII LEAK DETECTED"):
            _assert_no_pii_in_text(serialized, pii_values)


# ── Denial flow tests ────────────────────────────────────────────────


@pytest.mark.safe_pipe
class TestDenialFlow:
    """Verify that when upload is denied, zero network requests are made.

    The user can set a policy to deny SaaS uploads.  When this policy
    is active, no outbound network connections should be attempted.
    """

    def test_deny_upload_policy_makes_zero_outbound_connections(self):
        """Simulate deny-upload policy and verify no network calls.

        Uses the NetworkSocketMonitor to ensure complete network silence
        during provider streaming when upload is denied.
        """
        records = make_log_records_from_bundles()
        provider = MockDataProvider(records=records)

        # Simulate "deny upload" policy
        upload_allowed = False

        with NetworkSocketMonitor() as monitor:
            provider.connect()
            consumed_records = list(provider.stream_records())
            provider.close()

            # Conditional upload (should NOT happen)
            if upload_allowed:
                pass  # Would send to SaaS here

        assert len(consumed_records) == len(records)
        assert monitor.outbound_connections == [], (
            f"Network connections made despite deny-upload policy: {monitor.outbound_connections}"
        )

    @pytest.mark.skip(reason="Awaiting telemetry module")
    def test_deny_upload_skips_saas_handshake(self):
        """Verify the SaaS handshake is never initiated when denied."""
        # Future implementation: mock the SaaS client and verify
        # it is never called when policy is set to deny.
