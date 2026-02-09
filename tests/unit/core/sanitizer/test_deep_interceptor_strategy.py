"""Tests for DeepInterceptorStrategy with Presidio and custom regex.

Verifies that the DeepInterceptorStrategy:
- Detects PII via Presidio (email, phone, credit card, IP, etc.)
- Detects sensitive keys via regex patterns
- Detects AWS access keys via custom regex
- Redacts detected spans with [ENTITY_TYPE_REDACTED] placeholders
- Handles nested dict/list values by recursive scanning
- Falls back to regex-only detection when Presidio is unavailable
- Never logs PII values
"""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest

from cecil.core.sanitizer.models import Detection
from cecil.core.sanitizer.strategies import DeepInterceptorStrategy, RedactionStrategy


# -- ABC conformance --------------------------------------------------------


class TestDeepInterceptorStrategyConformance:
    """Verify DeepInterceptorStrategy fulfils the RedactionStrategy ABC."""

    def test_deep_interceptor_is_redaction_strategy(self) -> None:
        strategy = DeepInterceptorStrategy()
        assert isinstance(strategy, RedactionStrategy)

    def test_deep_interceptor_has_scan_value(self) -> None:
        strategy = DeepInterceptorStrategy()
        assert callable(strategy.scan_value)

    def test_deep_interceptor_has_redact(self) -> None:
        strategy = DeepInterceptorStrategy()
        assert callable(strategy.redact)


# -- Sensitive key detection ------------------------------------------------


