"""PyESO CLI - command-line interface for the ESO addon linter."""

from __future__ import annotations

import argparse
import pathlib
import sys

from pyeso import __version__
from pyeso.linter import ESOLinter
from pyeso.reporter import Reporter


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    if getattr(sys, "frozen", False):
        import io
        if isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout.reconfigure(line_buffering=True)  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(
        prog="pyeso",
        description="Static analysis and linting for Elder Scrolls Online addon LUA code.",
    )
    parser.add_argument(
        "paths", nargs="+",
        help="Addon .lua files or directories to lint.",
    )
    parser.add_argument(
        "--esoui", dest="esoui_dir", default=None,
        help="Path to ESOUI source directory for API extraction. "
             "If omitted, uses the built-in seed API database.",
    )
    parser.add_argument(
        "--no-color", action="store_true", default=False,
        help="Disable colored output.",
    )
    parser.add_argument(
        "--version", action="version", version=f"PyESO {__version__}",
    )
    parser.add_argument(
        "--stats", action="store_true", default=False,
        help="Print API database statistics before linting.",
    )

    args = parser.parse_args(argv)

    try:
        if args.esoui_dir:
            linter = ESOLinter(esoui_source_dir=args.esoui_dir)
        else:
            linter = ESOLinter()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.stats:
        db = linter.db
        print(f"API Database: {db.total_known} known names "
              f"({db.function_count} functions, {db.deprecated_count} deprecated)")
        print()

    all_diagnostics = linter.lint_paths(args.paths)

    # Count unique files scanned
    files_scanned: set[str] = set()
    for diag in all_diagnostics:
        if diag.file not in files_scanned and pathlib.Path(diag.file).exists():
            files_scanned.add(diag.file)
    # Also count files that produced no diagnostics
    for p in args.paths:
        path = pathlib.Path(p)
        if path.is_file():
            files_scanned.add(str(path))
        elif path.is_dir():
            for f in path.rglob("*.lua"):
                files_scanned.add(str(f))

    reporter = Reporter(color=not args.no_color)
    errors, warnings, infos = reporter.report(all_diagnostics)
    reporter.print_summary(len(files_scanned), errors, warnings, infos)

    return 1 if errors > 0 else 0
