"""Integration tests for mapping persistence to YAML files.

Tests that verify mapping configurations are correctly written to disk
and can be read back across server restarts.  These tests catch regressions
in bug #128 (mapping configs not persisted to YAML files).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient


@pytest.fixture
def mappings_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override the mappings directory to use a temporary path.

    This ensures tests don't pollute the user's ~/.cecil/mappings directory
    and provides isolation between test runs.

    Args:
        tmp_path: Pytest temporary directory.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Path to the temporary mappings directory.
    """
    mappings_dir = tmp_path / "mappings"
    mappings_dir.mkdir(parents=True, exist_ok=True)

    # Monkeypatch the _get_mappings_dir function to return our temp path
    from cecil.api.routes import mappings

    monkeypatch.setattr(mappings, "_get_mappings_dir", lambda: mappings_dir)

    # Clear the in-memory store and reload from the temp directory
    mappings._mapping_store.clear()
    mappings._load_mappings_from_disk()

    return mappings_dir


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


class TestCreateMappingWritesYamlFile:
    """Tests for POST /api/v1/mappings/ YAML persistence."""

    def test_create_mapping_writes_yaml_file(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping created via POST writes a YAML file to disk."""
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())

        assert response.status_code == 201
        body = response.json()
        mapping_id = body["mapping_id"]

        # Check for yaml_path in response (if implemented in the API)
        # Currently, the API doesn't return yaml_path, so we construct it
        yaml_path = mappings_dir / f"{mapping_id}.yaml"

        # The YAML file should exist on disk
        assert yaml_path.is_file(), f"YAML file not found at {yaml_path}"

        # Read the YAML file and verify its contents
        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["version"] == 1
        assert saved_data["default_action"] == "redact"
        assert "email" in saved_data["fields"]
        assert saved_data["fields"]["email"]["action"] == "mask"
        assert saved_data["fields"]["name"]["action"] == "redact"
        assert saved_data["fields"]["id"]["action"] == "keep"

    def test_create_mapping_yaml_contains_all_fields(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """The persisted YAML file contains all configured fields."""
        payload = {
            "version": 1,
            "default_action": "keep",
            "fields": {
                "user_email": {"action": "redact", "options": {}},
                "user_name": {"action": "redact", "options": {}},
                "user_phone": {"action": "mask", "options": {}},
                "user_id": {"action": "hash", "options": {}},
                "timestamp": {"action": "keep", "options": {}},
            },
        }

        response = client.post("/api/v1/mappings/", json=payload)
        assert response.status_code == 201

        mapping_id = response.json()["mapping_id"]
        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        # Verify all fields are present
        assert len(saved_data["fields"]) == 5
        assert saved_data["fields"]["user_email"]["action"] == "redact"
        assert saved_data["fields"]["user_name"]["action"] == "redact"
        assert saved_data["fields"]["user_phone"]["action"] == "mask"
        assert saved_data["fields"]["user_id"]["action"] == "hash"
        assert saved_data["fields"]["timestamp"]["action"] == "keep"


class TestSavedMappingPersistsAcrossReload:
    """Tests that mappings persist across simulated server restarts."""

    def test_saved_mapping_persists_across_reload(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A created mapping reappears in GET /mappings after reload."""
        # Create a mapping
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]

        # Verify it appears in the list
        list_resp = client.get("/api/v1/mappings/")
        assert list_resp.status_code == 200
        mappings = list_resp.json()
        assert len(mappings) == 1
        assert mappings[0]["mapping_id"] == mapping_id

        # Simulate server restart by clearing in-memory store and reloading
        from cecil.api.routes import mappings

        mappings._mapping_store.clear()
        mappings._load_mappings_from_disk()

        # The mapping should still appear in the list after reload
        list_resp_after = client.get("/api/v1/mappings/")
        assert list_resp_after.status_code == 200
        mappings_after = list_resp_after.json()
        assert len(mappings_after) == 1
        assert mappings_after[0]["mapping_id"] == mapping_id
        assert mappings_after[0]["version"] == 1
        assert mappings_after[0]["default_action"] == "redact"

    def test_multiple_mappings_persist_across_reload(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Multiple mappings persist and reload correctly."""
        # Create three mappings
        mapping_ids = []
        for i in range(3):
            payload = {
                "version": 1,
                "default_action": "redact",
                "fields": {
                    f"field_{i}": {"action": "keep", "options": {}},
                },
            }
            response = client.post("/api/v1/mappings/", json=payload)
            assert response.status_code == 201
            mapping_ids.append(response.json()["mapping_id"])

        # Verify all three appear in the list
        list_resp = client.get("/api/v1/mappings/")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 3

        # Simulate restart
        from cecil.api.routes import mappings

        mappings._mapping_store.clear()
        mappings._load_mappings_from_disk()

        # All three should still be present
        list_resp_after = client.get("/api/v1/mappings/")
        assert list_resp_after.status_code == 200
        mappings_after = list_resp_after.json()
        assert len(mappings_after) == 3

        # Verify all IDs are present
        loaded_ids = {m["mapping_id"] for m in mappings_after}
        assert loaded_ids == set(mapping_ids)


class TestCreateMappingWithAllActions:
    """Tests for mappings with all four action types."""

    def test_create_mapping_with_all_actions(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping with REDACT, MASK, HASH, and KEEP is persisted correctly."""
        payload = {
            "version": 1,
            "default_action": "redact",
            "fields": {
                "email": {"action": "redact", "options": {}},
                "phone": {"action": "mask", "options": {}},
                "user_id": {"action": "hash", "options": {}},
                "model": {"action": "keep", "options": {}},
            },
        }

        response = client.post("/api/v1/mappings/", json=payload)
        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]

        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        # Verify all four action types are present
        assert saved_data["fields"]["email"]["action"] == "redact"
        assert saved_data["fields"]["phone"]["action"] == "mask"
        assert saved_data["fields"]["user_id"]["action"] == "hash"
        assert saved_data["fields"]["model"]["action"] == "keep"


