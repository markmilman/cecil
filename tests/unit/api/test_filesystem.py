"""Tests for the filesystem browse API endpoint.

Covers: default path, explicit path, path traversal blocking, non-existent
directory, permission errors, hidden file exclusion, show_all mode, file
format detection, parent path computation, and symlink handling.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


class TestBrowseDefaults:
    """Tests for default browsing behaviour."""

    def test_browse_defaults_to_home_directory(
        self,
        client: TestClient,
    ) -> None:
        """GET /browse with no params returns the user's home directory."""
        resp = client.get("/api/v1/filesystem/browse")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_path"] == str(Path.home())
        assert data["error"] is None

    def test_browse_returns_parent_path(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Browse a subdirectory and verify parent_path is populated."""
        subdir = tmp_path / "child"
        subdir.mkdir()
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(subdir)})
        data = resp.json()
        assert data["parent_path"] == str(tmp_path)

    def test_browse_root_has_no_parent(
        self,
        client: TestClient,
    ) -> None:
        """Browsing the filesystem root returns parent_path=None."""
        resp = client.get("/api/v1/filesystem/browse", params={"path": "/"})
        data = resp.json()
        assert data["parent_path"] is None


class TestBrowseExplicitPath:
    """Tests for browsing an explicit directory."""

    def test_browse_explicit_directory(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Browse a tmp directory with known contents."""
        # Create test structure.
        (tmp_path / "subdir").mkdir()
        (tmp_path / "data.jsonl").write_text('{"a":1}\n')
        (tmp_path / "notes.txt").write_text("hello")

        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        data = resp.json()

        assert data["current_path"] == str(tmp_path)
        assert data["error"] is None

        dir_names = [d["name"] for d in data["directories"]]
        assert "subdir" in dir_names

        file_names = [f["name"] for f in data["files"]]
        assert "data.jsonl" in file_names
        # .txt is not a supported format — should be filtered out.
        assert "notes.txt" not in file_names

    def test_browse_includes_csv_and_parquet(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Supported formats (CSV, Parquet) appear in filtered mode."""
        (tmp_path / "report.csv").write_text("a,b\n1,2\n")
        (tmp_path / "table.parquet").write_bytes(b"\x00" * 10)

        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        data = resp.json()
        file_names = [f["name"] for f in data["files"]]
        assert "report.csv" in file_names
        assert "table.parquet" in file_names

    def test_browse_show_all_includes_unsupported_formats(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """show_all=true includes files with unsupported extensions."""
        (tmp_path / "notes.txt").write_text("hello")
        (tmp_path / "data.jsonl").write_text('{"a":1}\n')

        resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(tmp_path), "show_all": "true"},
        )
        data = resp.json()
        file_names = [f["name"] for f in data["files"]]
        assert "notes.txt" in file_names
        assert "data.jsonl" in file_names


class TestHiddenFiles:
    """Tests for hidden file (dotfile) exclusion."""

    def test_browse_excludes_hidden_files_by_default(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Dotfiles and dot-directories are excluded unless show_all."""
        (tmp_path / ".hidden").write_text("secret")
        (tmp_path / ".hiddendir").mkdir()
        (tmp_path / "visible.jsonl").write_text('{"a":1}\n')

        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        data = resp.json()
        all_names = [e["name"] for e in data["directories"] + data["files"]]
        assert ".hidden" not in all_names
        assert ".hiddendir" not in all_names
        assert "visible.jsonl" in all_names

    def test_browse_show_all_includes_hidden_files(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """show_all=true includes dotfiles."""
        (tmp_path / ".hidden").write_text("secret")
        (tmp_path / ".hiddendir").mkdir()

        resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(tmp_path), "show_all": "true"},
        )
        data = resp.json()
        all_names = [e["name"] for e in data["directories"] + data["files"]]
        assert ".hidden" in all_names
        assert ".hiddendir" in all_names


class TestFileFormatDetection:
    """Tests for automatic file format detection."""

    def test_browse_detects_jsonl_format(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """JSONL files have format='jsonl'."""
        (tmp_path / "data.jsonl").write_text('{"a":1}\n')
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        files = resp.json()["files"]
        jsonl_file = next(f for f in files if f["name"] == "data.jsonl")
        assert jsonl_file["format"] == "jsonl"

    def test_browse_detects_csv_format(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """CSV files have format='csv'."""
        (tmp_path / "data.csv").write_text("a,b\n1,2\n")
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        files = resp.json()["files"]
        csv_file = next(f for f in files if f["name"] == "data.csv")
        assert csv_file["format"] == "csv"

    def test_browse_detects_parquet_format(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Parquet files have format='parquet'."""
        (tmp_path / "data.parquet").write_bytes(b"\x00" * 10)
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        files = resp.json()["files"]
        parquet_file = next(f for f in files if f["name"] == "data.parquet")
        assert parquet_file["format"] == "parquet"

    def test_browse_directories_have_no_format(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Directory entries have format=None."""
        (tmp_path / "subdir").mkdir()
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        dirs = resp.json()["directories"]
        subdir = next(d for d in dirs if d["name"] == "subdir")
        assert subdir["format"] is None
        assert subdir["is_directory"] is True


class TestFileMetadata:
    """Tests for file entry metadata fields."""

    def test_browse_file_has_size(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """File entries include a non-None size."""
        content = '{"a":1}\n'
        (tmp_path / "data.jsonl").write_text(content)
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        files = resp.json()["files"]
        jsonl_file = next(f for f in files if f["name"] == "data.jsonl")
        assert jsonl_file["size"] is not None
        assert jsonl_file["size"] > 0

    def test_browse_directory_has_no_size(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Directory entries have size=None."""
        (tmp_path / "subdir").mkdir()
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        dirs = resp.json()["directories"]
        subdir = next(d for d in dirs if d["name"] == "subdir")
        assert subdir["size"] is None

    def test_browse_file_has_modified_timestamp(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """File entries include a modified timestamp."""
        (tmp_path / "data.jsonl").write_text('{"a":1}\n')
        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        files = resp.json()["files"]
        jsonl_file = next(f for f in files if f["name"] == "data.jsonl")
        assert jsonl_file["modified"] is not None


class TestSecurityPathTraversal:
    """Tests for path traversal blocking."""

    def test_browse_blocks_dotdot_traversal(
        self,
        client: TestClient,
    ) -> None:
        """Paths containing .. are rejected."""
        resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": "/tmp/../etc"},  # noqa: S108
        )
        data = resp.json()
        assert data["error"] == "Path traversal is not allowed"
        assert data["directories"] == []
        assert data["files"] == []

    def test_browse_blocks_nested_traversal(
        self,
        client: TestClient,
    ) -> None:
        """Deeply nested .. traversal is also blocked."""
        resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": "/home/user/../../etc/passwd"},
        )
        data = resp.json()
        assert data["error"] == "Path traversal is not allowed"


class TestSecurityErrorHandling:
    """Tests for error handling (non-existent paths, permissions)."""

    def test_browse_nonexistent_directory(
        self,
        client: TestClient,
    ) -> None:
        """Non-existent path returns error in response body."""
        resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": "/nonexistent/path/that/does/not/exist"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] is not None
        assert "does not exist" in data["error"]

    def test_browse_file_instead_of_directory(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Browsing a file path (not directory) returns an error."""
        file_path = tmp_path / "data.jsonl"
        file_path.write_text('{"a":1}\n')
        resp = client.get(
            "/api/v1/filesystem/browse",
            params={"path": str(file_path)},
        )
        data = resp.json()
        assert data["error"] is not None
        assert "not a directory" in data["error"]

    @pytest.mark.skipif(
        os.getuid() == 0,
        reason="Root user bypasses permission checks",
    )
    def test_browse_unreadable_directory(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Directory without read permission returns an error."""
        no_read = tmp_path / "noaccess"
        no_read.mkdir()
        no_read.chmod(0o000)
        try:
            resp = client.get(
                "/api/v1/filesystem/browse",
                params={"path": str(no_read)},
            )
            data = resp.json()
            assert data["error"] is not None
        finally:
            no_read.chmod(0o755)


class TestSortingOrder:
    """Tests for alphabetical sorting of entries."""

    def test_browse_entries_sorted_alphabetically(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Directories and files are sorted case-insensitively."""
        (tmp_path / "Zebra").mkdir()
        (tmp_path / "alpha").mkdir()
        (tmp_path / "beta.jsonl").write_text('{"a":1}\n')
        (tmp_path / "Alpha.csv").write_text("a\n1\n")

        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        data = resp.json()

        dir_names = [d["name"] for d in data["directories"]]
        assert dir_names == sorted(dir_names, key=str.lower)

        file_names = [f["name"] for f in data["files"]]
        assert file_names == sorted(file_names, key=str.lower)


class TestSymlinks:
    """Tests for symlink handling."""

    def test_browse_follows_symlinked_directory(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Symlinked directories that stay within scope are browsable."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "data.jsonl").write_text('{"a":1}\n')
        link = tmp_path / "link"
        link.symlink_to(real_dir)

        resp = client.get("/api/v1/filesystem/browse", params={"path": str(link)})
        data = resp.json()
        assert data["error"] is None
        file_names = [f["name"] for f in data["files"]]
        assert "data.jsonl" in file_names

    def test_browse_handles_broken_symlink(
        self,
        client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Broken symlinks are silently skipped (no crash)."""
        (tmp_path / "broken_link").symlink_to(tmp_path / "nonexistent_target")
        (tmp_path / "valid.jsonl").write_text('{"a":1}\n')

        resp = client.get("/api/v1/filesystem/browse", params={"path": str(tmp_path)})
        data = resp.json()
        assert data["error"] is None
        all_names = [e["name"] for e in data["directories"] + data["files"]]
        assert "broken_link" not in all_names
        assert "valid.jsonl" in all_names
