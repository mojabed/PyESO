"""Diagnostic reporter - formats and outputs lint results."""

from __future__ import annotations

import sys
from typing import TextIO

from pyeso.rules.base import Diagnostic, Severity


class Reporter:
    """Formats and outputs lint diagnostics."""

    def __init__(self, output: TextIO = sys.stdout, color: bool = True) -> None:
        self.output = output
        self.color = color and sys.stdout.isatty()

    def report(self, diagnostics: list[Diagnostic]) -> tuple[int, int, int]:
        """Output diagnostics and return counts of (errors, warnings, infos)."""
        errors = warnings = infos = 0

        # Sort by file, then line
        sorted_diags = sorted(diagnostics, key=lambda d: (d.file, d.line, d.column))

        for diag in sorted_diags:
            if diag.severity == Severity.ERROR:
                errors += 1
            elif diag.severity == Severity.WARNING:
                warnings += 1
            else:
                infos += 1

            self._print_diagnostic(diag)

        return errors, warnings, infos

    def print_summary(self, total_files: int, errors: int, warnings: int, infos: int) -> None:
        parts = []
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        if infos:
            parts.append(f"{infos} info(s)")

        if parts:
            msg = f"\n{total_files} file(s) scanned, " + ", ".join(parts)
        else:
            msg = f"\n{total_files} file(s) scanned, no issues found."

        if self.color:
            if errors:
                msg = f"\033[1;31m{msg}\033[0m"
            elif warnings:
                msg = f"\033[1;33m{msg}\033[0m"
            else:
                msg = f"\033[1;32m{msg}\033[0m"

        print(msg, file=self.output)

    def _print_diagnostic(self, diag: Diagnostic) -> None:
        severity_str = diag.severity.value.upper()
        if self.color:
            if diag.severity == Severity.ERROR:
                color = "\033[1;31m"  # bold red
            elif diag.severity == Severity.WARNING:
                color = "\033[1;33m"  # bold yellow
            else:
                color = "\033[1;36m"  # bold cyan
            reset = "\033[0m"
        else:
            color = reset = ""

        # Format: file:line:col [SEVERITY] CODE: message
        location = f"{diag.file}:{diag.line}"
        if diag.column:
            location += f":{diag.column}"

        print(
            f"{color}{location} [{severity_str}] {diag.code}:{reset} {diag.message}",
            file=self.output,
        )
