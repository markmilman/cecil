"""Unit tests for cecil.utils.paths — resource path resolution.

Tests cover both development mode (normal Python execution) and frozen
mode (simulated PyInstaller ``_MEIPASS`` environment).
"""

from __future__ import annotations

import sys

import pytest

from cecil.utils.paths import (
    _DEV_BASE_DIR,
    get_base_path,
    get_resource_path,
    get_ui_dist_path,
    is_frozen,
)


# ── is_frozen() ───────────────────────────────────────────────────────────


class TestIsFrozen:
    """Tests for the is_frozen() detection function."""

    def test_is_frozen_returns_false_in_development(self):
        """In a normal Python interpreter, is_frozen() should return False."""
        assert is_frozen() is False

    def test_is_frozen_returns_true_when_frozen_and_meipass(self, monkeypatch, tmp_path):
        """When sys.frozen is True and sys._MEIPASS exists, returns True."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        assert is_frozen() is True

    def test_is_frozen_returns_false_when_only_frozen(self, monkeypatch):
        """If sys.frozen is True but _MEIPASS is absent, returns False."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        # Ensure _MEIPASS is not set.
        if hasattr(sys, "_MEIPASS"):
            monkeypatch.delattr(sys, "_MEIPASS")
        assert is_frozen() is False


# ── get_base_path() ──────────────────────────────────────────────────────


class TestGetBasePath:
    """Tests for get_base_path() in dev and frozen modes."""

    def test_dev_mode_returns_src_cecil_dir(self):
        """In development, base path should be the src/cecil/ directory."""
        base = get_base_path()
        assert base == _DEV_BASE_DIR
        assert base.name == "cecil"
        assert (base / "utils" / "paths.py").exists()

    def test_frozen_mode_returns_meipass(self, monkeypatch, tmp_path):
        """In frozen mode, base path should be sys._MEIPASS."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        base = get_base_path()
        assert base == tmp_path


# ── get_resource_path() ──────────────────────────────────────────────────


class TestGetResourcePath:
    """Tests for get_resource_path() resolution and error handling."""

    def test_resolves_existing_file_in_dev(self):
        """Should resolve a known file relative to src/cecil/."""
        path = get_resource_path("utils/paths.py")
        assert path.exists()
        assert path.is_file()
        assert path.name == "paths.py"

    def test_resolves_existing_directory_in_dev(self):
        """Should resolve a known directory relative to src/cecil/."""
        path = get_resource_path("utils")
        assert path.exists()
        assert path.is_dir()

    def test_raises_file_not_found_for_missing_resource(self):
        """Should raise FileNotFoundError when the resource does not exist."""
        with pytest.raises(FileNotFoundError, match="nonexistent_resource"):
            get_resource_path("nonexistent_resource/missing.txt")

    def test_error_message_includes_frozen_status(self):
        """The FileNotFoundError message should indicate frozen status."""
        with pytest.raises(FileNotFoundError, match="frozen=False"):
            get_resource_path("does_not_exist.bin")

    def test_frozen_mode_resolves_from_meipass(self, monkeypatch, tmp_path):
        """In frozen mode, should resolve from sys._MEIPASS directory."""
        # Create a fake resource in the fake _MEIPASS.
        fake_resource = tmp_path / "ui_dist" / "index.html"
        fake_resource.parent.mkdir(parents=True, exist_ok=True)
        fake_resource.write_text("<html></html>")

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

        path = get_resource_path("ui_dist/index.html")
        assert path == fake_resource
        assert path.exists()

    def test_frozen_mode_raises_for_missing(self, monkeypatch, tmp_path):
        """In frozen mode, should raise FileNotFoundError for missing files."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

        with pytest.raises(FileNotFoundError, match="frozen=True"):
            get_resource_path("missing/file.txt")


# ── get_ui_dist_path() ──────────────────────────────────────────────────


class TestGetUiDistPath:
    """Tests for the get_ui_dist_path() convenience function."""

    def test_raises_when_ui_dist_missing(self):
        """Should raise FileNotFoundError when ui_dist/ does not exist.

        In normal development without a frontend build, ui_dist/ will
        not be present.
        """
        # This test relies on ui_dist/ not existing in the dev tree
        # (which is the expected state when the frontend hasn't been built).
        with pytest.raises(FileNotFoundError, match="ui_dist"):
            get_ui_dist_path()

    def test_returns_path_when_ui_dist_exists(self, monkeypatch, tmp_path):
        """Should return the ui_dist path when it exists in frozen mode."""
        ui_dist = tmp_path / "ui_dist"
        ui_dist.mkdir()

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

        path = get_ui_dist_path()
        assert path == ui_dist
        assert path.is_dir()


# ── Import re-exports ───────────────────────────────────────────────────


class TestUtilsReexports:
    """Verify that paths functions are importable from cecil.utils."""

    def test_get_resource_path_importable_from_utils(self):
        """get_resource_path should be importable from cecil.utils."""
        from cecil.utils import get_resource_path as imported_func

        assert callable(imported_func)

    def test_is_frozen_importable_from_utils(self):
        """is_frozen should be importable from cecil.utils."""
        from cecil.utils import is_frozen as imported_func

        assert callable(imported_func)

    def test_get_base_path_importable_from_utils(self):
        """get_base_path should be importable from cecil.utils."""
        from cecil.utils import get_base_path as imported_func

        assert callable(imported_func)

    def test_get_ui_dist_path_importable_from_utils(self):
        """get_ui_dist_path should be importable from cecil.utils."""
        from cecil.utils import get_ui_dist_path as imported_func

        assert callable(imported_func)
