"""Cecil CLI entry point.

Provides the top-level argument parser with subcommand dispatch.
"""

from __future__ import annotations

import argparse
import logging
import sys

from cecil.cli.scan import register_scan_parser


logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser.

    Returns:
        The configured :class:`argparse.ArgumentParser` with all
        subcommands registered.
    """
    parser = argparse.ArgumentParser(
        prog="cecil",
        description="Cecil Data Sanitizer & Cost Optimizer",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG) logging.",
    )

    subparsers = parser.add_subparsers(dest="command")
    register_scan_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Cecil CLI.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging level.
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )

    if args.command is None:
        parser.print_help()
        return 0

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0

    return func(args)  # type: ignore[no-any-return]


if __name__ == "__main__":
    sys.exit(main())
