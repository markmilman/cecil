"""The ``cecil scan`` CLI subcommand.

Wires up :class:`~cecil.core.providers.local_file.LocalFileProvider` to
read a local file, optionally sanitize its records (once the engine
exists), and write the output in the same format.

Since the Sanitization Engine is not yet available, the command requires
an explicit ``--unsafe-passthrough`` flag to acknowledge that records
will be streamed without sanitization.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

from cecil.core.providers.local_file import LocalFileProvider
from cecil.utils.errors import CecilError


logger = logging.getLogger(__name__)

# Formats that support output writing.
_WRITABLE_FORMATS = {"jsonl", "csv"}


def register_scan_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the ``scan`` subcommand with the CLI argument parser.

    Args:
        subparsers: The subparsers action from the parent
            :class:`argparse.ArgumentParser`.
    """
    parser = subparsers.add_parser(
        "scan",
        help="Scan a local file and write sanitized output.",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source URI (e.g. local://path/to/file.jsonl).",
    )
    parser.add_argument(
        "--output",
        default="./sanitized/",
        help="Output directory (default: ./sanitized/).",
    )
    parser.add_argument(
        "--format",
        dest="format_hint",
        default=None,
        help="Explicit format override (jsonl, csv, parquet).",
    )
    parser.add_argument(
        "--quarantine-dir",
        default=None,
        help="Directory for quarantine log files.",
    )
    parser.add_argument(
        "--unsafe-passthrough",
        action="store_true",
        default=False,
        help="Bypass sanitization engine (unsafe, for development only).",
    )
    parser.set_defaults(func=run_scan)


def _parse_source_uri(source: str) -> Path:
    """Extract a file path from a ``local://`` source URI.

    Args:
        source: The source URI string.

    Returns:
        The resolved file path.

    Raises:
        CecilError: If the URI scheme is not ``local://``.
    """
    prefix = "local://"
    if not source.startswith(prefix):
        raise CecilError(
            f"Unsupported source URI scheme: {source}. Expected '{prefix}<path>'.",
        )
    return Path(source[len(prefix) :])


def _resolve_output_path(source_path: Path, output_dir: str, fmt: str) -> Path:
    """Build the output file path from the source name and format.

    Creates the output directory if it does not exist.

    Args:
        source_path: Original source file path.
        output_dir: Target output directory.
        fmt: The detected file format.

    Returns:
        The resolved output file path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ext = ".jsonl" if fmt == "jsonl" else f".{fmt}"
    return out / f"{source_path.stem}_sanitized{ext}"


def _write_jsonl(records: Any, output_path: Path) -> int:
    """Write records to a JSONL file incrementally.

    Args:
        records: An iterable of dictionaries to write.
        output_path: Path for the output file.

    Returns:
        The number of records written.
    """
    count = 0
    with open(output_path, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")
            count += 1
    return count


def _write_csv(records: Any, output_path: Path) -> int:
    """Write records to a CSV file incrementally.

    Peeks at the first record to determine column headers, then writes
    all records including the first.

    Args:
        records: An iterable of dictionaries to write.
        output_path: Path for the output file.

    Returns:
        The number of records written.
    """
    count = 0
    writer: csv.DictWriter[str] | None = None
    fh = open(output_path, "w", newline="", encoding="utf-8")  # noqa: SIM115
    try:
        for record in records:
            if writer is None:
                fieldnames = list(record.keys())
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
            writer.writerow(record)
            count += 1
    finally:
        fh.close()
    return count


def run_scan(args: argparse.Namespace) -> int:
    """Execute the scan subcommand.

    Args:
        args: Parsed CLI arguments from :mod:`argparse`.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Gate behind --unsafe-passthrough until the sanitization engine is wired.
    if not args.unsafe_passthrough:
        sys.stderr.write(
            "Error: Sanitization engine not yet available. "
            "Use --unsafe-passthrough to bypass (unsafe, for development only).\n",
        )
        return 1

    logger.warning(
        "Running in pass-through mode -- records are NOT sanitized. Do not use on sensitive data.",
    )

    try:
        source_path = _parse_source_uri(args.source)
    except CecilError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1

    # Build provider kwargs.
    provider_kwargs: dict[str, Any] = {"file_path": source_path}
    if args.format_hint is not None:
        provider_kwargs["format_hint"] = args.format_hint

    if args.quarantine_dir is not None:
        q_dir = Path(args.quarantine_dir)
        q_dir.mkdir(parents=True, exist_ok=True)
        provider_kwargs["quarantine_path"] = q_dir / f"{source_path.stem}_quarantine.jsonl"

    try:
        provider = LocalFileProvider(**provider_kwargs)
    except CecilError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1

    try:
        with provider:
            fmt = provider.format

            if fmt not in _WRITABLE_FORMATS:
                sys.stderr.write(
                    f"Error: Output writing for '{fmt}' format is not yet supported. "
                    f"Supported: {', '.join(sorted(_WRITABLE_FORMATS))}.\n",
                )
                return 1

            output_path = _resolve_output_path(source_path, args.output, fmt)

            # TODO(#65): Wire sanitization engine -- pass-through mode is temporary
            records = provider.stream_records()

            if fmt == "jsonl":
                count = _write_jsonl(records, output_path)
            else:
                count = _write_csv(records, output_path)

            metadata = provider.fetch_metadata()

    except CecilError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1

    logger.info(
        "Scan complete",
        extra={
            "records_written": count,
            "output_path": str(output_path),
            "records_quarantined": metadata.get("records_quarantined", 0),
        },
    )

    sys.stdout.write(
        f"Sanitized data saved to {output_path} ({count} records).\n",
    )

    return 0