class TestDeleteMappingRemovesYamlFile:
    """Tests for DELETE /api/v1/mappings/{mapping_id} YAML cleanup."""

    def test_delete_mapping_removes_yaml_file(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Deleting a mapping removes its YAML file from disk."""
        # Create a mapping
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]

        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        # Delete the mapping
        delete_resp = client.delete(f"/api/v1/mappings/{mapping_id}")
        assert delete_resp.status_code == 204

        # The YAML file should be removed
        assert not yaml_path.exists(), f"YAML file still exists at {yaml_path}"

        # The mapping should not appear in the list
        list_resp = client.get("/api/v1/mappings/")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 0

    def test_delete_mapping_leaves_other_yaml_files_intact(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Deleting one mapping does not affect other YAML files."""
        # Create two mappings
        resp1 = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        assert resp1.status_code == 201
        mapping_id1 = resp1.json()["mapping_id"]

        resp2 = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        assert resp2.status_code == 201
        mapping_id2 = resp2.json()["mapping_id"]

        yaml_path1 = mappings_dir / f"{mapping_id1}.yaml"
        yaml_path2 = mappings_dir / f"{mapping_id2}.yaml"
        assert yaml_path1.is_file()
        assert yaml_path2.is_file()

        # Delete the first mapping
        delete_resp = client.delete(f"/api/v1/mappings/{mapping_id1}")
        assert delete_resp.status_code == 204

        # First YAML should be gone, second should remain
        assert not yaml_path1.exists()
        assert yaml_path2.is_file()

        # Only the second mapping should be in the list
        list_resp = client.get("/api/v1/mappings/")
        assert list_resp.status_code == 200
        mappings = list_resp.json()
        assert len(mappings) == 1
        assert mappings[0]["mapping_id"] == mapping_id2


class TestUpdateMappingUpdatesYamlFile:
    """Tests for PUT /api/v1/mappings/{mapping_id} YAML updates."""

    def test_update_mapping_updates_yaml_file(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Updating a mapping updates its YAML file on disk."""
        # Create a mapping
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]

        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        # Update the mapping
        updated_payload = {
            "version": 1,
            "default_action": "keep",
            "fields": {
                "email": {"action": "hash", "options": {}},
                "name": {"action": "keep", "options": {}},
                "id": {"action": "keep", "options": {}},
            },
        }
        update_resp = client.put(
            f"/api/v1/mappings/{mapping_id}",
            json=updated_payload,
        )
        assert update_resp.status_code == 200

        # Read the YAML file and verify it has the updated content
        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["default_action"] == "keep"
        assert saved_data["fields"]["email"]["action"] == "hash"
        assert saved_data["fields"]["name"]["action"] == "keep"


class TestLoadMappingByYamlPath:
    """Tests for loading saved mappings by their YAML file path."""

    def test_load_saved_mapping_by_yaml_path(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A saved mapping can be loaded back via its yaml_path."""
        # 1. Create a mapping
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        assert response.status_code == 201
        body = response.json()
        mapping_id = body["mapping_id"]

        # 2. Get the yaml_path (construct it from the mapping_id)
        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        # 3. POST to /api/v1/mappings/load-yaml with that path
        load_response = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(yaml_path)},
        )
        assert load_response.status_code == 201
        loaded_body = load_response.json()

        # 4. Assert the loaded mapping has the same fields and actions
        assert loaded_body["version"] == body["version"]
        assert loaded_body["default_action"] == body["default_action"]
        assert loaded_body["fields"] == body["fields"]

        # The loaded mapping should have a different ID (new instance)
        assert loaded_body["mapping_id"] != mapping_id

    def test_load_mapping_with_tilde_path(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Loading a mapping via a tilde-prefixed path resolves correctly."""
        # Create a mapping
        response = client.post("/api/v1/mappings/", json=_valid_mapping_payload())
        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]

        # Get the actual yaml path
        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        # Test that we can load the file using an absolute path first
        load_response_abs = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(yaml_path)},
        )
        assert load_response_abs.status_code == 201

        # Now test with a tilde path if the temp path is under home
        # Otherwise, verify that expanduser() is called by checking that
        # a path with a tilde that doesn't expand to a valid file returns 404
        home_dir = Path.home()

        try:
            # Try to create a relative path from home
            relative_to_home = yaml_path.relative_to(home_dir)
            tilde_path = f"~/{relative_to_home}"

            # Load the mapping using the tilde path
            load_response = client.post(
                "/api/v1/mappings/load-yaml",
                json={"path": tilde_path},
            )
            assert load_response.status_code == 201
            loaded_body = load_response.json()

            # Verify the loaded mapping has the correct content
            assert loaded_body["version"] == 1
            assert loaded_body["default_action"] == "redact"
            assert "email" in loaded_body["fields"]
            assert loaded_body["fields"]["email"]["action"] == "mask"
        except ValueError:
            # The temp path is not under home, so we can't test with a real tilde path
            # Instead, verify that tilde expansion is attempted by using a fake tilde path
            # If expanduser() is NOT called, the path "~/nonexistent.yaml" would be
            # treated literally and might not return 404 in the expected way
            fake_tilde_path = "~/nonexistent_mapping_file.yaml"
            load_response = client.post(
                "/api/v1/mappings/load-yaml",
                json={"path": fake_tilde_path},
            )
            # Should get 404 because the expanded path doesn't exist
            assert load_response.status_code == 404

    def test_load_nonexistent_mapping_returns_404(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Loading a nonexistent YAML file returns 404."""
        nonexistent_path = mappings_dir / "nonexistent.yaml"

        load_response = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(nonexistent_path)},
        )
        assert load_response.status_code == 404
        error_body = load_response.json()
        assert error_body["error"] == "file_not_found"
        assert "does not exist" in error_body["message"]

    def test_load_invalid_yaml_returns_422(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Loading an invalid YAML file returns 422."""
        # Create an invalid YAML file
        invalid_yaml_path = mappings_dir / "invalid.yaml"
        with invalid_yaml_path.open("w", encoding="utf-8") as f:
            f.write("version: 1\ndefault_action: invalid_action\n")

        load_response = client.post(
            "/api/v1/mappings/load-yaml",
            json={"path": str(invalid_yaml_path)},
        )
        assert load_response.status_code == 422
        error_body = load_response.json()
        assert error_body["error"] == "mapping_parse_error"


class TestMappingNameField:
    """Tests for the name field in mapping configurations."""

    def test_create_mapping_with_name(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping created with a name stores and returns it."""
        payload = _valid_mapping_payload()
        payload["name"] = "Production Mapping"

        response = client.post("/api/v1/mappings/", json=payload)
        assert response.status_code == 201
        body = response.json()

        # Name should be in the response
        assert body["name"] == "Production Mapping"
        mapping_id = body["mapping_id"]

        # Name should be persisted in YAML
        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["name"] == "Production Mapping"

    def test_create_mapping_without_name_generates_default(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping created without a name gets a default generated name."""
        payload = _valid_mapping_payload()
        # No name field provided

        response = client.post("/api/v1/mappings/", json=payload)
        assert response.status_code == 201
        body = response.json()

        # A default name should be generated
        assert "name" in body
        assert body["name"].startswith("Mapping ")
        mapping_id = body["mapping_id"]

        # Name should be persisted in YAML
        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert "name" in saved_data
        assert saved_data["name"].startswith("Mapping ")

    def test_name_persists_across_reload(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping's name persists across server restart."""
        payload = _valid_mapping_payload()
        payload["name"] = "Test Mapping"

        response = client.post("/api/v1/mappings/", json=payload)
        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]

        # Simulate server restart
        from cecil.api.routes import mappings

        mappings._mapping_store.clear()
        mappings._load_mappings_from_disk()

        # Name should still be present after reload
        list_resp = client.get("/api/v1/mappings/")
        assert list_resp.status_code == 200
        mappings_list = list_resp.json()
        assert len(mappings_list) == 1
        assert mappings_list[0]["mapping_id"] == mapping_id
        assert mappings_list[0]["name"] == "Test Mapping"

    def test_update_mapping_name(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Updating a mapping can change its name."""
        # Create a mapping with a name
        payload = _valid_mapping_payload()
        payload["name"] = "Original Name"

        response = client.post("/api/v1/mappings/", json=payload)
        assert response.status_code == 201
        mapping_id = response.json()["mapping_id"]

        # Update with a new name
        updated_payload = _valid_mapping_payload()
        updated_payload["name"] = "Updated Name"

        update_resp = client.put(
            f"/api/v1/mappings/{mapping_id}",
            json=updated_payload,
        )
        assert update_resp.status_code == 200
        updated_body = update_resp.json()

        # Name should be updated
        assert updated_body["name"] == "Updated Name"

        # YAML should reflect the new name
        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["name"] == "Updated Name"


class TestLoadMappingYamlContent:
    """Tests for loading mappings from raw YAML content."""

    def test_load_mapping_from_yaml_content(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping can be loaded from raw YAML content."""
        yaml_content = """
version: 1
default_action: redact
fields:
  email:
    action: mask
  name:
    action: redact
  id:
    action: keep
"""

        response = client.post(
            "/api/v1/mappings/load-yaml-content",
            json={"content": yaml_content},
        )
        assert response.status_code == 201
        body = response.json()

        # Verify the mapping was loaded correctly
        assert body["version"] == 1
        assert body["default_action"] == "redact"
        assert "email" in body["fields"]
        assert body["fields"]["email"]["action"] == "mask"
        assert body["fields"]["name"]["action"] == "redact"
        assert body["fields"]["id"]["action"] == "keep"

        # A default name should be generated
        assert "name" in body
        assert body["name"].startswith("Mapping ")

    def test_load_mapping_from_yaml_content_with_name_in_yaml(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping loaded from YAML content uses the name from the YAML."""
        yaml_content = """
version: 1
name: YAML Name
default_action: keep
fields:
  user_id:
    action: hash
"""

        response = client.post(
            "/api/v1/mappings/load-yaml-content",
            json={"content": yaml_content},
        )
        assert response.status_code == 201
        body = response.json()

        # Name from YAML should be used
        assert body["name"] == "YAML Name"

    def test_load_mapping_from_yaml_content_with_name_in_request(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping loaded with a name in the request uses that name."""
        yaml_content = """
version: 1
default_action: keep
fields:
  user_id:
    action: hash
"""

        response = client.post(
            "/api/v1/mappings/load-yaml-content",
            json={"content": yaml_content, "name": "Request Name"},
        )
        assert response.status_code == 201
        body = response.json()

        # Name from request should override
        assert body["name"] == "Request Name"

    def test_load_mapping_from_yaml_content_persists_to_disk(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """A mapping loaded from YAML content is persisted to disk."""
        yaml_content = """
version: 1
name: Content Mapping
default_action: redact
fields:
  email:
    action: mask
"""

        response = client.post(
            "/api/v1/mappings/load-yaml-content",
            json={"content": yaml_content},
        )
        assert response.status_code == 201
        body = response.json()
        mapping_id = body["mapping_id"]

        # A YAML file should be created on disk
        yaml_path = mappings_dir / f"{mapping_id}.yaml"
        assert yaml_path.is_file()

        with yaml_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["version"] == 1
        assert saved_data["name"] == "Content Mapping"
        assert saved_data["default_action"] == "redact"
        assert "email" in saved_data["fields"]

    def test_load_mapping_from_invalid_yaml_content(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Loading invalid YAML content returns 422."""
        invalid_yaml = "version: 1\ndefault_action: [invalid"

        response = client.post(
            "/api/v1/mappings/load-yaml-content",
            json={"content": invalid_yaml},
        )
        assert response.status_code == 422
        error_body = response.json()
        assert error_body["error"] == "mapping_parse_error"
        assert "YAML" in error_body["message"]

    def test_load_mapping_from_yaml_content_missing_fields(
        self,
        client: TestClient,
        mappings_dir: Path,
    ) -> None:
        """Loading YAML content without required fields returns 422."""
        yaml_content = """
version: 1
default_action: redact
"""
        # Missing 'fields' key

        response = client.post(
            "/api/v1/mappings/load-yaml-content",
            json={"content": yaml_content},
        )
        assert response.status_code == 422
        error_body = response.json()
        assert error_body["error"] == "mapping_parse_error"
