"""Tests for the /api/v1/mappings endpoints."""

from __future__ import annotations

import json
import uuid
from collections.abc import Generator
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
        "\n".join(
            json.dumps({"id": str(i), "name": f"user_{i}", "email": f"user{i}@example.com"})
            for i in range(records)
        )
        + "\n",
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
    lines = ["id,name,email"]
    for i in range(records):
        lines.append(f"{i},user_{i},user{i}@example.com")
    f.write_text("\n".join(lines) + "\n")
    return f


def _valid_mapping_payload() -> dict[str, object]:
    """Return a valid mapping request payload.

    Returns:
        A dict suitable for JSON serialization as a MappingConfigRequest.
    """
    return {
        "version": 1,
        "default_action": "redact",
        "fields": {
            "email": {"action": "mask", "options": {}},
            "name": {"action": "redact", "options": {}},
            "id": {"action": "keep", "options": {}},
        },
    }


@pytest.fixture(autouse=True)
def _clear_mapping_store() -> Generator[None, None, None]:
    """Clear the in-memory mapping store between tests."""
    from cecil.api.routes.mappings import _mapping_store

    _mapping_store.clear()
    yield
    _mapping_store.clear()


class TestPostMappings:
    """Tests for POST /api/v1/mappings endpoint."""

    def test_post_mapping_valid_returns_201(
        self,
        client: TestClient,
    ) -> None:
        """A valid mapping configuration returns 201 with mapping metadata."""
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())

        assert response.status_code == 201
        body = response.json()
        assert "mapping_id" in body
        assert "policy_hash" in body
        assert "created_at" in body
        assert body["version"] == 1
        assert body["default_action"] == "redact"
        assert "email" in body["fields"]
        assert body["fields"]["email"]["action"] == "mask"

    def test_post_mapping_id_is_uuid(
        self,
        client: TestClient,
    ) -> None:
        """The returned mapping_id is a valid UUID4."""
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())

        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]
        parsed = uuid.UUID(mapping_id, version=4)
        assert str(parsed) == mapping_id

    def test_post_mapping_invalid_action_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """An invalid redaction action returns 422."""
        payload = {
            "version": 1,
            "fields": {
                "email": {"action": "invalid_action", "options": {}},
            },
        }
        response = client.post("/api/v1/mappings/", json=payload)

        assert response.status_code == 422

    def test_post_mapping_missing_fields_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """A request missing the 'fields' key returns 422."""
        payload = {"version": 1}
        response = client.post("/api/v1/mappings/", json=payload)

        assert response.status_code == 422

    def test_post_mapping_empty_fields_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """A request with an empty fields dict returns 422."""
        payload = {
            "version": 1,
            "fields": {},
        }
        response = client.post("/api/v1/mappings/", json=payload)

        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "mapping_validation_error"


