"""Tests for the ``cecil scan`` CLI subcommand."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cecil.cli import build_parser, main
from cecil.cli.scan import (
    _parse_source_uri,
    _resolve_output_path,
    run_scan,
)
from tests.fixtures.pii_samples import generate_sample_csv


# ── URI parsing ──────────────────────────────────────────────────────


class TestParseSourceUri:
    """Tests for _parse_source_uri."""

    def test_parse_source_uri_valid_local(self) -> None:
        result = _parse_source_uri("local://some/file.jsonl")
        assert result == Path("some/file.jsonl")

    def test_parse_source_uri_absolute_path(self, tmp_path: Path) -> None:
        uri = f"local://{tmp_path}/data.csv"
        result = _parse_source_uri(uri)
        assert result == tmp_path / "data.csv"

    def test_parse_source_uri_rejects_unsupported_scheme(self) -> None:
        from cecil.utils.errors import CecilError

        with pytest.raises(CecilError, match="Unsupported source URI scheme"):
            _parse_source_uri("s3://bucket/key.jsonl")


# ── Output path resolution ───────────────────────────────────────────


class TestResolveOutputPath:
    """Tests for _resolve_output_path."""

    def test_resolve_output_path_jsonl(self, tmp_path: Path) -> None:
        result = _resolve_output_path(Path("input.jsonl"), str(tmp_path), "jsonl")
        assert result == tmp_path / "input_sanitized.jsonl"

    def test_resolve_output_path_csv(self, tmp_path: Path) -> None:
        result = _resolve_output_path(Path("data.csv"), str(tmp_path), "csv")
        assert result == tmp_path / "data_sanitized.csv"

    def test_resolve_output_path_creates_directory(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "new" / "nested"
        _resolve_output_path(Path("test.jsonl"), str(new_dir), "jsonl")
        assert new_dir.is_dir()


# ── Scan without --unsafe-passthrough ────────────────────────────────


class TestScanSafetyGate:
    """Tests that scan refuses to run without --unsafe-passthrough."""

    def test_scan_refuses_without_passthrough(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["scan", "--source", "local://test.jsonl"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Sanitization engine not yet available" in captured.err
        assert "--unsafe-passthrough" in captured.err

    def test_scan_refuses_without_passthrough_via_run_scan(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["scan", "--source", "local://test.jsonl"])
        exit_code = run_scan(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Sanitization engine not yet available" in captured.err


# ── Scan with --unsafe-passthrough (JSONL) ───────────────────────────


class TestScanJsonlPassthrough:
    """Tests for scan in pass-through mode with JSONL files."""

    def test_scan_jsonl_writes_output(
        self,
        sample_jsonl_path: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out_dir = str(tmp_path / "output")
        exit_code = main(
            [
                "scan",
                "--source",
                f"local://{sample_jsonl_path}",
                "--output",
                out_dir,
                "--unsafe-passthrough",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Sanitized data saved to" in captured.out

        output_file = tmp_path / "output" / "sample_logs_sanitized.jsonl"
        assert output_file.exists()

        lines = output_file.read_text().strip().splitlines()
        assert len(lines) > 0
        # Every line must be valid JSON.
        for line in lines:
            json.loads(line)

    def test_scan_jsonl_record_count_matches(
        self,
        sample_jsonl_path: Path,
        tmp_path: Path,
    ) -> None:
        out_dir = str(tmp_path / "output")
        main(
            [
                "scan",
                "--source",
                f"local://{sample_jsonl_path}",
                "--output",
                out_dir,
                "--unsafe-passthrough",
            ]
        )

        output_file = tmp_path / "output" / "sample_logs_sanitized.jsonl"
        input_count = len(sample_jsonl_path.read_text().strip().splitlines())
        output_count = len(output_file.read_text().strip().splitlines())
        assert input_count == output_count

    def test_scan_jsonl_passthrough_warning_logged(
        self,
        sample_jsonl_path: Path,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        import logging

        with caplog.at_level(logging.WARNING):
            main(
                [
                    "-v",
                    "scan",
                    "--source",
                    f"local://{sample_jsonl_path}",
                    "--output",
                    str(tmp_path / "output"),
                    "--unsafe-passthrough",
                ]
            )
        assert any("pass-through mode" in r.message for r in caplog.records)


# ── Scan with --unsafe-passthrough (CSV) ─────────────────────────────


class TestScanCsvPassthrough:
    """Tests for scan in pass-through mode with CSV files."""

    def test_scan_csv_writes_output(
        self,
        sample_csv_path: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out_dir = str(tmp_path / "output")
        exit_code = main(
            [
                "scan",
                "--source",
                f"local://{sample_csv_path}",
                "--output",
                out_dir,
                "--unsafe-passthrough",
            ]
        )
        assert exit_code == 0

        output_file = tmp_path / "output" / "sample_records_sanitized.csv"
        assert output_file.exists()

        lines = output_file.read_text().strip().splitlines()
        # At least header + 1 data row.
        assert len(lines) >= 2

    def test_scan_csv_record_count_matches(
        self,
        sample_csv_path: Path,
        tmp_path: Path,
    ) -> None:
        out_dir = str(tmp_path / "output")
        main(
            [
                "scan",
                "--source",
                f"local://{sample_csv_path}",
                "--output",
                out_dir,
                "--unsafe-passthrough",
            ]
        )

        output_file = tmp_path / "output" / "sample_records_sanitized.csv"
        # Input: header + N data rows.  Output: header + N data rows.
        input_data_rows = len(sample_csv_path.read_text().strip().splitlines()) - 1
        output_data_rows = len(output_file.read_text().strip().splitlines()) - 1
        assert input_data_rows == output_data_rows


# ── Quarantine directory ─────────────────────────────────────────────


class TestScanQuarantine:
    """Tests for quarantine directory option."""

    def test_scan_with_quarantine_dir(
        self,
        sample_jsonl_path: Path,
        tmp_path: Path,
    ) -> None:
        q_dir = str(tmp_path / "quarantine")
        exit_code = main(
            [
                "scan",
                "--source",
                f"local://{sample_jsonl_path}",
                "--output",
                str(tmp_path / "output"),
                "--quarantine-dir",
                q_dir,
                "--unsafe-passthrough",
            ]
        )
        assert exit_code == 0
        assert Path(q_dir).is_dir()


# ── Error cases ──────────────────────────────────────────────────────


class TestScanErrors:
    """Tests for scan error handling."""

    def test_scan_nonexistent_file(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        exit_code = main(
            [
                "scan",
                "--source",
                "local:///nonexistent/path.jsonl",
                "--output",
                str(tmp_path),
                "--unsafe-passthrough",
            ]
        )
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_scan_unsupported_uri_scheme(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        exit_code = main(
            [
                "scan",
                "--source",
                "s3://bucket/key.jsonl",
                "--output",
                ".",
                "--unsafe-passthrough",
            ]
        )
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Unsupported source URI scheme" in captured.err

    def test_scan_unsupported_output_format(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Create a minimal parquet file.
        parquet_file = tmp_path / "data.parquet"
        try:
            from tests.fixtures.pii_samples import generate_sample_parquet

            generate_sample_parquet(str(parquet_file), count=2)
        except ImportError:
            pytest.skip("pyarrow not installed")

        exit_code = main(
            [
                "scan",
                "--source",
                f"local://{parquet_file}",
                "--output",
                str(tmp_path / "output"),
                "--unsafe-passthrough",
            ]
        )
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not yet supported" in captured.err


# ── CLI parser ───────────────────────────────────────────────────────


class TestBuildParser:
    """Tests for the CLI argument parser construction."""

    def test_parser_has_scan_subcommand(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "scan",
                "--source",
                "local://test.jsonl",
                "--unsafe-passthrough",
            ]
        )
        assert args.command == "scan"
        assert args.source == "local://test.jsonl"
        assert args.unsafe_passthrough is True

    def test_parser_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["scan", "--source", "local://test.jsonl"])
        assert args.output == "./sanitized/"
        assert args.format_hint is None
        assert args.quarantine_dir is None
        assert args.unsafe_passthrough is False

    def test_no_command_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main([])
        assert exit_code == 0


# ── Format hint override ─────────────────────────────────────────────


class TestFormatHint:
    """Tests for the --format flag override."""

    def test_format_hint_overrides_detection(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Create a CSV file but give it a .txt extension.
        csv_file = tmp_path / "data.txt"
        generate_sample_csv(str(csv_file), count=3)

        exit_code = main(
            [
                "scan",
                "--source",
                f"local://{csv_file}",
                "--output",
                str(tmp_path / "output"),
                "--format",
                "csv",
                "--unsafe-passthrough",
            ]
        )
        assert exit_code == 0

        output_file = tmp_path / "output" / "data_sanitized.csv"
        assert output_file.exists()