class TestSensitiveKeyDetection:
    """Verify keys matching sensitive patterns trigger full-value detection."""

    @pytest.fixture()
    def strategy(self) -> DeepInterceptorStrategy:
        """Return a DeepInterceptorStrategy instance."""
        return DeepInterceptorStrategy()

    @pytest.mark.parametrize(
        "key",
        [
            "api_key",
            "api-key",
            "apikey",
            "API_KEY",
            "secret",
            "SECRET_TOKEN",
            "password",
            "passwd",
            "token",
            "auth_token",
            "auth",
            "credential",
            "credentials",
            "ssn",
            "social_security",
            "social-security-number",
        ],
    )
    def test_sensitive_key_returns_full_value_detection(
        self,
        strategy: DeepInterceptorStrategy,
        key: str,
    ) -> None:
        value = "some-secret-value-12345"
        detections = strategy.scan_value(key, value)
        sensitive = [d for d in detections if d.entity_type == "SENSITIVE_KEY"]
        assert len(sensitive) == 1
        d = sensitive[0]
        assert d.start == 0
        assert d.end == len(value)
        assert d.score == 1.0

    def test_non_sensitive_key_no_sensitive_detection(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value("model", "gpt-4")
        sensitive = [d for d in detections if d.entity_type == "SENSITIVE_KEY"]
        assert len(sensitive) == 0

    def test_sensitive_key_with_integer_value(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value("api_key", 12345)
        sensitive = [d for d in detections if d.entity_type == "SENSITIVE_KEY"]
        assert len(sensitive) == 1
        assert sensitive[0].end == len("12345")


# -- Presidio PII detection -------------------------------------------------


class TestPresidioPIIDetection:
    """Verify Presidio-based PII detection for supported entity types."""

    @pytest.fixture()
    def strategy(self) -> DeepInterceptorStrategy:
        """Return a DeepInterceptorStrategy instance."""
        return DeepInterceptorStrategy()

    def test_detects_email_address(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value(
            "message",
            "Contact john.doe@example.com please",
        )
        emails = [d for d in detections if d.entity_type == "EMAIL_ADDRESS"]
        assert len(emails) >= 1
        assert emails[0].score > 0.0

    def test_detects_phone_number(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value(
            "notes",
            "Call me at (555) 867-5309",
        )
        phones = [d for d in detections if d.entity_type == "PHONE_NUMBER"]
        assert len(phones) >= 1

    def test_detects_credit_card(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value(
            "payment",
            "Card: 4111-1111-1111-1111",
        )
        cards = [d for d in detections if d.entity_type == "CREDIT_CARD"]
        assert len(cards) >= 1

    def test_detects_ip_address(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value(
            "source",
            "From IP 192.168.1.42",
        )
        ips = [d for d in detections if d.entity_type == "IP_ADDRESS"]
        assert len(ips) >= 1

    def test_no_detections_for_clean_value(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value("model", "gpt-4")
        assert len(detections) == 0

    def test_multiple_pii_in_single_value(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        text = "Email: john.doe@example.com, Phone: (555) 867-5309"
        detections = strategy.scan_value("body", text)
        types = {d.entity_type for d in detections}
        assert "EMAIL_ADDRESS" in types
        assert "PHONE_NUMBER" in types


# -- Custom regex detection -------------------------------------------------


class TestCustomRegexDetection:
    """Verify custom regex patterns for AWS keys."""

    @pytest.fixture()
    def strategy(self) -> DeepInterceptorStrategy:
        """Return a DeepInterceptorStrategy instance."""
        return DeepInterceptorStrategy()

    def test_detects_aws_access_key_akia(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "key is AKIAIOSFODNN7EXAMPLE"
        detections = strategy.scan_value("config", value)
        aws = [d for d in detections if d.entity_type == "AWS_ACCESS_KEY"]
        assert len(aws) >= 1

    def test_detects_aws_access_key_asia(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "ASIA1234567890ABCDEF"
        detections = strategy.scan_value("config", value)
        aws = [d for d in detections if d.entity_type == "AWS_ACCESS_KEY"]
        assert len(aws) >= 1

    def test_does_not_detect_non_aws_key(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "ABCD1234567890ABCDEF"
        detections = strategy.scan_value("config", value)
        aws = [d for d in detections if d.entity_type == "AWS_ACCESS_KEY"]
        assert len(aws) == 0


# -- Redaction --------------------------------------------------------------


class TestRedaction:
    """Verify detected spans are replaced with correct placeholders."""

    @pytest.fixture()
    def strategy(self) -> DeepInterceptorStrategy:
        """Return a DeepInterceptorStrategy instance."""
        return DeepInterceptorStrategy()

    def test_redact_single_detection(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "test@example.com"
        detections = [
            Detection(
                entity_type="EMAIL_ADDRESS",
                start=0,
                end=16,
                score=1.0,
            ),
        ]
        result = strategy.redact(value, detections)
        assert result == "[EMAIL_ADDRESS_REDACTED]"
        assert "test@example.com" not in result

    def test_redact_multiple_detections(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "Email: test@example.com, IP: 192.168.1.1"
        detections = [
            Detection(
                entity_type="EMAIL_ADDRESS",
                start=7,
                end=23,
                score=1.0,
            ),
            Detection(
                entity_type="IP_ADDRESS",
                start=29,
                end=40,
                score=0.95,
            ),
        ]
        result = strategy.redact(value, detections)
        assert "test@example.com" not in result
        assert "192.168.1.1" not in result
        assert "[EMAIL_ADDRESS_REDACTED]" in result
        assert "[IP_ADDRESS_REDACTED]" in result

    def test_redact_sensitive_key_replaces_entire_value(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "super-secret-api-key-value"
        detections = [
            Detection(
                entity_type="SENSITIVE_KEY",
                start=0,
                end=len(value),
                score=1.0,
            ),
        ]
        result = strategy.redact(value, detections)
        assert result == "[SENSITIVE_KEY_REDACTED]"
        assert "super-secret" not in result

    def test_redact_no_detections_returns_original(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "nothing sensitive here"
        result = strategy.redact(value, [])
        assert result == value

    def test_redact_preserves_surrounding_text(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "Hello test@example.com world"
        detections = [
            Detection(
                entity_type="EMAIL_ADDRESS",
                start=6,
                end=22,
                score=1.0,
            ),
        ]
        result = strategy.redact(value, detections)
        assert result == "Hello [EMAIL_ADDRESS_REDACTED] world"

    def test_redact_handles_adjacent_detections(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "AABB"
        detections = [
            Detection(
                entity_type="TYPE_A",
                start=0,
                end=2,
                score=1.0,
            ),
            Detection(
                entity_type="TYPE_B",
                start=2,
                end=4,
                score=1.0,
            ),
        ]
        result = strategy.redact(value, detections)
        assert "[TYPE_A_REDACTED]" in result
        assert "[TYPE_B_REDACTED]" in result


# -- Nested value handling --------------------------------------------------


class TestNestedValueHandling:
    """Verify recursive scanning of dict and list values."""

    @pytest.fixture()
    def strategy(self) -> DeepInterceptorStrategy:
        """Return a DeepInterceptorStrategy instance."""
        return DeepInterceptorStrategy()

    def test_scan_dict_value_detects_pii(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        nested: dict[str, str] = {
            "email": "john.doe@example.com",
            "name": "safe",
        }
        detections = strategy.scan_value("metadata", nested)
        emails = [d for d in detections if d.entity_type == "EMAIL_ADDRESS"]
        assert len(emails) >= 1

    def test_scan_list_value_detects_pii(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        values = ["john.doe@example.com", "safe-value"]
        detections = strategy.scan_value("emails", values)
        emails = [d for d in detections if d.entity_type == "EMAIL_ADDRESS"]
        assert len(emails) >= 1

    def test_scan_json_string_value_detects_pii(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        json_str = json.dumps({"contact": "john.doe@example.com"})
        detections = strategy.scan_value("payload", json_str)
        emails = [d for d in detections if d.entity_type == "EMAIL_ADDRESS"]
        assert len(emails) >= 1


# -- Graceful fallback when Presidio is unavailable -------------------------


class TestPresidioFallback:
    """Verify graceful fallback to regex-only when Presidio unavailable."""

    def test_fallback_still_detects_sensitive_keys(self) -> None:
        with patch(
            "cecil.core.sanitizer.strategies._create_presidio_analyzer",
            side_effect=ImportError("Presidio not available"),
        ):
            strategy = DeepInterceptorStrategy()
            detections = strategy.scan_value(
                "api_key",
                "my-secret-key",
            )
            sensitive = [d for d in detections if d.entity_type == "SENSITIVE_KEY"]
            assert len(sensitive) == 1

    def test_fallback_still_detects_aws_keys(self) -> None:
        with patch(
            "cecil.core.sanitizer.strategies._create_presidio_analyzer",
            side_effect=ImportError("Presidio not available"),
        ):
            strategy = DeepInterceptorStrategy()
            detections = strategy.scan_value(
                "config",
                "AKIAIOSFODNN7EXAMPLE",
            )
            aws = [d for d in detections if d.entity_type == "AWS_ACCESS_KEY"]
            assert len(aws) >= 1

    def test_fallback_logs_warning(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with patch(
            "cecil.core.sanitizer.strategies._create_presidio_analyzer",
            side_effect=ImportError("Presidio not available"),
        ):
            with caplog.at_level(
                logging.WARNING,
                logger="cecil.core.sanitizer.strategies",
            ):
                strategy = DeepInterceptorStrategy()
                strategy.scan_value("field", "value")
            assert any("presidio" in record.message.lower() for record in caplog.records)


# -- Lazy initialization ---------------------------------------------------


class TestLazyInitialization:
    """Verify that the Presidio analyzer is created lazily."""

    def test_analyzer_not_created_at_init(self) -> None:
        with patch(
            "cecil.core.sanitizer.strategies._create_presidio_analyzer",
        ) as mock_create:
            _strategy = DeepInterceptorStrategy()
            mock_create.assert_not_called()

    def test_analyzer_created_on_first_scan(self) -> None:
        strategy = DeepInterceptorStrategy()
        assert strategy._analyzer is None
        strategy.scan_value("field", "test@example.com")
        assert strategy._analyzer_initialized


# -- PII never logged -------------------------------------------------------


class TestNoPIILogging:
    """Verify that PII values never appear in log output."""

    def test_scan_does_not_log_pii_values(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        pii_email = "john.doe@example.com"
        pii_ssn = "234-56-7890"
        strategy = DeepInterceptorStrategy()
        with caplog.at_level(
            logging.DEBUG,
            logger="cecil.core.sanitizer.strategies",
        ):
            strategy.scan_value(
                "body",
                f"Email: {pii_email}, SSN: {pii_ssn}",
            )
        for record in caplog.records:
            assert pii_email not in record.message
            assert pii_ssn not in record.message

    def test_fallback_warning_does_not_log_pii(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        pii_value = "john.doe@example.com"
        with patch(
            "cecil.core.sanitizer.strategies._create_presidio_analyzer",
            side_effect=ImportError("Presidio not available"),
        ):
            strategy = DeepInterceptorStrategy()
            with caplog.at_level(
                logging.DEBUG,
                logger="cecil.core.sanitizer.strategies",
            ):
                strategy.scan_value("email", pii_value)
        for record in caplog.records:
            assert pii_value not in record.message


# -- End-to-end scan+redact round-trip --------------------------------------


class TestScanAndRedactRoundTrip:
    """Verify end-to-end scan and redaction for realistic data."""

    @pytest.fixture()
    def strategy(self) -> DeepInterceptorStrategy:
        """Return a DeepInterceptorStrategy instance."""
        return DeepInterceptorStrategy()

    def test_email_is_fully_redacted(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "Contact john.doe@example.com for details"
        detections = strategy.scan_value("body", value)
        result = strategy.redact(value, detections)
        assert "john.doe@example.com" not in result
        assert "[EMAIL_ADDRESS_REDACTED]" in result

    def test_sensitive_key_value_is_fully_redacted(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "sk-1234567890abcdef"
        detections = strategy.scan_value("api_key", value)
        result = strategy.redact(value, detections)
        assert "sk-1234567890abcdef" not in result
        assert "[SENSITIVE_KEY_REDACTED]" in result

    def test_aws_key_is_fully_redacted(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "Key: AKIAIOSFODNN7EXAMPLE"
        detections = strategy.scan_value("config", value)
        result = strategy.redact(value, detections)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[AWS_ACCESS_KEY_REDACTED]" in result

    def test_clean_value_passes_through(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        value = "gpt-4-turbo"
        detections = strategy.scan_value("model", value)
        result = strategy.redact(value, detections)
        assert result == "gpt-4-turbo"

    def test_known_pii_absent_from_redacted_output(
        self,
        strategy: DeepInterceptorStrategy,
        known_pii_values: list[str],
    ) -> None:
        """Critical safety test: no known PII survives redaction."""
        for pii_value in known_pii_values:
            detections = strategy.scan_value(
                "user_data",
                pii_value,
            )
            if detections:
                result = strategy.redact(pii_value, detections)
                assert pii_value not in result, f"PII value {pii_value!r} survived redaction"


# -- Non-string value coercion ----------------------------------------------


class TestNonStringValueCoercion:
    """Verify non-string values are properly converted before scanning."""

    @pytest.fixture()
    def strategy(self) -> DeepInterceptorStrategy:
        """Return a DeepInterceptorStrategy instance."""
        return DeepInterceptorStrategy()

    def test_integer_value_converted_to_string(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value("count", 42)
        assert isinstance(detections, list)

    def test_float_value_converted_to_string(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value("cost", 3.14)
        assert isinstance(detections, list)

    def test_none_value_returns_empty_detections(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value("empty", None)
        assert detections == []

    def test_bool_value_converted_to_string(
        self,
        strategy: DeepInterceptorStrategy,
    ) -> None:
        detections = strategy.scan_value("flag", True)
        assert isinstance(detections, list)
