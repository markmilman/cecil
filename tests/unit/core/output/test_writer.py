"""Tests for the JsonlWriter output module."""

from __future__ import annotations

import json
from pathlib import Path

from cecil.core.output.writer import JsonlWriter


class TestJsonlWriter:
    """Tests for JsonlWriter."""

    def test_writer_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Writer creates parent directories if they don't exist."""
        nested = tmp_path / "a" / "b" / "c" / "output.jsonl"
        writer = JsonlWriter(nested)
        writer.close()

        assert nested.parent.is_dir()

    def test_writer_writes_jsonl_records(self, tmp_path: Path) -> None:
        """Writer writes records as JSON Lines with newline separators."""
        out = tmp_path / "output.jsonl"
        writer = JsonlWriter(out)
        writer.write_record({"id": 1, "name": "alice"})
        writer.write_record({"id": 2, "name": "bob"})
        writer.close()

        lines = out.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"id": 1, "name": "alice"}
        assert json.loads(lines[1]) == {"id": 2, "name": "bob"}

    def test_writer_context_manager(self, tmp_path: Path) -> None:
        """Writer supports the context manager protocol."""
        out = tmp_path / "output.jsonl"
        with JsonlWriter(out) as writer:
            writer.write_record({"key": "value"})

        lines = out.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0]) == {"key": "value"}

    def test_writer_tracks_count(self, tmp_path: Path) -> None:
        """Writer tracks the number of records written."""
        out = tmp_path / "output.jsonl"
        with JsonlWriter(out) as writer:
            assert writer.records_written == 0
            writer.write_record({"a": 1})
            assert writer.records_written == 1
            writer.write_record({"b": 2})
            writer.write_record({"c": 3})
            assert writer.records_written == 3

    def test_writer_handles_unicode(self, tmp_path: Path) -> None:
        """Writer correctly handles Unicode characters in records."""
        out = tmp_path / "output.jsonl"
        with JsonlWriter(out) as writer:
            writer.write_record({"name": "日本語テスト", "emoji": "🎉"})

        lines = out.read_text(encoding="utf-8").strip().split("\n")
        parsed = json.loads(lines[0])
        assert parsed["name"] == "日本語テスト"
        assert parsed["emoji"] == "🎉"