class TestGetMappings:
    """Tests for GET /api/v1/mappings and GET /api/v1/mappings/{mapping_id}."""

    def test_list_mappings_empty(
        self,
        client: TestClient,
    ) -> None:
        """Listing mappings when none exist returns an empty list."""
        response = client.get("/api/v1/mappings/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_mappings_after_create(
        self,
        client: TestClient,
    ) -> None:
        """Listing mappings after creating one returns that mapping."""
        client.post("/api/v1/mappings/", json=_valid_mapping_payload())

        response = client.get("/api/v1/mappings/")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert "mapping_id" in body[0]

    def test_get_mapping_by_id(
        self,
        client: TestClient,
    ) -> None:
        """Getting a mapping by ID returns the correct mapping."""
        post_resp = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        mapping_id = post_resp.json()["mapping_id"]

        response = client.get(f"/api/v1/mappings/{mapping_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["mapping_id"] == mapping_id
        assert body["version"] == 1

    def test_get_mapping_unknown_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Getting a mapping with an unknown ID returns 404."""
        unknown_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/mappings/{unknown_id}")

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "mapping_not_found"


class TestPutMappings:
    """Tests for PUT /api/v1/mappings/{mapping_id}."""

    def test_update_mapping_existing(
        self,
        client: TestClient,
    ) -> None:
        """Updating an existing mapping changes its configuration."""
        post_resp = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        mapping_id = post_resp.json()["mapping_id"]
        original_hash = post_resp.json()["policy_hash"]

        updated_payload = {
            "version": 1,
            "default_action": "keep",
            "fields": {
                "email": {"action": "hash", "options": {}},
                "name": {"action": "keep", "options": {}},
                "id": {"action": "keep", "options": {}},
            },
        }
        response = client.put(f"/api/v1/mappings/{mapping_id}", json=updated_payload)

        assert response.status_code == 200
        body = response.json()
        assert body["mapping_id"] == mapping_id
        assert body["default_action"] == "keep"
        assert body["fields"]["email"]["action"] == "hash"
        assert body["policy_hash"] != original_hash

    def test_update_mapping_unknown_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Updating a mapping with an unknown ID returns 404."""
        unknown_id = str(uuid.uuid4())

        response = client.put(
            f"/api/v1/mappings/{unknown_id}",
            json=_valid_mapping_payload(),
        )

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "mapping_not_found"


class TestDeleteMappings:
    """Tests for DELETE /api/v1/mappings/{mapping_id}."""

    def test_delete_mapping_existing_returns_204(
        self,
        client: TestClient,
    ) -> None:
        """Deleting an existing mapping returns 204 and removes it."""
        post_resp = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        mapping_id = post_resp.json()["mapping_id"]

        response = client.delete(f"/api/v1/mappings/{mapping_id}")

        assert response.status_code == 204

        # Verify it's gone.
        get_resp = client.get(f"/api/v1/mappings/{mapping_id}")
        assert get_resp.status_code == 404

    def test_delete_mapping_unknown_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Deleting a mapping with an unknown ID returns 404."""
        unknown_id = str(uuid.uuid4())

        response = client.delete(f"/api/v1/mappings/{unknown_id}")

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "mapping_not_found"


class TestValidateMapping:
    """Tests for POST /api/v1/mappings/validate."""

    def test_validate_mapping_all_fields_match(
        self,
        client: TestClient,
    ) -> None:
        """A mapping that covers all record fields is valid."""
        payload = {
            "mapping": {
                "version": 1,
                "fields": {
                    "id": {"action": "keep", "options": {}},
                    "name": {"action": "redact", "options": {}},
                    "email": {"action": "mask", "options": {}},
                },
            },
            "sample_record": {
                "id": "1",
                "name": "Alice",
                "email": "alice@example.com",
            },
        }
        response = client.post("/api/v1/mappings/validate", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["is_valid"] is True
        assert sorted(body["matched_fields"]) == ["email", "id", "name"]
        assert body["unmapped_fields"] == []
        assert body["missing_fields"] == []

    def test_validate_mapping_with_missing_fields(
        self,
        client: TestClient,
    ) -> None:
        """A mapping referencing fields not in the record reports missing fields."""
        payload = {
            "mapping": {
                "version": 1,
                "fields": {
                    "id": {"action": "keep", "options": {}},
                    "name": {"action": "redact", "options": {}},
                    "phone": {"action": "redact", "options": {}},
                },
            },
            "sample_record": {
                "id": "1",
                "name": "Alice",
                "email": "alice@example.com",
            },
        }
        response = client.post("/api/v1/mappings/validate", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["is_valid"] is False
        assert "phone" in body["missing_fields"]
        assert "email" in body["unmapped_fields"]


class TestPreviewMapping:
    """Tests for POST /api/v1/mappings/preview."""

    def test_preview_redact_action(
        self,
        client: TestClient,
    ) -> None:
        """Preview with REDACT action replaces value with placeholder."""
        payload = {
            "fields": {
                "name": {"action": "redact", "options": {}},
            },
            "sample_record": {"name": "Alice Smith"},
        }
        response = client.post("/api/v1/mappings/preview", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert len(body["entries"]) == 1
        entry = body["entries"][0]
        assert entry["field_name"] == "name"
        assert entry["original"] == "Alice Smith"
        assert entry["transformed"] == "[NAME_REDACTED]"
        assert entry["action"] == "redact"

    def test_preview_mask_action(
        self,
        client: TestClient,
    ) -> None:
        """Preview with MASK action partially hides the value."""
        payload = {
            "fields": {
                "email": {"action": "mask", "options": {}},
            },
            "sample_record": {"email": "alice@example.com"},
        }
        response = client.post("/api/v1/mappings/preview", json=payload)

        assert response.status_code == 200
        entry = response.json()["entries"][0]
        assert entry["field_name"] == "email"
        assert entry["transformed"] == "a***@example.com"
        assert entry["action"] == "mask"

    def test_preview_hash_action(
        self,
        client: TestClient,
    ) -> None:
        """Preview with HASH action returns a hash string."""
        payload = {
            "fields": {
                "name": {"action": "hash", "options": {}},
            },
            "sample_record": {"name": "Alice"},
        }
        response = client.post("/api/v1/mappings/preview", json=payload)

        assert response.status_code == 200
        entry = response.json()["entries"][0]
        assert entry["field_name"] == "name"
        assert entry["transformed"].startswith("hash_")
        assert entry["action"] == "hash"

    def test_preview_keep_action(
        self,
        client: TestClient,
    ) -> None:
        """Preview with KEEP action returns the value unchanged."""
        payload = {
            "fields": {
                "id": {"action": "keep", "options": {}},
            },
            "sample_record": {"id": "12345"},
        }
        response = client.post("/api/v1/mappings/preview", json=payload)

        assert response.status_code == 200
        entry = response.json()["entries"][0]
        assert entry["field_name"] == "id"
        assert entry["original"] == "12345"
        assert entry["transformed"] == "12345"
        assert entry["action"] == "keep"

    def test_preview_truncates_long_values(
        self,
        client: TestClient,
    ) -> None:
        """Preview truncates values longer than 200 characters."""
        long_value = "x" * 300
        payload = {
            "fields": {
                "data": {"action": "keep", "options": {}},
            },
            "sample_record": {"data": long_value},
        }
        response = client.post("/api/v1/mappings/preview", json=payload)

        assert response.status_code == 200
        entry = response.json()["entries"][0]
        assert len(entry["original"]) == 200
        assert len(entry["transformed"]) == 200


class TestSampleRecord:
    """Tests for POST /api/v1/mappings/sample."""

    def test_sample_jsonl_file(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Reading a sample from a JSONL file returns the first record."""
        jsonl_file = _create_jsonl_file(tmp_path)

        response = client.post(
            "/api/v1/mappings/sample",
            json={"source": str(jsonl_file)},
        )

        assert response.status_code == 200
        body = response.json()
        assert "record" in body
        assert body["field_count"] == 3
        assert body["record"]["id"] == "0"
        assert body["record"]["name"] == "user_0"

    def test_sample_csv_file(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Reading a sample from a CSV file returns the first data row."""
        csv_file = _create_csv_file(tmp_path)

        response = client.post(
            "/api/v1/mappings/sample",
            json={"source": str(csv_file)},
        )

        assert response.status_code == 200
        body = response.json()
        assert "record" in body
        assert body["field_count"] == 3
        assert body["record"]["id"] == "0"
        assert body["record"]["name"] == "user_0"

    def test_sample_nonexistent_file_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """A nonexistent file path returns 404."""
        response = client.post(
            "/api/v1/mappings/sample",
            json={"source": "/nonexistent/path.jsonl"},
        )

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "file_not_found"

    def test_sample_truncates_long_values(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Sample record values are truncated to 200 characters."""
        f = tmp_path / "long.jsonl"
        long_value = "y" * 300
        f.write_text(json.dumps({"data": long_value}) + "\n")

        response = client.post(
            "/api/v1/mappings/sample",
            json={"source": str(f)},
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["record"]["data"]) == 200

    def test_sample_values_are_strings(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """All values in the sample record are converted to strings."""
        f = tmp_path / "types.jsonl"
        f.write_text(json.dumps({"count": 42, "active": True, "rate": 3.14}) + "\n")

        response = client.post(
            "/api/v1/mappings/sample",
            json={"source": str(f)},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["record"]["count"] == "42"
        assert body["record"]["active"] == "True"
        assert body["record"]["rate"] == "3.14"


def _create_valid_mapping_yaml(tmp_path: Path) -> Path:
    """Create a temporary valid mapping YAML file.

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
        "  email:\n"
        "    action: mask\n"
        "  name:\n"
        "    action: redact\n"
        "  id:\n"
        "    action: keep\n",
    )
    return f


class TestLoadMappingYaml:
    """Tests for POST /api/v1/mappings/load-yaml."""

    def test_load_yaml_valid_returns_201(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A valid YAML mapping file returns 201 with mapping metadata."""
        yaml_file = _create_valid_mapping_yaml(tmp_path)

        response = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(yaml_file)},
        )

        assert response.status_code == 201
        body = response.json()
        assert "mapping_id" in body
        assert "policy_hash" in body
        assert "created_at" in body
        assert body["version"] == 1
        assert body["default_action"] == "redact"
        assert "email" in body["fields"]
        assert body["fields"]["email"]["action"] == "mask"
        assert body["fields"]["name"]["action"] == "redact"
        assert body["fields"]["id"]["action"] == "keep"

    def test_load_yaml_nonexistent_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """A nonexistent file path returns 404."""
        response = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": "/nonexistent/mapping.yaml"},
        )

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "file_not_found"

    def test_load_yaml_invalid_yaml_returns_422(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """An invalid YAML file returns 422."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{{{{ not: valid: yaml ::::\n")

        response = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(bad_file)},
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "mapping_parse_error"

    def test_load_yaml_missing_fields_returns_422(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A YAML file missing required 'fields' key returns 422."""
        bad_file = tmp_path / "incomplete.yaml"
        bad_file.write_text("version: 1\n")

        response = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(bad_file)},
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "mapping_parse_error"

    def test_load_yaml_stores_in_memory(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """A loaded mapping can be retrieved by ID via GET."""
        yaml_file = _create_valid_mapping_yaml(tmp_path)

        post_resp = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(yaml_file)},
        )
        mapping_id = post_resp.json()["mapping_id"]

        get_resp = client.get(f"/api/v1/mappings/{mapping_id}")

        assert get_resp.status_code == 200
        body = get_resp.json()
        assert body["mapping_id"] == mapping_id
        assert body["version"] == 1
        assert "email" in body["fields"]
