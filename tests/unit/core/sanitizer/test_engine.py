"""Tests for SanitizationEngine composition and streaming.

Covers construction, stream processing with StrictStrategy, error handling
policies (SKIP_RECORD and ABORT_STREAM), counter tracking, generator
semantics, audit trail generation, and PII leak detection.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

import pytest

from cecil.core.sanitizer.engine import SanitizationEngine
from cecil.core.sanitizer.models import (
    Detection,
    FieldMapping,
    RedactionAction,
    RedactionAudit,
    SanitizedRecord,
    StreamErrorPolicy,
)
from cecil.core.sanitizer.strategies import RedactionStrategy, StrictStrategy
from cecil.utils.errors import RecordSanitizationError


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture()
def simple_mapping() -> FieldMapping:
    """Return a mapping with one field per action type."""
    return FieldMapping(
        {
            "email": RedactionAction.REDACT,
            "name": RedactionAction.MASK,
            "user_id": RedactionAction.HASH,
            "model": RedactionAction.KEEP,
        },
    )


@pytest.fixture()
def strict_strategy(simple_mapping: FieldMapping) -> StrictStrategy:
    """Return a StrictStrategy configured with the simple mapping."""
    return StrictStrategy(mapping=simple_mapping)


@pytest.fixture()
def engine(strict_strategy: StrictStrategy) -> SanitizationEngine:
    """Return a SanitizationEngine with default SKIP_RECORD policy."""
    return SanitizationEngine(strategy=strict_strategy)


@pytest.fixture()
def abort_engine(strict_strategy: StrictStrategy) -> SanitizationEngine:
    """Return a SanitizationEngine with ABORT_STREAM policy."""
    return SanitizationEngine(
        strategy=strict_strategy,
        error_policy=StreamErrorPolicy.ABORT_STREAM,
    )


def _make_records(
    records: list[dict[str, Any]],
) -> Generator[dict[str, Any], None, None]:
    """Wrap a list of records as a generator to simulate streaming."""
    yield from records


# -- Constructor -------------------------------------------------------------


class TestSanitizationEngineInit:
    """Tests for SanitizationEngine construction."""

    def test_init_accepts_strategy(self, strict_strategy: StrictStrategy) -> None:
        eng = SanitizationEngine(strategy=strict_strategy)
        assert eng is not None

    def test_init_stores_strategy(self, strict_strategy: StrictStrategy) -> None:
        eng = SanitizationEngine(strategy=strict_strategy)
        assert eng.strategy is strict_strategy

    def test_init_default_error_policy_is_skip(
        self,
        strict_strategy: StrictStrategy,
    ) -> None:
        eng = SanitizationEngine(strategy=strict_strategy)
        assert eng.error_policy is StreamErrorPolicy.SKIP_RECORD

    def test_init_accepts_abort_policy(
        self,
        strict_strategy: StrictStrategy,
    ) -> None:
        eng = SanitizationEngine(
            strategy=strict_strategy,
            error_policy=StreamErrorPolicy.ABORT_STREAM,
        )
        assert eng.error_policy is StreamErrorPolicy.ABORT_STREAM

    def test_init_counters_are_zero(self, engine: SanitizationEngine) -> None:
        assert engine.records_processed == 0
        assert engine.records_sanitized == 0
        assert engine.records_failed == 0


# -- process_stream: basic functionality -------------------------------------


class TestProcessStreamBasic:
    """Tests for basic process_stream functionality."""

    def test_process_stream_returns_generator(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"model": "gpt-4"}])
        result = engine.process_stream(records)
        assert hasattr(result, "__next__")

    def test_process_stream_yields_sanitized_records(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"model": "gpt-4"}])
        results = list(engine.process_stream(records))
        assert len(results) == 1
        assert isinstance(results[0], SanitizedRecord)

    def test_process_stream_sanitized_record_has_data(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"model": "gpt-4"}])
        result = next(engine.process_stream(records))
        assert isinstance(result.data, dict)

    def test_process_stream_sanitized_record_has_audit(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"model": "gpt-4"}])
        result = next(engine.process_stream(records))
        assert isinstance(result.audit, RedactionAudit)

    def test_process_stream_empty_generator_yields_nothing(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([])
        results = list(engine.process_stream(records))
        assert results == []


# -- process_stream: field redaction -----------------------------------------


class TestProcessStreamRedaction:
    """Tests for field-level redaction through the engine."""

    def test_keep_field_passes_through(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"model": "gpt-4"}])
        result = next(engine.process_stream(records))
        assert result.data["model"] == "gpt-4"

    def test_redact_field_is_replaced(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"email": "john@example.com"}])
        result = next(engine.process_stream(records))
        assert result.data["email"] == "[EMAIL_REDACTED]"

    def test_mask_field_is_masked(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"name": "John Doe"}])
        result = next(engine.process_stream(records))
        assert result.data["name"] == "J***e"

    def test_hash_field_is_hashed(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"user_id": "uid-42"}])
        result = next(engine.process_stream(records))
        assert result.data["user_id"].startswith("hash_")

    def test_unmapped_field_defaults_to_redact(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"secret": "supersecret"}])
        result = next(engine.process_stream(records))
        assert result.data["secret"] == "[SECRET_REDACTED]"  # noqa: S105

    def test_multiple_fields_processed_correctly(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records(
            [
                {
                    "email": "john@example.com",
                    "name": "John Doe",
                    "user_id": "uid-42",
                    "model": "gpt-4",
                },
            ],
        )
        result = next(engine.process_stream(records))
        assert result.data["email"] == "[EMAIL_REDACTED]"
        assert result.data["name"] == "J***e"
        assert result.data["user_id"].startswith("hash_")
        assert result.data["model"] == "gpt-4"


# -- process_stream: audit trail --------------------------------------------


class TestProcessStreamAudit:
    """Tests for RedactionAudit generation in process_stream."""

    def test_audit_record_id_is_sequential(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"email": "a@b.com"}, {"email": "c@d.com"}])
        results = list(engine.process_stream(records))
        assert results[0].audit.record_id == "0"
        assert results[1].audit.record_id == "1"

    def test_audit_has_timestamp(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"email": "test@example.com"}])
        result = next(engine.process_stream(records))
        assert result.audit.timestamp is not None

    def test_audit_tracks_redacted_fields(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"email": "test@example.com", "model": "gpt-4"}])
        result = next(engine.process_stream(records))
        field_names = [fr.field_name for fr in result.audit.fields_redacted]
        assert "email" in field_names

    def test_audit_does_not_track_kept_fields(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"model": "gpt-4"}])
        result = next(engine.process_stream(records))
        assert len(result.audit.fields_redacted) == 0

    def test_audit_field_redaction_has_entity_type(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"email": "test@example.com"}])
        result = next(engine.process_stream(records))
        fr = result.audit.fields_redacted[0]
        assert fr.entity_type == "REDACT"

    def test_audit_field_redaction_has_action(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"email": "test@example.com"}])
        result = next(engine.process_stream(records))
        fr = result.audit.fields_redacted[0]
        assert fr.action is RedactionAction.REDACT

    def test_audit_field_redaction_count(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"email": "test@example.com"}])
        result = next(engine.process_stream(records))
        fr = result.audit.fields_redacted[0]
        assert fr.count == 1


# -- process_stream: counters -----------------------------------------------


class TestProcessStreamCounters:
    """Tests for records_processed, records_sanitized, records_failed counters."""

    def test_counters_after_single_record(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"model": "gpt-4"}])
        list(engine.process_stream(records))
        assert engine.records_processed == 1
        assert engine.records_sanitized == 1
        assert engine.records_failed == 0

    def test_counters_after_multiple_records(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records(
            [{"model": "gpt-4"}, {"email": "a@b.com"}, {"name": "John"}],
        )
        list(engine.process_stream(records))
        assert engine.records_processed == 3
        assert engine.records_sanitized == 3
        assert engine.records_failed == 0

    def test_counters_after_empty_stream(
        self,
        engine: SanitizationEngine,
    ) -> None:
        list(engine.process_stream(_make_records([])))
        assert engine.records_processed == 0


# -- Error handling: SKIP_RECORD -------------------------------------------


class _FailingStrategy(RedactionStrategy):
    """Strategy that fails on specific keys for testing error handling."""

    def __init__(self, fail_on_key: str = "bad_field") -> None:
        self._fail_on_key = fail_on_key

    def scan_value(self, key: str, value: Any) -> list[Detection]:
        """Raise RuntimeError for the designated key."""
        if key == self._fail_on_key:
            raise RuntimeError("Simulated scan failure")
        return []

    def redact(self, value: str, detections: list[Detection]) -> str:
        """Return value unchanged."""
        return value


class TestProcessStreamSkipRecord:
    """Tests for SKIP_RECORD error policy."""

    def test_skip_record_continues_after_failure(self) -> None:
        strategy = _FailingStrategy()
        eng = SanitizationEngine(
            strategy=strategy,
            error_policy=StreamErrorPolicy.SKIP_RECORD,
        )
        records = _make_records(
            [{"bad_field": "fail"}, {"good_field": "ok"}],
        )
        results = list(eng.process_stream(records))
        assert len(results) == 1
        assert results[0].data["good_field"] == "ok"

    def test_skip_record_increments_failed_counter(self) -> None:
        strategy = _FailingStrategy()
        eng = SanitizationEngine(
            strategy=strategy,
            error_policy=StreamErrorPolicy.SKIP_RECORD,
        )
        records = _make_records(
            [{"bad_field": "fail"}, {"good_field": "ok"}],
        )
        list(eng.process_stream(records))
        assert eng.records_processed == 2
        assert eng.records_sanitized == 1
        assert eng.records_failed == 1

    def test_skip_record_logs_warning(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        strategy = _FailingStrategy()
        eng = SanitizationEngine(
            strategy=strategy,
            error_policy=StreamErrorPolicy.SKIP_RECORD,
        )
        records = _make_records([{"bad_field": "fail"}])
        with caplog.at_level(logging.WARNING):
            list(eng.process_stream(records))
        assert any("record_index=0" in msg for msg in caplog.messages)

    def test_skip_record_does_not_log_pii(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        strategy = _FailingStrategy()
        eng = SanitizationEngine(
            strategy=strategy,
            error_policy=StreamErrorPolicy.SKIP_RECORD,
        )
        records = _make_records([{"bad_field": "secret-pii-12345"}])
        with caplog.at_level(logging.WARNING):
            list(eng.process_stream(records))
        for msg in caplog.messages:
            assert "secret-pii-12345" not in msg


# -- Error handling: ABORT_STREAM ------------------------------------------


class TestProcessStreamAbortStream:
    """Tests for ABORT_STREAM error policy."""

    def test_abort_stream_raises_on_failure(self) -> None:
        strategy = _FailingStrategy()
        eng = SanitizationEngine(
            strategy=strategy,
            error_policy=StreamErrorPolicy.ABORT_STREAM,
        )
        records = _make_records([{"bad_field": "fail"}])
        with pytest.raises(RecordSanitizationError):
            list(eng.process_stream(records))

    def test_abort_stream_stops_processing(self) -> None:
        strategy = _FailingStrategy()
        eng = SanitizationEngine(
            strategy=strategy,
            error_policy=StreamErrorPolicy.ABORT_STREAM,
        )
        records = _make_records(
            [{"bad_field": "fail"}, {"good_field": "never reached"}],
        )
        with pytest.raises(RecordSanitizationError):
            list(eng.process_stream(records))
        assert eng.records_processed == 1
        assert eng.records_failed == 1
        assert eng.records_sanitized == 0

    def test_abort_stream_preserves_exception_chain(self) -> None:
        strategy = _FailingStrategy()
        eng = SanitizationEngine(
            strategy=strategy,
            error_policy=StreamErrorPolicy.ABORT_STREAM,
        )
        records = _make_records([{"bad_field": "fail"}])
        with pytest.raises(RecordSanitizationError) as exc_info:
            list(eng.process_stream(records))
        assert exc_info.value.__cause__ is not None


# -- Generator semantics ----------------------------------------------------


class TestProcessStreamGeneratorSemantics:
    """Tests that process_stream maintains lazy generator semantics."""

    def test_process_stream_is_lazy(self, engine: SanitizationEngine) -> None:
        call_count = 0

        def counting_gen() -> Generator[dict[str, Any], None, None]:
            nonlocal call_count
            for i in range(3):
                call_count += 1
                yield {"model": f"gpt-{i}"}

        gen = engine.process_stream(counting_gen())
        assert call_count == 0
        next(gen)
        assert call_count == 1

    def test_process_stream_incremental_counters(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"model": f"gpt-{i}"} for i in range(5)])
        gen = engine.process_stream(records)
        next(gen)
        assert engine.records_processed == 1
        next(gen)
        assert engine.records_processed == 2


# -- Policy hash ------------------------------------------------------------


class TestPolicyHash:
    """Tests for policy hash computation."""

    def test_policy_hash_is_sha256_hex(self, engine: SanitizationEngine) -> None:
        assert isinstance(engine.policy_hash, str)
        assert len(engine.policy_hash) == 64

    def test_policy_hash_is_deterministic(
        self,
        simple_mapping: FieldMapping,
    ) -> None:
        s1 = StrictStrategy(mapping=simple_mapping)
        s2 = StrictStrategy(mapping=simple_mapping)
        e1 = SanitizationEngine(strategy=s1)
        e2 = SanitizationEngine(strategy=s2)
        assert e1.policy_hash == e2.policy_hash

    def test_different_strategies_produce_different_hashes(self) -> None:
        m1 = FieldMapping({"email": RedactionAction.REDACT})
        m2 = FieldMapping({"email": RedactionAction.KEEP})
        e1 = SanitizationEngine(strategy=StrictStrategy(mapping=m1))
        e2 = SanitizationEngine(strategy=StrictStrategy(mapping=m2))
        assert e1.policy_hash != e2.policy_hash


# -- reset_counters ----------------------------------------------------------


class TestEntityTypeToAction:
    """Tests for _entity_type_to_action mapping."""

    def test_known_action_maps_directly(self) -> None:
        result = SanitizationEngine._entity_type_to_action("REDACT")
        assert result is RedactionAction.REDACT

    def test_pii_entity_type_maps_to_redact(self) -> None:
        result = SanitizationEngine._entity_type_to_action("EMAIL_ADDRESS")
        assert result is RedactionAction.REDACT

    def test_unknown_entity_type_maps_to_redact(self) -> None:
        result = SanitizationEngine._entity_type_to_action("SENSITIVE_KEY")
        assert result is RedactionAction.REDACT


class TestResetCounters:
    """Tests for counter reset functionality."""

    def test_reset_counters_clears_all(self, engine: SanitizationEngine) -> None:
        list(engine.process_stream(_make_records([{"model": "gpt-4"}])))
        assert engine.records_processed == 1
        engine.reset_counters()
        assert engine.records_processed == 0
        assert engine.records_sanitized == 0
        assert engine.records_failed == 0


# -- PII leak detection (safety-critical) -----------------------------------


class TestPIILeakDetection:
    """Verify that known PII values never appear in sanitized output."""

    def test_email_not_in_output(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"email": "john.doe@example.com"}])
        result = next(engine.process_stream(records))
        assert "john.doe@example.com" not in str(result.data)

    def test_name_not_in_output(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"name": "Jane Smith"}])
        result = next(engine.process_stream(records))
        assert "Jane Smith" not in str(result.data)

    def test_user_id_not_in_output(self, engine: SanitizationEngine) -> None:
        records = _make_records([{"user_id": "uid-42"}])
        result = next(engine.process_stream(records))
        assert "uid-42" not in str(result.data)

    def test_unmapped_secret_not_in_output(
        self,
        engine: SanitizationEngine,
    ) -> None:
        records = _make_records([{"api_key": "sk-supersecret123456"}])
        result = next(engine.process_stream(records))
        assert "sk-supersecret123456" not in str(result.data)


# -- Integration: full pipeline round-trip -----------------------------------


class TestFullPipelineRoundTrip:
    """End-to-end test: records in, sanitized records out."""

    def test_multi_record_stream(self, engine: SanitizationEngine) -> None:
        input_records = [
            {"email": "alice@example.com", "model": "gpt-4"},
            {"email": "bob@example.com", "name": "Bob", "model": "claude"},
            {"model": "llama-2"},
        ]
        results = list(engine.process_stream(_make_records(input_records)))
        assert len(results) == 3

        assert results[0].data["email"] == "[EMAIL_REDACTED]"
        assert results[0].data["model"] == "gpt-4"

        assert results[1].data["email"] == "[EMAIL_REDACTED]"
        assert results[1].data["name"] == "***"  # "Bob" is 3 chars => ***
        assert results[1].data["model"] == "claude"

        assert results[2].data["model"] == "llama-2"

        assert engine.records_processed == 3
        assert engine.records_sanitized == 3
        assert engine.records_failed == 0
